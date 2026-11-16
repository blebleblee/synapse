# Lesson 2: Differentiation Theory, Mean Value Theorems

## 1. First-Principles Intuition & Invariants

The derivative stands as the central object of differential calculus, encoding the instantaneous rate of change of a function at a point. While intuitive notions of velocity and tangent lines motivated its historical development through the work of Newton and Leibniz, the rigorous foundation rests on the epsilon-delta framework of limits established in our preceding study of continuity and convergence. The derivative transforms local linear approximation from geometric intuition into algebraic machinery, permitting us to answer questions about optimization, curve behavior, and function approximation with rigorous precision.

We begin with the formal definition. Let $f: D \to \mathbb{R}$ where $D \subseteq \mathbb{R}$, and let $c \in D$ be an interior point of the domain. The function $f$ is **differentiable at $c$** if the limit

$$f'(c) = \lim_{h \to 0} \frac{f(c+h) - f(c)}{h}$$

exists and is finite. This limit, when it exists, is called the **derivative of $f$ at $c$**. The expression $\frac{f(c+h) - f(c)}{h}$ represents the slope of the secant line connecting $(c, f(c))$ to $(c+h, f(c+h))$, and the limiting process captures the slope of the tangent line as the second point approaches the first.

An equivalent formulation replaces $h$ with $x - c$, yielding

$$f'(c) = \lim_{x \to c} \frac{f(x) - f(c)}{x - c}$$

This symmetric difference quotient perspective proves particularly useful when working with sequences and establishing continuity properties. The existence of this limit imposes a strong constraint: differentiability at a point implies continuity at that point. To prove this fundamental invariant, observe that if $f'(c)$ exists, then for $x \neq c$ in a neighborhood of $c$, we may write

$$f(x) - f(c) = \frac{f(x) - f(c)}{x - c} \cdot (x - c)$$

Taking limits as $x \to c$, the right side becomes $f'(c) \cdot 0 = 0$, establishing that $\lim_{x \to c} f(x) = f(c)$, which is precisely the definition of continuity at $c$. The converse fails dramatically: continuity does not imply differentiability, as witnessed by the absolute value function $f(x) = |x|$ at $x = 0$, where the left and right limits of the difference quotient yield $-1$ and $+1$ respectively.

The algebraic structure of derivatives emerges through the standard differentiation rules. For constant functions $f(x) = k$, the difference quotient $\frac{k - k}{h} = 0$ vanishes identically, yielding $f'(x) = 0$. For the power function $f(x) = x^n$ where $n \in \mathbb{N}$, the binomial theorem provides

$$\frac{(x+h)^n - x^n}{h} = \frac{\sum_{k=0}^{n} \binom{n}{k} x^{n-k} h^k - x^n}{h} = \sum_{k=1}^{n} \binom{n}{k} x^{n-k} h^{k-1}$$

As $h \to 0$, only the $k=1$ term survives, producing $f'(x) = nx^{n-1}$. This power rule extends to negative integers and rational exponents through the quotient and chain rules, ultimately holding for all real exponents under appropriate domain restrictions.

The **sum rule** $(f + g)' = f' + g'$ follows immediately from limit arithmetic: the difference quotient of a sum decomposes as a sum of difference quotients. The **product rule** requires more care. For functions $f$ and $g$ differentiable at $c$, we manipulate the difference quotient by adding and subtracting a strategic term:

$$\frac{f(c+h)g(c+h) - f(c)g(c)}{h} = \frac{f(c+h)g(c+h) - f(c)g(c+h) + f(c)g(c+h) - f(c)g(c)}{h}$$

Factoring yields

$$= g(c+h) \cdot \frac{f(c+h) - f(c)}{h} + f(c) \cdot \frac{g(c+h) - g(c)}{h}$$

Since $g$ is differentiable at $c$, it is continuous there, so $g(c+h) \to g(c)$ as $h \to 0$. Taking limits produces $(fg)'(c) = g(c)f'(c) + f(c)g'(c)$, the product rule. The **quotient rule** for $h = f/g$ where $g(c) \neq 0$ follows by applying the product rule to $f = hg$ and solving for $h'$:

