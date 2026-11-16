# Lesson 5: Conformal Mappings, Möbius Transformations, Harmonic Functions

## 1. First-Principles Intuition & Invariants

The geometric content of complex differentiability emerges most vividly through the concept of conformality. A mapping $f: \Omega \to \mathbb{C}$ preserves angles at a point $z_0$ if for any two smooth curves intersecting at $z_0$ with angle $\theta$, their images under $f$ intersect at $f(z_0)$ with the same angle $\theta$, including orientation. This angle-preservation property serves as the geometric signature of analyticity, transforming the algebraic condition of complex differentiability into a visually interpretable deformation of the plane.

Consider a holomorphic function $f$ with $f'(z_0) \neq 0$. The derivative $f'(z_0)$ encodes both rotation and scaling: writing $f'(z_0) = r e^{i\alpha}$ with $r > 0$, we observe that near $z_0$, the mapping behaves approximately as $f(z) \approx f(z_0) + f'(z_0)(z - z_0)$. This linear approximation multiplies displacements by the complex number $r e^{i\alpha}$, rotating vectors by angle $\alpha$ and scaling magnitudes by factor $r$. Crucially, because multiplication by a fixed complex number applies the same rotation to all vectors, the angle between any two vectors remains unchanged. This infinitesimal angle-preservation at every point where $f'(z) \neq 0$ constitutes the conformal property.

The converse holds with equal force: if a continuously differentiable mapping preserves angles and orientations, it must satisfy the Cauchy-Riemann equations and hence be holomorphic. This bidirectional correspondence establishes conformality as an equivalent characterization of analyticity, one that proves especially powerful when constructing explicit mappings between domains or solving boundary value problems.

The failure of conformality at points where $f'(z) = 0$ deserves careful attention. At such critical points, the mapping may branch or exhibit other singularities in its local geometry. For instance, the function $f(z) = z^n$ maps neighborhoods of the origin by rotating rays through angle $n\theta$ when $z = re^{i\theta}$, effectively wrapping $n$ copies of a neighborhood onto a single neighborhood of zero. The angle between two curves at the origin gets multiplied by $n$, destroying conformality precisely where the derivative vanishes.

Harmonic functions enter this framework through their intimate connection with holomorphic functions. A real-valued function $u: \Omega \to \mathbb{R}$ is harmonic if it satisfies Laplace's equation $\Delta u = u_{xx} + u_{yy} = 0$. The Cauchy-Riemann equations immediately imply that both the real and imaginary parts of any holomorphic function are harmonic: if $f = u + iv$ is holomorphic, then $u_x = v_y$ and $u_y = -v_x$, so differentiating the first equation with respect to $x$ and the second with respect to $y$ yields $u_{xx} = v_{yx}$ and $u_{yy} = -v_{xy}$. Because $f$ is holomorphic and hence infinitely differentiable, mixed partials commute, giving $u_{xx} + u_{yy} = v_{yx} - v_{xy} = 0$.

Conversely, given a harmonic function $u$ on a simply connected domain, we can construct a harmonic conjugate $v$ such that $f = u + iv$ is holomorphic. The construction exploits path independence: define $v(z) = \int_{z_0}^z (-u_y \, dx + u_x \, dy)$. The condition $\Delta u = 0$ ensures that the mixed partials $(-u_y)_y = (u_x)_x$, guaranteeing path independence and making $v$ well-defined. The resulting function $f$ automatically satisfies the Cauchy-Riemann equations by construction.

This correspondence between harmonic and holomorphic functions transforms boundary value problems for harmonic functions into contour integral problems for holomorphic functions, a strategy that pervades applications from electrostatics to fluid dynamics. The real part of a holomorphic function solving a particular geometric mapping problem simultaneously solves a Dirichlet problem with boundary conditions inherited from the mapping.

