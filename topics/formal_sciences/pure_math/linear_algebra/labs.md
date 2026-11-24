# Operational Verification Labs: Linear Algebra

## Objective & Mathematical Computing Setup

Linear algebra serves as the computational backbone of modern mathematics, connecting abstract vector space theory to concrete numerical algorithms that power everything from cryptographic protocols to machine learning pipelines. These operational verification labs bridge the gap between theoretical elegance and computational reality, transforming classical theorems into executable code that you can probe, stress-test, and validate against edge cases that textbooks rarely examine.

The primary objective is threefold: first, to verify fundamental linear algebraic properties through symbolic computation, ensuring that abstract claims about determinants, eigenvalues, and matrix decompositions hold under scrutiny; second, to identify the computational boundary conditions where numerical instability, singularities, and ill-conditioning reveal the limitations of floating-point arithmetic; third, to implement formal algebraic structures from first principles, constructing vector spaces, linear transformations, and canonical forms through executable code that mirrors the axiomatic foundations.

You will work primarily in Python with SymPy for symbolic computation and NumPy for numerical linear algebra, supplemented by SageMath for algebraic field extensions and optionally Lean or Coq for formal proof verification. This environment allows you to toggle between exact rational arithmetic and approximate floating-point computation, exposing the practical consequences of theoretical assumptions. The verification workflow follows a rigorous pattern: state the theorem formally, encode its hypotheses as computational predicates, execute the verification across a parameter space, and analyze failure modes to understand where theory meets computational reality.

Begin by establishing your computing environment. Install Python 3.11 or later, then provision the symbolic and numerical libraries:

```bash
pip install sympy numpy scipy matplotlib
```

Verify that SymPy can perform symbolic matrix operations:

```bash
python -c "import sympy as sp; M = sp.Matrix([[1, 2], [3, 4]]); print(M.det())"
```

You should see the output `-2`, confirming that symbolic determinant computation functions correctly. For advanced algebraic structures, install SageMath through your system package manager or via conda:

```bash
conda install -c conda-forge sage
```

Test SageMath by constructing a finite field and verifying closure under multiplication:

```bash
sage -c "F = GF(7); print(F(3) * F(5))"
```

The result `1` confirms that $3 \times 5 \equiv 1 \pmod{7}$ in the field $\mathbb{F}_7$. If you intend to pursue formal proof verification, install Lean 4:

```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

Initialize a Lean project and verify the installation:

```bash
lake new linear_algebra_proofs
cd linear_algebra_proofs
lake build
```

With the environment configured, you are ready to execute computational verifications that transform abstract linear algebra into tangible mathematical reality.

## Exercise 1: Computational Verification of Core Theorems

The foundational theorems of linear algebra—rank-nullity, the determinant-trace relationship for eigenvalues, and the spectral theorem for symmetric matrices—form the bedrock of both pure theory and numerical computation. This exercise systematically verifies these results through symbolic manipulation, exposing the algebraic identities that textbooks often state without computational confirmation.

### Rank-Nullity Theorem Verification

The rank-nullity theorem asserts that for any linear transformation $T: V \to W$ represented by an $m \times n$ matrix $A$, the fundamental equation $\text{rank}(A) + \text{nullity}(A) = n$ holds universally. The rank measures the dimension of the column space, while the nullity quantifies the dimension of the kernel. Computationally verify this identity across diverse matrix families, including rectangular matrices, singular square matrices, and matrices with symbolic entries.

Construct a symbolic verification framework that tests rank-nullity for parameterized matrix families:

```python
import sympy as sp
from sympy import symbols, Matrix, eye, zeros, randMatrix

def verify_rank_nullity(A):
    """
    Verify rank-nullity theorem: rank(A) + nullity(A) = n
    Returns (rank, nullity, n, theorem_holds)
    """
    n = A.cols
    rank_A = A.rank()
    # Nullity = dimension of null space
    null_basis = A.nullspace()
    nullity_A = len(null_basis)
    
    theorem_holds = (rank_A + nullity_A == n)
    return rank_A, nullity_A, n, theorem_holds

# Test Case 1: Full-rank square matrix
A1 = Matrix([[1, 2], [3, 4]])
r1, n1, dim1, holds1 = verify_rank_nullity(A1)
print(f"Full-rank 2x2: rank={r1}, nullity={n1}, n={dim1}, holds={holds1}")

# Test Case 2: Rank-deficient square matrix
A2 = Matrix([[1, 2, 3], [2, 4, 6], [1, 1, 1]])
r2, n2, dim2, holds2 = verify_rank_nullity(A2)
print(f"Rank-deficient 3x3: rank={r2}, nullity={n2}, n={dim2}, holds={holds2}")

# Test Case 3: Rectangular matrix (more columns than rows)
A3 = Matrix([[1, 2, 3, 4], [5, 6, 7, 8]])
r3, n3, dim3, holds3 = verify_rank_nullity(A3)
print(f"2x4 rectangular: rank={r3}, nullity={n3}, n={dim3}, holds={holds3}")

# Test Case 4: Symbolic parameter matrix
x, y = symbols('x y', real=True)
A4 = Matrix([[1, x], [y, x*y]])
r4, n4, dim4, holds4 = verify_rank_nullity(A4)
print(f"Symbolic 2x2: rank={r4}, nullity={n4}, n={dim4}, holds={holds4}")
print(f"Null space basis: {A4.nullspace()}")
```

Execute this verification script and observe that the theorem holds across all test cases, including the symbolic parameterization. For the rank-deficient matrix, the rank equals 2 and the nullity equals 1, satisfying $2 + 1 = 3$. The rectangular matrix exhibits rank 2 with nullity 2, confirming $2 + 2 = 4$. The symbolic case reveals that the matrix is always rank-deficient with rank 1 (the second row is always a scalar multiple of the first), but the symbolic computation correctly captures the null space structure for all parameter values.

Extend the verification to explore how rank and nullity change under elementary row operations, which preserve the row space but modify the explicit representation:

```python
def verify_row_operations_preserve_rank(A):
    """Verify that elementary row operations preserve rank"""
    original_rank = A.rank()
    
    # Apply various row operations
    A_rref, pivots = A.rref()
    rref_rank = A_rref.rank()
    
    # Row swap
    A_swap = A.copy()
    if A.rows >= 2:
        A_swap.row_swap(0, 1)
        swap_rank = A_swap.rank()
    else:
        swap_rank = original_rank
    
    # Row scaling
    A_scale = A.copy()
    A_scale[0, :] = 3 * A_scale[0, :]
    scale_rank = A_scale.rank()
    
    # Row addition
    A_add = A.copy()
    if A.rows >= 2:
        A_add[1, :] = A_add[1, :] + 2 * A_add[0, :]
        add_rank = A_add.rank()
    else:
        add_rank = original_rank
    
    all_ranks = [original_rank, rref_rank, swap_rank, scale_rank, add_rank]
    invariant_holds = all(r == original_rank for r in all_ranks)
    
    return original_rank, all_ranks, invariant_holds

A = Matrix([[2, 4, 6], [1, 2, 3], [3, 6, 9]])
orig_rank, ranks, invariant = verify_row_operations_preserve_rank(A)
print(f"Original rank: {orig_rank}")
print(f"Ranks after operations: {ranks}")
print(f"Rank invariance holds: {invariant}")
```

The rank remains invariant under all three classes of elementary row operations, confirming that the row-reduction algorithm correctly identifies the dimension of the row space.

### Cayley-Hamilton Theorem Verification

The Cayley-Hamilton theorem states that every square matrix satisfies its own characteristic polynomial. For a matrix $A$ with characteristic polynomial $p_A(\lambda) = \det(\lambda I - A)$, the substitution $p_A(A) = 0$ yields the zero matrix. This remarkable result connects eigenvalue theory to polynomial algebra, enabling the computation of matrix functions through polynomial expansions.

Construct a symbolic verification that tests the Cayley-Hamilton theorem across diverse matrix families, including diagonalizable and non-diagonalizable examples:

```python
import sympy as sp
from sympy import Matrix, eye, symbols, simplify, det

