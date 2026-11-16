# Lesson 3: Finite Difference Differentiation, Quadrature Rules, Convergence Orders

## 1. First-Principles Intuition & Invariants

The calculus of Newton and Leibniz provides a symbolic language for rates of change and accumulation, but when we step from the realm of closed-form expressions into the domain of discrete computation, we face a fundamental epistemological shift. A computer cannot manipulate infinitesimals or evaluate limits in the analytical sense; it operates on finite grids of floating-point numbers. Numerical differentiation and integration therefore constitute a bridge between continuous mathematics and discrete arithmetic, and this bridge is constructed from two profound ideas: Taylor series expansion and polynomial interpolation.

Consider the problem of differentiating a function $f : \mathbb{R} \to \mathbb{R}$ at a point $x_0$ when we possess only a finite set of function evaluations $\{f(x_0 + jh) : j \in \mathbb{Z}\}$ on a uniform grid with spacing $h > 0$. The analytical derivative $f'(x_0) = \lim_{h \to 0} \frac{f(x_0 + h) - f(x_0)}{h}$ is an idealization that assumes we can shrink $h$ to zero while maintaining perfect arithmetic precision. In finite-precision computation, this limit process fails catastrophically: as $h$ decreases, the numerator $f(x_0 + h) - f(x_0)$ suffers from catastrophic cancellation, amplifying relative roundoff errors until the computed derivative bears no resemblance to the true value. The art of finite difference methods lies in balancing two competing error sources—truncation error from the discrete approximation and roundoff error from floating-point arithmetic.

The Taylor expansion furnishes the key to understanding truncation error. Suppose $f$ is sufficiently smooth in a neighborhood of $x_0$. Then we may write

$$f(x_0 + h) = f(x_0) + h f'(x_0) + \frac{h^2}{2} f''(x_0) + \frac{h^3}{6} f'''(x_0) + \cdots = \sum_{k=0}^{\infty} \frac{h^k}{k!} f^{(k)}(x_0)$$

provided the series converges. Rearranging to isolate $f'(x_0)$, we obtain

$$f'(x_0) = \frac{f(x_0 + h) - f(x_0)}{h} - \frac{h}{2} f''(x_0) - \frac{h^2}{6} f'''(x_0) - \cdots$$

The expression $\frac{f(x_0 + h) - f(x_0)}{h}$ is the forward difference approximation, and the remainder terms constitute the truncation error. The leading error term is $-\frac{h}{2} f''(x_0)$, which is first-order in $h$. We write this compactly as $\mathcal{O}(h)$, meaning the error behaves asymptotically like $C h$ for some constant $C$ dependent on $f''$ as $h \to 0$.

The same Taylor machinery generates higher-order approximations by combining evaluations at multiple grid points. Expanding $f(x_0 - h)$ in the opposite direction,

$$f(x_0 - h) = f(x_0) - h f'(x_0) + \frac{h^2}{2} f''(x_0) - \frac{h^3}{6} f'''(x_0) + \cdots$$

we can subtract the forward expansion from the backward expansion to cancel the even-order terms:

$$f(x_0 + h) - f(x_0 - h) = 2h f'(x_0) + \frac{2h^3}{6} f'''(x_0) + \cdots$$

yielding the centered difference formula

$$f'(x_0) = \frac{f(x_0 + h) - f(x_0 - h)}{2h} + \mathcal{O}(h^2)$$

The truncation error is now second-order, giving quadratic convergence as $h$ decreases. This principle generalizes: by forming linear combinations of function evaluations at strategically chosen points, we can construct finite difference stencils of arbitrarily high order, limited only by the smoothness of $f$ and the stability of the resulting algebraic system.