The maximum modulus principle provides a fundamental constraint on harmonic functions and their holomorphic parents. If $f$ is holomorphic on a domain $\Omega$ and continuous on its closure $\overline{\Omega}$, then $|f|$ attains its maximum on the boundary $\partial \Omega$. If $|f|$ attains a local maximum at an interior point, then $f$ must be constant. This principle follows from the mean value property: a holomorphic function equals its average over any circle centered at a point in its domain. If $|f(z_0)| \geq |f(z)|$ for all nearby $z$, then the integral average cannot exceed $|f(z_0)|$, forcing equality everywhere on a neighborhood and hence everywhere by analytic continuation.

For harmonic functions, the maximum principle takes a parallel form: a non-constant harmonic function $u$ on a domain $\Omega$ cannot attain its maximum or minimum at an interior point. This result governs the behavior of temperature distributions, electrostatic potentials, and fluid flows, ensuring that extremal values occur on boundaries rather than in the interior.

## 2. Core Architecture & Mechanics

Möbius transformations form the bedrock of conformal geometry, serving as the automorphisms of the extended complex plane or Riemann sphere $\hat{\mathbb{C}} = \mathbb{C} \cup \{\infty\}$. A Möbius transformation takes the form

$$T(z) = \frac{az + b}{cz + d}$$

where $a, b, c, d \in \mathbb{C}$ satisfy $ad - bc \neq 0$. The determinant condition prevents the numerator and denominator from being proportional, which would collapse the transformation to a constant. These transformations extend naturally to the point at infinity: $T(\infty) = a/c$ when $c \neq 0$, and $T(\infty) = \infty$ when $c = 0$. Similarly, $T(-d/c) = \infty$ when $c \neq 0$.

The group structure of Möbius transformations emerges from their matrix representation. Associate to $T$ the matrix

$$M = \begin{pmatrix} a & b \\ c & d \end{pmatrix}$$

with $\det M = ad - bc \neq 0$. Composition of Möbius transformations corresponds to matrix multiplication: if $T_1$ corresponds to $M_1$ and $T_2$ corresponds to $M_2$, then $T_1 \circ T_2$ corresponds to $M_1 M_2$. Scalar multiples of a matrix induce the same Möbius transformation, so the group of Möbius transformations is isomorphic to $\text{PSL}(2, \mathbb{C}) = \text{SL}(2, \mathbb{C}) / \{\pm I\}$, the projective special linear group.

Every Möbius transformation decomposes into elementary operations: translations $z \mapsto z + b$, rotations and scalings $z \mapsto az$, and the inversion $z \mapsto 1/z$. To verify this, write

$$T(z) = \frac{az + b}{cz + d} = \frac{a}{c} - \frac{ad - bc}{c(cz + d)}$$

when $c \neq 0$. This expresses $T$ as a composition: first translate by $-d/c$, then scale by $c$, then invert, then scale by $(bc - ad)/c$, then translate by $a/c$. When $c = 0$, the transformation simplifies to $T(z) = (a/d)z + b/d$, an affine map.

The circle-preserving property stands as the defining geometric characteristic of Möbius transformations. A generalized circle means either a circle in $\mathbb{C}$ or a line, the latter understood as a circle through infinity. Möbius transformations map generalized circles to generalized circles. To prove this, we verify the claim for each elementary type. Translations and scalings clearly preserve circles and map lines to lines. Inversion $z \mapsto 1/z$ transforms circles not passing through the origin into circles, circles through the origin into lines, and lines not through the origin into circles through the origin. Since every Möbius transformation decomposes into these elementary operations, the circle-preserving property holds universally.

Cross-ratios provide the fundamental invariant of Möbius transformations. Given four distinct points $z_1, z_2, z_3, z_4 \in \hat{\mathbb{C}}$, their cross-ratio is

$$(z_1, z_2; z_3, z_4) = \frac{(z_1 - z_3)(z_2 - z_4)}{(z_1 - z_4)(z_2 - z_3)}$$

with appropriate limit conventions when one point is infinite. Every Möbius transformation $T$ preserves cross-ratios:

$$(T(z_1), T(z_2); T(z_3), T(z_4)) = (z_1, z_2; z_3, z_4)$$

This invariance follows from direct algebraic verification, substituting the transformation formula and simplifying. The determinant condition $ad - bc \neq 0$ ensures that cancellations yield the original cross-ratio.