def verify_cayley_hamilton(A):
    """
    Verify Cayley-Hamilton theorem: p_A(A) = 0
    where p_A(λ) = det(λI - A) is the characteristic polynomial
    """
    n = A.rows
    lam = symbols('lambda')
    
    # Compute characteristic polynomial
    char_poly = det(lam * eye(n) - A)
    print(f"Characteristic polynomial: {char_poly}")
    
    # Substitute A into the characteristic polynomial
    # p_A(A) = c_n A^n + c_{n-1} A^{n-1} + ... + c_1 A + c_0 I
    poly_coeffs = sp.Poly(char_poly, lam).all_coeffs()
    
    result = sp.zeros(n, n)
    for i, coeff in enumerate(poly_coeffs):
        power = len(poly_coeffs) - 1 - i
        if power == 0:
            term = coeff * eye(n)
        else:
            term = coeff * (A ** power)
        result += term
    
    # Simplify and check if result is zero matrix
    result_simplified = simplify(result)
    is_zero = result_simplified == zeros(n, n)
    
    return char_poly, result_simplified, is_zero

# Test Case 1: Diagonalizable 2x2 matrix
A1 = Matrix([[3, 1], [0, 2]])
poly1, result1, holds1 = verify_cayley_hamilton(A1)
print(f"2x2 diagonalizable: p_A(A) = 0? {holds1}\n")

# Test Case 2: Non-diagonalizable (nilpotent) matrix
A2 = Matrix([[0, 1], [0, 0]])
poly2, result2, holds2 = verify_cayley_hamilton(A2)
print(f"2x2 nilpotent: p_A(A) = 0? {holds2}\n")

# Test Case 3: 3x3 matrix with complex eigenvalues
A3 = Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 2]])
poly3, result3, holds3 = verify_cayley_hamilton(A3)
print(f"3x3 with complex eigenvalues: p_A(A) = 0? {holds3}\n")

# Test Case 4: Symbolic parameter matrix
a, b = symbols('a b', real=True)
A4 = Matrix([[a, b], [0, a]])
poly4, result4, holds4 = verify_cayley_hamilton(A4)
print(f"Symbolic 2x2: p_A(A) = 0? {holds4}")
print(f"Result matrix: {result4}\n")
```

Execute this verification and observe that the Cayley-Hamilton theorem holds universally. For the nilpotent matrix $A_2 = \begin{pmatrix} 0 & 1 \\ 0 & 0 \end{pmatrix}$, the characteristic polynomial is $\lambda^2$, and indeed $A_2^2 = 0$. For the rotation-dilation matrix $A_3$, the characteristic polynomial factors as $(\lambda - 2)(\lambda^2 + 1)$, and the substitution yields the zero matrix despite the presence of complex eigenvalues $\pm i$.

Leverage the Cayley-Hamilton theorem to compute matrix exponentials and logarithms efficiently:

```python
from sympy import exp, log, I, sqrt, factorial

def compute_matrix_exponential_via_cayley_hamilton(A, t):
    """
    Compute e^(At) using Cayley-Hamilton reduction
    Reduces matrix polynomial to degree < n
    """
    n = A.rows
    lam = symbols('lambda')
    
    # Get eigenvalues
    eigenvals = A.eigenvals()
    
    # For each eigenvalue λ, we have e^(λt) = Σ c_k λ^k
    # Use interpolation at eigenvalues to find coefficients
    
    # For 2x2, use direct formula
    if n == 2:
        trace_A = A.trace()
        det_A = A.det()
        
        # e^(At) = e^(t·tr(A)/2) [cosh(t·d/2)I + sinh(t·d/2)/d · (A - tr(A)/2·I)]
        # where d = sqrt(tr(A)^2 - 4det(A))
        
        discriminant = trace_A**2 - 4*det_A
        
        if discriminant >= 0:
            d = sqrt(discriminant)
            exp_matrix = exp(t * trace_A / 2) * (
                sp.cosh(t * d / 2) * eye(n) +
                sp.sinh(t * d / 2) / d * (A - trace_A / 2 * eye(n))
            )
        else:
            # Complex eigenvalues
            d = sqrt(-discriminant)
            exp_matrix = exp(t * trace_A / 2) * (
                sp.cos(t * d / 2) * eye(n) +
                sp.sin(t * d / 2) / d * (A - trace_A / 2 * eye(n))
            )
    else:
        # General case: use eigendecomposition
        exp_matrix = Matrix.zeros(n, n)
        for eigval, mult in eigenvals.items():
            # Project onto eigenspace and scale
            for vec in A.eigenvects():
                if vec[0] == eigval:
                    for v in vec[2]:
                        v_norm = v / sqrt((v.T * v)[0])
                        v_mat = v_norm * v_norm.T
                        exp_matrix += exp(eigval * t) * v_mat
    
    return simplify(exp_matrix)

# Test exponential of nilpotent matrix
A_nilp = Matrix([[0, 1], [0, 0]])
exp_A = compute_matrix_exponential_via_cayley_hamilton(A_nilp, symbols('t'))
print(f"e^(At) for nilpotent matrix:\n{exp_A}\n")

# Verify: should equal I + tA (truncated series)
t = symbols('t')
expected = eye(2) + t * A_nilp
print(f"Expected (I + tA):\n{expected}\n")
print(f"Match: {simplify(exp_A - expected) == zeros(2, 2)}")
```

For the nilpotent matrix, the exponential series terminates after the linear term, yielding $e^{At} = I + tA = \begin{pmatrix} 1 & t \\ 0 & 1 \end{pmatrix}$, which the Cayley-Hamilton approach recovers exactly.

### Spectral Theorem for Symmetric Matrices

The spectral theorem guarantees that every real symmetric matrix $A$ admits an orthogonal diagonalization $A = Q \Lambda Q^T$, where $Q$ is orthogonal ($Q^T Q = I$) and $\Lambda$ is diagonal with real eigenvalues. This result is fundamental to quadratic form theory, principal component analysis, and the geometry of ellipsoids. Verify the spectral theorem computationally by constructing symmetric matrices, computing their eigendecompositions, and confirming orthogonality.

```python
import sympy as sp
from sympy import Matrix, eye, simplify, sqrt