$$f' = h'g + hg' \implies h' = \frac{f' - hg'}{g} = \frac{f'g - fg'}{g^2}$$

yielding the standard quotient rule formula.

The **chain rule** stands as the most sophisticated and powerful differentiation rule, permitting composition of differentiable functions. If $g$ is differentiable at $c$ and $f$ is differentiable at $g(c)$, then the composite $f \circ g$ is differentiable at $c$ with derivative

$$(f \circ g)'(c) = f'(g(c)) \cdot g'(c)$$

The standard proof via difference quotients encounters a subtle obstacle: the denominator $g(c+h) - g(c)$ may vanish for arbitrarily small nonzero $h$ even when $g'(c) \neq 0$. A rigorous proof introduces an auxiliary function. Since $f$ is differentiable at $g(c)$, we may write

$$f(y) - f(g(c)) = f'(g(c))(y - g(c)) + \epsilon(y)(y - g(c))$$

where $\epsilon(y) \to 0$ as $y \to g(c)$, and we define $\epsilon(g(c)) = 0$ to maintain continuity. Substituting $y = g(c+h)$ yields

$$f(g(c+h)) - f(g(c)) = f'(g(c))(g(c+h) - g(c)) + \epsilon(g(c+h))(g(c+h) - g(c))$$

Dividing by $h$ and taking limits as $h \to 0$, the continuity of $g$ at $c$ ensures $\epsilon(g(c+h)) \to 0$, and we obtain

$$(f \circ g)'(c) = f'(g(c)) \cdot g'(c) + 0 \cdot g'(c) = f'(g(c)) \cdot g'(c)$$

completing the proof with full rigor.

These algebraic rules, combined with known derivatives of elementary functions—$\frac{d}{dx}\sin x = \cos x$, $\frac{d}{dx}e^x = e^x$, $\frac{d}{dx}\ln x = \frac{1}{x}$—permit mechanical computation of derivatives for vast classes of functions. The derivative of $\sin x$ follows from the addition formula $\sin(x+h) = \sin x \cos h + \cos x \sin h$ combined with the fundamental limits $\lim_{h \to 0} \frac{\sin h}{h} = 1$ and $\lim_{h \to 0} \frac{\cos h - 1}{h} = 0$, which we established through geometric squeeze theorems in the limits chapter. The exponential derivative $\frac{d}{dx}e^x = e^x$ characterizes the exponential function as the unique solution to the differential equation $f'(x) = f(x)$ with $f(0) = 1$, a fixed-point property under differentiation that permeates analysis and differential equations.

## 2. Core Architecture & Mechanics

The derivative encodes local linear approximation: if $f$ is differentiable at $c$, then near $c$ we have the first-order Taylor expansion

$$f(x) = f(c) + f'(c)(x - c) + o(x - c)$$

where the Landau notation $o(x-c)$ denotes a term that vanishes faster than linearly as $x \to c$. This linearization principle underlies Newton's method for root-finding, optimization algorithms, and numerical differential equation solvers. The tangent line $L(x) = f(c) + f'(c)(x-c)$ provides the best linear approximation to $f$ near $c$ in the sense that the error $|f(x) - L(x)|$ is $o(|x-c|)$.

The global implications of local derivative information emerge through the **Mean Value Theorem** and its precursor, **Rolle's Theorem**. These theorems establish the fundamental principle that derivative values control function behavior over intervals, transforming pointwise information into global conclusions. Rolle's Theorem states: if $f: [a,b] \to \mathbb{R}$ is continuous on $[a,b]$, differentiable on $(a,b)$, and satisfies $f(a) = f(b)$, then there exists $c \in (a,b)$ such that $f'(c) = 0$.

The proof proceeds by cases. If $f$ is constant on $[a,b]$, then $f'(x) = 0$ for all $x \in (a,b)$ and any point suffices. Otherwise, $f$ attains either a maximum or minimum value strictly greater or less than $f(a) = f(b)$ at some interior point $c \in (a,b)$ by the Extreme Value Theorem, since continuous functions on compact intervals attain their supremum and infimum. Without loss of generality, suppose $f$ attains a maximum at $c$. For $h > 0$ sufficiently small that $c + h \in (a,b)$, we have $f(c+h) \leq f(c)$, yielding