Numerical integration, or quadrature, presents the dual problem: approximate the definite integral $I(f) = \int_a^b f(x) \, dx$ using only finitely many function evaluations. The Riemann sum $\sum_{j=0}^{n-1} f(a + jh) h$ with $h = (b - a)/n$ is the simplest quadrature rule, but it converges slowly at rate $\mathcal{O}(h)$. The fundamental insight, due to Newton and Cotes in the 17th century, is that we can integrate a polynomial interpolant of $f$ exactly, and if $f$ is smooth, this interpolant will closely approximate $f$ itself.

Let $p_n(x)$ be the unique polynomial of degree at most $n$ that interpolates $f$ at the nodes $x_0, x_1, \ldots, x_n$ in $[a, b]$. Then $\int_a^b p_n(x) \, dx$ can be computed analytically, and the quadrature error is $\int_a^b [f(x) - p_n(x)] \, dx$. The Lagrange interpolation formula expresses $p_n$ as

$$p_n(x) = \sum_{j=0}^n f(x_j) \ell_j(x), \quad \ell_j(x) = \prod_{k \neq j} \frac{x - x_k}{x_j - x_k}$$

so the quadrature rule becomes

$$\int_a^b f(x) \, dx \approx \sum_{j=0}^n w_j f(x_j), \quad w_j = \int_a^b \ell_j(x) \, dx$$

The weights $w_j$ depend only on the node positions, not on $f$. This is the Newton-Cotes family: the trapezoidal rule ($n = 1$), Simpson's rule ($n = 2$), and higher-order variants are all instances of this construction.

The convergence order of a quadrature rule is determined by its degree of exactness: the highest polynomial degree $d$ for which the rule integrates all polynomials of degree at most $d$ exactly. Newton-Cotes rules based on $n+1$ equally spaced nodes have degree of exactness $n$ (or $n+1$ if $n$ is even, due to symmetry), but there exist superior node placements. Gaussian quadrature, discovered by Gauss in 1814, achieves degree of exactness $2n + 1$ using only $n + 1$ nodes by positioning them at the zeros of orthogonal polynomials. This doubling of exactness degree is a deep consequence of the orthogonality properties of Legendre polynomials on $[-1, 1]$.

The theoretical bedrock of quadrature error analysis is the Peano kernel theorem, which represents the error functional $E(f) = I(f) - Q(f)$ as an integral of $f^{(k)}$ against a kernel function determined by the rule itself. For smooth integrands, this yields error bounds of the form $|E(f)| \leq C h^{p+1} \|f^{(p+1)}\|_{\infty}$, where $p$ is the degree of exactness and $C$ depends on the interval length and the rule's kernel. This $h$-dependence governs the computational cost of achieving a target accuracy: a method of order $p$ requires $\mathcal{O}(\epsilon^{-1/p})$ function evaluations to attain error $\epsilon$.

## 2. Core Architecture & Mechanics

The systematic derivation of finite difference stencils begins with the method of undetermined coefficients applied to Taylor expansions. Suppose we wish to approximate $f^{(m)}(x_0)$, the $m$-th derivative at $x_0$, using function values at $x_0 + s_j h$ for $j = 0, 1, \ldots, n$, where the stencil offsets $s_j \in \mathbb{Z}$ are given. We seek coefficients $c_j$ such that

$$f^{(m)}(x_0) \approx \frac{1}{h^m} \sum_{j=0}^n c_j f(x_0 + s_j h)$$

Expanding each function evaluation in a Taylor series around $x_0$,

$$f(x_0 + s_j h) = \sum_{k=0}^{\infty} \frac{(s_j h)^k}{k!} f^{(k)}(x_0)$$

and substituting into the linear combination,

$$\sum_{j=0}^n c_j f(x_0 + s_j h) = \sum_{k=0}^{\infty} \frac{h^k}{k!} f^{(k)}(x_0) \sum_{j=0}^n c_j s_j^k$$

For this expression to equal $h^m f^{(m)}(x_0)$ through order $h^p$ (where $p > m$ determines the truncation error order), we require the coefficients to satisfy the linear system