def verify_spectral_theorem(A):
    """
    Verify spectral theorem for symmetric matrix:
    1. All eigenvalues are real
    2. Eigenvectors are orthogonal
    3. A = Q Λ Q^T with Q orthogonal
    """
    n = A.rows
    
    # Check symmetry
    is_symmetric = A == A.T
    if not is_symmetric:
        return False, "Matrix is not symmetric"
    
    # Compute eigendecomposition
    eigenvects = A.eigenvects()
    
    # Extract eigenvalues and eigenvectors
    eigenvalues = []
    eigenvectors = []
    
    for eigval, mult, vecs in eigenvects:
        # Check eigenvalue is real
        if eigval.is_real is False:
            return False, f"Complex eigenvalue found: {eigval}"
        
        eigenvalues.extend([eigval] * mult)
        
        # Orthonormalize eigenvectors if multiplicity > 1
        if mult > 1:
            # Apply Gram-Schmidt
            orthonormal_vecs = []
            for vec in vecs:
                v = vec
                for u in orthonormal_vecs:
                    v = v - (v.dot(u) / u.dot(u)) * u
                v = v / sqrt(v.dot(v))
                orthonormal_vecs.append(v)
            eigenvectors.extend(orthonormal_vecs)
        else:
            # Normalize single eigenvector
            v = vecs[0]
            v_normalized = v / sqrt(v.dot(v))
            eigenvectors.append(v_normalized)
    
    # Construct Q (eigenvectors as columns)
    Q = Matrix.hstack(*[vec for vec in eigenvectors])
    
    # Construct Λ (diagonal matrix of eigenvalues)
    Lambda = sp.diag(*eigenvalues)
    
    # Verify Q is orthogonal: Q^T Q = I
    QTQ = simplify(Q.T * Q)
    is_orthogonal = QTQ == eye(n)
    
    # Verify A = Q Λ Q^T
    reconstructed = simplify(Q * Lambda * Q.T)
    reconstruction_correct = reconstructed == A
    
    return {
        'is_symmetric': is_symmetric,
        'eigenvalues_real': True,
        'Q': Q,
        'Lambda': Lambda,
        'Q_orthogonal': is_orthogonal,
        'reconstruction_correct': reconstruction_correct,
        'QTQ': QTQ
    }

# Test Case 1: Simple 2x2 symmetric matrix
A1 = Matrix([[4, 2], [2, 3]])
result1 = verify_spectral_theorem(A1)
print("2x2 symmetric matrix:")
print(f"  Q orthogonal: {result1['Q_orthogonal']}")
print(f"  Reconstruction correct: {result1['reconstruction_correct']}")
print(f"  Eigenvalues: {result1['Lambda'].diagonal()}\n")

# Test Case 2: 3x3 symmetric matrix with repeated eigenvalue
A2 = Matrix([[2, 0, 0], [0, 2, 1], [0, 1, 2]])
result2 = verify_spectral_theorem(A2)
print("3x3 symmetric with repeated eigenvalue:")
print(f"  Q orthogonal: {result2['Q_orthogonal']}")
print(f"  Reconstruction correct: {result2['reconstruction_correct']}")
print(f"  Q^T Q:\n{result2['QTQ']}\n")

# Test Case 3: Positive definite matrix
A3 = Matrix([[2, -1, 0], [-1, 2, -1], [0, -1, 2]])
result3 = verify_spectral_theorem(A3)
eigenvals3 = result3['Lambda'].diagonal()
all_positive = all(ev > 0 for ev in eigenvals3)
print("3x3 tridiagonal (positive definite):")
print(f"  All eigenvalues positive: {all_positive}")
print(f"  Eigenvalues: {eigenvals3}")
print(f"  Reconstruction correct: {result3['reconstruction_correct']}\n")
```

Execute this verification across the test cases. The 2×2 symmetric matrix yields eigenvalues $5$ and $2$, with orthonormal eigenvectors forming the columns of $Q$. The 3×3 matrix with repeated eigenvalue $2$ requires Gram-Schmidt orthogonalization of the eigenspace, which the code handles explicitly. The tridiagonal matrix has eigenvalues $2 - \sqrt{2}$, $2$, and $2 + \sqrt{2}$, all positive, confirming positive definiteness.

Extend the verification to explore the connection between the spectral decomposition and quadratic forms:

```python
from sympy import symbols

def verify_quadratic_form_via_spectral(A):
    """
    For symmetric A, the quadratic form x^T A x can be diagonalized:
    x^T A x = y^T Λ y where y = Q^T x
    """
    n = A.rows
    result = verify_spectral_theorem(A)
    
    if not result['reconstruction_correct']:
        return None
    
    Q = result['Q']
    Lambda = result['Lambda']
    
    # Construct symbolic vector x
    x = Matrix([symbols(f'x_{i}', real=True) for i in range(n)])
    
    # Compute quadratic form x^T A x
    quad_form_original = (x.T * A * x)[0]
    
    # Change of variables: y = Q^T x, so x = Q y
    y = Matrix([symbols(f'y_{i}', real=True) for i in range(n)])
    x_in_y = Q * y
    
    # Compute quadratic form in new coordinates
    quad_form_transformed = (y.T * Lambda * y)[0]
    
    # Verify they match by substitution
    quad_form_check = (x_in_y.T * A * x_in_y)[0]
    quad_form_check_simplified = simplify(quad_form_check)
    
    return {
        'original_form': quad_form_original,
        'diagonal_form': quad_form_transformed,
        'verification_form': quad_form_check_simplified,
        'eigenvalues': Lambda.diagonal()
    }

A = Matrix([[3, 1], [1, 3]])
quad_result = verify_quadratic_form_via_spectral(A)
print("Quadratic form diagonalization:")
print(f"  Original: {quad_result['original_form']}")
print(f"  Diagonal: {quad_result['diagonal_form']}")
print(f"  Eigenvalues: {quad_result['eigenvalues']}\n")
```

The quadratic form $3x_0^2 + 2x_0 x_1 + 3x_1^2$ diagonalizes to $4y_0^2 + 2y_1^2$ under the orthogonal transformation, exposing the principal axes of the ellipsoid defined by $x^T A x = 1$.

## Exercise 2: Boundary Value Stress Testing & Singularities

Theoretical linear algebra operates in the realm of exact arithmetic, where matrices are either invertible or singular, eigenvalues are precise, and decompositions exist by fiat. Numerical computation forces us to confront the messy reality of floating-point approximation, where ill-conditioned matrices produce wildly inaccurate results, near-singular systems amplify rounding errors, and iterative algorithms fail to converge. This exercise systematically stress-tests linear algebraic algorithms at the boundary between well-posed and ill-posed problems, revealing where numerical instability lurks.

### Condition Number and Numerical Stability

The condition number $\kappa(A) = \|A\| \|A^{-1}\|$ quantifies how sensitive the solution to $Ax = b$ is to perturbations in $A$ and $b$. For a relative perturbation $\delta A$ in the matrix and $\delta b$ in the right-hand side, the relative error in the solution satisfies $\frac{\|\delta x\|}{\|x\|} \le \kappa(A) \left( \frac{\|\delta A\|}{\|A\|} + \frac{\|\delta b\|}{\|b\|} \right)$. Matrices with large condition numbers amplify small input errors into large output errors, rendering numerical solutions unreliable.

Construct a stress test that generates ill-conditioned matrices and measures the degradation of solution accuracy:

```python
import numpy as np
from numpy.linalg import cond, norm, solve

def generate_ill_conditioned_matrix(n, target_condition_number):
    """
    Generate an nxn matrix with specified condition number
    using singular value decomposition: A = U Σ V^T
    """
    # Generate random orthogonal matrices
    U, _ = np.linalg.qr(np.random.randn(n, n))
    V, _ = np.linalg.qr(np.random.randn(n, n))
    
    # Construct singular values to achieve target condition number
    sigma_max = 1.0
    sigma_min = sigma_max / target_condition_number
    
    # Logarithmic spacing between sigma_max and sigma_min
    singular_values = np.logspace(np.log10(sigma_min), np.log10(sigma_max), n)
    Sigma = np.diag(singular_values)
    
    A = U @ Sigma @ V.T
    
    return A, cond(A)