$$\frac{f(c+h) - f(c)}{h} \leq 0$$

Taking the limit as $h \to 0^+$ gives $f'(c) \leq 0$. Similarly, for $h < 0$ with $c + h \in (a,b)$, we obtain $f(c+h) \leq f(c)$, so

$$\frac{f(c+h) - f(c)}{h} \geq 0$$

since dividing by negative $h$ reverses the inequality. Taking the limit as $h \to 0^-$ yields $f'(c) \geq 0$. Combining these inequalities forces $f'(c) = 0$, completing the proof.

The **Mean Value Theorem** generalizes Rolle's result by removing the constraint $f(a) = f(b)$. It asserts: if $f: [a,b] \to \mathbb{R}$ is continuous on $[a,b]$ and differentiable on $(a,b)$, then there exists $c \in (a,b)$ such that

$$f'(c) = \frac{f(b) - f(a)}{b - a}$$

Geometrically, this states that the instantaneous rate of change at some interior point equals the average rate of change over the interval. The proof reduces to Rolle's Theorem through a change of variables. Define the auxiliary function

$$g(x) = f(x) - f(a) - \frac{f(b) - f(a)}{b - a}(x - a)$$

This function $g$ represents the vertical distance between $f(x)$ and the secant line connecting $(a, f(a))$ to $(b, f(b))$. By construction, $g(a) = 0$ and $g(b) = f(b) - f(a) - (f(b) - f(a)) = 0$. Since $f$ is continuous on $[a,b]$ and differentiable on $(a,b)$, so is $g$. Rolle's Theorem guarantees a point $c \in (a,b)$ where $g'(c) = 0$. Computing the derivative yields

$$g'(c) = f'(c) - \frac{f(b) - f(a)}{b - a} = 0$$

establishing the Mean Value Theorem. This result has profound consequences: it implies that functions with zero derivative on an interval are constant, that functions with positive derivative are increasing, and provides the foundation for Taylor's theorem and the Fundamental Theorem of Calculus.

As a corollary, if $f'(x) = 0$ for all $x$ in an interval $I$, then $f$ is constant on $I$. To prove this, fix any two points $a < b$ in $I$. The Mean Value Theorem produces $c \in (a,b)$ with $f(b) - f(a) = f'(c)(b-a) = 0 \cdot (b-a) = 0$, so $f(b) = f(a)$. Since $a$ and $b$ were arbitrary, $f$ is constant on $I$. This innocent-looking result underpins uniqueness theorems for differential equations and antiderivatives.

The Mean Value Theorem extends to vector-valued functions through careful componentwise application, but a naive vector statement fails: there need not exist a single point $c$ where the vector derivative equals the average vector change. However, for real-valued functions, the theorem permits sharp inequalities. If $|f'(x)| \leq M$ for all $x \in (a,b)$, then applying the Mean Value Theorem to any subinterval $[x_1, x_2]$ yields $|f(x_2) - f(x_1)| = |f'(c)||x_2 - x_1| \leq M|x_2 - x_1|$, establishing that $f$ is Lipschitz continuous with constant $M$. This provides quantitative control on function variation from derivative bounds.

