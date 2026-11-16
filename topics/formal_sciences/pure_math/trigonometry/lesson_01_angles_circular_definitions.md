# Lesson 1: Angles, the Unit Circle, and Circular Function Definitions

## 1. First-Principles Intuition & Invariants

The genesis of trigonometry lies not in arbitrary conventions but in the profound relationship between rotational symmetry and the invariant geometric structure of the circle. While elementary treatments often introduce trigonometric functions through right-triangle ratios, this approach conceals their true nature as projections of uniform circular motion onto orthogonal axes. The pure mathematician recognizes trigonometric functions as the fundamental periodic coordinate functions on the unit circle, providing the canonical parameterization of $\mathbb{S}^1$ as a one-dimensional compact Lie group under rotation.

The conceptual foundation rests upon a single geometric primitive: the unit circle embedded in the Euclidean plane $\mathbb{R}^2$, defined by the algebraic constraint $x^2 + y^2 = 1$. Every point on this circle can be uniquely parameterized by a signed arc length measured from a distinguished reference point, conventionally taken as $(1, 0)$ on the positive horizontal axis. This signed arc length, measured counterclockwise as positive and clockwise as negative, constitutes the **radian measure** of the angle subtended at the origin. The radian is not merely a unit convention but the natural geometric unit: it is the unique angular measure under which the arc length along the unit circle equals the angle itself. An angle of $\theta$ radians corresponds to an arc of length $\theta$ on the unit circle, establishing an isometry between the angular parameter space and the real line $\mathbb{R}$.

This geometric correspondence immediately yields the fundamental conversion relationship between radians and degrees. Since the complete circumference of the unit circle has length $2\pi$ (from the integral definition of $\pi$ as half the circumference of the unit circle), one complete revolution corresponds to $2\pi$ radians or $360°$. The conversion formula follows directly:

$$\theta_{\text{rad}} = \frac{\pi}{180°} \cdot \theta_{\text{deg}}$$

The primacy of radian measure manifests in calculus: when angles are measured in radians, the derivatives of trigonometric functions assume their simplest forms. The derivative $\frac{d}{d\theta}\sin\theta = \cos\theta$ holds only when $\theta$ is measured in radians; any other angular unit introduces spurious multiplicative constants that obscure the underlying geometric structure.

With the unit circle as our foundational object, we define the six classical trigonometric functions through coordinate projections and their reciprocals. Let $P(\theta)$ denote the point on the unit circle obtained by traversing counterclockwise an arc of length $\theta$ from the initial point $(1, 0)$. The Cartesian coordinates of $P(\theta)$ define the two fundamental functions:

$$P(\theta) = (\cos\theta, \sin\theta)$$

This notation embeds the critical geometric insight: the **cosine function** $\cos\theta$ yields the horizontal coordinate (projection onto the $x$-axis), while the **sine function** $\sin\theta$ yields the vertical coordinate (projection onto the $y$-axis) of the terminal point of the arc. The Pythagorean identity $\cos^2\theta + \sin^2\theta = 1$ is not a theorem to be proven but a tautology expressing the constraint that $P(\theta)$ lies on the unit circle.

The remaining four trigonometric functions arise as derived ratios and reciprocals. The **tangent function** measures the ratio of vertical to horizontal displacement:

$$\tan\theta = \frac{\sin\theta}{\cos\theta}$$

provided $\cos\theta \neq 0$. Geometrically, $\tan\theta$ represents the slope of the line from the origin through $P(\theta)$, or equivalently, the signed length of the vertical tangent segment from $(1, 0)$ to the intersection of the terminal ray with the vertical line $x = 1$.

The three reciprocal functions complete the classical framework. The **cosecant** $\csc\theta = \frac{1}{\sin\theta}$ (defined for $\sin\theta \neq 0$), the **secant** $\sec\theta = \frac{1}{\cos\theta}$ (defined for $\cos\theta \neq 0$), and the **cotangent** $\cot\theta = \frac{\cos\theta}{\sin\theta} = \frac{1}{\tan\theta}$ (defined for $\sin\theta \neq 0$) historically arose from computational convenience in spherical astronomy and navigation, though their modern utility lies primarily in simplifying certain algebraic identities and differential equations.