def test_condition_number_impact(n, condition_numbers):
    """
    Test how condition number affects solution accuracy
    """
    results = []
    
    for kappa_target in condition_numbers:
        A, kappa_actual = generate_ill_conditioned_matrix(n, kappa_target)
        
        # True solution
        x_true = np.ones(n)
        b = A @ x_true
        
        # Add small perturbation to b (relative error ~1e-10)
        perturbation_size = 1e-10
        b_perturbed = b + perturbation_size * np.random.randn(n)
        
        # Solve perturbed system
        x_computed = solve(A, b_perturbed)
        
        # Compute relative error
        rel_error = norm(x_computed - x_true) / norm(x_true)
        
        # Theoretical error bound
        rel_perturbation = norm(b_perturbed - b) / norm(b)
        theoretical_bound = kappa_actual * rel_perturbation
        
        results.append({
            'kappa_target': kappa_target,
            'kappa_actual': kappa_actual,
            'rel_error': rel_error,
            'theoretical_bound': theoretical_bound,
            'bound_satisfied': rel_error <= theoretical_bound * 10  # Factor of 10 for constants
        })
    
    return results

# Test across range of condition numbers
n = 10
condition_numbers = [1e2, 1e4, 1e6, 1e8, 1e10, 1e12, 1e14]
results = test_condition_number_impact(n, condition_numbers)

print("Condition Number Impact on Solution Accuracy:")
print(f"{'κ(A) target':<15} {'κ(A) actual':<15} {'Relative Error':<20} {'Theoretical Bound':<20} {'Bound OK'}")
print("-" * 90)
for r in results:
    print(f"{r['kappa_target']:<15.2e} {r['kappa_actual']:<15.2e} {r['rel_error']:<20.10e} {r['theoretical_bound']:<20.10e} {r['bound_satisfied']}")
```

Execute this stress test and observe the exponential growth in relative error as the condition number increases. For $\kappa(A) \approx 10^{14}$, the relative error approaches $10^{-4}$, meaning four decimal digits of accuracy are lost despite double-precision arithmetic providing 16 decimal digits. When $\kappa(A)$ exceeds $10^{16}$, the matrix is numerically singular and the solution is meaningless.

The error bound is not merely theoretical—it accurately predicts the observed error magnitudes. For $\kappa(A) = 10^{10}$ and a perturbation of size $10^{-10}$, the theoretical bound is $10^{10} \cdot 10^{-10} = 1$, indicating that the entire solution can be contaminated. This phenomenon is not a bug in the solver; it is an inescapable consequence of finite-precision arithmetic acting on ill-conditioned problems.

### Singular Value Decomposition at Singularities

The singular value decomposition (SVD) $A = U \Sigma V^T$ decomposes any $m \times n$ matrix into orthogonal matrices $U$ and $V$ and a diagonal matrix $\Sigma$ of singular values. The SVD remains well-defined even for singular and rank-deficient matrices, making it the preferred tool for analyzing near-singular systems. The condition number can be computed directly as $\kappa(A) = \sigma_{\max} / \sigma_{\min}$, where $\sigma_{\max}$ and $\sigma_{\min}$ are the largest and smallest nonzero singular values.

Stress-test the SVD by constructing matrices with clustered singular values and verifying that the decomposition correctly identifies the numerical rank:

```python
import numpy as np
from numpy.linalg import svd

def analyze_singular_values(A, tolerance=1e-10):
    """
    Perform SVD and analyze singular value structure
    """
    U, sigma, Vt = svd(A)
    
    # Determine numerical rank (number of singular values above tolerance)
    numerical_rank = np.sum(sigma > tolerance * sigma[0])
    
    # Compute condition number
    if numerical_rank > 0 and sigma[-1] > tolerance:
        condition_number = sigma[0] / sigma[-1]
    else:
        condition_number = np.inf
    
    # Identify singular value gaps (sudden drops)
    if len(sigma) > 1:
        ratios = sigma[:-1] / sigma[1:]
        gap_indices = np.where(ratios > 100)[0]  # Gaps where ratio exceeds 100
    else:
        gap_indices = []
    
    return {
        'U': U,
        'sigma': sigma,
        'Vt': Vt,
        'numerical_rank': numerical_rank,
        'condition_number': condition_number,
        'gap_indices': gap_indices
    }

# Test Case 1: Matrix with clustered singular values
A1 = np.array([[1.0, 1.0, 1.0],
               [1.0, 1.0 + 1e-8, 1.0],
               [1.0, 1.0, 1.0 + 1e-8]])

result1 = analyze_singular_values(A1)
print("Clustered singular values:")
print(f"  Singular values: {result1['sigma']}")
print(f"  Numerical rank: {result1['numerical_rank']}")
print(f"  Condition number: {result1['condition_number']:.2e}\n")

# Test Case 2: Rank-deficient matrix (two identical rows)
A2 = np.array([[1.0, 2.0, 3.0],
               [1.0, 2.0, 3.0],
               [4.0, 5.0, 6.0]])

result2 = analyze_singular_values(A2, tolerance=1e-10)
print("Rank-deficient (identical rows):")
print(f"  Singular values: {result2['sigma']}")
print(f"  Numerical rank: {result2['numerical_rank']}")
print(f"  Gap indices: {result2['gap_indices']}\n")

# Test Case 3: Nearly singular matrix (determinant near zero)
A3 = np.array([[1.0, 2.0],
               [1.0, 2.0 + 1e-12]])

result3 = analyze_singular_values(A3, tolerance=1e-10)
print("Nearly singular (parallel rows):")
print(f"  Singular values: {result3['sigma']}")
print(f"  Numerical rank: {result3['numerical_rank']}")
print(f"  Condition number: {result3['condition_number']:.2e}\n")

# Test Case 4: Exponentially decaying singular values
n = 5
A4 = np.diag([10**(-i) for i in range(n)])
result4 = analyze_singular_values(A4, tolerance=1e-10)
print("Exponentially decaying singular values:")
print(f"  Singular values: {result4['sigma']}")
print(f"  Numerical rank: {result4['numerical_rank']}")
print(f"  Condition number: {result4['condition_number']:.2e}\n")
```

Execute this analysis and observe how the numerical rank differs from the mathematical rank. For the nearly singular matrix $A_3$, the SVD reveals two singular values: one of order $1$ and one of order $10^{-12}$. While the mathematical rank is 2, the numerical rank with tolerance $10^{-10}$ is also 2, but any tolerance greater than $10^{-12}$ would classify this as rank 1. This ambiguity reflects the continuous nature of rank near singularities.

The rank-deficient matrix $A_2$ exhibits a singular value gap: the first two singular values are nonzero, the third is effectively zero (below machine epsilon), indicating mathematical rank 2. The gap index identifies where the sudden drop occurs, providing a heuristic for choosing the numerical rank.

Leverage the SVD to construct the Moore-Penrose pseudoinverse, which provides the least-squares solution to singular and rectangular systems:

```python
def compute_pseudoinverse(A, tolerance=1e-10):
    """
    Compute Moore-Penrose pseudoinverse using SVD
    A^+ = V Σ^+ U^T, where Σ^+ inverts nonzero singular values
    """
    U, sigma, Vt = svd(A, full_matrices=False)
    
    # Invert singular values above tolerance
    sigma_inv = np.zeros_like(sigma)
    for i, s in enumerate(sigma):
        if s > tolerance * sigma[0]:
            sigma_inv[i] = 1.0 / s
    
    A_pseudoinv = Vt.T @ np.diag(sigma_inv) @ U.T
    
    return A_pseudoinv

# Test pseudoinverse on rank-deficient system
A = np.array([[1, 2], [2, 4], [3, 6]], dtype=float)  # Rank 1, 3x2
b = np.array([1, 2, 3], dtype=float)

A_pinv = compute_pseudoinverse(A)
x_ls = A_pinv @ b

print("Least-squares solution via pseudoinverse:")
print(f"  A shape: {A.shape}, rank: {np.linalg.matrix_rank(A)}")
print(f"  Solution x: {x_ls}")
print(f"  Residual ||Ax - b||: {np.linalg.norm(A @ x_ls - b):.10e}\n")