**L'Hôpital's Rule** offers a powerful technique for evaluating indeterminate limits of the form $\frac{0}{0}$ or $\frac{\infty}{\infty}$. The theorem states: if $f$ and $g$ are differentiable on an open interval containing $a$ (possibly extended to include $\pm\infty$), if $\lim_{x \to a} f(x) = \lim_{x \to a} g(x) = 0$ or both limits are $\pm\infty$, if $g'(x) \neq 0$ for $x$ near $a$ (but $x \neq a$), and if $\lim_{x \to a} \frac{f'(x)}{g'(x)}$ exists (finite or infinite), then

$$\lim_{x \to a} \frac{f(x)}{g(x)} = \lim_{x \to a} \frac{f'(x)}{g'(x)}$$

The proof for the $\frac{0}{0}$ case employs a generalized Mean Value Theorem due to Cauchy. Define $f(a) = g(a) = 0$ to extend continuity to $a$. For $x$ near $a$, Cauchy's Mean Value Theorem asserts the existence of $c$ between $a$ and $x$ such that

$$\frac{f(x) - f(a)}{g(x) - g(a)} = \frac{f'(c)}{g'(c)}$$

which simplifies to $\frac{f(x)}{g(x)} = \frac{f'(c)}{g'(c)}$ using our extension. As $x \to a$, the point $c$ is squeezed toward $a$, and the hypothesis that $\lim_{x \to a} \frac{f'(x)}{g'(x)}$ exists ensures $\frac{f'(c)}{g'(c)}$ converges to the same limit. Cauchy's theorem itself follows by applying Rolle's Theorem to the function $h(x) = (f(b) - f(a))g(x) - (g(b) - g(a))f(x)$, which satisfies $h(a) = h(b)$. The $\frac{\infty}{\infty}$ case requires more delicate epsilon-delta arguments and potential changes of variables to transform the problem into a $\frac{0}{0}$ case.

L'Hôpital's Rule applies iteratively when derivatives also yield indeterminate forms, as in $\lim_{x \to 0} \frac{e^x - 1 - x}{x^2}$. The first application gives $\lim_{x \to 0} \frac{e^x - 1}{2x}$, still $\frac{0}{0}$, and a second application yields $\lim_{x \to 0} \frac{e^x}{2} = \frac{1}{2}$. However, care must be exercised: the rule requires that the limit of the derivative ratio exists, and oscillatory behavior in derivatives can prevent convergence even when the original limit exists.

**Higher-order derivatives** capture acceleration, jerk, and higher rates of change. If $f'$ is differentiable at $c$, we define the **second derivative** $f''(c) = (f')'(c)$, and iteratively define the $n$-th derivative $f^{(n)}$ as the derivative of $f^{(n-1)}$. A function possessing $n$ continuous derivatives on an interval is said to be of class $C^n$; functions with derivatives of all orders are **smooth** or $C^\infty$. The class $C^\omega$ denotes **real analytic functions**, which equal their Taylor series in a neighborhood of each point—a strictly stronger condition than smoothness.

The second derivative test for local extrema exploits higher-order information. If $f'(c) = 0$ and $f''(c) > 0$, then $f$ has a local minimum at $c$; if $f''(c) < 0$, a local maximum. The proof examines the derivative $f'$ near $c$. Since $f''(c) > 0$, the derivative $f'$ is increasing near $c$. Because $f'(c) = 0$, we have $f'(x) < 0$ for $x$ slightly less than $c$ and $f'(x) > 0$ for $x$ slightly greater than $c$, so $f$ decreases to the left of $c$ and increases to the right, establishing a local minimum. The test is inconclusive when $f''(c) = 0$, as witnessed by $f(x) = x^3$ (inflection point) and $g(x) = x^4$ (minimum) at $x = 0$, both having vanishing first and second derivatives.

**Taylor's Theorem** provides the capstone of differentiation theory, expressing a function as a polynomial approximation plus a remainder term. For a function $f$ that is $(n+1)$ times differentiable on an open interval containing $a$ and $x$, we have

$$f(x) = \sum_{k=0}^{n} \frac{f^{(k)}(a)}{k!}(x-a)^k + R_n(x)$$

where $R_n(x)$ is the remainder. The **Lagrange form** of the remainder asserts the existence of $c$ strictly between $a$ and $x$ such that

$$R_n(x) = \frac{f^{(n+1)}(c)}{(n+1)!}(x-a)^{n+1}$$

This form mirrors the Mean Value Theorem, which is precisely the $n=0$ case. The **Cauchy form** provides

$$R_n(x) = \frac{f^{(n+1)}(c)}{n!}(x-c)^n(x-a)$$

for some $c$ between $a$ and $x$, while the **integral form** expresses

$$R_n(x) = \frac{1}{n!}\int_a^x (x-t)^n f^{(n+1)}(t) \, dt$$

The integral form follows from repeated integration by parts applied to $f(x) = f(a) + \int_a^x f'(t) \, dt$. Integrating by parts $n$ times extracts the polynomial terms and leaves the integral remainder. The Lagrange form then follows by applying the integral Mean Value Theorem to the integrand, which is permissible when $f^{(n+1)}$ is continuous.