The periodicity of these functions emerges immediately from the circular geometry. Since traversing an additional complete revolution of $2\pi$ radians returns to the same point on the unit circle, we have the fundamental period identities:

$$\sin(\theta + 2\pi k) = \sin\theta \quad \text{and} \quad \cos(\theta + 2\pi k) = \cos\theta$$

for all integers $k \in \mathbb{Z}$. The tangent and cotangent functions exhibit a shorter fundamental period of $\pi$ radians because opposite points on a diameter determine the same slope. The secant and cosecant inherit the period $2\pi$ from their reciprocal relationships with cosine and sine respectively.

Symmetry properties arise from the geometric transformations of the unit circle under reflection. Reflection across the $x$-axis sends $P(\theta) = (\cos\theta, \sin\theta)$ to $(\cos\theta, -\sin\theta) = P(-\theta)$, establishing the **even-odd identities**:

$$\cos(-\theta) = \cos\theta \quad \text{(even function)}$$
$$\sin(-\theta) = -\sin\theta \quad \text{(odd function)}$$

Reflection across the $y$-axis transforms $(\cos\theta, \sin\theta)$ to $(-\cos\theta, \sin\theta) = P(\pi - \theta)$, yielding the supplementary angle formulas:

$$\cos(\pi - \theta) = -\cos\theta$$
$$\sin(\pi - \theta) = \sin\theta$$

Reflection across the line $y = x$ exchanges the roles of sine and cosine, corresponding to complementary angles:

$$\sin\left(\frac{\pi}{2} - \theta\right) = \cos\theta$$
$$\cos\left(\frac{\pi}{2} - \theta\right) = \sin\theta$$

These complementary angle relationships explain the nomenclature: "cosine" abbreviates "complement's sine," reflecting this $\frac{\pi}{2}$-radian phase shift relationship.

The domain and range specifications follow directly from the geometric construction. Since arc length on the unit circle can be arbitrarily large or small, both sine and cosine accept all real numbers as inputs: $\text{dom}(\sin) = \text{dom}(\cos) = \mathbb{R}$. The unit circle constraint ensures that the outputs remain bounded: $\text{range}(\sin) = \text{range}(\cos) = [-1, 1]$. The tangent function inherits its domain from the requirement $\cos\theta \neq 0$, excluding odd multiples of $\frac{\pi}{2}$: $\text{dom}(\tan) = \mathbb{R} \setminus \left\{\frac{\pi}{2} + k\pi : k \in \mathbb{Z}\right\}$. As $\theta$ approaches these excluded values, $\tan\theta$ diverges to $\pm\infty$, establishing $\text{range}(\tan) = \mathbb{R}$.

## 2. Core Architecture & Mechanics

The computational evaluation of trigonometric functions at arbitrary angles reduces to two core operations: range reduction via periodicity and symmetry, followed by lookup or series approximation for a canonical reference set. The reference angles that admit exact closed-form radical expressions constitute a distinguished discrete subset of the parameter space, arising from constructible regular polygons by compass and straightedge.

The most fundamental exact values occur at the quadrantal angles corresponding to the cardinal points of the unit circle. At $\theta = 0$, the arc has traversed no distance, so $P(0) = (1, 0)$, yielding $\cos 0 = 1$ and $\sin 0 = 0$. A quarter-revolution to $\theta = \frac{\pi}{2}$ radians reaches the north pole $(0, 1)$, giving $\cos\frac{\pi}{2} = 0$ and $\sin\frac{\pi}{2} = 1$. Continuing to $\theta = \pi$ reaches the antipodal point $(-1, 0)$: $\cos\pi = -1$ and $\sin\pi = 0$. The three-quarter mark at $\theta = \frac{3\pi}{2}$ yields $(0, -1)$, and the cycle completes at $\theta = 2\pi$ returning to $(1, 0)$.

The next level of exact values arises from angles that subtend arcs corresponding to regular hexagons and squares. For $\theta = \frac{\pi}{6}$ radians ($30°$), geometric analysis via an equilateral triangle inscribed in the unit circle yields:

$$\cos\frac{\pi}{6} = \frac{\sqrt{3}}{2}, \quad \sin\frac{\pi}{6} = \frac{1}{2}$$

The complementary angle $\theta = \frac{\pi}{3}$ ($60°$) exchanges these values:

$$\cos\frac{\pi}{3} = \frac{1}{2}, \quad \sin\frac{\pi}{3} = \frac{\sqrt{3}}{2}$$

For $\theta = \frac{\pi}{4}$ radians ($45°$), the point $P\left(\frac{\pi}{4}\right)$ lies on the diagonal $y = x$ of the unit circle. The constraint $x^2 + y^2 = 1$ with $x = y$ yields $2x^2 = 1$, so $x = y = \frac{1}{\sqrt{2}} = \frac{\sqrt{2}}{2}$, establishing:

$$\cos\frac{\pi}{4} = \sin\frac{\pi}{4} = \frac{\sqrt{2}}{2}$$

These three angles—$\frac{\pi}{6}$, $\frac{\pi}{4}$, and $\frac{\pi}{3}$—together with the quadrantal angles, form the complete set of first-quadrant angles with elementary radical expressions. The values at all other angles in the remaining three quadrants follow mechanically by symmetry transformations.

To systematize the computation of any trigonometric value, we employ a reduction algorithm based on the reference angle concept. For an arbitrary angle $\theta$, we first apply periodicity to reduce modulo $2\pi$ (or modulo $\pi$ for tangent and cotangent), obtaining an equivalent angle $\theta_0 \in [0, 2\pi)$. We then identify which quadrant contains the terminal point $P(\theta_0)$ by comparing $\theta_0$ against the quadrantal boundaries $\frac{\pi}{2}$, $\pi$, and $\frac{3\pi}{2}$.

The **reference angle** $\alpha$ is defined as the acute angle between the terminal ray and the nearest horizontal axis. The formulas for $\alpha$ depend on the quadrant:

- **Quadrant I** ($0 \le \theta_0 < \frac{\pi}{2}$): $\alpha = \theta_0$
- **Quadrant II** ($\frac{\pi}{2} \le \theta_0 < \pi$): $\alpha = \pi - \theta_0$
- **Quadrant III** ($\pi \le \theta_0 < \frac{3\pi}{2}$): $\alpha = \theta_0 - \pi$
- **Quadrant IV** ($\frac{3\pi}{2} \le \theta_0 < 2\pi$): $\alpha = 2\pi - \theta_0$

The absolute values of all six trigonometric functions at $\theta_0$ equal their values at the reference angle $\alpha$. The correct signs are then determined by the quadrant-specific sign conventions. The mnemonic "All Students Take Calculus" encodes the sign pattern: in Quadrant I, **A**ll functions are positive; in Quadrant II, only **S**ine (and its reciprocal cosecant) are positive; in Quadrant III, only **T**angent (and cotangent) are positive; in Quadrant IV, only **C**osine (and secant) are positive.

As a concrete example, consider evaluating $\sin\frac{5\pi}{6}$. The angle $\frac{5\pi}{6}$ lies in Quadrant II since $\frac{\pi}{2} < \frac{5\pi}{6} < \pi$. The reference angle is $\alpha = \pi - \frac{5\pi}{6} = \frac{\pi}{6}$. Sine is positive in Quadrant II, so:

$$\sin\frac{5\pi}{6} = +\sin\frac{\pi}{6} = \frac{1}{2}$$

For $\cos\frac{5\pi}{6}$, cosine is negative in Quadrant II:

$$\cos\frac{5\pi}{6} = -\cos\frac{\pi}{6} = -\frac{\sqrt{3}}{2}$$

The tangent value follows by division:

$$\tan\frac{5\pi}{6} = \frac{\sin\frac{5\pi}{6}}{\cos\frac{5\pi}{6}} = \frac{1/2}{-\sqrt{3}/2} = -\frac{1}{\sqrt{3}} = -\frac{\sqrt{3}}{3}$$

For computational work beyond exact radical expressions, series expansions provide the foundation for numerical evaluation. The Taylor series centered at $\theta = 0$ converge globally for sine and cosine:

$$\sin\theta = \sum_{n=0}^{\infty} \frac{(-1)^n}{(2n+1)!} \theta^{2n+1} = \theta - \frac{\theta^3}{3!} + \frac{\theta^5}{5!} - \frac{\theta^7}{7!} + \cdots$$

$$\cos\theta = \sum_{n=0}^{\infty} \frac{(-1)^n}{(2n)!} \theta^{2n} = 1 - \frac{\theta^2}{2!} + \frac{\theta^4}{4!} - \frac{\theta^6}{6!} + \cdots$$