# Verify pseudoinverse properties: A A^+ A = A and A^+ A A^+ = A^+
AA_pinv_A = A @ A_pinv @ A
A_pinv_A_A_pinv = A_pinv @ A @ A_pinv

print("Pseudoinverse properties:")
print(f"  ||A A^+ A - A||: {np.linalg.norm(AA_pinv_A - A):.10e}")
print(f"  ||A^+ A A^+ - A^+||: {np.linalg.norm(A_pinv_A_A_pinv - A_pinv):.10e}")
```

The pseudoinverse provides the least-squares solution with minimum norm, satisfying the four defining properties even when $A$ is singular. The residual is minimized subject to the constraint that $x$ lies in the row space of $A$.

### Eigenvalue Perturbation and Spectral Stability

Eigenvalues of non-symmetric matrices can be highly sensitive to perturbations, a phenomenon quantified by the Bauer-Fike theorem. For a matrix $A$ with eigenvalues $\lambda_i$ and a perturbed matrix $A + E$, the perturbed eigenvalues $\tilde{\lambda}_i$ satisfy the bound $\min_j |\tilde{\lambda} - \lambda_j| \le \kappa(X) \|E\|$, where $X$ is the matrix of eigenvectors and $\kappa(X)$ is its condition number. For defective matrices (those lacking a complete set of eigenvectors), the eigenvector matrix $X$ is ill-conditioned or does not exist, causing extreme sensitivity.

Construct a stress test that explores eigenvalue stability for symmetric versus non-symmetric matrices:

```python
import numpy as np
from numpy.linalg import eigvals, cond, norm

def test_eigenvalue_stability(A, perturbation_sizes):
    """
    Test eigenvalue stability under perturbations
    """
    eigenvals_original = eigvals(A)
    results = []
    
    for eps in perturbation_sizes:
        # Add random perturbation
        E = eps * np.random.randn(*A.shape)
        A_perturbed = A + E
        
        eigenvals_perturbed = eigvals(A_perturbed)
        
        # Compute maximum eigenvalue change
        # Match eigenvalues by magnitude (greedy pairing)
        ev_orig_sorted = np.sort(np.abs(eigenvals_original))
        ev_pert_sorted = np.sort(np.abs(eigenvals_perturbed))
        
        max_change = np.max(np.abs(ev_orig_sorted - ev_pert_sorted))
        avg_change = np.mean(np.abs(ev_orig_sorted - ev_pert_sorted))
        
        results.append({
            'perturbation': eps,
            'max_eigenvalue_change': max_change,
            'avg_eigenvalue_change': avg_change
        })
    
    return eigenvals_original, results

# Test Case 1: Symmetric matrix (stable eigenvalues)
A_sym = np.array([[4, 1, 0],
                  [1, 3, 1],
                  [0, 1, 2]], dtype=float)

perturbations = [1e-8, 1e-6, 1e-4, 1e-2]
eigenvals_sym, results_sym = test_eigenvalue_stability(A_sym, perturbations)

print("Eigenvalue stability: Symmetric matrix")
print(f"Original eigenvalues: {np.sort(eigenvals_sym)}")
print(f"{'Perturbation':<15} {'Max Change':<20} {'Avg Change':<20}")
print("-" * 55)
for r in results_sym:
    print(f"{r['perturbation']:<15.2e} {r['max_eigenvalue_change']:<20.10e} {r['avg_eigenvalue_change']:<20.10e}")
print()

# Test Case 2: Non-symmetric matrix (potentially unstable)
A_nonsym = np.array([[1, 5, 0],
                     [0, 2, 5],
                     [0, 0, 3]], dtype=float)

eigenvals_nonsym, results_nonsym = test_eigenvalue_stability(A_nonsym, perturbations)

print("Eigenvalue stability: Non-symmetric (upper triangular)")
print(f"Original eigenvalues: {np.sort(np.abs(eigenvals_nonsym))}")
print(f"{'Perturbation':<15} {'Max Change':<20} {'Avg Change':<20}")
print("-" * 55)
for r in results_nonsym:
    print(f"{r['perturbation']:<15.2e} {r['max_eigenvalue_change']:<20.10e} {r['avg_eigenvalue_change']:<20.10e}")
print()

# Test Case 3: Defective matrix (Jordan block - highly unstable)
A_defective = np.array([[1, 1, 0],
                        [0, 1, 1],
                        [0, 0, 1]], dtype=float)

eigenvals_defective, results_defective = test_eigenvalue_stability(A_defective, perturbations)

print("Eigenvalue stability: Defective matrix (Jordan block)")
print(f"Original eigenvalues: {np.sort(np.abs(eigenvals_defective))}")
print(f"{'Perturbation':<15} {'Max Change':<20} {'Avg Change':<20}")
print("-" * 55)
for r in results_defective:
    print(f"{r['perturbation']:<15.2e} {r['max_eigenvalue_change']:<20.10e} {r['avg_eigenvalue_change']:<20.10e}")
```

Execute this stress test and observe the dramatic difference in stability. For the symmetric matrix, eigenvalue changes scale linearly with the perturbation size: a perturbation of $10^{-8}$ induces eigenvalue changes of order $10^{-8}$. This reflects the well-conditioned nature of symmetric eigenproblems.

The upper triangular matrix exhibits moderate sensitivity, with eigenvalue changes roughly proportional to the perturbation but with a larger constant. The defective matrix reveals catastrophic instability: a perturbation of $10^{-4}$ can shift eigenvalues by order $10^{-2}$ or larger, a magnification factor of $100$. This occurs because the eigenvector matrix has infinite condition number (it does not exist as a basis), causing the Bauer-Fike bound to become vacuous.

The lesson is clear: eigenvalue computations on non-symmetric matrices require extreme caution. Always check the eigenvector condition number, and consider using the Schur decomposition or generalized eigenvalue algorithms for improved stability.

## Exercise 3: Algorithmic Implementation of Formal Structures

Linear algebra is not merely a collection of computational recipes—it is a formal algebraic structure governed by axioms that define vector spaces, modules, and linear transformations. This exercise implements these structures from first principles, constructing vector spaces over finite fields, linear transformations as explicit mappings, and canonical forms through constructive algorithms. The goal is to bridge the gap between abstract algebra and executable code, demonstrating that formal definitions translate directly into computational objects.

### Finite Field Vector Spaces and Linear Independence

A vector space $V$ over a field $\mathbb{F}$ is an abelian group under vector addition, equipped with scalar multiplication satisfying the distributive, associative, and unital axioms. When the field is finite, such as $\mathbb{F}_2 = \{0, 1\}$ or $\mathbb{F}_p$ for prime $p$, the vector space has finitely many elements, enabling exhaustive verification of linear independence and spanning properties.

Implement a finite field vector space class that enforces the vector space axioms and provides algorithms for checking linear independence:

```python
class FiniteFieldVectorSpace:
    """
    Vector space V = F^n over finite field F_p
    """
    def __init__(self, p, n):
        """
        p: prime modulus (field size)
        n: dimension
        """
        self.p = p
        self.n = n
        self.size = p ** n
    
    def add(self, u, v):
        """Component-wise addition mod p"""
        return tuple((u[i] + v[i]) % self.p for i in range(self.n))
    
    def scalar_mult(self, c, v):
        """Scalar multiplication mod p"""
        return tuple((c * v[i]) % self.p for i in range(self.n))
    
    def zero(self):
        """Zero vector"""
        return tuple(0 for _ in range(self.n))
    
    def negate(self, v):
        """Additive inverse"""
        return tuple((-v[i]) % self.p for i in range(self.n))
    
    def is_linear_combination(self, target, vectors):
        """
        Check if target is a linear combination of vectors
        Exhaustive search over all scalar combinations
        """
        if not vectors:
            return target == self.zero()
        
        # Try all combinations of scalars
        from itertools import product
        for scalars in product(range(self.p), repeat=len(vectors)):
            # Compute linear combination
            result = self.zero()
            for c, v in zip(scalars, vectors):
                result = self.add(result, self.scalar_mult(c, v))
            
            if result == target:
                return True, scalars
        
        return False, None
    
    def are_linearly_independent(self, vectors):
        """
        Check if vectors are linearly independent
        They're independent iff the only linear combination giving 0 is trivial
        """
        if not vectors:
            return True
        
        from itertools import product
        # Try all non-trivial scalar combinations
        for scalars in product(range(self.p), repeat=len(vectors)):
            if all(c == 0 for c in scalars):
                continue  # Skip trivial combination
            
            # Compute linear combination
            result = self.zero()
            for c, v in zip(scalars, vectors):
                result = self.add(result, self.scalar_mult(c, v))
            
            if result == self.zero():
                return False, scalars  # Found non-trivial dependence
        
        return True, None
    
    def compute_span(self, vectors):
        """
        Compute all vectors in span(vectors)
        """
        span = {self.zero()}
        
        from itertools import product
        for scalars in product(range(self.p), repeat=len(vectors)):
            result = self.zero()
            for c, v in zip(scalars, vectors):
                result = self.add(result, self.scalar_mult(c, v))
            span.add(result)
        
        return span
    
    def dimension_of_span(self, vectors):
        """Compute dimension of span(vectors) = size of maximal independent subset"""
        if not vectors:
            return 0
        
        # Greedy algorithm: build maximal independent set
        independent_set = []
        for v in vectors:
            # Check if v is independent of current set
            test_set = independent_set + [v]
            is_indep, _ = self.are_linearly_independent(test_set)
            if is_indep:
                independent_set.append(v)
        
        return len(independent_set)