$$\sum_{j=0}^n c_j s_j^k = \begin{cases} k! & \text{if } k = m \\ 0 & \text{if } 0 \leq k < m \text{ or } m < k \leq p \end{cases}$$

This is a Vandermonde-like system in the unknowns $c_j$. Once solved, the truncation error is determined by the first unsatisfied equation, typically yielding $\mathcal{O}(h^{p+1-m})$ accuracy.

For the centered second-order approximation to $f'(x_0)$ using stencil offsets $s_0 = -1, s_1 = 0, s_2 = 1$, we solve

$$\begin{aligned}
c_{-1} + c_0 + c_1 &= 0 \quad (k=0) \\
-c_{-1} + 0 \cdot c_0 + c_1 &= 1 \quad (k=1) \\
c_{-1} + 0 \cdot c_0 + c_1 &= 0 \quad (k=2)
\end{aligned}$$

The first and third equations together imply $c_{-1} + c_1 = 0$, and the second gives $c_1 - c_{-1} = 1$. Solving yields $c_{-1} = -\frac{1}{2}, c_0 = 0, c_1 = \frac{1}{2}$, which produces the centered difference formula

$$f'(x_0) = \frac{f(x_0 + h) - f(x_0 - h)}{2h} + \mathcal{O}(h^2)$$

as previously derived. To obtain a fourth-order accurate formula, we extend the stencil to five points with $s = \{-2, -1, 0, 1, 2\}$ and solve the augmented system through $k = 4$. The resulting coefficients are $c = \{\frac{1}{12}, -\frac{2}{3}, 0, \frac{2}{3}, -\frac{1}{12}\}$, giving

$$f'(x_0) = \frac{-f(x_0 + 2h) + 8f(x_0 + h) - 8f(x_0 - h) + f(x_0 - 2h)}{12h} + \mathcal{O}(h^4)$$

The pattern continues: each increase in order by 2 requires one additional grid point on each side of $x_0$, maintaining symmetry to cancel even-order error terms.

For second derivatives, the canonical centered three-point stencil arises from solving

$$\begin{aligned}
c_{-1} + c_0 + c_1 &= 0 \quad (k=0) \\
-c_{-1} + 0 \cdot c_0 + c_1 &= 0 \quad (k=1) \\
c_{-1} + 0 \cdot c_0 + c_1 &= 2 \quad (k=2)
\end{aligned}$$

yielding $c_{-1} = 1, c_0 = -2, c_1 = 1$, hence

$$f''(x_0) = \frac{f(x_0 + h) - 2f(x_0) + f(x_0 - h)}{h^2} + \mathcal{O}(h^2)$$

The leading truncation error term, obtained from the $k = 4$ Taylor coefficient, is $-\frac{h^2}{12} f^{(4)}(x_0)$.

Turning to quadrature, the Newton-Cotes rules on $[a, b]$ partition the interval into $n$ subintervals of width $h = (b - a)/n$, placing nodes at $x_j = a + jh$ for $j = 0, 1, \ldots, n$. The trapezoidal rule ($n = 1$) interpolates $f$ by a linear polynomial connecting $(a, f(a))$ and $(b, f(b))$, yielding

$$T(f) = \frac{b - a}{2} [f(a) + f(b)]$$

The error for a twice-differentiable integrand is

$$E_T(f) = -\frac{(b - a)^3}{12} f''(\xi)$$

for some $\xi \in (a, b)$, derived by integrating the Lagrange interpolation error formula. Simpson's rule ($n = 2$) uses three equally spaced nodes $a, \frac{a+b}{2}, b$ and fits a quadratic interpolant. After integrating the Lagrange basis polynomials, the weights emerge as

$$w_0 = \frac{b - a}{6}, \quad w_1 = \frac{2(b - a)}{3}, \quad w_2 = \frac{b - a}{6}$$

giving

$$S(f) = \frac{b - a}{6} \left[ f(a) + 4f\left(\frac{a + b}{2}\right) + f(b) \right]$$