These series reveal the analytic structure of the trigonometric functions as entire functions on $\mathbb{C}$, with the alternating signs reflecting the oscillatory nature. The tangent series, known as the Gregory-Leibniz expansion, involves Bernoulli numbers and converges only for $|\theta| < \frac{\pi}{2}$:

$$\tan\theta = \theta + \frac{\theta^3}{3} + \frac{2\theta^5}{15} + \frac{17\theta^7}{315} + \cdots$$

Modern computational libraries implement trigonometric functions via range reduction combined with minimax polynomial approximations or CORDIC (Coordinate Rotation Digital Computer) algorithms, achieving machine precision with minimal arithmetic operations.

The unit circle framework extends naturally to complex analysis via Euler's formula, which expresses the exponential function of an imaginary argument as a point on the unit circle:

$$e^{i\theta} = \cos\theta + i\sin\theta$$

This identity reveals trigonometric functions as the real and imaginary parts of the complex exponential, establishing the deep connection between circular functions, exponential growth, and the structure of the multiplicative group $\mathbb{C}^*$. From Euler's formula, we derive the exponential definitions:

$$\cos\theta = \frac{e^{i\theta} + e^{-i\theta}}{2}, \quad \sin\theta = \frac{e^{i\theta} - e^{-i\theta}}{2i}$$

These expressions show that sine and cosine are the unique real-valued solutions to the differential equation $f''(\theta) + f(\theta) = 0$ satisfying the initial conditions $\cos 0 = 1$, $\cos' 0 = 0$ for cosine and $\sin 0 = 0$, $\sin' 0 = 1$ for sine. The periodicity, bounded range, and oscillatory behavior all follow from this second-order differential characterization.

The functional equations satisfied by trigonometric functions encode their algebraic and geometric properties. Beyond the periodicity and symmetry identities already established, the addition formulas constitute the most important algebraic structure:

$$\sin(\alpha + \beta) = \sin\alpha\cos\beta + \cos\alpha\sin\beta$$
$$\cos(\alpha + \beta) = \cos\alpha\cos\beta - \sin\alpha\sin\beta$$

These formulas admit purely geometric proofs via rotation matrices or distance formulas on the unit circle, but they also follow algebraically from Euler's formula and the exponential addition law $e^{i(\alpha+\beta)} = e^{i\alpha} \cdot e^{i\beta}$. Setting $\beta = \alpha$ yields the double-angle formulas:

$$\sin 2\alpha = 2\sin\alpha\cos\alpha$$
$$\cos 2\alpha = \cos^2\alpha - \sin^2\alpha = 2\cos^2\alpha - 1 = 1 - 2\sin^2\alpha$$

The multiple equivalent forms of the double-angle formula for cosine arise from substituting the Pythagorean identity $\sin^2\alpha + \cos^2\alpha = 1$ in different ways, each form optimized for particular computational contexts.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of trigonometric computation in numerical algorithms and mathematical software requires careful attention to argument reduction accuracy, cancellation errors, and domain boundary handling. The primary challenge in high-precision trigonometric evaluation lies in the range reduction step: for very large arguments, determining the equivalent angle in $[0, 2\pi)$ requires knowing $\pi$ to sufficient precision that the accumulated rounding error in the modular reduction does not corrupt the final result.

Consider evaluating $\sin(10^{100})$. The mathematically exact reduction computes $10^{100} \mod 2\pi$, but performing this modular arithmetic in finite-precision floating-point introduces catastrophic error. If $\pi$ is approximated to $d$ decimal digits, the reduction error propagates as approximately $\frac{10^{100}}{10^d}$ radians, which quickly overwhelms the argument range unless $d \gg 100$. High-quality mathematical libraries implement extended-precision range reduction algorithms, often using multi-word representations of $\pi$ or employing Payne-Hanek reduction algorithms that extract the fractional part of $\frac{\theta}{2\pi}$ without computing the full quotient.

