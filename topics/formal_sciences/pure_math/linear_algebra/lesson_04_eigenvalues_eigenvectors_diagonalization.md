# Lesson 4: Eigenvalues, Eigenvectors, Diagonalization

## 1. First-Principles Intuition & Invariants

The theory of eigenvalues and eigenvectors represents one of the most penetrating insights in all of linear algebra: that within the bewildering complexity of an arbitrary linear transformation, there exist distinguished directions that the transformation leaves invariant, merely scaling them rather than rotating or shearing. This fundamental observation transforms the study of linear operators from the general chaos of matrix multiplication into the tractable realm of diagonal matrices, where each basis vector is scaled independently.

Consider a linear transformation $T: V \to V$ on a finite-dimensional vector space $V$ over a field $\mathbb{F}$. The transformation $T$ acts upon vectors in $V$, generally producing outputs that bear little obvious relationship to the inputs. Yet for certain special vectors $\mathbf{v} \in V$ with $\mathbf{v} \neq \mathbf{0}$, the transformation simplifies dramatically: $T(\mathbf{v}) = \lambda \mathbf{v}$ for some scalar $\lambda \in \mathbb{F}$. Such a vector $\mathbf{v}$ is called an **eigenvector** corresponding to the **eigenvalue** $\lambda$. The German prefix "eigen" meaning "characteristic" or "inherent" captures the essence perfectly: these vectors reveal the intrinsic directional structure of the transformation itself.

The existence of eigenvectors depends critically on the underlying field. Over algebraically closed fields like $\mathbb{C}$, every linear operator on a finite-dimensional space possesses at least one eigenvalue, guaranteed by the Fundamental Theorem of Algebra. Over $\mathbb{R}$, this fails spectacularly: the rotation matrix $\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$ representing counterclockwise rotation by ninety degrees has no real eigenvectors, since no nonzero real vector is merely scaled by this transformation. Yet over $\mathbb{C}$, this same matrix admits eigenvalues $i$ and $-i$ with corresponding eigenvectors that spiral through the complex plane.

The problem of computing eigenvalues reduces to a polynomial equation. If $T(\mathbf{v}) = \lambda \mathbf{v}$, then $(T - \lambda I)(\mathbf{v}) = \mathbf{0}$ where $I$ denotes the identity operator. This homogeneous linear system admits nontrivial solutions if and only if the operator $T - \lambda I$ fails to be invertible, which occurs precisely when $\det(T - \lambda I) = 0$. For a matrix representation $A$ of $T$, this determinant condition becomes $\det(A - \lambda I) = 0$, yielding the **characteristic polynomial** $p_A(\lambda) = \det(\lambda I - A)$, a monic polynomial of degree $n = \dim(V)$. The roots of this characteristic polynomial are precisely the eigenvalues of $A$.

The characteristic polynomial encodes profound structural information. By the Fundamental Theorem of Algebra applied over $\mathbb{C}$, we can factor $p_A(\lambda) = (\lambda - \lambda_1)^{m_1}(\lambda - \lambda_2)^{m_2} \cdots (\lambda - \lambda_k)^{m_k}$ where $\lambda_1, \ldots, \lambda_k$ are the distinct eigenvalues and $m_1 + m_2 + \cdots + m_k = n$. The exponent $m_i$ is called the **algebraic multiplicity** of eigenvalue $\lambda_i$, representing how many times that root appears in the characteristic polynomial. This algebraic quantity must be distinguished from the **geometric multiplicity**, defined as $\dim(\ker(A - \lambda_i I))$, the dimension of the eigenspace corresponding to $\lambda_i$. The geometric multiplicity counts the maximum number of linearly independent eigenvectors sharing the same eigenvalue.

A fundamental inequality governs these multiplicities: for every eigenvalue $\lambda$, we have $1 \le \text{geometric multiplicity} \le \text{algebraic multiplicity}$. The lower bound holds because eigenvalues must possess at least one eigenvector by definition. The upper bound follows from the fact that the eigenspace $\ker(A - \lambda I)$ contributes at most $\lambda$'s algebraic multiplicity to the dimension count. When geometric and algebraic multiplicities coincide for all eigenvalues, the matrix enjoys special structural properties that permit diagonalization.

A matrix $A \in \mathbb{F}^{n \times n}$ is **diagonalizable** if there exists an invertible matrix $P$ and a diagonal matrix $D$ such that $A = PDP^{-1}$. Equivalently, $A$ is diagonalizable if and only if $\mathbb{F}^n$ admits a basis consisting entirely of eigenvectors of $A$. The columns of $P$ in the factorization $A = PDP^{-1}$ are precisely these eigenvector basis elements, while the diagonal entries of $D$ are the corresponding eigenvalues. This factorization transforms the action of $A$ into a change of basis to the eigenvector coordinate system, scaling by eigenvalues, then changing back to the original coordinates.