To prove Taylor's theorem with Lagrange remainder, we employ a generalization of Rolle's theorem. Define the auxiliary function

$$g(t) = f(x) - \sum_{k=0}^{n} \frac{f^{(k)}(t)}{k!}(x-t)^k - R_n(x)\left(\frac{x-t}{x-a}\right)^{n+1}$$

where $R_n(x)$ is chosen so that $g(a) = 0$. By construction, $g(x) = 0$ as well, since the sum telescopes and the remainder term vanishes when $t = x$. Applying Rolle's theorem to $g$ on $[a,x]$ produces $c \in (a,x)$ where $g'(c) = 0$. Computing $g'(t)$ using the product and chain rules, most terms cancel telescopically, yielding

$$g'(t) = -\frac{f^{(n+1)}(t)}{n!}(x-t)^n + R_n(x)\frac{(n+1)(x-t)^n}{(x-a)^{n+1}}$$

Setting $g'(c) = 0$ and solving for $R_n(x)$ produces the Lagrange remainder formula. This proof, while technical, demonstrates how Rolle's theorem extends to control higher-order behavior.

## 3. High-Performance Optimization & Failure Modes

Computational evaluation of derivatives in symbolic algebra systems exploits automatic differentiation techniques that avoid explicit symbolic manipulation of increasingly complex expressions. **Automatic differentiation** decomposes functions into sequences of elementary operations, applies the chain rule mechanically, and propagates derivative information forward or backward through the computation graph. Forward-mode accumulates directional derivatives $\frac{\partial f}{\partial x_i}$ by augmenting each intermediate variable with its derivative, while reverse-mode (backpropagation) computes gradients $\nabla f$ efficiently when $f: \mathbb{R}^n \to \mathbb{R}$ with large $n$ by propagating adjoint variables backward. These techniques achieve machine-precision derivative computation at a constant factor overhead compared to function evaluation, avoiding the exponential blowup of symbolic differentiation for deeply nested compositions.

Numerical differentiation via finite differences approximates $f'(x)$ by $\frac{f(x+h) - f(x)}{h}$ for small $h$, but faces catastrophic cancellation when $h$ becomes too small relative to machine epsilon. The truncation error from Taylor expansion behaves as $O(h)$ for forward differences, $O(h^2)$ for centered differences $\frac{f(x+h) - f(x-h)}{2h}$, and decreases further for higher-order stencils. However, roundoff error grows as $O(\frac{\epsilon}{h})$ where $\epsilon$ is machine precision, creating a tradeoff. Optimal step size for centered differences in double precision ($\epsilon \approx 10^{-16}$) is $h \approx \epsilon^{1/3} \approx 10^{-5}$, yielding accuracy around $10^{-10}$. Richardson extrapolation accelerates convergence by combining estimates at multiple step sizes, but automatic differentiation dominates when implementation effort is amortized.

The Mean Value Theorem often appears in proofs of algorithm correctness and convergence rates. Newton's method for root-finding, $x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$, achieves quadratic convergence near simple roots precisely because Taylor's theorem with Lagrange remainder bounds the error $e_{n+1} = x_{n+1} - r$ by $e_{n+1} \approx -\frac{f''(\xi)}{2f'(x_n)} e_n^2$ for some $\xi$ between $x_n$ and $r$. When $|f''(\xi)|$ and $\frac{1}{|f'(x_n)|}$ remain bounded, the error squares at each iteration, producing the characteristic doubling of correct digits. The Mean Value Theorem also underpins interval arithmetic: if $f'(x) \in [a,b]$ for $x \in I$, then $f(x_2) - f(x_1) \in [a,b] \cdot (x_2 - x_1)$ for $x_1, x_2 \in I$, permitting rigorous enclosure of function ranges.

Failure modes in applying L'Hôpital's Rule often stem from neglecting the requirement that the limit of the derivative ratio must exist. The oscillating example $\lim_{x \to \infty} \frac{x + \sin x}{x}$ tempts application of L'Hôpital, yielding $\lim_{x \to \infty} \frac{1 + \cos x}{1}$, which fails to exist due to oscillation. However, the original limit equals $1$ by direct manipulation: $\frac{x + \sin x}{x} = 1 + \frac{\sin x}{x} \to 1 + 0 = 1$. L'Hôpital's Rule is a sufficient condition for limit existence, not a necessary one. The rule also requires the functions to be differentiable on a punctured neighborhood of the limit point, failing for piecewise-defined functions with jump discontinuities in derivatives.