For arguments near the zeros or extrema of trigonometric functions, catastrophic cancellation becomes the dominant error source. Evaluating $\sin(\pi - \epsilon)$ for small $\epsilon$ using the reduction $\sin(\pi - \epsilon) = \sin\epsilon$ preserves accuracy, but directly computing $\sin(\pi - \epsilon)$ by evaluating sine at the double-precision approximation of $\pi$ suffers from the fact that the stored value of $\pi$ has rounding error on the order of machine epsilon, and this error is amplified by the derivative $\cos(\pi) = -1$. The resulting absolute error in $\sin(\pi - \epsilon)$ can be comparable to $\epsilon$ itself, yielding zero relative precision.

Evaluating tangent near its poles requires special handling. As $\theta \to \frac{\pi}{2}^-$, the naive computation $\tan\theta = \frac{\sin\theta}{\cos\theta}$ divides a number close to $1$ by a number close to $0$, producing a large result with small absolute error but potentially large relative error. The reciprocal formulation $\cot\left(\frac{\pi}{2} - \theta\right)$ near the pole offers better numerical stability by transforming the problem to evaluating cotangent near zero, where both sine and cosine are well-conditioned.

The inverse trigonometric functions—$\arcsin$, $\arccos$, and $\arctan$—present their own computational challenges due to their restricted domains and multi-valuedness. The principal branch of $\arcsin$ maps $[-1, 1]$ to $\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$, while $\arccos$ maps $[-1, 1]$ to $[0, \pi]$. Near the endpoints $x = \pm 1$, the derivatives $\frac{d}{dx}\arcsin x = \frac{1}{\sqrt{1-x^2}}$ and $\frac{d}{dx}\arccos x = -\frac{1}{\sqrt{1-x^2}}$ become unbounded, leading to severe conditioning issues. For $x$ near $\pm 1$, direct series evaluation loses precision, and alternative representations via $\arctan$ or asymptotic expansions become necessary.

The two-argument arctangent function $\operatorname{atan2}(y, x)$, which computes the angle $\theta \in (-\pi, \pi]$ such that $(\cos\theta, \sin\theta)$ is parallel to $(x, y)$, resolves the multi-valued ambiguity of the standard arctangent and avoids division-by-zero when $x = 0$. This function is essential in coordinate transformations, robotics, and signal processing where the full range of angles must be distinguished. The implementation requires careful branch-cut handling to ensure continuity and correct sign determination across all four quadrants.

From a theoretical perspective, the question of which angles admit exact radical expressions connects to Galois theory and the constructibility of regular polygons. An angle $\theta$ has trigonometric values expressible in radicals over $\mathbb{Q}$ if and only if the regular polygon with central angle $\theta$ is constructible by compass and straightedge, which occurs precisely when the number of sides is a product of a power of $2$ and distinct Fermat primes. The known Fermat primes are $3, 5, 17, 257, 65537$, so exact radical expressions exist for angles like $\frac{2\pi}{17}$ and $\frac{2\pi}{257}$, though these expressions are algebraically complex. The angle $\frac{2\pi}{7}$ corresponding to the regular heptagon has trigonometric values that are algebraic over $\mathbb{Q}$ (roots of cyclotomic polynomials) but not expressible in real radicals, because $7$ is not a Fermat prime and the Galois group of the seventh cyclotomic extension contains non-solvable structure when restricted to real radicals.

In computational geometry and graphics, efficient evaluation of multiple trigonometric values at uniformly spaced angles exploits recurrence relations. To compute $\sin(n\theta)$ and $\cos(n\theta)$ for $n = 0, 1, 2, \ldots, N$, the Chebyshev recurrence:

$$\cos((n+1)\theta) = 2\cos\theta \cdot \cos(n\theta) - \cos((n-1)\theta)$$

requires only one multiplication and two additions per iteration after computing the initial values $\cos 0 = 1$ and $\cos\theta$. This recurrence propagates rounding error linearly rather than exponentially, making it numerically stable for moderate $N$. For very large $N$ or high-precision requirements, FFT-based approaches that evaluate all $N$ values simultaneously via Bluestein's algorithm provide $O(N \log N)$ complexity with superior error characteristics.

The ubiquity of trigonometric functions in Fourier analysis, signal processing, and quantum mechanics establishes them as the canonical basis for decomposing periodic phenomena. The orthogonality relations:

$$\int_0^{2\pi} \sin(m\theta)\sin(n\theta) \, d\theta = \pi \delta_{mn}$$
$$\int_0^{2\pi} \cos(m\theta)\cos(n\theta) \, d\theta = \pi \delta_{mn}$$