# Test over F_2 (binary field)
V2 = FiniteFieldVectorSpace(p=2, n=3)

# Test linear independence
v1 = (1, 0, 0)
v2 = (0, 1, 0)
v3 = (1, 1, 0)

is_indep_12, _ = V2.are_linearly_independent([v1, v2])
is_indep_123, coeff = V2.are_linearly_independent([v1, v2, v3])

print("Linear independence over F_2^3:")
print(f"  {v1}, {v2} independent: {is_indep_12}")
print(f"  {v1}, {v2}, {v3} independent: {is_indep_123}")
if not is_indep_123:
    print(f"  Dependence relation with coefficients: {coeff}\n")

# Compute span
vectors = [(1, 0, 0), (0, 1, 0)]
span = V2.compute_span(vectors)
print(f"Span of {vectors}:")
print(f"  Elements: {sorted(span)}")
print(f"  Size: {len(span)} = 2^{V2.dimension_of_span(vectors)}\n")

# Test over F_3
V3 = FiniteFieldVectorSpace(p=3, n=2)
w1 = (1, 0)
w2 = (2, 1)

span_3 = V3.compute_span([w1, w2])
dim_3 = V3.dimension_of_span([w1, w2])

print(f"Span of {[w1, w2]} over F_3^2:")
print(f"  Elements: {sorted(span_3)}")
print(f"  Size: {len(span_3)} = 3^{dim_3}")
```

Execute this implementation and verify that the vector space axioms hold. The vectors $(1,0,0)$ and $(0,1,0)$ are linearly independent over $\mathbb{F}_2^3$, but adding $(1,1,0)$ creates a dependence: $(1,1,0) = (1,0,0) + (0,1,0)$ with coefficients $(1,1,1)$ satisfying $1 \cdot (1,0,0) + 1 \cdot (0,1,0) + 1 \cdot (1,1,0) = (0,0,0)$ in $\mathbb{F}_2$.

The span of $(1,0,0)$ and $(0,1,0)$ over $\mathbb{F}_2$ contains exactly $2^2 = 4$ elements: $(0,0,0)$, $(1,0,0)$, $(0,1,0)$, $(1,1,0)$. The dimension formula $|\text{span}(S)| = p^{\dim(\text{span}(S))}$ holds precisely.

### Matrix Representations of Linear Transformations

A linear transformation $T: V \to W$ between vector spaces is uniquely determined by its action on a basis. Given bases $\mathcal{B}_V = \{v_1, \ldots, v_n\}$ for $V$ and $\mathcal{B}_W = \{w_1, \ldots, w_m\}$ for $W$, the matrix representation $[T]_{\mathcal{B}_V}^{\mathcal{B}_W}$ has columns equal to the coordinate vectors of $T(v_i)$ with respect to $\mathcal{B}_W$. Implement this construction explicitly, including change-of-basis transformations.

```python
import numpy as np
from numpy.linalg import solve

class LinearTransformation:
    """
    Linear transformation T: R^n -> R^m represented by matrix
    """
    def __init__(self, matrix, domain_basis=None, codomain_basis=None):
        """
        matrix: m x n matrix representing T
        domain_basis: n x n matrix with basis vectors as columns (default: standard basis)
        codomain_basis: m x m matrix with basis vectors as columns (default: standard basis)
        """
        self.matrix = np.array(matrix, dtype=float)
        self.m, self.n = self.matrix.shape
        
        if domain_basis is None:
            self.domain_basis = np.eye(self.n)
        else:
            self.domain_basis = np.array(domain_basis, dtype=float)
        
        if codomain_basis is None:
            self.codomain_basis = np.eye(self.m)
        else:
            self.codomain_basis = np.array(codomain_basis, dtype=float)
    
    def apply(self, v):
        """Apply transformation to vector v"""
        return self.matrix @ v
    
    def change_domain_basis(self, new_basis):
        """
        Compute matrix representation in new domain basis
        [T]_new = [T]_std @ P, where P is change-of-basis matrix
        P converts new basis coords to standard coords: P = [new_basis]
        So [T]_new = [T]_std @ [new_basis]^{-1}... actually:
        [T]_{B'}^{C} = [I]_C^{std} [T]_B^{std} [I]_{std}^{B'}
                     = [T] [new_basis]^{-1}
        """
        new_basis = np.array(new_basis, dtype=float)
        # Change of basis: if v' are coords in new basis, v = new_basis @ v'
        # So T(v) = T(new_basis @ v') = matrix @ new_basis @ v'
        # In new basis: [T]_new @ v' = [T]_std @ new_basis @ v'
        # Wait, need to express output in new basis too if we change both
        
        # Correct formula: [T]_{B'}^{C'} = [C']^{-1} [T]_B^C [B']
        new_domain_basis = new_basis
        P = new_domain_basis  # Columns are new basis vectors
        
        # Matrix in new domain basis (keeping codomain standard)
        new_matrix = self.matrix @ P
        
        return LinearTransformation(new_matrix, new_domain_basis, self.codomain_basis)
    
    def change_codomain_basis(self, new_basis):
        """Compute matrix representation with new codomain basis"""
        new_basis = np.array(new_basis, dtype=float)
        Q = new_basis
        
        # To express output in new basis, apply Q^{-1}
        Q_inv = np.linalg.inv(Q)
        new_matrix = Q_inv @ self.matrix
        
        return LinearTransformation(new_matrix, self.domain_basis, new_basis)
    
    def change_both_bases(self, new_domain_basis, new_codomain_basis):
        """Change both domain and codomain bases simultaneously"""
        P = np.array(new_domain_basis, dtype=float)
        Q = np.array(new_codomain_basis, dtype=float)
        Q_inv = np.linalg.inv(Q)
        
        # [T]_{B'}^{C'} = [Q]^{-1} [T] [P]
        new_matrix = Q_inv @ self.matrix @ P
        
        return LinearTransformation(new_matrix, P, Q)
    
    def kernel_basis(self):
        """Compute basis for kernel (null space)"""
        # Use SVD to find null space
        U, s, Vt = np.linalg.svd(self.matrix, full_matrices=True)
        
        # Null space corresponds to right singular vectors with zero singular values
        tolerance = 1e-10
        rank = np.sum(s > tolerance * s[0])
        null_basis = Vt[rank:].T
        
        return null_basis
    
    def image_basis(self):
        """Compute basis for image (column space)"""
        # Use SVD
        U, s, Vt = np.linalg.svd(self.matrix, full_matrices=False)
        
        # Image corresponds to left singular vectors with nonzero singular values
        tolerance = 1e-10
        rank = np.sum(s > tolerance * s[0])
        image_basis = U[:, :rank]
        
        return image_basis