Taylor series convergence presents another subtlety. A smooth function need not equal its Taylor series: the canonical counterexample $f(x) = e^{-1/x^2}$ for $x \neq 0$ and $f(0) = 0$ is $C^\infty$ on $\mathbb{R}$ with $f^{(n)}(0) = 0$ for all $n$, yielding the identically zero Taylor series at $x = 0$, which fails to represent $f$ on any neighborhood of zero. Real analytic functions avoid this pathology, with convergence guaranteed by bounding the Lagrange remainder. For $e^x$, the remainder $\frac{e^c}{(n+1)!}x^{n+1}$ vanishes as $n \to \infty$ for any fixed $x$ since factorials dominate exponentials. For $\sin x$ and $\cos x$, the $(n+1)$-th derivative is bounded by $1$, and $\frac{|x|^{n+1}}{(n+1)!} \to 0$ for all $x$, establishing convergence.

In optimization contexts, the second derivative test may fail to detect local extrema when $f''(c) = 0$. Higher-order tests examine the first nonzero derivative: if $f^{(k)}(c)$ is the first nonzero derivative at a critical point $c$, then $k$ even with $f^{(k)}(c) > 0$ indicates a local minimum, $f^{(k)}(c) < 0$ a local maximum, while $k$ odd signals an inflection point with no extremum. The proof follows from Taylor expansion: $f(x) = f(c) + \frac{f^{(k)}(c)}{k!}(x-c)^k + o((x-c)^k)$. For $x$ near $c$, the sign of $f(x) - f(c)$ is controlled by the leading term $\frac{f^{(k)}(c)}{k!}(x-c)^k$. When $k$ is even, $(x-c)^k > 0$ for $x \neq c$, so the sign depends only on $f^{(k)}(c)$, establishing extrema. When $k$ is odd, $(x-c)^k$ changes sign across $c$, producing an inflection point.

Implicit differentiation extends derivative computation to relations $F(x,y) = 0$ not explicitly solved for $y$. Treating $y$ as an implicit function of $x$ and differentiating both sides with respect to $x$ using the chain rule yields $\frac{\partial F}{\partial x} + \frac{\partial F}{\partial y}\frac{dy}{dx} = 0$, giving $\frac{dy}{dx} = -\frac{\partial F/\partial x}{\partial F/\partial y}$ when the partial derivative $\frac{\partial F}{\partial y} \neq 0$. The Implicit Function Theorem from multivariable calculus provides rigorous justification, guaranteeing local solvability and differentiability under nondegeneracy conditions. This technique proves essential for analyzing level curves, constrained optimization via Lagrange multipliers, and differential geometry of implicitly defined manifolds.

Parametric differentiation for curves $(x(t), y(t))$ yields the tangent vector $(\frac{dx}{dt}, \frac{dy}{dt})$ and the derivative $\frac{dy}{dx} = \frac{dy/dt}{dx/dt}$ when $\frac{dx}{dt} \neq 0$. Arc length parameterization by $s = \int_a^t \sqrt{(x'(u))^2 + (y'(u))^2} \, du$ produces unit-speed curves with $|\frac{d}{ds}(x(s), y(s))| = 1$, simplifying curvature calculations to $\kappa = |\frac{d^2}{ds^2}(x(s), y(s))|$. These differential-geometric constructs underpin robotics path planning, computer graphics spline interpolation, and general relativity's spacetime curvature.

In summary, differentiation theory provides a complete algebraic and analytical framework for studying local function behavior, extracting global properties through mean value theorems, and approximating functions via Taylor polynomials. The interplay between pointwise derivatives and interval-wide conclusions—mediated by Rolle's theorem, the Mean Value Theorem, and Taylor's theorem—exemplifies analysis at its most powerful, transforming infinitesimal information into finite, actionable conclusions. Mastery of these techniques equips the mathematician with tools for optimization, differential equations, numerical analysis, and the vast landscape of applications where rate-of-change considerations drive theory and practice.