The **Diagonalizability Criterion** states that $A$ is diagonalizable if and only if the geometric multiplicity equals the algebraic multiplicity for every eigenvalue. When this equality holds, the eigenspaces collectively span the entire space $\mathbb{F}^n$, providing the requisite basis of eigenvectors. Conversely, when geometric multiplicity falls short of algebraic multiplicity for some eigenvalue, the eigenspaces fail to span, and diagonalization becomes impossible. Such matrices are called **defective**, and they require the more sophisticated Jordan canonical form for complete structural analysis.

Several sufficient conditions guarantee diagonalizability without computing multiplicities explicitly. If $A$ possesses $n$ distinct eigenvalues, then $A$ is automatically diagonalizable, since eigenvectors corresponding to distinct eigenvalues are always linearly independent. Symmetric matrices over $\mathbb{R}$ (satisfying $A^T = A$) are always diagonalizable with real eigenvalues, a cornerstone result known as the **Spectral Theorem for Real Symmetric Matrices**. More generally, normal matrices over $\mathbb{C}$ (satisfying $A^*A = AA^*$ where $A^*$ denotes the conjugate transpose) are diagonalizable by unitary matrices, meaning $A = UDU^*$ where $U^*U = I$.

The Spectral Theorem extends far beyond finite-dimensional linear algebra, forming the foundation for functional analysis and quantum mechanics. In infinite-dimensional Hilbert spaces, self-adjoint operators admit spectral decompositions that generalize eigenvalue expansions, permitting the rigorous mathematical treatment of observable physical quantities. The position and momentum operators of quantum mechanics, despite being unbounded operators on infinite-dimensional spaces, possess spectral decompositions that directly correspond to the possible measurement outcomes and their associated quantum states.

## 2. Core Architecture & Mechanics

The computational architecture for eigenvalue and eigenvector analysis proceeds through several distinct phases: characteristic polynomial construction, root finding, eigenspace computation, and diagonalization verification. Each phase presents unique algebraic challenges and opportunities for optimization.

### Characteristic Polynomial Construction

Given a matrix $A \in \mathbb{F}^{n \times n}$, we construct the characteristic polynomial $p_A(\lambda) = \det(\lambda I - A)$. For small $n$, direct determinant expansion via cofactor recursion suffices. Consider the $3 \times 3$ matrix

$$A = \begin{pmatrix} 4 & 1 & 0 \\ 1 & 4 & 1 \\ 0 & 1 & 4 \end{pmatrix}.$$

The characteristic matrix is

$$\lambda I - A = \begin{pmatrix} \lambda - 4 & -1 & 0 \\ -1 & \lambda - 4 & -1 \\ 0 & -1 & \lambda - 4 \end{pmatrix}.$$

Expanding along the first row yields

$$\det(\lambda I - A) = (\lambda - 4) \det\begin{pmatrix} \lambda - 4 & -1 \\ -1 & \lambda - 4 \end{pmatrix} - (-1) \det\begin{pmatrix} -1 & -1 \\ 0 & \lambda - 4 \end{pmatrix}.$$

The first $2 \times 2$ determinant evaluates to $(\lambda - 4)^2 - 1 = \lambda^2 - 8\lambda + 15$. The second determinant gives $-(\lambda - 4)$. Combining these:

$$p_A(\lambda) = (\lambda - 4)(\lambda^2 - 8\lambda + 15) - (\lambda - 4) = (\lambda - 4)(\lambda^2 - 8\lambda + 15 - 1) = (\lambda - 4)(\lambda^2 - 8\lambda + 14).$$

We can factor further: $\lambda^2 - 8\lambda + 14 = (\lambda - 4)^2 - 2$, so

$$p_A(\lambda) = (\lambda - 4)[(\lambda - 4)^2 - 2] = (\lambda - 4)^3 - 2(\lambda - 4).$$

Setting $u = \lambda - 4$ gives $u^3 - 2u = u(u^2 - 2) = u(u - \sqrt{2})(u + \sqrt{2})$. Thus the eigenvalues are $\lambda_1 = 4$, $\lambda_2 = 4 + \sqrt{2}$, and $\lambda_3 = 4 - \sqrt{2}$, all with algebraic multiplicity one.

For larger matrices, direct determinant computation becomes prohibitively expensive, scaling as $O(n!)$ via naive cofactor expansion. The adjoint method reduces this to $O(n^4)$ when combined with Gaussian elimination for subdeterminants, but practical eigenvalue algorithms avoid explicit characteristic polynomial construction entirely, employing instead iterative methods like QR decomposition or power iteration.

### Eigenspace Computation and Geometric Multiplicity

Once eigenvalues are known, we compute eigenspaces via null space analysis. For eigenvalue $\lambda_i$, the eigenspace is $E_{\lambda_i} = \ker(A - \lambda_i I)$. This requires solving the homogeneous system $(A - \lambda_i I)\mathbf{x} = \mathbf{0}$ via Gaussian elimination to row-reduced echelon form.

Continuing the previous example with $\lambda_1 = 4$:

$$A - 4I = \begin{pmatrix} 0 & 1 & 0 \\ 1 & 0 & 1 \\ 0 & 1 & 0 \end{pmatrix}.$$

Row reduction proceeds by swapping rows one and two:

$$\begin{pmatrix} 1 & 0 & 1 \\ 0 & 1 & 0 \\ 0 & 1 & 0 \end{pmatrix} \to \begin{pmatrix} 1 & 0 & 1 \\ 0 & 1 & 0 \\ 0 & 0 & 0 \end{pmatrix}.$$

The reduced system gives $x_1 + x_3 = 0$ and $x_2 = 0$, so $x_3$ is free and $\mathbf{x} = x_3 \begin{pmatrix} -1 \\ 0 \\ 1 \end{pmatrix}$. Thus $E_4 = \text{span}\left\{\begin{pmatrix} -1 \\ 0 \\ 1 \end{pmatrix}\right\}$ has dimension one, matching the algebraic multiplicity.

For $\lambda_2 = 4 + \sqrt{2}$, we compute

$$A - (4 + \sqrt{2})I = \begin{pmatrix} -\sqrt{2} & 1 & 0 \\ 1 & -\sqrt{2} & 1 \\ 0 & 1 & -\sqrt{2} \end{pmatrix}.$$

Row reducing this system yields a single free variable, confirming geometric multiplicity one. Similarly for $\lambda_3 = 4 - \sqrt{2}$. Since all three eigenvalues have algebraic and geometric multiplicity equal to one, and $1 + 1 + 1 = 3 = \dim(\mathbb{R}^3)$, the matrix $A$ is diagonalizable.

### Diagonalization Protocol

The diagonalization factorization $A = PDP^{-1}$ assembles as follows. The columns of $P$ are linearly independent eigenvectors, one for each dimension. The diagonal matrix $D$ contains corresponding eigenvalues in the same column order. For our tridiagonal example, if $\mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3$ are eigenvectors for $\lambda_1, \lambda_2, \lambda_3$ respectively, then

$$P = \begin{pmatrix} | & | & | \\ \mathbf{v}_1 & \mathbf{v}_2 & \mathbf{v}_3 \\ | & | & | \end{pmatrix}, \quad D = \begin{pmatrix} \lambda_1 & 0 & 0 \\ 0 & \lambda_2 & 0 \\ 0 & 0 & \lambda_3 \end{pmatrix}.$$

To verify diagonalization, compute $AP = PD$ by checking that $A\mathbf{v}_i = \lambda_i \mathbf{v}_i$ for each column. If $P$ is invertible (guaranteed when eigenvectors are linearly independent), then multiplication by $P^{-1}$ on the right yields $A = PDP^{-1}$.

The power of diagonalization manifests in computing matrix powers and exponentials. If $A = PDP^{-1}$, then

$$A^k = (PDP^{-1})(PDP^{-1}) \cdots (PDP^{-1}) = PD^k P^{-1}$$

since the interior $P^{-1}P$ factors cancel. The diagonal matrix $D^k$ is trivial to compute: simply raise each diagonal entry to the $k$-th power. This reduces an $O(n^3)$ matrix multiplication repeated $k$ times to a single diagonalization cost plus $O(n)$ scalar exponentiations.

For the matrix exponential $e^{At} = \sum_{k=0}^{\infty} \frac{(At)^k}{k!}$ arising in differential equations, diagonalization gives

$$e^{At} = P e^{Dt} P^{-1} = P \begin{pmatrix} e^{\lambda_1 t} & 0 & \cdots & 0 \\ 0 & e^{\lambda_2 t} & \cdots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \cdots & e^{\lambda_n t} \end{pmatrix} P^{-1}.$$

This exponential matrix provides the fundamental solution to the linear system $\frac{d\mathbf{x}}{dt} = A\mathbf{x}$, yielding $\mathbf{x}(t) = e^{At}\mathbf{x}(0)$.

### Defective Matrices and Jordan Form

When geometric multiplicity falls short of algebraic multiplicity, diagonalization fails but a near-diagonal structure remains attainable. The **Jordan canonical form** organizes the matrix into Jordan blocks:

$$J = \begin{pmatrix} J_1 & 0 & \cdots & 0 \\ 0 & J_2 & \cdots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \cdots & J_k \end{pmatrix}$$

where each Jordan block $J_i$ has the form

$$J_i = \begin{pmatrix} \lambda_i & 1 & 0 & \cdots & 0 \\ 0 & \lambda_i & 1 & \cdots & 0 \\ \vdots & \vdots & \ddots & \ddots & \vdots \\ 0 & 0 & 0 & \lambda_i & 1 \\ 0 & 0 & 0 & 0 & \lambda_i \end{pmatrix}.$$

Consider the $3 \times 3$ nilpotent matrix

$$N = \begin{pmatrix} 0 & 1 & 0 \\ 0 & 0 & 1 \\ 0 & 0 & 0 \end{pmatrix}.$$

