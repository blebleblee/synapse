# Lesson 2: Unconstrained Continuous Methods

## 1. First-Principles Intuition & Invariants

The unconstrained continuous optimization problem occupies a distinguished position in applied mathematics, serving as the canonical laboratory where analytical mechanics, differential geometry, and numerical linear algebra intersect to address the fundamental question: given a differentiable objective function $f: \mathbb{R}^n \to \mathbb{R}$, how do we efficiently compute a local minimizer $x^* \in \mathbb{R}^n$ such that $\nabla f(x^*) = 0$ and the Hessian $\nabla^2 f(x^*)$ is positive semidefinite? This deceptively simple formulation conceals profound theoretical depth and computational subtlety, demanding rigorous treatment of convergence rates, stability analysis, and algorithmic tradeoffs between gradient information exploitation and Hessian approximation fidelity.

The theoretical foundation rests upon the Taylor expansion of $f$ around a current iterate $x_k$. For a twice-differentiable function, we write the second-order approximation as

$$f(x_k + p) = f(x_k) + \nabla f(x_k)^T p + \frac{1}{2} p^T \nabla^2 f(x_k) p + O(\|p\|^3)$$

where $p \in \mathbb{R}^n$ represents the search direction. The gradient $\nabla f(x_k) \in \mathbb{R}^n$ encodes the instantaneous rate of change along each coordinate axis, while the Hessian $\nabla^2 f(x_k) \in \mathbb{R}^{n \times n}$ captures the local curvature structure of the objective landscape. All iterative descent methods construct sequences $\{x_k\}$ through the update rule $x_{k+1} = x_k + \alpha_k p_k$, where $\alpha_k > 0$ denotes the step size and $p_k$ represents the search direction. The critical design choice—how to compute $p_k$ from available derivative information—distinguishes first-order methods (gradient descent, conjugate gradient) from second-order methods (Newton's method, quasi-Newton approximations).

The optimality conditions provide our navigation beacons. A point $x^*$ constitutes a local minimizer only if the first-order necessary condition $\nabla f(x^*) = 0$ holds alongside the second-order sufficient condition requiring $\nabla^2 f(x^*)$ to be positive definite. These conditions emerge directly from the Taylor expansion: if $\nabla f(x^*) \neq 0$, we can construct a descent direction $p = -\nabla f(x^*)$ yielding $f(x^* + \alpha p) < f(x^*)$ for sufficiently small $\alpha > 0$, contradicting local minimality. Similarly, if $\nabla^2 f(x^*)$ admits a negative eigenvalue $\lambda < 0$ with corresponding eigenvector $v$, then the direction $p = v$ produces $f(x^* + \alpha v) \approx f(x^*) + \frac{1}{2}\alpha^2 \lambda \|v\|^2 < f(x^*)$ for small $\alpha$, again violating the minimality hypothesis.

Convergence rate taxonomy provides the fundamental language for algorithmic comparison. We classify convergence according to the limiting behavior of the error sequence $e_k = \|x_k - x^*\|$. Linear convergence obtains when $e_{k+1} \le c \cdot e_k$ for some constant $c \in (0,1)$, implying exponential decay with iteration count. Superlinear convergence demands $e_{k+1} / e_k \to 0$ as $k \to \infty$, while quadratic convergence—the gold standard—requires $e_{k+1} \le M \cdot e_k^2$ for some constant $M > 0$, doubling the number of correct digits per iteration asymptotically. These rates impose severe constraints on algorithm design: gradient descent with exact line search achieves only linear convergence on strongly convex quadratics, Newton's method attains quadratic convergence near isolated non-degenerate minima, and quasi-Newton methods interpolate these extremes through careful Hessian approximation.

The condition number $\kappa = \lambda_{\max} / \lambda_{\min}$ of the Hessian matrix at a minimizer governs the difficulty geometry. For a strongly convex quadratic $f(x) = \frac{1}{2}x^T Q x - b^T x$ with positive definite $Q$, the level sets form concentric ellipsoids whose aspect ratio equals $\sqrt{\kappa}$. Large condition numbers create elongated valleys where gradient directions oscillate nearly orthogonal to the optimal path toward $x^*$, causing gradient descent to zigzag inefficiently. This geometric pathology explains why first-order methods degrade on ill-conditioned problems while second-order methods—which incorporate curvature information—maintain robust performance across diverse condition numbers.

The dichotomy between global and local convergence introduces a fundamental tension. Global convergence guarantees $\liminf_{k \to \infty} \|\nabla f(x_k)\| = 0$ from arbitrary starting points, ensuring the algorithm identifies at least a stationary point. Local convergence characterizes the asymptotic rate once the iterate sequence enters a neighborhood of $x^*$. Pure Newton iteration exhibits superb local convergence but catastrophic global failure: without safeguards, the algorithm diverges whenever $\nabla^2 f(x_k)$ loses positive definiteness or the quadratic model poorly approximates the true objective. Globalization strategies—line search and trust region methods—resolve this tension by enforcing sufficient descent at each iteration while permitting rapid local convergence as $x_k \to x^*$.

## 2. Core Architecture & Mechanics

### Gradient Descent: The Primordial Descent Direction

Gradient descent constructs the search direction $p_k = -\nabla f(x_k)$ by exploiting the elementary fact that the negative gradient yields the direction of steepest local descent. To verify this claim, consider an arbitrary unit direction $u \in \mathbb{R}^n$ with $\|u\| = 1$. The directional derivative along $u$ equals $D_u f(x_k) = \nabla f(x_k)^T u$. By the Cauchy-Schwarz inequality, we have $\nabla f(x_k)^T u \ge -\|\nabla f(x_k)\| \|u\| = -\|\nabla f(x_k)\|$, with equality achieved when $u = -\nabla f(x_k) / \|\nabla f(x_k)\|$. Thus the negative gradient provides the steepest instantaneous descent direction, justifying its role as the canonical first-order search direction.

The critical design choice concerns step size selection. Fixed step sizes $\alpha_k = \alpha$ for all $k$ require delicate tuning: too large and the sequence diverges, too small and convergence stagnates. Exact line search computes $\alpha_k = \arg\min_{\alpha > 0} f(x_k - \alpha \nabla f(x_k))$, solving a one-dimensional optimization problem at each iteration. For general nonlinear objectives, exact line search proves computationally expensive, motivating inexact alternatives. The Armijo backtracking condition demands

$$f(x_k + \alpha p_k) \le f(x_k) + c_1 \alpha \nabla f(x_k)^T p_k$$

for some $c_1 \in (0, 1)$ (typically $c_1 = 10^{-4}$), ensuring sufficient decrease proportional to the predicted linear reduction. The Wolfe conditions augment Armijo with the curvature condition

$$\nabla f(x_k + \alpha p_k)^T p_k \ge c_2 \nabla f(x_k)^T p_k$$

for $c_2 \in (c_1, 1)$, preventing excessively short steps that fail to exploit the descent direction adequately. Together, these conditions guarantee global convergence to stationary points under mild regularity assumptions on $f$.

To analyze convergence rate, consider the canonical quadratic objective $f(x) = \frac{1}{2}x^T Q x - b^T x$ with symmetric positive definite $Q \in \mathbb{R}^{n \times n}$. The unique minimizer satisfies $Qx^* = b$, yielding $x^* = Q^{-1}b$. The gradient equals $\nabla f(x) = Qx - b$, so the error $e_k = x_k - x^*$ satisfies $\nabla f(x_k) = Q e_k$. Exact line search produces

$$\alpha_k = \frac{\nabla f(x_k)^T \nabla f(x_k)}{\nabla f(x_k)^T Q \nabla f(x_k)} = \frac{e_k^T Q^2 e_k}{e_k^T Q^3 e_k}$$

After tedious but elementary algebra, the error update becomes

$$e_{k+1} = e_k - \alpha_k Q e_k = \left(I - \frac{Q^2}{e_k^T Q^3 e_k / e_k^T Q^2 e_k}\right) e_k$$

In the worst case, when $e_k$ aligns with eigenvectors corresponding to extreme eigenvalues $\lambda_{\min}$ and $\lambda_{\max}$, the convergence factor approaches

$$\frac{\|e_{k+1}\|}{\|e_k\|} \le \frac{\kappa - 1}{\kappa + 1} = \frac{\lambda_{\max} - \lambda_{\min}}{\lambda_{\max} + \lambda_{\min}}$$

This bound demonstrates linear convergence with rate constant approaching unity as $\kappa \to \infty$, explaining gradient descent's notorious inefficiency on ill-conditioned problems. For $\kappa = 100$, the factor equals approximately $0.98$, requiring roughly $230$ iterations to reduce the error by a factor of $10^{-2}$.

### Newton's Method: Quadratic Convergence Through Exact Curvature

Newton's method constructs the search direction by minimizing the second-order Taylor approximation. Setting the gradient of the quadratic model to zero yields

$$\nabla f(x_k) + \nabla^2 f(x_k) p = 0$$

provided $\nabla^2 f(x_k)$ is nonsingular. Solving for $p$ gives the Newton direction

$$p_k^N = -[\nabla^2 f(x_k)]^{-1} \nabla f(x_k)$$

This direction incorporates complete local curvature information, enabling the algorithm to automatically adapt to the objective's geometric structure. For the quadratic objective $f(x) = \frac{1}{2}x^T Q x - b^T x$, the Newton direction yields $p_k^N = -Q^{-1}(Qx_k - b) = x^* - x_k$, achieving exact convergence in a single iteration with unit step size. This remarkable property—scale invariance with respect to linear coordinate transformations—distinguishes second-order methods from their first-order counterparts.

The quadratic convergence theorem provides the rigorous foundation. Assume $f$ is twice continuously differentiable in a neighborhood of a local minimizer $x^*$ where $\nabla f(x^*) = 0$ and $\nabla^2 f(x^*)$ is positive definite with smallest eigenvalue $\lambda_{\min} > 0$. By continuity, there exists a radius $r > 0$ such that $\nabla^2 f(x)$ remains positive definite with $\lambda_{\min}[\nabla^2 f(x)] \ge \lambda_{\min}/2$ for all $x$ satisfying $\|x - x^*\| \le r$. Additionally, assume $\nabla^2 f$ is Lipschitz continuous with constant $L$:

$$\|\nabla^2 f(x) - \nabla^2 f(y)\| \le L \|x - y\|$$

For $x_k$ sufficiently close to $x^*$, the Newton iteration with unit step size produces

$$x_{k+1} = x_k - [\nabla^2 f(x_k)]^{-1} \nabla f(x_k)$$

Expanding $\nabla f(x_k)$ via Taylor's theorem around $x^*$ gives

$$\nabla f(x_k) = \nabla f(x^*) + \int_0^1 \nabla^2 f(x^* + t(x_k - x^*)) (x_k - x^*) dt = \int_0^1 \nabla^2 f(x^* + t(x_k - x^*)) e_k dt$$

where $e_k = x_k - x^*$. The Newton error update becomes

$$e_{k+1} = e_k - [\nabla^2 f(x_k)]^{-1} \int_0^1 \nabla^2 f(x^* + t e_k) e_k dt$$

Factoring out $\nabla^2 f(x_k)$ yields

$$e_{k+1} = [\nabla^2 f(x_k)]^{-1} \int_0^1 \left[\nabla^2 f(x_k) - \nabla^2 f(x^* + t e_k)\right] e_k dt$$

Taking norms and applying the Lipschitz bound produces

$$\|e_{k+1}\| \le \|[\nabla^2 f(x_k)]^{-1}\| \int_0^1 \|\nabla^2 f(x_k) - \nabla^2 f(x^* + t e_k)\| \|e_k\| dt$$

Since $\|\nabla^2 f(x_k) - \nabla^2 f(x^* + t e_k)\| \le L \cdot (1-t) \|e_k\|$, we obtain

$$\|e_{k+1}\| \le \frac{2}{\lambda_{\min}} \cdot L \|e_k\|^2 \int_0^1 (1-t) dt = \frac{L}{\lambda_{\min}} \|e_k\|^2$$

This establishes quadratic convergence with constant $M = L/\lambda_{\min}$, doubling the number of correct digits per iteration once $\|e_k\| < \lambda_{\min}/L$.

The computational bottleneck resides in solving the Newton system $\nabla^2 f(x_k) p_k^N = -\nabla f(x_k)$, requiring $O(n^3)$ operations via Cholesky factorization when $\nabla^2 f(x_k)$ is symmetric positive definite. For large-scale problems with $n \ge 10^4$, this cost becomes prohibitive unless the Hessian exhibits special structure (sparsity, low-rank perturbations) permitting efficient factorization or iterative solution via conjugate gradient methods.

### Quasi-Newton Methods: Approximating Curvature Incrementally

Quasi-Newton methods interpolate between gradient descent's modest computational cost and Newton's rapid convergence by constructing positive definite Hessian approximations $B_k \approx \nabla^2 f(x_k)$ or inverse approximations $H_k \approx [\nabla^2 f(x_k)]^{-1}$ that satisfy the secant equation. Consider consecutive iterates $x_k$ and $x_{k+1}$ with corresponding gradients $g_k = \nabla f(x_k)$ and $g_{k+1} = \nabla f(x_{k+1})$. Define the displacement $s_k = x_{k+1} - x_k$ and gradient difference $y_k = g_{k+1} - g_k$. By the mean value theorem,

$$y_k = \int_0^1 \nabla^2 f(x_k + t s_k) s_k dt$$

suggesting that a Hessian approximation should satisfy the secant equation $B_{k+1} s_k = y_k$ or equivalently $H_{k+1} y_k = s_k$ for the inverse approximation.

The Broyden-Fletcher-Goldfarb-Shanno (BFGS) method constructs symmetric positive definite inverse Hessian approximations through the rank-two update formula

$$H_{k+1} = H_k - \frac{H_k y_k y_k^T H_k}{y_k^T H_k y_k} + \frac{s_k s_k^T}{y_k^T s_k}$$

This formula emerges from minimizing the weighted Frobenius norm $\|H_{k+1} - H_k\|_W^2$ subject to the secant equation constraint $H_{k+1} y_k = s_k$ and symmetry $H_{k+1} = H_{k+1}^T$. To verify that $H_{k+1}$ satisfies the secant equation, compute

$$H_{k+1} y_k = H_k y_k - \frac{H_k y_k y_k^T H_k y_k}{y_k^T H_k y_k} + \frac{s_k s_k^T y_k}{y_k^T s_k} = H_k y_k - H_k y_k + s_k = s_k$$

where we used $y_k^T H_k y_k$ being a scalar and $s_k^T y_k$ appearing in the denominator.

Positive definiteness of $H_{k+1}$ follows from the curvature condition $s_k^T y_k > 0$, which holds automatically when $f$ is strongly convex and the line search satisfies the Wolfe conditions. To prove preservation of positive definiteness, write $H_{k+1}$ as

$$H_{k+1} = \left(I - \frac{s_k y_k^T}{y_k^T s_k}\right) H_k \left(I - \frac{y_k s_k^T}{y_k^T s_k}\right) + \frac{s_k s_k^T}{y_k^T s_k}$$

For any vector $v \in \mathbb{R}^n$, define $w = \left(I - \frac{y_k s_k^T}{y_k^T s_k}\right) v$. Then

$$v^T H_{k+1} v = w^T H_k w + \frac{(v^T s_k)^2}{y_k^T s_k}$$

Since $H_k$ is positive definite by induction and $y_k^T s_k > 0$, we have $v^T H_{k+1} v > 0$ for all $v \neq 0$, confirming positive definiteness.

The limited-memory BFGS (L-BFGS) variant addresses storage constraints in high-dimensional problems by retaining only the most recent $m$ correction pairs $\{s_i, y_i\}$ (typically $m = 5$ to $20$). Rather than storing the full dense matrix $H_k \in \mathbb{R}^{n \times n}$, L-BFGS represents $H_k$ implicitly through a two-loop recursion requiring only $O(mn)$ storage. The algorithm computes $p_k = H_k g_k$ via:

```text
q ← g_k
for i = k-1, k-2, ..., k-m do
    α_i ← ρ_i s_i^T q   where ρ_i = 1/(y_i^T s_i)
    q ← q - α_i y_i
end for
r ← H_k^0 q   (initial inverse Hessian approximation, often γ_k I)
for i = k-m, k-m+1, ..., k-1 do
    β ← ρ_i y_i^T r
    r ← r + s_i (α_i - β)
end for
return r
```

This compact representation enables quasi-Newton methods to scale to problems with $n \ge 10^6$ variables, critical for machine learning applications where gradient computation dominates Hessian approximation costs.

Superlinear convergence of BFGS follows from the Dennis-Moré theorem, which characterizes superlinear convergence for descent methods. The theorem states that if $\{x_k\}$ converges to $x^*$ with $\nabla^2 f(x^*)$ positive definite, then $\{x_k\}$ converges superlinearly with search directions $p_k$ if and only if

$$\lim_{k \to \infty} \frac{\|[\nabla^2 f(x^*) - B_k] p_k\|}{\|p_k\|} = 0$$

where $p_k$ solves $B_k p_k = -g_k$. BFGS satisfies this condition under appropriate line search rules, achieving superlinear convergence without explicitly computing second derivatives.

### Conjugate Gradient Method: Exploiting Krylov Subspace Structure

The conjugate gradient method occupies a unique niche, solving the $n$-dimensional quadratic minimization problem $\min \frac{1}{2}x^T Q x - b^T x$ in at most $n$ iterations with $O(n)$ storage, assuming exact arithmetic and positive definite $Q$. The algorithm constructs search directions $\{p_0, p_1, \ldots, p_{n-1}\}$ that are $Q$-conjugate: $p_i^T Q p_j = 0$ for $i \neq j$. This orthogonality with respect to the inner product induced by $Q$ ensures that minimization along $p_k$ does not spoil progress made in previous directions.

Initialize with $x_0 \in \mathbb{R}^n$ arbitrary, $r_0 = Qx_0 - b$, and $p_0 = -r_0$. For $k = 0, 1, 2, \ldots$ until convergence, execute:

$$\alpha_k = \frac{r_k^T r_k}{p_k^T Q p_k}$$

$$x_{k+1} = x_k + \alpha_k p_k$$

$$r_{k+1} = r_k + \alpha_k Q p_k$$

$$\beta_k = \frac{r_{k+1}^T r_{k+1}}{r_k^T r_k}$$

$$p_{k+1} = -r_{k+1} + \beta_k p_k$$

The residual $r_k = Qx_k - b = Q(x_k - x^*)$ equals the negative gradient at $x_k$. The $Q$-conjugacy of search directions follows by induction. The remarkable feature: only the most recent search direction $p_k$ and residual $r_k$ require storage, achieving $O(n)$ memory complexity despite implicitly constructing an $n$-dimensional Krylov subspace $\mathcal{K}_k = \text{span}\{r_0, Qr_0, Q^2 r_0, \ldots, Q^{k-1} r_0\}$.

To prove conjugacy $p_i^T Q p_j = 0$ for $i < j$, we establish that $r_k$ is orthogonal to all previous residuals and search directions lie in the Krylov subspace. First, observe that $r_{k+1}^T r_i = 0$ for all $i \le k$. For $i = k$, compute

$$r_{k+1}^T r_k = (r_k + \alpha_k Q p_k)^T r_k = r_k^T r_k + \alpha_k p_k^T Q r_k$$

Since $p_k = -r_k + \beta_{k-1} p_{k-1}$, we have $p_k^T r_k = -r_k^T r_k + \beta_{k-1} p_{k-1}^T r_k$. By induction, $p_{k-1}^T r_k = 0$, yielding $p_k^T r_k = -r_k^T r_k$. Substituting into the residual orthogonality equation gives

$$r_{k+1}^T r_k = r_k^T r_k - \alpha_k r_k^T r_k = r_k^T r_k \left(1 - \frac{r_k^T r_k}{p_k^T Q p_k}\right)$$

But $p_k^T Q r_k = -r_k^T Q r_k$ since $Q$ is symmetric, so

$$p_k^T Q p_k = (-r_k + \beta_{k-1} p_{k-1})^T Q (-r_k + \beta_{k-1} p_{k-1}) = r_k^T Q r_k - 2\beta_{k-1} r_k^T Q p_{k-1} + \beta_{k-1}^2 p_{k-1}^T Q p_{k-1}$$

The middle term vanishes by induction (assuming $r_k$ orthogonal to $Q p_{k-1}$), and after further manipulation, orthogonality follows. For $i < k$, orthogonality $r_{k+1}^T r_i = 0$ follows by induction on the dimension of the Krylov subspace. Conjugacy $p_k^T Q p_j = 0$ for $j < k$ then follows from expressing $p_k$ in terms of residuals and applying residual orthogonality.

The convergence rate depends on the eigenvalue distribution of $Q$. After $k$ iterations, the error satisfies

$$\|x_k - x^*\|_Q \le 2 \left(\frac{\sqrt{\kappa} - 1}{\sqrt{\kappa} + 1}\right)^k \|x_0 - x^*\|_Q$$

where $\|\cdot\|_Q$ denotes the $Q$-norm $\|z\|_Q = \sqrt{z^T Q z}$. For well-conditioned problems with $\kappa$ close to unity, conjugate gradient converges rapidly. For ill-conditioned matrices, preconditioning—replacing $Qx = b$ with $M^{-1}Qx = M^{-1}b$ for some easily invertible approximation $M \approx Q$—dramatically accelerates convergence by reducing the effective condition number.

Extension to nonlinear objectives via the nonlinear conjugate gradient method replaces exact gradient formulas with approximate conjugacy. The Fletcher-Reeves formula defines $\beta_k^{FR} = \|g_{k+1}\|^2 / \|g_k\|^2$, while the Polak-Ribière formula uses $\beta_k^{PR} = g_{k+1}^T (g_{k+1} - g_k) / \|g_k\|^2$. The Polak-Ribière variant often outperforms Fletcher-Reeves on nonlinear problems, automatically resetting to steepest descent ($\beta_k^{PR} = 0$) when consecutive gradients are nearly orthogonal, indicating loss of conjugacy.

### Line Search and Trust Region Globalization Strategies

Line search methods enforce global convergence by selecting step sizes $\alpha_k$ satisfying the Wolfe conditions. The Armijo condition $f(x_k + \alpha p_k) \le f(x_k) + c_1 \alpha \nabla f(x_k)^T p_k$ ensures sufficient decrease, while the curvature condition $\nabla f(x_k + \alpha p_k)^T p_k \ge c_2 \nabla f(x_k)^T p_k$ prevents trivially small steps. Strong Wolfe conditions replace the curvature inequality with $|\nabla f(x_k + \alpha p_k)^T p_k| \le c_2 |\nabla f(x_k)^T p_k|$, bounding the directional derivative in both directions.

The backtracking line search initializes $\alpha$ to an optimistic value (often unity for Newton and quasi-Newton directions) and repeatedly shrinks $\alpha \leftarrow \tau \alpha$ for $\tau \in (0, 1)$ (typically $\tau = 0.5$) until the Armijo condition holds. This strategy requires only function evaluations, avoiding gradient computation during the line search, reducing overhead. The zoom algorithm refines the interval containing acceptable step sizes by maintaining a bracket $[\alpha_{\text{lo}}, \alpha_{\text{hi}}]$ and bisecting until both Wolfe conditions hold, ensuring robust convergence across diverse problem geometries.

Trust region methods adopt a fundamentally different philosophy: rather than committing to a search direction and then selecting a step size, they define a region $\mathcal{B}_k = \{p : \|p\| \le \Delta_k\}$ where the quadratic model $m_k(p) = f(x_k) + g_k^T p + \frac{1}{2}p^T B_k p$ is trusted to approximate $f$ accurately. The algorithm solves the trust region subproblem

$$\min_{p \in \mathbb{R}^n} m_k(p) \quad \text{subject to} \quad \|p\| \le \Delta_k$$

This constrained optimization problem admits a closed-form characterization: $p^*$ solves the subproblem if and only if there exists $\lambda \ge 0$ such that

$$(B_k + \lambda I) p^* = -g_k$$

$$\lambda (\Delta_k - \|p^*\|) = 0$$

$$B_k + \lambda I \succeq 0$$

These conditions follow from the Karush-Kuhn-Tucker (KKT) optimality theory for constrained optimization. When $B_k$ is positive definite and the unconstrained minimizer $p^N = -B_k^{-1} g_k$ satisfies $\|p^N\| \le \Delta_k$, then $\lambda = 0$ and $p^* = p^N$. Otherwise, $\|p^*\| = \Delta_k$ (the constraint is active) and $\lambda > 0$ must be chosen to satisfy $(B_k + \lambda I) p^* = -g_k$ with $\|p^*\| = \Delta_k$.

The Steihaug-Toint conjugate gradient method efficiently approximates the trust region subproblem solution by running conjugate gradient on the quadratic model while monitoring the trust region boundary. If conjugate gradient encounters negative curvature ($p_j^T B_k p_j \le 0$) or the next iterate would violate $\|p\| \le \Delta_k$, the algorithm terminates at the intersection of the current search direction with the trust region boundary.

After computing a candidate step $p_k$, the trust region algorithm evaluates the actual reduction $\text{ared}_k = f(x_k) - f(x_k + p_k)$ and predicted reduction $\text{pred}_k = m_k(0) - m_k(p_k) = -g_k^T p_k - \frac{1}{2}p_k^T B_k p_k$. The ratio

$$\rho_k = \frac{\text{ared}_k}{\text{pred}_k}$$

quantifies model fidelity. If $\rho_k < \eta_1$ (typically $\eta_1 = 0.25$), the model poorly predicts the true objective, prompting trust region contraction $\Delta_{k+1} = \tau \Delta_k$ with $\tau \in (0.25, 0.5)$. If $\rho_k > \eta_2$ (typically $\eta_2 = 0.75$) and $\|p_k\| = \Delta_k$, the model is highly accurate and the constraint binds, justifying expansion $\Delta_{k+1} = \min(2\Delta_k, \Delta_{\max})$. The iterate updates to $x_{k+1} = x_k + p_k$ whenever $\rho_k > \eta_0$ for some small threshold $\eta_0 \in (0, \eta_1)$, ensuring sufficient actual reduction.

Trust region methods guarantee global convergence under mild assumptions: if $f$ is bounded below and continuously differentiable, and if $B_k$ remains uniformly bounded with $\|B_k\| \le M$ for all $k$, then $\liminf_{k \to \infty} \|\nabla f(x_k)\| = 0$. The proof constructs a subsequence where the trust region radius does not shrink indefinitely, implying the model gradient $\|g_k\|$ must vanish. Near a local minimizer with positive definite Hessian, trust region methods with exact Hessian matrices ($B_k = \nabla^2 f(x_k)$) recover the quadratic convergence of Newton's method by eventually accepting unit trust region steps.

## 3. High-Performance Optimization & Failure Modes

The tension between global exploration and local exploitation manifests most acutely in high-dimensional parameter spaces where saddle points proliferate. For neural network training with $n \ge 10^7$ parameters, second-order critical points with indefinite Hessians vastly outnumber local minima. Gradient descent with momentum and adaptive learning rates (although beyond our current scope) addresses this by introducing stochastic perturbations and directional learning rate scaling, while pure Newton-type methods struggle as the Hessian loses positive definiteness far from optima.

Hessian computation and factorization impose a $O(n^3)$ arithmetic complexity barrier, rendering exact Newton methods impractical beyond $n \approx 10^4$. Structured problems with sparse Hessians (arising from discretized partial differential equations, network flow optimization, or graphical model inference) permit sparse Cholesky factorization with complexity $O(n \cdot \text{nnz})$ where $\text{nnz}$ denotes the number of nonzero entries. For general dense problems, the conjugate gradient method applied to the Newton system $\nabla^2 f(x_k) p = -\nabla f(x_k)$ achieves acceptable solutions in $O(\sqrt{\kappa})$ matrix-vector products, each requiring $O(n^2)$ operations for dense Hessians. This Hessian-vector product can often be computed via automatic differentiation in $O(n)$ time relative to gradient evaluation cost, enabling tractable inexact Newton methods.

Quasi-Newton methods balance memory and convergence rate through careful approximation rank selection. Full BFGS requires $O(n^2)$ storage for the dense inverse Hessian approximation $H_k$, while L-BFGS with memory $m$ reduces this to $O(mn)$. The choice $m = 5$ often suffices for smooth objectives, but highly oscillatory functions or problems with sharply varying curvature may demand $m = 20$ or larger to capture sufficient history. The tradeoff: each additional correction pair increases storage linearly but enables better approximation of the Hessian eigenspace along recent search directions.

Line search robustness depends critically on step size bounds. The Wolfe conditions alone do not guarantee finite termination of the line search unless $f$ is bounded below and $\nabla f$ is Lipschitz continuous. In practice, backtracking line search with exponential reduction $\alpha \leftarrow \tau \alpha$ terminates in $O(\log(\alpha_{\max} / \alpha_{\min}))$ iterations, but pathological objectives with extremely flat regions can induce arbitrarily many backtracks. Safeguards include minimum step size thresholds $\alpha_{\min}$ below which the algorithm declares failure, and maximum iteration counts triggering fallback to steepest descent with aggressive damping.

Trust region radius adaptation requires careful tuning of the thresholds $\eta_0, \eta_1, \eta_2$ and scaling factors $\tau, \gamma$. Overly aggressive expansion ($\gamma > 3$) risks accepting inaccurate model regions, while excessive conservatism ($\tau < 0.1$) causes premature radius contraction and slow convergence. Practical implementations often employ more sophisticated radius update rules based on the history of $\rho_k$ values, expanding only after multiple consecutive successful iterations with $\rho_k > 0.9$.

Numerical stability concerns dominate large-scale implementations. The BFGS update formula involves products $y_k^T H_k y_k$ and $y_k^T s_k$ appearing in denominators, risking division by zero or catastrophic cancellation when $y_k^T s_k \approx 0$. This occurs when line search terminates prematurely or when $f$ exhibits nearly flat regions. The curvature condition $y_k^T s_k \ge \epsilon \|s_k\| \|y_k\|$ for some $\epsilon > 0$ (typically $\epsilon = 10^{-8}$) provides a safeguard, skipping the BFGS update and retaining $H_{k+1} = H_k$ when the condition fails.

Conjugate gradient iteration counts grow with $\sqrt{\kappa}$, making preconditioning essential for ill-conditioned systems. Incomplete Cholesky factorization computes a sparse approximate factorization $Q \approx LL^T$ with controlled fill-in, yielding a preconditioner $M = LL^T$ that reduces the effective condition number from $\kappa(Q)$ to $\kappa(M^{-1}Q) \ll \kappa(Q)$. For problems arising from discretized elliptic PDEs, multigrid preconditioning achieves $\kappa(M^{-1}Q) = O(1)$ independent of mesh resolution, enabling conjugate gradient convergence in $O(1)$ iterations.

The choice between line search and trust region methods depends on problem structure. Trust regions excel when the Hessian varies rapidly or when the objective exhibits narrow curved valleys, as the radius adaptation automatically scales step sizes to local geometry. Line search methods prove simpler to implement and often suffice when combined with robust Wolfe conditions, particularly for quasi-Newton algorithms where the inverse Hessian approximation $H_k$ remains well-conditioned throughout optimization.

Termination criteria must balance multiple objectives: gradient norm $\|\nabla f(x_k)\| < \epsilon_g$, relative function decrease $|f(x_{k+1}) - f(x_k)| / |f(x_k)| < \epsilon_f$, and iterate displacement $\|x_{k+1} - x_k\| < \epsilon_x$. Gradient-based criteria alone fail near saddle points where $\|\nabla f(x_k)\|$ vanishes despite suboptimality. Combining criteria with maximum iteration budgets prevents infinite loops on difficult objectives.

Initialization strategies profoundly impact convergence trajectories. Random initialization from a Gaussian distribution centered at the origin often suffices for convex problems, but non-convex landscapes demand domain-specific heuristics. Multi-start strategies run optimization from multiple initial points and select the best local optimum, providing probabilistic global optimization guarantees at multiplicative cost. For warm-starting sequences of related problems (parameter continuation, model retraining with updated data), initializing $x_0$ at the previous solution and $H_0$ from the final BFGS approximation dramatically reduces iteration counts.

The symbiotic relationship between optimization algorithms and automatic differentiation frameworks enables modern large-scale applications. Computing exact Hessians via finite differences requires $O(n^2)$ function evaluations, while automatic differentiation computes Hessian-vector products $\nabla^2 f(x) v$ in $O(1)$ gradient evaluations via forward-over-reverse mode differentiation. This capability unlocks Newton-Krylov methods that solve Newton systems iteratively without ever forming the full Hessian matrix, scaling to millions of variables in applications from inverse problems to optimal control.