Conversely, the cross-ratio characterizes Möbius transformations uniquely: given two ordered triples of distinct points $(z_1, z_2, z_3)$ and $(w_1, w_2, w_3)$, there exists a unique Möbius transformation $T$ with $T(z_j) = w_j$ for $j = 1, 2, 3$. To construct $T$, we equate cross-ratios:

$$(w, w_1; w_2, w_3) = (T(z), T(z_1); T(z_2), T(z_3)) = (z, z_1; z_2, z_3)$$

This equation defines $w = T(z)$ implicitly. Solving for $w$ yields the explicit formula for $T$, expressed in terms of cross-ratios. The determinant condition follows from the distinctness of the $z_j$ and $w_j$.

Standard conformal mappings between elementary domains illustrate these principles concretely. The mapping from the upper half-plane $\mathbb{H} = \{z : \text{Im}(z) > 0\}$ to the unit disk $\mathbb{D} = \{z : |z| < 1\}$ takes the form

$$f(z) = \frac{z - i}{z + i}$$

To verify that $f$ maps $\mathbb{H}$ onto $\mathbb{D}$, observe that $f(i) = 0$ and $f(\infty) = 1$. For $z = x + iy$ with $y > 0$, compute

$$|f(z)|^2 = \frac{|z - i|^2}{|z + i|^2} = \frac{x^2 + (y - 1)^2}{x^2 + (y + 1)^2} = \frac{x^2 + y^2 - 2y + 1}{x^2 + y^2 + 2y + 1}$$

The numerator is less than the denominator if and only if $-2y < 2y$, which holds precisely when $y > 0$. Thus $f$ maps $\mathbb{H}$ into $\mathbb{D}$. The inverse

$$f^{-1}(w) = i \frac{1 + w}{1 - w}$$

maps $\mathbb{D}$ back to $\mathbb{H}$, confirming that $f$ is a conformal equivalence.

The Riemann mapping theorem stands as the crowning achievement of conformal mapping theory, asserting the essential uniqueness of simply connected domains under conformal equivalence. The precise statement requires care: let $\Omega \subsetneq \mathbb{C}$ be a simply connected domain that is not the entire plane. Then there exists a conformal bijection $f: \Omega \to \mathbb{D}$. Moreover, given a point $z_0 \in \Omega$ and a direction $\theta \in [0, 2\pi)$, we can normalize $f$ uniquely by requiring $f(z_0) = 0$ and $\arg f'(z_0) = \theta$.

The constructive proof proceeds through normal families and extremal problems. Consider the class $\mathcal{F}$ of injective holomorphic functions $g: \Omega \to \mathbb{D}$ with $g(z_0) = 0$. The Riemann mapping theorem equivalent to showing that some element of $\mathcal{F}$ is surjective. To find such a function, we maximize $|g'(z_0)|$ over $\mathcal{F}$. By the Koebe distortion theorem and normal family arguments, a maximizing sequence converges to a limit function $f \in \mathcal{F}$. If $f$ were not surjective, there would exist $w_0 \in \mathbb{D}$ not in the image. An automorphism of $\mathbb{D}$ moving $w_0$ to the origin, composed with a square root branch and another automorphism, would produce a function $h: \Omega \to \mathbb{D}$ with $h(z_0) = 0$ and $|h'(z_0)| > |f'(z_0)|$, contradicting maximality. Therefore $f$ is surjective, establishing the existence of a conformal map.

The uniqueness portion follows from the Schwarz lemma. If $f, g: \Omega \to \mathbb{D}$ are two conformal bijections with $f(z_0) = g(z_0) = 0$ and $f'(z_0), g'(z_0) > 0$, then $h = g \circ f^{-1}: \mathbb{D} \to \mathbb{D}$ is a conformal automorphism fixing the origin. The Schwarz lemma implies $|h(w)| \leq |w|$ with equality only if $h(w) = e^{i\alpha} w$ for some $\alpha \in \mathbb{R}$. Applying the same reasoning to $h^{-1}$ yields $|h^{-1}(w)| \leq |w|$, forcing $|h(w)| = |w|$. Therefore $h(w) = e^{i\alpha} w$, and the condition $h'(0) > 0$ forces $\alpha = 0$, giving $h(w) = w$ and hence $f = g$.