for positive integers $m, n$ (with appropriate normalization for $n = 0$) make the trigonometric system $\{1, \cos\theta, \sin\theta, \cos 2\theta, \sin 2\theta, \ldots\}$ an orthogonal basis for the space $L^2([0, 2\pi])$ of square-integrable functions. This orthogonality, combined with the completeness of the trigonometric system (a consequence of the Weierstrass approximation theorem), justifies Fourier series expansions and spectral methods for solving differential equations.

The numerical stability of computing Fourier coefficients via discrete sampling depends critically on the relationship between the sampling frequency and the signal's spectral content. The Nyquist-Shannon sampling theorem guarantees that a band-limited signal can be perfectly reconstructed from samples taken at twice the maximum frequency, but aliasing artifacts arise when high-frequency components fold back into the observable spectrum. In the trigonometric context, evaluating $\sin(k\theta_n)$ where $\theta_n = \frac{2\pi n}{N}$ for $n = 0, 1, \ldots, N-1$ and $k > \frac{N}{2}$ produces values indistinguishable from $\sin((N-k)\theta_n)$, demonstrating the aliasing phenomenon directly in the circular function framework.

For symbolic computation and computer algebra systems, representing trigonometric expressions in canonical form requires rewrite rules based on the functional equations. The challenge lies in determining an optimal simplification strategy: expanding $\sin(3\theta)$ via addition formulas yields $3\sin\theta - 4\sin^3\theta$, while factoring reduces $\sin\theta + \sin\phi$ to $2\sin\frac{\theta+\phi}{2}\cos\frac{\theta-\phi}{2}$. No single canonical form minimizes both expression size and computational cost across all contexts, so advanced symbolic systems employ cost heuristics and user-directed strategies to navigate the space of equivalent trigonometric expressions.

The extension of real trigonometric functions to complex arguments via the definitions $\sin z = \frac{e^{iz} - e^{-iz}}{2i}$ and $\cos z = \frac{e^{iz} + e^{-iz}}{2}$ for $z \in \mathbb{C}$ transforms sine and cosine into entire functions that are no longer bounded. For purely imaginary arguments $z = i y$ with $y \in \mathbb{R}$, we obtain:

$$\sin(iy) = i\sinh y, \quad \cos(iy) = \cosh y$$

revealing the deep connection between circular and hyperbolic functions. The unbounded growth of hyperbolic functions as $|y| \to \infty$ contrasts sharply with the oscillatory behavior of real trigonometric functions, yet both families satisfy analogous addition formulas and differential equations, unified through their common exponential foundation.

In the context of numerical differential equations, trigonometric integrators exploit the oscillatory structure of solutions to Hamiltonian systems by exactly preserving certain trigonometric or polynomial invariants. For the harmonic oscillator $\ddot{x} + \omega^2 x = 0$ with solution $x(t) = A\cos(\omega t) + B\sin(\omega t)$, standard Runge-Kutta methods accumulate phase error that grows linearly with time, causing the numerical orbit to spiral outward or inward from the true circular trajectory in phase space. Trigonometric integrators parameterize the solution in terms of $\cos(\omega h)$ and $\sin(\omega h)$ where $h$ is the time step, exactly preserving energy and ensuring bounded long-time error.

The manifold structure of the unit circle as $\mathbb{S}^1 \cong \mathbb{R}/2\pi\mathbb{Z}$ places trigonometric functions within the framework of differential geometry. The tangent bundle $T\mathbb{S}^1$ at each point $P(\theta) = (\cos\theta, \sin\theta)$ is spanned by the velocity vector $\frac{d}{d\theta}P(\theta) = (-\sin\theta, \cos\theta)$, which is orthogonal to the position vector and has unit length, confirming that arc length parameterization by $\theta$ yields a unit-speed curve. The curvature of $\mathbb{S}^1$ is constant at $\kappa = 1$, corresponding to the second derivative $\frac{d^2}{d\theta^2}P(\theta) = (-\cos\theta, -\sin\theta) = -P(\theta)$, which always points toward the center of the circle with magnitude $1$. This geometric interpretation of the second-derivative relationship $P''(\theta) = -P(\theta)$ unifies the differential equation perspective with the intrinsic curvature of the circular trajectory.