# Example: Rotation transformation in R^2
theta = np.pi / 4  # 45 degrees
rotation_matrix = np.array([
    [np.cos(theta), -np.sin(theta)],
    [np.sin(theta), np.cos(theta)]
])

T_rot = LinearTransformation(rotation_matrix)

# Test application
v = np.array([1, 0])
v_rotated = T_rot.apply(v)
print(f"Rotation by 45°:")
print(f"  Original: {v}")
print(f"  Rotated: {v_rotated}\n")

# Change to non-standard basis: {(1,1), (1,-1)}
new_basis = np.array([[1, 1], [1, -1]]).T  # Columns are basis vectors
T_rot_new = T_rot.change_domain_basis(new_basis)

print(f"Rotation matrix in new basis:")
print(f"{T_rot_new.matrix}\n")

# Example: Projection onto subspace
# Project R^3 onto xy-plane (kernel of z-axis)
projection_matrix = np.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 0]
])

T_proj = LinearTransformation(projection_matrix)

kernel = T_proj.kernel_basis()
image = T_proj.image_basis()

print(f"Projection onto xy-plane:")
print(f"  Kernel basis (z-axis):\n{kernel}")
print(f"  Image basis (xy-plane):\n{image}")
print(f"  Rank: {image.shape[1]}, Nullity: {kernel.shape[1]}")
```

Execute this implementation and verify the change-of-basis formulas. The rotation matrix in the standard basis is $\begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$. In the basis $\{(1,1), (1,-1)\}$, the matrix representation changes to reflect the fact that $(1,1)$ and $(1,-1)$ are not eigenvectors of rotation (except for $\theta = \pi/2$).

For the projection, the kernel basis correctly identifies the $z$-axis as the null space, and the image basis spans the $xy$-plane, confirming that rank plus nullity equals the domain dimension: $2 + 1 = 3$.

### Canonical Forms: Jordan Normal Form Construction

Every square matrix over an algebraically closed field is similar to a Jordan normal form, a block-diagonal matrix where each block corresponds to an eigenvalue. The Jordan form exposes the geometric and algebraic multiplicities of eigenvalues and identifies the maximal chains of generalized eigenvectors. Implement the Jordan decomposition algorithm constructively, computing the Jordan blocks and transformation matrix.

```python
import numpy as np
from numpy.linalg import matrix_rank
import sympy as sp

def compute_jordan_form_sympy(A):
    """
    Compute Jordan normal form using SymPy for exact computation
    Returns (P, J) where A = P J P^{-1}
    """
    A_sympy = sp.Matrix(A)
    
    # Compute Jordan form
    P, J = A_sympy.jordan_form()
    
    return np.array(P).astype(float), np.array(J).astype(float)

def verify_jordan_decomposition(A, P, J):
    """Verify that A = P J P^{-1}"""
    P_inv = np.linalg.inv(P)
    A_reconstructed = P @ J @ P_inv
    
    error = np.linalg.norm(A - A_reconstructed)
    return error < 1e-10, error

def identify_jordan_blocks(J):
    """
    Parse Jordan form to identify blocks
    Returns list of (eigenvalue, block_size) tuples
    """
    n = J.shape[0]
    blocks = []
    i = 0
    
    while i < n:
        eigenvalue = J[i, i]
        block_size = 1
        
        # Check for 1's on superdiagonal (indicating Jordan block continuation)
        j = i
        while j < n - 1 and abs(J[j, j+1] - 1.0) < 1e-10:
            block_size += 1
            j += 1
        
        blocks.append((eigenvalue, block_size))
        i += block_size
    
    return blocks

# Test Case 1: Diagonalizable matrix
A1 = np.array([
    [2, 0],
    [0, 3]
], dtype=float)

P1, J1 = compute_jordan_form_sympy(A1)
valid1, error1 = verify_jordan_decomposition(A1, P1, J1)
blocks1 = identify_jordan_blocks(J1)

print("Diagonalizable matrix:")
print(f"  A = \n{A1}")
print(f"  Jordan form J = \n{J1}")
print(f"  Blocks: {blocks1}")
print(f"  Verification: {valid1}, error = {error1:.2e}\n")

# Test Case 2: Non-diagonalizable (nilpotent) matrix
A2 = np.array([
    [0, 1, 0],
    [0, 0, 1],
    [0, 0, 0]
], dtype=float)

P2, J2 = compute_jordan_form_sympy(A2)
valid2, error2 = verify_jordan_decomposition(A2, P2, J2)
blocks2 = identify_jordan_blocks(J2)

print("Nilpotent matrix (single Jordan block):")
print(f"  A = \n{A2}")
print(f"  Jordan form J = \n{J2}")
print(f"  Blocks: {blocks2}")
print(f"  Verification: {valid2}, error = {error2:.2e}\n")

# Test Case 3: Matrix with repeated eigenvalue, multiple blocks
A3 = np.array([
    [2, 1, 0, 0],
    [0, 2, 0, 0],
    [0, 0, 2, 1],
    [0, 0, 0, 2]
], dtype=float)

P3, J3 = compute_jordan_form_sympy(A3)
valid3, error3 = verify_jordan_decomposition(A3, P3, J3)
blocks3 = identify_jordan_blocks(J3)

print("Repeated eigenvalue with two Jordan blocks:")
print(f"  A = \n{A3}")
print(f"  Jordan form J = \n{J3}")
print(f"  Blocks: {blocks3}")
print(f"  Verification: {valid3}, error = {error3:.2e}\n")

# Compute generalized eigenvectors explicitly
def compute_generalized_eigenvectors(A, eigenvalue, algebraic_multiplicity):
    """
    Compute chain of generalized eigenvectors for given eigenvalue
    """
    n = A.shape[0]
    I = np.eye(n)
    A_shifted = A - eigenvalue * I
    
    # Compute kernels of increasing powers
    kernels = []
    for k in range(1, algebraic_multiplicity + 1):
        A_power = np.linalg.matrix_power(A_shifted, k)
        
        # Find null space
        U, s, Vt = np.linalg.svd(A_power, full_matrices=True)
        tolerance = 1e-10
        rank = np.sum(s > tolerance * s.max())
        null_space = Vt[rank:].T
        
        kernels.append((k, null_space))
    
    return kernels

# Test generalized eigenvectors for A2
eigenvalue_A2 = 0
alg_mult_A2 = 3
gen_eigenvecs = compute_generalized_eigenvectors(A2, eigenvalue_A2, alg_mult_A2)

print("Generalized eigenvectors for nilpotent matrix:")
for k, kernel in gen_eigenvecs:
    print(f"  Kernel of (A - {eigenvalue_A2}I)^{k}: dimension {kernel.shape[1]}")