Schwarz-Christoffel mappings provide an explicit constructive technique for conformally mapping the upper half-plane onto polygonal domains. Given a polygon $P$ with vertices $w_1, \ldots, w_n$ and interior angles $\alpha_1 \pi, \ldots, \alpha_n \pi$ (where $\sum \alpha_j = n - 2$ by the angle sum formula), the Schwarz-Christoffel formula constructs a conformal map $f: \mathbb{H} \to P$ as

$$f(z) = A + C \int_{z_0}^z \prod_{j=1}^n (\zeta - x_j)^{\alpha_j - 1} \, d\zeta$$

where $x_1 < x_2 < \cdots < x_n$ are real parameters corresponding to the preimages of the vertices, and $A, C$ are complex constants. The derivative

$$f'(z) = C \prod_{j=1}^n (z - x_j)^{\alpha_j - 1}$$

exhibits branch points at each $x_j$ where the argument jumps by $(\alpha_j - 1)\pi$ as $z$ crosses the real axis. This argument change corresponds precisely to the exterior angle of the polygon at vertex $w_j$, ensuring that the image of the real axis (excluding the points $x_j$) forms the sides of the polygon.

To apply the Schwarz-Christoffel formula concretely, consider mapping the upper half-plane onto the infinite strip $\{w : 0 < \text{Im}(w) < 1\}$. This "polygon" has vertices at $0, 1, \infty$ in the $w$-plane with interior angles $\pi/2, \pi/2, \pi$. We place the preimages at $x_1 = -1, x_2 = 1$, and $x_3 = \infty$. The formula gives

$$f'(z) = C (z + 1)^{-1/2} (z - 1)^{-1/2} = \frac{C}{\sqrt{z^2 - 1}}$$

Integrating yields

$$f(z) = C \int_{z_0}^z \frac{d\zeta}{\sqrt{\zeta^2 - 1}} = C \cosh^{-1}(z) + A$$

Choosing the branch and constants appropriately gives $f(z) = (\pi)^{-1} \log(z + \sqrt{z^2 - 1})$, which maps $\mathbb{H}$ onto the strip as desired. The square root branch cuts and logarithm branch must be chosen consistently to achieve the correct geometry.

Dirichlet problems seek harmonic functions satisfying prescribed boundary conditions. Given a domain $\Omega$ with boundary $\partial \Omega$ and a continuous function $\varphi: \partial \Omega \to \mathbb{R}$, the Dirichlet problem asks for a harmonic function $u: \Omega \to \mathbb{R}$, continuous on $\overline{\Omega}$, with $u|_{\partial \Omega} = \varphi$. The maximum principle immediately guarantees uniqueness: if $u_1$ and $u_2$ both solve the problem, then $u_1 - u_2$ is harmonic with zero boundary values, forcing $u_1 - u_2 \equiv 0$ by the maximum principle.

Conformal mapping transforms Dirichlet problems on complicated domains to Dirichlet problems on standard domains like the disk. If $f: \Omega \to \mathbb{D}$ is a conformal bijection and $u$ is harmonic on $\mathbb{D}$, then $u \circ f$ is harmonic on $\Omega$. To see this, observe that $u \circ f$ is the real part of a holomorphic function: if $u = \text{Re}(g)$ for some holomorphic $g$ on $\mathbb{D}$, then $u \circ f = \text{Re}(g \circ f)$, and $g \circ f$ is holomorphic on $\Omega$ by the chain rule.

The Poisson formula solves the Dirichlet problem explicitly on the unit disk. Given a continuous function $\varphi: \partial \mathbb{D} \to \mathbb{R}$, the solution is

$$u(re^{i\theta}) = \frac{1}{2\pi} \int_0^{2\pi} \varphi(e^{i\phi}) \frac{1 - r^2}{1 - 2r\cos(\theta - \phi) + r^2} \, d\phi$$