The characteristic polynomial is $p_N(\lambda) = \lambda^3$, so the only eigenvalue is $\lambda = 0$ with algebraic multiplicity three. Computing the null space $\ker(N)$:

$$N\mathbf{x} = \mathbf{0} \implies \begin{pmatrix} 0 & 1 & 0 \\ 0 & 0 & 1 \\ 0 & 0 & 0 \end{pmatrix} \begin{pmatrix} x_1 \\ x_2 \\ x_3 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix}.$$

This forces $x_2 = x_3 = 0$ with $x_1$ free, so $\ker(N) = \text{span}\left\{\begin{pmatrix} 1 \\ 0 \\ 0 \end{pmatrix}\right\}$ has dimension one. The geometric multiplicity is one while the algebraic multiplicity is three, a clear mismatch preventing diagonalization. The Jordan form is $N$ itself, already a single $3 \times 3$ Jordan block.

To compute generalized eigenvectors forming the Jordan chain, solve $(N - \lambda I)^k \mathbf{v} = \mathbf{0}$ for increasing $k$ until the null space stabilizes. For $N$ with $\lambda = 0$, we need $N^2 \mathbf{v}_2 = \mathbf{0}$ and $N\mathbf{v}_2 \neq \mathbf{0}$, giving $\mathbf{v}_2 = \begin{pmatrix} 0 \\ 1 \\ 0 \end{pmatrix}$. Then $N^3 \mathbf{v}_3 = \mathbf{0}$ and $N^2 \mathbf{v}_3 \neq \mathbf{0}$ yields $\mathbf{v}_3 = \begin{pmatrix} 0 \\ 0 \\ 1 \end{pmatrix}$. The matrix $P = \begin{pmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{pmatrix} = I$ leaves $N$ unchanged, confirming Jordan form.

### Spectral Theorem for Symmetric Matrices

Real symmetric matrices possess exceptional spectral properties. **The Spectral Theorem** states that every real symmetric matrix $A$ is orthogonally diagonalizable: there exists an orthogonal matrix $Q$ (satisfying $Q^T Q = I$) and a diagonal matrix $D$ with real entries such that $A = QDQ^T$. The columns of $Q$ form an orthonormal basis of eigenvectors, and the diagonal entries of $D$ are the corresponding real eigenvalues.

The proof proceeds through several stages. First, we establish that all eigenvalues of a real symmetric matrix are real. Suppose $\lambda$ is an eigenvalue with eigenvector $\mathbf{v}$, potentially complex. Then $A\mathbf{v} = \lambda \mathbf{v}$. Taking the conjugate transpose: $\mathbf{v}^* A^T = \bar{\lambda} \mathbf{v}^*$. Since $A^T = A$ for symmetric matrices, we have $\mathbf{v}^* A = \bar{\lambda} \mathbf{v}^*$. Multiplying the first equation by $\mathbf{v}^*$ on the left and the second by $\mathbf{v}$ on the right:

$$\mathbf{v}^* A \mathbf{v} = \lambda \mathbf{v}^* \mathbf{v}, \quad \mathbf{v}^* A \mathbf{v} = \bar{\lambda} \mathbf{v}^* \mathbf{v}.$$

Since $\mathbf{v} \neq \mathbf{0}$, we have $\mathbf{v}^* \mathbf{v} > 0$, implying $\lambda = \bar{\lambda}$, so $\lambda$ is real.

Next, eigenvectors corresponding to distinct eigenvalues are orthogonal. Suppose $A\mathbf{v}_1 = \lambda_1 \mathbf{v}_1$ and $A\mathbf{v}_2 = \lambda_2 \mathbf{v}_2$ with $\lambda_1 \neq \lambda_2$. Then

$$\lambda_1 \mathbf{v}_1^T \mathbf{v}_2 = (A\mathbf{v}_1)^T \mathbf{v}_2 = \mathbf{v}_1^T A^T \mathbf{v}_2 = \mathbf{v}_1^T A \mathbf{v}_2 = \mathbf{v}_1^T (\lambda_2 \mathbf{v}_2) = \lambda_2 \mathbf{v}_1^T \mathbf{v}_2.$$

Thus $(\lambda_1 - \lambda_2) \mathbf{v}_1^T \mathbf{v}_2 = 0$. Since $\lambda_1 \neq \lambda_2$, we conclude $\mathbf{v}_1^T \mathbf{v}_2 = 0$.

The final step uses induction on dimension. For $n = 1$, the result is trivial. Assume the theorem holds for $(n-1) \times (n-1)$ symmetric matrices. Given $n \times n$ symmetric $A$, choose an eigenvalue $\lambda_1$ and corresponding unit eigenvector $\mathbf{q}_1$. Let $Q_1 = [\mathbf{q}_1 \mid Q_1']$ where columns of $Q_1'$ form an orthonormal basis for $\mathbf{q}_1^{\perp}$. Then $Q_1$ is orthogonal and

$$Q_1^T A Q_1 = \begin{pmatrix} \lambda_1 & \mathbf{w}^T \\ \mathbf{w} & B \end{pmatrix}$$

where $B$ is $(n-1) \times (n-1)$. Symmetry forces $\mathbf{w} = \mathbf{0}$: the $(1, j)$ entry equals the $(j, 1)$ entry, but $(Q_1^T A Q_1)_{1j} = \mathbf{q}_1^T A (\text{column } j \text{ of } Q_1') = \lambda_1 \mathbf{q}_1^T (\text{column } j \text{ of } Q_1') = 0$ by orthogonality. Thus

$$Q_1^T A Q_1 = \begin{pmatrix} \lambda_1 & \mathbf{0}^T \\ \mathbf{0} & B \end{pmatrix}.$$

The matrix $B$ is symmetric since $Q_1^T A Q_1$ is symmetric. By induction, $B = Q_2 D' Q_2^T$ for orthogonal $(n-1) \times (n-1)$ matrix $Q_2$. Define

$$Q = Q_1 \begin{pmatrix} 1 & \mathbf{0}^T \\ \mathbf{0} & Q_2 \end{pmatrix}.$$

Then $Q$ is orthogonal and

$$Q^T A Q = \begin{pmatrix} 1 & \mathbf{0}^T \\ \mathbf{0} & Q_2^T \end{pmatrix} \begin{pmatrix} \lambda_1 & \mathbf{0}^T \\ \mathbf{0} & B \end{pmatrix} \begin{pmatrix} 1 & \mathbf{0}^T \\ \mathbf{0} & Q_2 \end{pmatrix} = \begin{pmatrix} \lambda_1 & \mathbf{0}^T \\ \mathbf{0} & D' \end{pmatrix} = D.$$

This completes the inductive proof of the Spectral Theorem.

### Dynamical Systems and Stability Analysis

The eigenvalue spectrum governs the long-term behavior of discrete-time dynamical systems $\mathbf{x}_{k+1} = A\mathbf{x}_k$ and continuous-time systems $\frac{d\mathbf{x}}{dt} = A\mathbf{x}$. For diagonalizable $A = PDP^{-1}$, the discrete system iterates as

$$\mathbf{x}_k = A^k \mathbf{x}_0 = P D^k P^{-1} \mathbf{x}_0.$$

Writing $\mathbf{x}_0 = c_1 \mathbf{v}_1 + \cdots + c_n \mathbf{v}_n$ in the eigenvector basis yields

$$\mathbf{x}_k = c_1 \lambda_1^k \mathbf{v}_1 + c_2 \lambda_2^k \mathbf{v}_2 + \cdots + c_n \lambda_n^k \mathbf{v}_n.$$

The eigenvalue with largest absolute value dominates asymptotically. If $|\lambda_1| > |\lambda_i|$ for all $i > 1$, then $\mathbf{x}_k \sim c_1 \lambda_1^k \mathbf{v}_1$ as $k \to \infty$ provided $c_1 \neq 0$. The system converges to the origin if and only if $|\lambda_i| < 1$ for all $i$, explodes if any $|\lambda_i| > 1$, and exhibits periodic or quasiperiodic behavior if eigenvalues lie on the unit circle.

For continuous systems $\frac{d\mathbf{x}}{dt} = A\mathbf{x}$, the solution is $\mathbf{x}(t) = e^{At} \mathbf{x}_0 = P e^{Dt} P^{-1} \mathbf{x}_0$, giving

$$\mathbf{x}(t) = c_1 e^{\lambda_1 t} \mathbf{v}_1 + c_2 e^{\lambda_2 t} \mathbf{v}_2 + \cdots + c_n e^{\lambda_n t} \mathbf{v}_n.$$

Stability requires $\text{Re}(\lambda_i) < 0$ for all eigenvalues. If any eigenvalue has positive real part, solutions grow exponentially. Pure imaginary eigenvalues produce oscillations without growth or decay.

Consider the coupled oscillator system described by

$$\frac{d}{dt} \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} = \begin{pmatrix} -2 & 1 \\ 1 & -2 \end{pmatrix} \begin{pmatrix} x_1 \\ x_2 \end{pmatrix}.$$

The characteristic polynomial is $\det(\lambda I - A) = (\lambda + 2)^2 - 1 = \lambda^2 + 4\lambda + 3 = (\lambda + 1)(\lambda + 3)$, yielding eigenvalues $\lambda_1 = -1$ and $\lambda_2 = -3$, both negative. For $\lambda_1 = -1$:

$$(A + I)\mathbf{v} = \begin{pmatrix} -1 & 1 \\ 1 & -1 \end{pmatrix} \mathbf{v} = \mathbf{0} \implies \mathbf{v}_1 = \begin{pmatrix} 1 \\ 1 \end{pmatrix}.$$

For $\lambda_2 = -3$:

$$(A + 3I)\mathbf{v} = \begin{pmatrix} 1 & 1 \\ 1 & 1 \end{pmatrix} \mathbf{v} = \mathbf{0} \implies \mathbf{v}_2 = \begin{pmatrix} 1 \\ -1 \end{pmatrix}.$$

The general solution is

$$\begin{pmatrix} x_1(t) \\ x_2(t) \end{pmatrix} = c_1 e^{-t} \begin{pmatrix} 1 \\ 1 \end{pmatrix} + c_2 e^{-3t} \begin{pmatrix} 1 \\ -1 \end{pmatrix}.$$

Both modes decay exponentially, with the $\lambda_2 = -3$ mode decaying three times faster than the $\lambda_1 = -1$ mode. As $t \to \infty$, the solution approaches the origin, confirming asymptotic stability.

## 3. High-Performance Optimization & Failure Modes

Computational eigenvalue analysis presents formidable numerical challenges. Direct characteristic polynomial methods fail for large matrices due to catastrophic cancellation in polynomial root finding and the exponential cost of determinant computation. Modern eigenvalue algorithms bypass characteristic polynomials entirely, employing iterative techniques that converge to eigenvalues without explicit polynomial construction.

### Power Iteration and Dominant Eigenvalue Extraction

The **power method** computes the dominant eigenvalue (largest in absolute value) through repeated matrix-vector multiplication. Starting from a random initial vector $\mathbf{x}_0$, iterate

$$\mathbf{x}_{k+1} = \frac{A\mathbf{x}_k}{\|A\mathbf{x}_k\|}.$$

If $A$ is diagonalizable with eigenvalues satisfying $|\lambda_1| > |\lambda_2| \ge \cdots \ge |\lambda_n|$, then $\mathbf{x}_k \to \pm \mathbf{v}_1$ where $\mathbf{v}_1$ is the dominant eigenvector. The eigenvalue is recovered via the **Rayleigh quotient**:

$$\lambda_1 \approx \frac{\mathbf{x}_k^T A \mathbf{x}_k}{\mathbf{x}_k^T \mathbf{x}_k}.$$

Convergence rate depends on the ratio $|\lambda_2 / \lambda_1|$. When eigenvalues are well-separated, convergence is rapid; when they cluster, convergence stalls. The iteration count scales as $O(\log(\epsilon) / \log(|\lambda_2 / \lambda_1|))$ to achieve error $\epsilon$.

For symmetric matrices, the **Rayleigh quotient iteration** accelerates convergence through adaptive shifting. At each step, compute the Rayleigh quotient $\mu_k = \frac{\mathbf{x}_k^T A \mathbf{x}_k}{\mathbf{x}_k^T \mathbf{x}_k}$, then solve

$$(A - \mu_k I)\mathbf{y}_{k+1} = \mathbf{x}_k, \quad \mathbf{x}_{k+1} = \frac{\mathbf{y}_{k+1}}{\|\mathbf{y}_{k+1}\|}.$$

This achieves cubic convergence near an eigenvalue, a dramatic improvement over the linear convergence of standard power iteration. However, each iteration requires solving a linear system, increasing per-iteration cost.

### QR Algorithm and Complete Spectrum Computation

The **QR algorithm** computes all eigenvalues simultaneously through a sequence of orthogonal similarity transformations. Initialize $A_0 = A$, then iterate:

1. Compute the QR factorization $A_k = Q_k R_k$ where $Q_k$ is orthogonal and $R_k$ is upper triangular.
2. Form $A_{k+1} = R_k Q_k = Q_k^T A_k Q_k$.

Since $A_{k+1}$ is similar to $A_k$, all $A_k$ share the same eigenvalues. Under mild conditions, the sequence $A_k$ converges to a quasi-triangular form (block upper triangular with $1 \times 1$ and $2 \times 2$ diagonal blocks), from which eigenvalues are immediately readable.

For symmetric matrices, $A_k$ converges to a diagonal matrix, with convergence accelerated by preliminary reduction to tridiagonal form via Householder reflections. The tridiagonal QR algorithm achieves $O(n^2)$ cost per iteration, making it practical for matrices of dimension several thousand.

Shifted variants improve convergence dramatically. The **shifted QR iteration** uses

$$A_k - \sigma_k I = Q_k R_k, \quad A_{k+1} = R_k Q_k + \sigma_k I$$

where the shift $\sigma_k$ is chosen to approximate an eigenvalue, typically the $(n,n)$ entry of $A_k$ for deflation. With optimal shifting strategies like the Wilkinson shift, convergence becomes cubic near eigenvalues.

### Krylov Subspace Methods for Large Sparse Matrices

When $A$ is large and sparse, forming full factorizations becomes impractical. **Krylov subspace methods** compute a few eigenvalues without dense matrix storage by operating within the subspace

$$\mathcal{K}_m(A, \mathbf{v}) = \text{span}\{\mathbf{v}, A\mathbf{v}, A^2\mathbf{v}, \ldots, A^{m-1}\mathbf{v}\}.$$

The **Lanczos algorithm** for symmetric matrices constructs an orthonormal basis $\{\mathbf{q}_1, \mathbf{q}_2, \ldots, \mathbf{q}_m\}$ for $\mathcal{K}_m(A, \mathbf{v})$ such that $Q_m^T A Q_m = T_m$ is tridiagonal. The eigenvalues of the small $m \times m$ tridiagonal matrix $T_m$ approximate eigenvalues of $A$, with extremal eigenvalues converging rapidly.

For non-symmetric matrices, the **Arnoldi iteration** produces an orthonormal basis such that $Q_m^T A Q_m = H_m$ is upper Hessenberg (zeros below the first subdiagonal). The eigenvalues of $H_m$ provide Ritz approximations to eigenvalues of $A$.

These methods enable eigenvalue computation for matrices of dimension $10^6$ or larger when only a few eigenvalues are needed, particularly extremal or interior eigenvalues near a specified shift. Restart strategies like implicitly restarted Arnoldi prevent basis size from growing indefinitely while preserving convergence.

### Numerical Stability and Conditioning

Eigenvalue computation is inherently ill-conditioned for non-normal matrices. The **condition number** of eigenvalue $\lambda$ with right eigenvector $\mathbf{v}$ and left eigenvector $\mathbf{w}$ (satisfying $\mathbf{w}^T A = \lambda \mathbf{w}^T$) is

$$\kappa(\lambda) = \frac{1}{|\mathbf{w}^T \mathbf{v}| / (\|\mathbf{w}\| \|\mathbf{v}\|)}.$$

For normal matrices ($A^*A = AA^*$), all eigenvalues have condition number one. For defective matrices with near-coalescing eigenvalues, condition numbers become astronomically large, meaning tiny perturbations in matrix entries produce enormous eigenvalue shifts.

The Jordan form highlights this instability. Consider the $n \times n$ Jordan block with eigenvalue zero:

$$J = \begin{pmatrix} 0 & 1 & 0 & \cdots & 0 \\ 0 & 0 & 1 & \cdots & 0 \\ \vdots & \vdots & \ddots & \ddots & \vdots \\ 0 & 0 & 0 & 0 & 1 \\ 0 & 0 & 0 & 0 & 0 \end{pmatrix}.$$

Perturbing the $(n,1)$ entry by $\epsilon$ gives eigenvalues $\epsilon^{1/n} e^{2\pi i k / n}$ for $k = 0, 1, \ldots, n-1$, an $O(\epsilon^{1/n})$ shift. For $n = 20$ and $\epsilon = 10^{-16}$ (machine precision), eigenvalues shift by $10^{-16/20} \approx 10^{-0.8} \approx 0.16$, a macroscopic error. This exponential amplification of errors renders eigenvalue computation for severely non-normal matrices fundamentally unreliable without extended precision arithmetic.

### Failure Mode: Repeated Eigenvalues with Deficiency

The most catastrophic failure mode arises when algebraic and geometric multiplicities diverge. Attempting to diagonalize a defective matrix produces numerical algorithms that fail to converge or converge to spurious results. Consider the family of matrices

$$A_\epsilon = \begin{pmatrix} 1 & 1 \\ \epsilon & 1 \end{pmatrix}.$$

For $\epsilon \neq 0$, the characteristic polynomial is $(\lambda - 1)^2 - \epsilon = 0$, yielding distinct eigenvalues $\lambda = 1 \pm \sqrt{\epsilon}$. As $\epsilon \to 0$, these eigenvalues coalesce to the repeated eigenvalue $\lambda = 1$. At $\epsilon = 0$:

$$A_0 = \begin{pmatrix} 1 & 1 \\ 0 & 1 \end{pmatrix}$$

has characteristic polynomial $(\lambda - 1)^2$ with repeated eigenvalue $\lambda = 1$. The eigenspace is

$$(A_0 - I)\mathbf{v} = \begin{pmatrix} 0 & 1 \\ 0 & 0 \end{pmatrix} \mathbf{v} = \mathbf{0} \implies \mathbf{v} = \begin{pmatrix} 1 \\ 0 \end{pmatrix},$$

giving geometric multiplicity one against algebraic multiplicity two. The matrix $A_0$ is defective and non-diagonalizable.

Numerical eigenvalue algorithms applied to $A_0$ may report two eigenvalues near $\lambda = 1$ with wildly different eigenvectors due to roundoff error introducing effective $\epsilon \neq 0$ perturbations. The computed eigenvector matrix $P$ becomes nearly singular, producing enormous errors in the computed diagonalization $A \approx P D P^{-1}$ as $\text{cond}(P) \to \infty$.

The resolution is recognizing defectiveness and computing the Jordan form instead. Alternatively, for applications requiring only spectral information rather than eigenvector bases, the **Schur decomposition** $A = QTQ^*$ with $Q$ unitary and $T$ upper triangular provides a numerically stable alternative. The eigenvalues appear on the diagonal of $T$, and the decomposition exists for all matrices without requiring diagonalizability.

### Exploiting Structure: Symmetric, Hermitian, and Tridiagonal Forms

Symmetric and Hermitian matrices permit specialized algorithms with superior stability and efficiency. The symmetric tridiagonal eigenvalue problem reduces via the QR algorithm to $O(n^2)$ total cost for all eigenvalues and $O(n)$ cost for each eigenvector. Preliminary reduction from full symmetric to tridiagonal form via Householder reflections costs $O(n^3)$ once, after which the tridiagonal structure enables rapid eigenvalue extraction.

For sparse symmetric matrices arising in graph Laplacians or discretized differential operators, exploiting sparsity through Krylov methods yields eigenvalue computations scaling linearly in the number of nonzero entries rather than the dimension squared. The Lanczos algorithm combined with sparse matrix-vector products achieves this efficiency, computing the $k$ extremal eigenvalues in $O(k \cdot \text{nnz}(A))$ time where $\text{nnz}(A)$ denotes the number of nonzero entries.

Banded matrices (nonzero only near the diagonal) permit specialized banded QR algorithms with reduced storage and computational costs proportional to bandwidth rather than full dimension. Tridiagonal matrices represent the extreme case of bandwidth two, enabling $O(n)$ storage and $O(n)$ eigenvalue extraction after $O(n^2)$ QR iterations.

### Application: Principal Component Analysis and Data Dimensionality Reduction

Principal Component Analysis (PCA) exemplifies eigenvalue theory applied to high-dimensional data analysis. Given a data matrix $X \in \mathbb{R}^{m \times n}$ with $m$ observations and $n$ features, the covariance matrix is $C = \frac{1}{m} X^T X$ (assuming centered data). The eigenvectors of $C$ are the **principal components**, and the corresponding eigenvalues measure the variance explained by each component.

Sorting eigenvalues $\lambda_1 \ge \lambda_2 \ge \cdots \ge \lambda_n$ identifies the dominant directions of variation. Projecting data onto the top $k$ eigenvectors provides optimal rank-$k$ approximation in the least-squares sense:

$$X \approx X V_k V_k^T$$

where $V_k = [\mathbf{v}_1, \mathbf{v}_2, \ldots, \mathbf{v}_k]$ contains the top $k$ eigenvectors. This reduces dimension from $n$ to $k$ while minimizing information loss, measured as the residual variance $\sum_{i=k+1}^n \lambda_i$.

For large datasets with $n \gg m$, forming the $n \times n$ covariance matrix is impractical. Instead, compute the eigendecomposition of the $m \times m$ Gram matrix $XX^T$, whose eigenvalues relate to those of $X^T X$ by $\lambda_i(X^T X) = \lambda_i(XX^T)$ for the nonzero eigenvalues. This dimension reduction trick, combined with randomized algorithms for approximate eigenvalue decomposition, enables PCA on matrices with billions of entries.

### Failure Recovery: Deflation and Shifted Inverse Iteration

When power iteration converges to the dominant eigenvector but additional eigenvectors are needed, **deflation** removes the dominant component from the matrix. If $(\lambda_1, \mathbf{v}_1)$ is known, define

$$A_1 = A - \lambda_1 \mathbf{v}_1 \mathbf{v}_1^T / (\mathbf{v}_1^T \mathbf{v}_1).$$

For symmetric $A$ with orthonormal eigenvectors, $A_1$ has eigenvalues $\{0, \lambda_2, \lambda_3, \ldots, \lambda_n\}$, so power iteration on $A_1$ converges to $\mathbf{v}_2$. Repeated deflation extracts all eigenpairs sequentially.

For eigenvalues in the interior of the spectrum, **inverse iteration** with shift $\sigma$ computes eigenpairs near $\sigma$. Iterate

$$(A - \sigma I)^{-1} \mathbf{x}_k = \mathbf{y}_{k+1}, \quad \mathbf{x}_{k+1} = \frac{\mathbf{y}_{k+1}}{\|\mathbf{y}_{k+1}\|}.$$

The matrix $(A - \sigma I)^{-1}$ has eigenvalues $(\lambda_i - \sigma)^{-1}$, so the eigenvalue nearest $\sigma$ becomes dominant for the inverse. Solving the shifted system via LU factorization once followed by forward and backward substitution per iteration achieves convergence to the eigenpair nearest $\sigma$ in $O(n^3)$ setup plus $O(n^2)$ per iteration.

These techniques combine to form complete eigenvalue toolkits capable of extracting any desired portion of the spectrum with controlled accuracy and computational cost. Understanding the mathematical structure underlying each algorithm enables practitioners to select the optimal method for their specific matrix structure, spectral distribution, and accuracy requirements, transforming eigenvalue computation from an opaque black box into a precisely calibrated instrument for linear algebraic analysis.