```

Execute this Jordan form computation and observe the structure. The diagonalizable matrix yields two 1×1 Jordan blocks, one for each distinct eigenvalue. The nilpotent matrix produces a single 3×3 Jordan block with eigenvalue 0 and superdiagonal entries of 1. The matrix with repeated eigenvalue 2 decomposes into two 2×2 Jordan blocks, reflecting the fact that the geometric multiplicity (dimension of eigenspace) is 2 while the algebraic multiplicity is 4.

The generalized eigenvector computation reveals that for the nilpotent matrix, $\ker(A) = 1$, $\ker(A^2) = 2$, and $\ker(A^3) = 3$, demonstrating the filtration $\ker(A) \subset \ker(A^2) \subset \ker(A^3)$ that characterizes the Jordan block structure.

## Formal Axioms Cheat Sheet & Verification Reference

This cheat sheet summarizes the core axioms and computational verification strategies for linear algebraic structures. Use it as a reference when implementing formal structures or debugging computational anomalies.

### Vector Space Axioms (over field $\mathbb{F}$)

A vector space $V$ over field $\mathbb{F}$ satisfies eight axioms under addition $+: V \times V \to V$ and scalar multiplication $\cdot: \mathbb{F} \times V \to V$:

**Addition Axioms:**
1. **Commutativity:** $u + v = v + u$ for all $u, v \in V$
2. **Associativity:** $(u + v) + w = u + (v + w)$ for all $u, v, w \in V$
3. **Identity:** There exists $0 \in V$ such that $v + 0 = v$ for all $v \in V$
4. **Inverse:** For each $v \in V$, there exists $-v \in V$ such that $v + (-v) = 0$

**Scalar Multiplication Axioms:**
5. **Distributivity (vectors):** $c \cdot (u + v) = c \cdot u + c \cdot v$ for all $c \in \mathbb{F}$, $u, v \in V$
6. **Distributivity (scalars):** $(c + d) \cdot v = c \cdot v + d \cdot v$ for all $c, d \in \mathbb{F}$, $v \in V$
7. **Compatibility:** $(cd) \cdot v = c \cdot (d \cdot v)$ for all $c, d \in \mathbb{F}$, $v \in V$
8. **Identity:** $1 \cdot v = v$ for all $v \in V$, where $1$ is the multiplicative identity in $\mathbb{F}$

**Computational Verification:** Instantiate concrete vectors and scalars, perform operations, and assert equality. For finite fields, enumerate all elements to verify universally quantified axioms.

### Rank-Nullity Theorem

For linear transformation $T: V \to W$ with $\dim V = n$:

$$\text{rank}(T) + \text{nullity}(T) = n$$

where $\text{rank}(T) = \dim(\text{im}(T))$ and $\text{nullity}(T) = \dim(\ker(T))$.

**Verification:** Compute bases for kernel and image using SVD or row reduction. Count dimensions and verify sum.

### Determinant Properties

For $n \times n$ matrices $A$ and $B$:

1. **Multiplicativity:** $\det(AB) = \det(A) \det(B)$
2. **Transpose:** $\det(A^T) = \det(A)$
3. **Inverse:** $\det(A^{-1}) = 1/\det(A)$ if $A$ is invertible
4. **Scaling:** $\det(cA) = c^n \det(A)$ for scalar $c$
5. **Block triangular:** For block matrix $\begin{pmatrix} A & C \\ 0 & B \end{pmatrix}$, $\det = \det(A) \det(B)$

**Verification:** Use symbolic computation to verify identities. Test edge cases: identity, zero, singular matrices.

### Eigenvalue-Trace-Determinant Relations

For $n \times n$ matrix $A$ with eigenvalues $\lambda_1, \ldots, \lambda_n$ (counting multiplicities):

1. **Trace:** $\text{tr}(A) = \sum_{i=1}^n \lambda_i$
2. **Determinant:** $\det(A) = \prod_{i=1}^n \lambda_i$
3. **Characteristic polynomial:** $p_A(\lambda) = \det(\lambda I - A) = \prod_{i=1}^n (\lambda - \lambda_i)$

**Verification:** Compute eigenvalues numerically, then verify sum equals trace and product equals determinant.

### Cayley-Hamilton Theorem

Every square matrix $A$ satisfies its characteristic polynomial: $p_A(A) = 0$.

**Verification:** Compute $p_A(\lambda) = \sum_{k=0}^n c_k \lambda^k$, then evaluate $\sum_{k=0}^n c_k A^k$ and verify it equals the zero matrix.

### Spectral Theorem (Real Symmetric Matrices)

For real symmetric $A$ ($A = A^T$):

1. All eigenvalues are real
2. Eigenvectors corresponding to distinct eigenvalues are orthogonal
3. $A = Q \Lambda Q^T$ where $Q$ orthogonal ($Q^T Q = I$) and $\Lambda$ diagonal

**Verification:** Compute eigendecomposition, check $Q^T Q = I$ (orthogonality), verify $A = Q \Lambda Q^T$ (reconstruction).

### Singular Value Decomposition

For $m \times n$ matrix $A$:

$$A = U \Sigma V^T$$

where $U$ is $m \times m$ orthogonal, $V$ is $n \times n$ orthogonal, and $\Sigma$ is $m \times n$ diagonal with non-negative singular values $\sigma_1 \ge \sigma_2 \ge \cdots \ge \sigma_r > 0$ ($r = \text{rank}(A)$).

**Properties:**
- $\text{rank}(A) =$ number of nonzero singular values
- $\|A\|_2 = \sigma_1$ (spectral norm)
- $\kappa(A) = \sigma_1 / \sigma_r$ (condition number)

**Verification:** Compute SVD, verify $U^T U = I$, $V^T V = I$, and $A = U \Sigma V^T$.

### Jordan Normal Form

For $n \times n$ matrix $A$ over algebraically closed field, there exists invertible $P$ such that:

$$A = P J P^{-1}$$

where $J$ is block-diagonal with Jordan blocks $J_k(\lambda) = \begin{pmatrix} \lambda & 1 & & \\ & \lambda & \ddots & \\ & & \ddots & 1 \\ & & & \lambda \end{pmatrix}$.

**Properties:**
- Number of Jordan blocks for eigenvalue $\lambda$ equals geometric multiplicity
- Largest Jordan block size for eigenvalue $\lambda$ determines index of nilpotency of $(A - \lambda I)$

**Verification:** Compute Jordan form symbolically, verify $A = PJP^{-1}$, check block structure.

### Condition Number Bounds

For solving $Ax = b$, the relative error in solution satisfies:

$$\frac{\|\delta x\|}{\|x\|} \le \kappa(A) \left( \frac{\|\delta A\|}{\|A\|} + \frac{\|\delta b\|}{\|b\|} \right)$$

where $\kappa(A) = \|A\| \|A^{-1}\|$ is the condition number.

**Verification:** Generate ill-conditioned matrices with controlled $\kappa(A)$, introduce perturbations, measure error amplification, confirm bound.

### Moore-Penrose Pseudoinverse

For $m \times n$ matrix $A$, the pseudoinverse $A^+$ satisfies:

1. $A A^+ A = A$
2. $A^+ A A^+ = A^+$
3. $(A A^+)^T = A A^+$ (symmetric)
4. $(A^+ A)^T = A^+ A$ (symmetric)

**Construction via SVD:** $A^+ = V \Sigma^+ U^T$, where $\Sigma^+$ inverts nonzero singular values.

**Verification:** Compute $A^+$ via SVD, verify all four properties hold numerically.

This cheat sheet grounds your computational experiments in rigorous mathematical foundations. When verification fails, diagnose whether the failure stems from incorrect implementation, numerical instability, or a genuine violation of assumptions (e.g., applying symmetric matrix theorems to non-symmetric matrices). The interplay between formal axioms and computational reality is where true mathematical understanding emerges.