for $0 \leq r < 1$. The kernel

$$P_r(\theta - \phi) = \frac{1 - r^2}{1 - 2r\cos(\theta - \phi) + r^2}$$

is the Poisson kernel, a family of positive functions that approximate the Dirac delta as $r \to 1^-$. The solution $u$ extends continuously to the boundary by dominated convergence, reproducing $\varphi$ at each boundary point.

To derive the Poisson formula, observe that for $|z| < 1$ and $|w| = 1$, the function

$$K(z, w) = \text{Re}\left(\frac{w + z}{w - z}\right) = \text{Re}\left(\frac{(w + z)(\overline{w} - \overline{z})}{|w - z|^2}\right) = \frac{1 - |z|^2}{|w - z|^2}$$

is the real part of the holomorphic function $(w + z)/(w - z)$ in $z$. For fixed $w$, integrating against a boundary distribution yields a harmonic function. The normalization ensures that integrating $P_r$ over the circle gives $1$, making constant functions their own solutions.

## 3. High-Performance Optimization & Failure Modes

Computational construction of conformal maps demands careful numerical treatment of several subtle issues. The Schwarz-Christoffel mapping, while explicit in formula, requires solving a nonlinear parameter problem: given the target polygon vertices $w_j$, we must determine the preimage parameters $x_j$ and constants $A, C$. This inversion problem reduces to a system of nonlinear equations derived from the integral formula. For a polygon with $n$ vertices, we have $n + 2$ parameters ($n$ values $x_j$, plus $A$ and $C$), but only $n$ constraints from vertex correspondence. The excess degrees of freedom correspond to the symmetries of the problem: Möbius automorphisms of the half-plane (three real degrees of freedom) and scaling/rotation of the target polygon (three more degrees of freedom). Fixing three parameters $x_j$ breaks this symmetry, leaving a well-posed system of $n - 3$ equations for the remaining $x_j$, then direct integration to recover $A$ and $C$.

Numerical instability arises when polygon vertices cluster or when angles approach multiples of $\pi$. The integrand $(z - x_j)^{\alpha_j - 1}$ exhibits singular behavior when $\alpha_j \to 0$ or $\alpha_j \to 2$, corresponding to cusps or reflex angles. Adaptive quadrature with careful attention to branch cuts becomes essential. Gauss-Jacobi quadrature tailored to the power-law weights provides superior convergence compared to naive Simpson or trapezoidal methods.

The Riemann mapping theorem, while existentially constructive through maximization arguments, does not provide practical algorithms for arbitrary domains. Modern computational conformal mapping relies on boundary integral methods, particularly the Kerzman-Stein kernel approach. Given a Jordan domain $\Omega$ with smooth boundary $\Gamma$, the Riemann map $f: \Omega \to \mathbb{D}$ satisfies a singular integral equation on $\Gamma$. Discretizing this equation yields a linear system whose solution approximates $f$ on the boundary, from which Cauchy's formula recovers $f$ in the interior. The computational complexity scales as $O(N^2)$ or $O(N \log N)$ depending on whether fast multipole or FFT acceleration is employed, where $N$ denotes the number of boundary discretization points.

Accuracy verification leverages invariant properties that the discrete solution must preserve. The conformal modulus of an annulus $\{z : r < |z| < R\}$ equals $\log(R/r) / (2\pi)$. If a computed map purports to transform a given doubly connected domain onto a canonical annulus, computing the modulus by integrating the derivative around a curve and comparing against the geometric value provides a quantitative error measure. Discrepancies exceeding tolerance indicate insufficient resolution or numerical pathology.

Failure modes in harmonic function solvers often trace to poor boundary representation. The Poisson formula converges slowly when the boundary function $\varphi$ lacks smoothness; discontinuities produce Gibbs phenomena that pollute the interior solution. Mollifying the boundary data or using spectral filtering mitigates this issue. For domains with corners, the solution itself develops singularities: the gradient of $u$ typically exhibits $O(r^{\alpha - 1})$ growth near a corner of angle $\alpha \pi$, where $r$ measures distance from the vertex. Uniform meshes waste resolution in smooth regions while underresolving near corners. Adaptive refinement guided by a posteriori error estimators, derived from residual jumps and gradient recovery, achieves optimal convergence rates.