The symmetry of the node placement causes cancellation of the cubic error term, elevating the degree of exactness to 3. The error formula is

$$E_S(f) = -\frac{(b - a)^5}{2880} f^{(4)}(\xi)$$

exhibiting fourth-order convergence in $h = (b - a)/2$.

Composite rules partition $[a, b]$ into $n$ subintervals $[x_j, x_{j+1}]$ with $x_j = a + jh$ and $h = (b - a)/n$, applying a low-order rule on each subinterval. The composite trapezoidal rule sums the contributions:

$$T_n(f) = h \left[ \frac{f(a)}{2} + \sum_{j=1}^{n-1} f(x_j) + \frac{f(b)}{2} \right]$$

The error analysis leverages the Euler-Maclaurin formula, which relates the trapezoidal sum to the integral plus correction terms involving derivatives at the endpoints:

$$T_n(f) = \int_a^b f(x) \, dx + \frac{h^2}{12} [f'(a) - f'(b)] - \frac{h^4}{720} [f'''(a) - f'''(b)] + \mathcal{O}(h^6)$$

This reveals that for periodic functions, where endpoint derivatives match, the error jumps to $\mathcal{O}(h^4)$ or higher, making the composite trapezoidal rule spectacularly accurate. For general smooth functions, the error is $\mathcal{O}(h^2)$, which translates to $\mathcal{O}(n^{-2})$ since $h = (b - a)/n$.

Gaussian quadrature achieves optimal efficiency by choosing both nodes and weights freely. On the interval $[-1, 1]$, the $n$-point Gaussian rule uses nodes $x_1, \ldots, x_n$ that are the zeros of the Legendre polynomial $P_n(x)$, defined by the three-term recurrence

$$P_0(x) = 1, \quad P_1(x) = x, \quad (k+1) P_{k+1}(x) = (2k + 1) x P_k(x) - k P_{k-1}(x)$$

with orthogonality property $\int_{-1}^1 P_m(x) P_n(x) \, dx = 0$ for $m \neq n$. The weights are computed via