The maximum modulus principle serves as both theoretical foundation and practical diagnostic. Numerical solutions of Laplace's equation that violate the maximum principle at interior points signal instability in the discretization or solver. Discrete maximum principles impose structural constraints on finite difference and finite element stencils: the matrix must be an M-matrix, with positive diagonal, non-positive off-diagonal entries, and row sums equal to zero. Centered finite differences on uniform grids satisfy this property, but higher-order schemes or unstructured meshes may violate it, admitting spurious oscillations.

Multivalued mappings introduce branch cut management challenges. The logarithm $\log z = \log|z| + i \arg z$ requires choosing an argument branch. In multiply connected domains, conformal maps necessarily exhibit monodromy: traversing a cycle yields an additive or multiplicative change in the function value. The Schwarz-Christoffel formula for multiply connected domains incorporates these periods as additional parameters, determined by imposing normalization conditions or solving period integrals. Numerical evaluation must track accumulated argument changes, switching branches coherently as paths wind around obstacles.

Boundary layer resolution in fluid dynamics applications often requires conformal mapping onto domains with extreme aspect ratios, such as thin channels or boundary layers. The Jacobian determinant $|f'(z)|^2$ measures area distortion under the map. If $f$ maps a nearly square domain onto a thin strip, $|f'|$ must vary by several orders of magnitude across the domain, concentrating resolution near boundaries. Ensuring adequate floating-point precision to represent this range without overflow or underflow demands careful scaling and possibly quad-precision arithmetic in critical regions.

The Schwarz reflection principle extends conformal maps across analytic boundary arcs, enabling symmetry exploitation. If $f$ maps the upper half-plane to a domain symmetric about the real axis, then $f(\overline{z}) = \overline{f(z)}$ continues $f$ analytically across the real axis. Iterating reflections across multiple symmetric boundaries bootstraps a map on a small fundamental domain to a map on a larger symmetric union. This technique proves especially powerful for tiling problems and periodic configurations, where a single period cell determines the entire map. Computational savings scale multiplicatively with the symmetry group order, but geometric constraints on the fundamental domain boundary must align with the reflection symmetries to avoid monodromy obstructions.

Convergence acceleration for iterative Schwarz-Christoffel parameter solvers benefits from good initial guesses. Heuristics based on vertex distribution, such as placing $x_j$ uniformly or according to cumulative side lengths, provide starting points. Newton-Raphson iteration converges quadratically near the solution, but requires Jacobian matrix computation. Finite difference approximations to the Jacobian introduce $O(N)$ additional function evaluations per iteration, where $N$ is the parameter count. Automatic differentiation techniques reduce this overhead, propagating derivative information through the integration process to compute sensitivities without finite differencing.

Regularization techniques stabilize ill-conditioned Dirichlet problems. Domains with slits or nearly touching boundaries exhibit exponentially small eigenvalues in the Laplace operator, making the solution sensitive to boundary perturbations. Adding a small Helmholtz term $\Delta u - \epsilon u = 0$ with $\epsilon \ll 1$ damps high-frequency modes, trading exact solution for robustness. As $\epsilon \to 0$, the regularized solution converges to the true solution, but the conditioning improves drastically for finite $\epsilon$. Practical choices of $\epsilon$ balance residual error against stability.

Visualization of conformal maps illuminates geometric distortion patterns. Plotting images of coordinate grid lines reveals how the map stretches and compresses different regions. Circles centered at points in the source domain map to ellipses in the target domain (except at critical points where they remain circular). The ratio of ellipse axes equals $|f'(z)|$, encoding the local magnification factor. Coloring the source domain by $\log|f'(z)|$ produces a heatmap of distortion intensity, identifying regions of extreme compression or expansion. Such visualizations guide mesh adaptation and identify potential numerical trouble spots before running simulations.