$$w_j = \int_{-1}^1 \prod_{k \neq j} \frac{x - x_k}{x_j - x_k} \, dx = \frac{2}{(1 - x_j^2) [P_n'(x_j)]^2}$$

For arbitrary $[a, b]$, apply the affine transformation $x = \frac{b - a}{2} t + \frac{a + b}{2}$ to map $[-1, 1]$ to $[a, b]$, scaling weights by $\frac{b - a}{2}$.

The two-point Gaussian rule ($n = 2$) uses nodes $x_1 = -\frac{1}{\sqrt{3}}, x_2 = \frac{1}{\sqrt{3}}$ with weights $w_1 = w_2 = 1$, giving degree of exactness 3. For $[a, b]$, this becomes

$$G_2(f) = \frac{b - a}{2} \left[ f\left(\frac{a + b}{2} - \frac{b - a}{2\sqrt{3}}\right) + f\left(\frac{a + b}{2} + \frac{b - a}{2\sqrt{3}}\right) \right]$$

The error satisfies $|E_{G_2}(f)| \leq \frac{(b - a)^5}{4320} \|f^{(4)}\|_{\infty}$, matching Simpson's rule but using one fewer function evaluation.

Richardson extrapolation exploits the asymptotic error expansion to accelerate convergence. If a method produces approximations $A(h)$ to a quantity $L$ with error expansion

$$A(h) = L + c_1 h^p + c_2 h^{2p} + \cdots$$

then computing $A(h)$ and $A(h/2)$ allows elimination of the leading error term by forming

$$\hat{A}(h) = \frac{2^p A(h/2) - A(h)}{2^p - 1} = L + \tilde{c}_2 h^{2p} + \mathcal{O}(h^{3p})$$

This process iterates: each extrapolation step doubles the convergence order at the cost of one additional function evaluation at a finer grid. The Romberg integration method applies Richardson extrapolation recursively to the composite trapezoidal rule, generating a triangular tableau where each row corresponds to a higher order of accuracy. The $(k, m)$ entry in the tableau, denoted $R_{k,m}$, satisfies

$$R_{k,0} = T_{2^k}(f), \quad R_{k,m} = \frac{4^m R_{k,m-1} - R_{k-1,m-1}}{4^m - 1}$$

The diagonal entries $R_{k,k}$ converge with order $2k + 2$, achieving exponential convergence for smooth integrands.

## 3. High-Performance Optimization & Failure Modes

The computational efficiency of finite difference and quadrature methods hinges on balancing truncation error reduction against the cost of additional function evaluations. For finite differences, the optimal step size $h_{\text{opt}}$ minimizes the sum of truncation error and roundoff error. Denoting machine epsilon as $\epsilon_{\text{mach}}$ (approximately $10^{-16}$ in IEEE 754 double precision), the forward difference approximation

$$D_h f(x_0) = \frac{f(x_0 + h) - f(x_0)}{h}$$

incurs truncation error $\mathcal{O}(h)$ and roundoff error amplified by $\frac{1}{h}$, giving total error

$$E_{\text{total}}(h) \approx C_1 h + C_2 \frac{\epsilon_{\text{mach}}}{h}$$

Minimizing with respect to $h$ yields $h_{\text{opt}} \sim \sqrt{\epsilon_{\text{mach}}} \approx 10^{-8}$, at which point the error is approximately $\sqrt{\epsilon_{\text{mach}}} \approx 10^{-8}$. For the centered difference formula with truncation error $\mathcal{O}(h^2)$, the optimal step size increases to $h_{\text{opt}} \sim \epsilon_{\text{mach}}^{1/3} \approx 10^{-5}$, achieving error $\epsilon_{\text{mach}}^{2/3} \approx 10^{-11}$. This analysis reveals that finite difference methods cannot deliver full machine precision for first derivatives without resorting to higher-order stencils or complex-step differentiation.

Complex-step differentiation exploits the Cauchy-Riemann equations to eliminate roundoff error entirely. Extending $f$ analytically to the complex plane, we write

$$f(x_0 + ih) = f(x_0) + ih f'(x_0) - \frac{h^2}{2} f''(x_0) + \mathcal{O}(h^3)$$

Taking the imaginary part and dividing by $h$ gives

$$f'(x_0) = \frac{\text{Im}[f(x_0 + ih)]}{h} + \mathcal{O}(h^2)$$

No subtraction occurs in the numerator, so catastrophic cancellation is absent. With $h = 10^{-100}$, this formula delivers derivatives accurate to machine precision, provided $f$ extends holomorphically and the implementation uses complex arithmetic throughout.

For quadrature, adaptive methods dynamically refine the partition based on local error estimates. The canonical adaptive Simpson's rule recursively subdivides intervals where the error indicator exceeds a tolerance. Given an interval $[a, b]$, compute

$$S_1 = \frac{b - a}{6} \left[ f(a) + 4f\left(\frac{a + b}{2}\right) + f(b) \right]$$

and split the interval in half, computing

$$S_2 = \frac{b - a}{12} \left[ f(a) + 4f\left(\frac{3a + b}{4}\right) + 2f\left(\frac{a + b}{2}\right) + 4f\left(\frac{a + 3b}{4}\right) + f(b) \right]$$

The error estimate $|S_2 - S_1| / 15$ (derived from Richardson extrapolation) governs the refinement decision. If the estimate exceeds the local tolerance $(b - a) \epsilon / (B - A)$ (scaled by subinterval length relative to the global interval $[A, B]$), recursively apply the procedure to $[a, (a+b)/2]$ and $[(a+b)/2, b]$. This strategy concentrates function evaluations near singularities and regions of high curvature, achieving target accuracy with near-optimal cost.

The Clenshaw-Curtis quadrature rule provides a competitive alternative to Gaussian quadrature with superior numerical stability and reusable node sets. It employs Chebyshev points of the first kind $x_j = \cos(\pi j / n)$ for $j = 0, 1, \ldots, n$ on $[-1, 1]$, leveraging the discrete cosine transform to compute weights in $\mathcal{O}(n \log n)$ operations via the fast Fourier transform. While Gaussian quadrature achieves degree of exactness $2n + 1$ compared to Clenshaw-Curtis's approximate degree $n + 1$, the latter's nested node property enables efficient error estimation and adaptive refinement without discarding previous function evaluations. For analytic integrands, both methods converge exponentially, and Clenshaw-Curtis often outperforms Gaussian quadrature in wall-clock time due to FFT acceleration.

Ill-conditioned integrands exhibiting boundary layers, oscillations, or near-singularities demand specialized techniques. For integrals with algebraic endpoint singularities $\int_0^1 x^{\alpha} g(x) \, dx$ where $-1 < \alpha < 0$ and $g$ is smooth, the singularity at $x = 0$ causes standard rules to converge slowly. Applying a change of variables $x = t^{1/(1 + \alpha)}$ removes the singularity, transforming the integral to

$$\frac{1}{1 + \alpha} \int_0^1 g(t^{1/(1 + \alpha)}) \, dt$$

where the new integrand is smooth and amenable to high-order quadrature. For oscillatory integrands $\int_a^b f(x) e^{i \omega x} \, dx$ with large $\omega$, the method of stationary phase or Filon-type methods exploit asymptotic expansions to achieve $\omega$-independent convergence rates.

Multidimensional quadrature faces the curse of dimensionality: tensor product rules require $n^d$ function evaluations in $d$ dimensions to achieve the same accuracy as a one-dimensional $n$-point rule. Sparse grids, constructed via the Smolyak algorithm, mitigate this by selecting a carefully chosen subset of the full tensor product, reducing cost to $\mathcal{O}(n \log^{d-1} n)$ while preserving comparable accuracy for smooth integrands. Monte Carlo and quasi-Monte Carlo methods offer dimension-independent convergence rates $\mathcal{O}(N^{-1/2})$ and $\mathcal{O}(N^{-1} (\log N)^d)$ respectively, where $N$ is the sample count, making them indispensable for high-dimensional integration in statistical mechanics, finance, and uncertainty quantification.

Rigorous error certification requires computable bounds on derivatives appearing in error formulas. For $f'' \in C^0[a, b]$, the trapezoidal error bound $|E_T| \leq \frac{(b - a)^3}{12} \|f''\|_{\infty}$ is attainable if $\|f''\|_{\infty}$ is known. In practice, automatic differentiation or interval arithmetic provides conservative bounds on derivative ranges. Alternatively, posteriori error estimation compares results at successive refinement levels, as in Romberg integration or adaptive Simpson's rule, though these estimates assume asymptotic convergence regimes and may underestimate error in pre-asymptotic regimes.

The choice between competing quadrature methods depends on integrand regularity, available function evaluation budget, and required accuracy. For smooth periodic integrands, the composite trapezoidal rule with $n$ nodes achieves spectral accuracy $\mathcal{O}(e^{-cn})$ for some $c > 0$. For analytic non-periodic integrands, Gaussian or Clenshaw-Curtis quadrature with $n = 10$ to $50$ points typically suffices for engineering accuracy ($10^{-6}$ to $10^{-12}$). For rough integrands with limited smoothness $f \in C^p$, low-order Newton-Cotes rules or adaptive methods with dense refinement near irregularities provide the most robust approach. Understanding these trade-offs and the underlying convergence theory transforms numerical quadrature from a black-box procedure into a principled tool for scientific computation, where every approximation carries a quantifiable pedigree and every algorithm choice reflects a deliberate optimization over the space of allowable errors.
