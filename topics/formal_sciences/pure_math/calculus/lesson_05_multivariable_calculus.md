# Lesson 5: Multivariable Calculus, Partial Derivatives

## 1. First-Principles Intuition & Invariants

The transition from single-variable calculus to multivariable calculus represents a profound conceptual leap. Where Newton and Leibniz concerned themselves with the rate of change of a function $f(x)$ along a single real line, the study of functions $f: \mathbb{R}^n \to \mathbb{R}^m$ demands that we grapple with simultaneous variation across multiple independent dimensions. This is not merely a technical generalization—it is the natural language of physics, economics, optimization theory, and differential geometry. Every equilibrium condition in thermodynamics, every optimal allocation in resource economics, and every geodesic on a curved manifold emerges from the machinery we develop here.

The central challenge is this: when a function depends on multiple variables, how do we measure its rate of change? In single-variable calculus, there is only one direction along which $x$ can vary. In $\mathbb{R}^n$, however, there are infinitely many directions radiating from any given point. We must therefore distinguish between several notions of derivative. The **partial derivative** measures change along coordinate axes while holding all other variables fixed. The **directional derivative** generalizes this to arbitrary directions specified by unit vectors. The **gradient** unifies these concepts into a single geometric object that points in the direction of steepest ascent and whose magnitude quantifies that steepness. Finally, the **total derivative** or **differential** captures the best linear approximation to the function near a point, encoding all directional information simultaneously through a linear transformation.

Before we can differentiate, we must first establish when a multivariable function is even continuous, and more subtly, when limits exist. The epsilon-delta framework from single-variable calculus extends naturally to metric spaces, but the topology of $\mathbb{R}^n$ introduces new pathologies. A function may approach different limits along different paths, or oscillate wildly near a point. The existence of all partial derivatives at a point does not guarantee continuity there, let alone differentiability. These distinctions, which collapse in the single-variable case, become critical in higher dimensions.

The fundamental invariant that governs differentiability in $\mathbb{R}^n$ is the **total derivative**: a linear transformation $Df(\mathbf{a}): \mathbb{R}^n \to \mathbb{R}^m$ such that the function $f$ is well-approximated near $\mathbf{a}$ by the affine map $f(\mathbf{a}) + Df(\mathbf{a})(\mathbf{x} - \mathbf{a})$. When $f: \mathbb{R}^n \to \mathbb{R}$ is a scalar-valued function, the total derivative is represented by the gradient vector $\nabla f(\mathbf{a})$, and the directional derivative in the direction of a unit vector $\mathbf{u}$ is simply the inner product $\nabla f(\mathbf{a}) \cdot \mathbf{u}$. This geometric interpretation—that the gradient is orthogonal to level sets and points toward increasing function values—underlies gradient descent optimization, the method of steepest ascent in variational calculus, and the formulation of conservative vector fields in physics.

When we compose multivariable functions, the single-variable chain rule $\frac{d}{dx}[f(g(x))] = f'(g(x)) g'(x)$ generalizes to a matrix multiplication formula involving Jacobian matrices. If $f: \mathbb{R}^n \to \mathbb{R}^m$ and $g: \mathbb{R}^p \to \mathbb{R}^n$, then the Jacobian of the composition $f \circ g$ at a point $\mathbf{a}$ is the matrix product $Df(g(\mathbf{a})) \cdot Dg(\mathbf{a})$. This seemingly abstract rule has immediate computational power: it allows us to differentiate implicitly defined functions, change coordinate systems systematically, and prove the Inverse Function Theorem, which guarantees local invertibility of smooth maps when the Jacobian determinant is nonzero.

The capstone applications of multivariable calculus are optimization problems. Finding local extrema of unconstrained functions reduces to solving $\nabla f = \mathbf{0}$ and analyzing the Hessian matrix of second partial derivatives. The Second Derivative Test in multiple variables requires eigenvalue analysis: a critical point is a local minimum if the Hessian is positive definite, a local maximum if negative definite, and a saddle point if indefinite. Constrained optimization, where we seek extrema of $f(\mathbf{x})$ subject to $g(\mathbf{x}) = c$, introduces the method of **Lagrange multipliers**. The key insight is geometric: at an extremum, the gradient of $f$ must be parallel to the gradient of the constraint $g$, so $\nabla f = \lambda \nabla g$ for some scalar $\lambda$. This transforms a constrained problem into solving a system of nonlinear equations, a method ubiquitous in economics (utility maximization under budget constraints), machine learning (support vector machines), and classical mechanics (variational principles).

Throughout this lesson, we maintain three organizing principles. First, **geometric intuition precedes algebraic formalism**: we visualize level curves, tangent planes, and gradient fields before manipulating symbols. Second, **computational tractability guides theoretical development**: we prove theorems that yield explicit algorithms, not merely existence statements. Third, **rigor is non-negotiable**: every theorem receives a complete proof, every algebraic transition is justified, and every limiting process is epsilon-delta validated. Multivariable calculus is the gateway to differential geometry, functional analysis, and partial differential equations; we lay foundations that will bear the weight of those structures.

## 2. Core Architecture & Mechanics

### Topology and Limits in Euclidean Space

We begin with the ambient space $\mathbb{R}^n$, equipped with the Euclidean norm $\|\mathbf{x}\| = \sqrt{x_1^2 + x_2^2 + \cdots + x_n^2}$ for $\mathbf{x} = (x_1, x_2, \ldots, x_n)$. This norm induces a metric $d(\mathbf{x}, \mathbf{y}) = \|\mathbf{x} - \mathbf{y}\|$, which in turn defines the topology: open balls $B(\mathbf{a}, r) = \{\mathbf{x} \in \mathbb{R}^n : \|\mathbf{x} - \mathbf{a}\| < r\}$, open sets (unions of open balls), and the notion of neighborhood. A set $U \subseteq \mathbb{R}^n$ is open if for every $\mathbf{a} \in U$, there exists $r > 0$ such that $B(\mathbf{a}, r) \subseteq U$. A point $\mathbf{a}$ is a **limit point** of a set $S$ if every neighborhood of $\mathbf{a}$ contains a point of $S$ distinct from $\mathbf{a}$ itself.

**Definition (Limit).** Let $f: D \subseteq \mathbb{R}^n \to \mathbb{R}^m$ and let $\mathbf{a}$ be a limit point of $D$. We say that $\lim_{\mathbf{x} \to \mathbf{a}} f(\mathbf{x}) = \mathbf{L}$ if for every $\epsilon > 0$, there exists $\delta > 0$ such that for all $\mathbf{x} \in D$ with $0 < \|\mathbf{x} - \mathbf{a}\| < \delta$, we have $\|f(\mathbf{x}) - \mathbf{L}\| < \epsilon$.

This definition is coordinate-free and works in arbitrary dimensions. The critical property is that the limit, if it exists, is unique. The proof is identical to the single-variable case: if $\mathbf{L}_1$ and $\mathbf{L}_2$ are both limits, then for any $\epsilon > 0$, we can make $\|f(\mathbf{x}) - \mathbf{L}_1\| < \epsilon/2$ and $\|f(\mathbf{x}) - \mathbf{L}_2\| < \epsilon/2$ simultaneously, so by the triangle inequality $\|\mathbf{L}_1 - \mathbf{L}_2\| < \epsilon$. Since $\epsilon$ is arbitrary, $\mathbf{L}_1 = \mathbf{L}_2$.

However, computing limits in $\mathbb{R}^n$ is substantially more difficult than in $\mathbb{R}$. In single-variable calculus, $x$ can approach $a$ from only two directions (left and right), and if the one-sided limits agree, the limit exists. In $\mathbb{R}^2$, there are infinitely many paths along which $\mathbf{x}$ can approach $\mathbf{a}$: along straight lines, parabolas, spirals. The limit exists only if $f(\mathbf{x})$ approaches the same value along every possible path.

**Example (Path-Dependent Limit).** Consider $f(x, y) = \frac{xy}{x^2 + y^2}$ for $(x,y) \neq (0,0)$. We investigate whether $\lim_{(x,y) \to (0,0)} f(x,y)$ exists. Approach along the $x$-axis by setting $y = 0$: then $f(x, 0) = 0$ for all $x \neq 0$, so the limit along this path is $0$. Approach along the line $y = x$: then $f(x, x) = \frac{x^2}{2x^2} = \frac{1}{2}$ for all $x \neq 0$. Since the limits along different paths disagree, the limit does not exist.

**Theorem (Continuity and Limits).** A function $f: D \subseteq \mathbb{R}^n \to \mathbb{R}^m$ is continuous at $\mathbf{a} \in D$ if and only if $\lim_{\mathbf{x} \to \mathbf{a}} f(\mathbf{x}) = f(\mathbf{a})$. Equivalently, $f$ is continuous at $\mathbf{a}$ if for every $\epsilon > 0$, there exists $\delta > 0$ such that $\|\mathbf{x} - \mathbf{a}\| < \delta$ implies $\|f(\mathbf{x}) - f(\mathbf{a})\| < \epsilon$.

The algebra of limits carries over: if $\lim_{\mathbf{x} \to \mathbf{a}} f(\mathbf{x}) = \mathbf{L}$ and $\lim_{\mathbf{x} \to \mathbf{a}} g(\mathbf{x}) = \mathbf{M}$, then $\lim_{\mathbf{x} \to \mathbf{a}} [f(\mathbf{x}) + g(\mathbf{x})] = \mathbf{L} + \mathbf{M}$, and if $f$ and $g$ are scalar-valued, $\lim_{\mathbf{x} \to \mathbf{a}} [f(\mathbf{x}) g(\mathbf{x})] = LM$. Compositions of continuous functions are continuous. Vector-valued functions $f: \mathbb{R}^n \to \mathbb{R}^m$ are continuous if and only if each component function is continuous, reducing vector problems to scalar ones.

### Partial Derivatives and the Tangent Plane

Let $f: \mathbb{R}^n \to \mathbb{R}$ be a scalar-valued function. The **partial derivative** of $f$ with respect to the $i$-th variable at a point $\mathbf{a} = (a_1, \ldots, a_n)$ is defined as the ordinary derivative of the single-variable function obtained by fixing all variables except $x_i$:

$$\frac{\partial f}{\partial x_i}(\mathbf{a}) = \lim_{h \to 0} \frac{f(a_1, \ldots, a_i + h, \ldots, a_n) - f(a_1, \ldots, a_n)}{h}$$

This is the instantaneous rate of change of $f$ in the direction parallel to the $i$-th coordinate axis. We also write $\partial_i f(\mathbf{a})$ or $f_{x_i}(\mathbf{a})$ for brevity. In two variables, the notation $f_x(a, b)$ and $f_y(a, b)$ is standard. Geometrically, $\frac{\partial f}{\partial x}(a, b)$ is the slope of the curve formed by intersecting the surface $z = f(x, y)$ with the vertical plane $y = b$.

**Example.** Let $f(x, y) = x^2 y + e^{xy}$. Then:

$$\frac{\partial f}{\partial x} = 2xy + y e^{xy}, \quad \frac{\partial f}{\partial y} = x^2 + x e^{xy}$$

At the point $(1, 0)$, we have $\frac{\partial f}{\partial x}(1, 0) = 0$ and $\frac{\partial f}{\partial y}(1, 0) = 1$.

Partial derivatives are computed using the same rules as single-variable differentiation, treating all other variables as constants. Higher-order partial derivatives are obtained by iterating: $\frac{\partial^2 f}{\partial x \partial y} = \frac{\partial}{\partial x}\left(\frac{\partial f}{\partial y}\right)$. A critical theorem governs when the order of differentiation can be interchanged.

**Theorem (Clairaut's Theorem / Schwarz's Theorem).** If $f: \mathbb{R}^n \to \mathbb{R}$ has continuous second partial derivatives in a neighborhood of $\mathbf{a}$, then the mixed partial derivatives are equal: $\frac{\partial^2 f}{\partial x_i \partial x_j}(\mathbf{a}) = \frac{\partial^2 f}{\partial x_j \partial x_i}(\mathbf{a})$.

**Proof (for $n=2$).** Let $f$ be defined near $(a, b)$ with continuous $f_{xy}$ and $f_{yx}$. Define the difference quotient:

$$\Delta(h, k) = \frac{f(a+h, b+k) - f(a+h, b) - f(a, b+k) + f(a, b)}{hk}$$

We evaluate this expression in two ways. First, apply the Mean Value Theorem to $x$: for each fixed $y$, there exists $\xi$ between $a$ and $a+h$ such that:

$$f(a+h, y) - f(a, y) = h f_x(\xi, y)$$

Applying this with $y = b+k$ and $y = b$:

$$\Delta(h, k) = \frac{h f_x(\xi_1, b+k) - h f_x(\xi_2, b)}{hk} = \frac{f_x(\xi_1, b+k) - f_x(\xi_2, b)}{k}$$

Now apply the Mean Value Theorem to $y$: there exists $\eta$ between $b$ and $b+k$ such that:

$$f_x(\xi_1, b+k) - f_x(\xi_1, b) = k f_{xy}(\xi_1, \eta)$$

Thus $\Delta(h, k) = f_{xy}(\xi_1, \eta)$ for some $(\xi_1, \eta)$ near $(a, b)$. By symmetry, reversing the order of operations yields $\Delta(h, k) = f_{yx}(\xi_3, \eta_2)$ for some $(\xi_3, \eta_2)$ near $(a, b)$. Taking $h, k \to 0$ and using the continuity of $f_{xy}$ and $f_{yx}$, we obtain $f_{xy}(a, b) = f_{yx}(a, b)$. $\square$

The geometric content of partial derivatives is encoded in the **tangent plane**. For $f: \mathbb{R}^2 \to \mathbb{R}$, the graph is a surface $S = \{(x, y, z) : z = f(x, y)\}$ in $\mathbb{R}^3$. At a point $(a, b, f(a,b))$, the tangent plane is the best linear approximation to $S$. The equation of this plane is:

$$z - f(a, b) = f_x(a, b)(x - a) + f_y(a, b)(y - b)$$

This is the affine function $L(x, y) = f(a, b) + f_x(a, b)(x - a) + f_y(a, b)(y - b)$ that matches $f$ at $(a, b)$ and has the same partial derivatives there. The existence of partial derivatives, however, is insufficient to guarantee that this tangent plane actually approximates the surface well. A stronger condition is needed.

### Differentiability and the Total Derivative

**Definition (Differentiability).** A function $f: \mathbb{R}^n \to \mathbb{R}$ is **differentiable** at $\mathbf{a}$ if there exists a linear transformation $L: \mathbb{R}^n \to \mathbb{R}$ such that:

$$\lim_{\mathbf{h} \to \mathbf{0}} \frac{\|f(\mathbf{a} + \mathbf{h}) - f(\mathbf{a}) - L(\mathbf{h})\|}{\|\mathbf{h}\|} = 0$$

The linear map $L$ is called the **total derivative** or **differential** of $f$ at $\mathbf{a}$, denoted $Df(\mathbf{a})$ or $df_{\mathbf{a}}$. This definition captures the idea that near $\mathbf{a}$, the function $f$ is well-approximated by the affine map $f(\mathbf{a}) + L(\mathbf{h})$, with an error that goes to zero faster than linearly in $\|\mathbf{h}\|$.

For scalar-valued functions $f: \mathbb{R}^n \to \mathbb{R}$, any linear map $L: \mathbb{R}^n \to \mathbb{R}$ can be represented as $L(\mathbf{h}) = \mathbf{v} \cdot \mathbf{h}$ for some vector $\mathbf{v} \in \mathbb{R}^n$. If $f$ is differentiable at $\mathbf{a}$ and all partial derivatives exist there, then $\mathbf{v} = \left(\frac{\partial f}{\partial x_1}(\mathbf{a}), \ldots, \frac{\partial f}{\partial x_n}(\mathbf{a})\right)$. This vector is the **gradient** of $f$ at $\mathbf{a}$, denoted $\nabla f(\mathbf{a})$.

**Theorem (Differentiability Implies Continuity).** If $f: \mathbb{R}^n \to \mathbb{R}$ is differentiable at $\mathbf{a}$, then $f$ is continuous at $\mathbf{a}$.

**Proof.** By definition of differentiability, there exists a linear map $L$ such that:

$$f(\mathbf{a} + \mathbf{h}) = f(\mathbf{a}) + L(\mathbf{h}) + \|\mathbf{h}\| \epsilon(\mathbf{h})$$

where $\epsilon(\mathbf{h}) \to 0$ as $\mathbf{h} \to \mathbf{0}$. Since $L$ is linear, it is continuous, so $L(\mathbf{h}) \to 0$ as $\mathbf{h} \to \mathbf{0}$. Hence:

$$\lim_{\mathbf{h} \to \mathbf{0}} f(\mathbf{a} + \mathbf{h}) = f(\mathbf{a}) + 0 + 0 = f(\mathbf{a})$$

which establishes continuity. $\square$

The converse is false: continuity does not imply differentiability, as the single-variable example $f(x) = |x|$ at $x = 0$ demonstrates. Moreover, the existence of all partial derivatives does not even imply continuity, let alone differentiability.

**Counterexample.** Define $f(x, y) = \begin{cases} \frac{xy^2}{x^2 + y^4} & (x,y) \neq (0,0) \\ 0 & (x,y) = (0,0) \end{cases}$. Along any line $y = mx$ through the origin, $f(mx, mx) = \frac{m^3 x^3}{x^2(1 + m^4 x^2)} = \frac{m^3 x}{1 + m^4 x^2} \to 0$ as $x \to 0$, so $f$ appears continuous. However, along the parabola $x = y^2$, we have $f(y^2, y) = \frac{y^4}{2y^4} = \frac{1}{2}$, so the limit along this path is $\frac{1}{2} \neq 0$. Thus $f$ is not continuous at the origin. The partial derivatives exist at $(0,0)$: $f_x(0,0) = \lim_{h \to 0} \frac{f(h, 0) - f(0,0)}{h} = 0$ and similarly $f_y(0,0) = 0$. Yet $f$ is discontinuous, hence not differentiable.

The sufficient condition for differentiability is the continuity of partial derivatives.

**Theorem (Sufficient Condition for Differentiability).** If all partial derivatives $\frac{\partial f}{\partial x_i}$ exist in a neighborhood of $\mathbf{a}$ and are continuous at $\mathbf{a}$, then $f$ is differentiable at $\mathbf{a}$.

**Proof (for $n=2$).** Let $f: \mathbb{R}^2 \to \mathbb{R}$ have continuous partial derivatives near $(a, b)$. We must show that:

$$f(a+h, b+k) - f(a, b) = f_x(a, b) h + f_y(a, b) k + \sqrt{h^2 + k^2} \epsilon(h, k)$$

where $\epsilon(h, k) \to 0$ as $(h, k) \to (0, 0)$. Write:

$$f(a+h, b+k) - f(a, b) = [f(a+h, b+k) - f(a, b+k)] + [f(a, b+k) - f(a, b)]$$

By the Mean Value Theorem applied to the function $x \mapsto f(x, b+k)$ on the interval $[a, a+h]$, there exists $\xi$ between $a$ and $a+h$ such that:

$$f(a+h, b+k) - f(a, b+k) = h f_x(\xi, b+k)$$

Similarly, applying the MVT to $y \mapsto f(a, y)$ on $[b, b+k]$, there exists $\eta$ between $b$ and $b+k$ such that:

$$f(a, b+k) - f(a, b) = k f_y(a, \eta)$$

Thus:

$$f(a+h, b+k) - f(a, b) = h f_x(\xi, b+k) + k f_y(a, \eta)$$

Since $f_x$ and $f_y$ are continuous at $(a, b)$, as $(h, k) \to (0, 0)$, we have $(\xi, b+k) \to (a, b)$ and $(a, \eta) \to (a, b)$, so:

$$f_x(\xi, b+k) = f_x(a, b) + \epsilon_1(h, k), \quad f_y(a, \eta) = f_y(a, b) + \epsilon_2(h, k)$$

where $\epsilon_1, \epsilon_2 \to 0$. Substituting:

$$f(a+h, b+k) - f(a, b) = h f_x(a, b) + k f_y(a, b) + h \epsilon_1(h, k) + k \epsilon_2(h, k)$$

The error term is bounded by:

$$|h \epsilon_1 + k \epsilon_2| \le \sqrt{h^2 + k^2}(|\epsilon_1| + |\epsilon_2|) = \sqrt{h^2 + k^2} \epsilon(h, k)$$

where $\epsilon(h, k) = |\epsilon_1| + |\epsilon_2| \to 0$. This establishes differentiability. $\square$

When $f$ is differentiable at $\mathbf{a}$, the gradient $\nabla f(\mathbf{a})$ is the unique vector representing the total derivative, so the tangent plane equation becomes:

$$L(\mathbf{x}) = f(\mathbf{a}) + \nabla f(\mathbf{a}) \cdot (\mathbf{x} - \mathbf{a})$$

This is the natural generalization of the tangent line $L(x) = f(a) + f'(a)(x - a)$ from single-variable calculus.

### Directional Derivatives and the Gradient

Partial derivatives measure change along coordinate directions. We now generalize to arbitrary directions. Let $\mathbf{u} = (u_1, \ldots, u_n)$ be a unit vector in $\mathbb{R}^n$ (so $\|\mathbf{u}\| = 1$). The **directional derivative** of $f$ at $\mathbf{a}$ in the direction $\mathbf{u}$ is:

$$D_{\mathbf{u}} f(\mathbf{a}) = \lim_{t \to 0} \frac{f(\mathbf{a} + t \mathbf{u}) - f(\mathbf{a})}{t}$$

This is the rate of change of $f$ as we move from $\mathbf{a}$ in the direction $\mathbf{u}$. Partial derivatives are special cases: $\frac{\partial f}{\partial x_i}(\mathbf{a}) = D_{\mathbf{e}_i} f(\mathbf{a})$, where $\mathbf{e}_i$ is the $i$-th standard basis vector.

**Theorem (Gradient and Directional Derivatives).** If $f: \mathbb{R}^n \to \mathbb{R}$ is differentiable at $\mathbf{a}$, then for any unit vector $\mathbf{u}$, the directional derivative exists and equals:

$$D_{\mathbf{u}} f(\mathbf{a}) = \nabla f(\mathbf{a}) \cdot \mathbf{u}$$

**Proof.** Since $f$ is differentiable at $\mathbf{a}$, we have:

$$f(\mathbf{a} + \mathbf{h}) = f(\mathbf{a}) + \nabla f(\mathbf{a}) \cdot \mathbf{h} + \|\mathbf{h}\| \epsilon(\mathbf{h})$$

where $\epsilon(\mathbf{h}) \to 0$ as $\mathbf{h} \to \mathbf{0}$. Substitute $\mathbf{h} = t \mathbf{u}$ with $t > 0$:

$$f(\mathbf{a} + t \mathbf{u}) = f(\mathbf{a}) + t \nabla f(\mathbf{a}) \cdot \mathbf{u} + |t| \epsilon(t \mathbf{u})$$

Dividing by $t$ and taking $t \to 0^+$:

$$D_{\mathbf{u}} f(\mathbf{a}) = \lim_{t \to 0^+} \frac{f(\mathbf{a} + t \mathbf{u}) - f(\mathbf{a})}{t} = \nabla f(\mathbf{a}) \cdot \mathbf{u} + \lim_{t \to 0^+} \epsilon(t \mathbf{u}) = \nabla f(\mathbf{a}) \cdot \mathbf{u}$$

The same argument works for $t \to 0^-$. $\square$

This theorem has profound geometric consequences. By the Cauchy-Schwarz inequality, $\nabla f(\mathbf{a}) \cdot \mathbf{u} \le \|\nabla f(\mathbf{a})\| \|\mathbf{u}\| = \|\nabla f(\mathbf{a})\|$, with equality when $\mathbf{u}$ is parallel to $\nabla f(\mathbf{a})$. Thus:

1. The gradient $\nabla f(\mathbf{a})$ points in the direction of **maximum rate of increase** of $f$ at $\mathbf{a}$.
2. The magnitude $\|\nabla f(\mathbf{a})\|$ equals this maximum rate.
3. The directional derivative is minimized (most negative) in the direction $-\nabla f(\mathbf{a})$.
4. The directional derivative is zero in directions orthogonal to $\nabla f(\mathbf{a})$.

The fourth point reveals the gradient's relationship to level sets. The **level set** $f^{-1}(c) = \{\mathbf{x} : f(\mathbf{x}) = c\}$ is the set of points where $f$ takes the constant value $c$. In $\mathbb{R}^2$, level sets are curves called **level curves**; in $\mathbb{R}^3$, they are **level surfaces**. If $\mathbf{r}(t)$ is a curve lying in the level set $f^{-1}(c)$, then $f(\mathbf{r}(t)) = c$ for all $t$. Differentiating both sides by the chain rule (to be proven shortly):

$$\nabla f(\mathbf{r}(t)) \cdot \mathbf{r}'(t) = 0$$

Thus $\nabla f$ is orthogonal to the tangent vector $\mathbf{r}'(t)$ of any curve in the level set. Since this holds for every such curve, $\nabla f(\mathbf{a})$ is orthogonal to the entire level set passing through $\mathbf{a}$. In $\mathbb{R}^2$, this means the gradient is perpendicular to the level curve; in $\mathbb{R}^3$, it is normal to the level surface.

**Example.** Consider $f(x, y) = x^2 + y^2$, representing the squared distance from the origin. The gradient is $\nabla f = (2x, 2y)$, which at any point $(x, y)$ points radially outward from the origin. The level curves are circles $x^2 + y^2 = c$, and indeed the gradient is everywhere perpendicular to these circles, pointing toward increasing values of $f$.

### The Multivariable Chain Rule

The chain rule for compositions of multivariable functions generalizes the single-variable formula via matrix multiplication. Let $\mathbf{r}: \mathbb{R} \to \mathbb{R}^n$ be a parameterized curve $\mathbf{r}(t) = (x_1(t), \ldots, x_n(t))$ and $f: \mathbb{R}^n \to \mathbb{R}$ a scalar field. The composition $h(t) = f(\mathbf{r}(t))$ is a single-variable function. If $\mathbf{r}$ is differentiable at $t$ and $f$ is differentiable at $\mathbf{r}(t)$, then:

$$\frac{dh}{dt} = \nabla f(\mathbf{r}(t)) \cdot \mathbf{r}'(t) = \sum_{i=1}^n \frac{\partial f}{\partial x_i}(\mathbf{r}(t)) \frac{dx_i}{dt}$$

This is the **single-parameter chain rule**. The proof follows from the definition of differentiability: $f(\mathbf{r}(t + \Delta t)) - f(\mathbf{r}(t)) = \nabla f(\mathbf{r}(t)) \cdot [\mathbf{r}(t + \Delta t) - \mathbf{r}(t)] + o(\|\mathbf{r}(t + \Delta t) - \mathbf{r}(t)\|)$. Dividing by $\Delta t$ and taking $\Delta t \to 0$ yields the result.

For compositions of multivariable functions $f: \mathbb{R}^n \to \mathbb{R}^m$ and $\mathbf{g}: \mathbb{R}^p \to \mathbb{R}^n$, the chain rule involves the **Jacobian matrix**. The Jacobian of $f$ at $\mathbf{a}$ is the $m \times n$ matrix:

$$Df(\mathbf{a}) = \begin{pmatrix} \frac{\partial f_1}{\partial x_1} & \cdots & \frac{\partial f_1}{\partial x_n} \\ \vdots & & \vdots \\ \frac{\partial f_m}{\partial x_1} & \cdots & \frac{\partial f_m}{\partial x_n} \end{pmatrix}_{\mathbf{a}}$$

where $f = (f_1, \ldots, f_m)$. Each row is the gradient of a component function.

**Theorem (Multivariable Chain Rule).** If $\mathbf{g}: \mathbb{R}^p \to \mathbb{R}^n$ is differentiable at $\mathbf{a}$ and $f: \mathbb{R}^n \to \mathbb{R}^m$ is differentiable at $\mathbf{g}(\mathbf{a})$, then the composition $f \circ \mathbf{g}$ is differentiable at $\mathbf{a}$, and:

$$D(f \circ \mathbf{g})(\mathbf{a}) = Df(\mathbf{g}(\mathbf{a})) \cdot D\mathbf{g}(\mathbf{a})$$

In component form, if $\mathbf{g} = (g_1, \ldots, g_n)$ depends on $(t_1, \ldots, t_p)$ and $f = (f_1, \ldots, f_m)$ depends on $(x_1, \ldots, x_n)$, then:

$$\frac{\partial (f_i \circ \mathbf{g})}{\partial t_j} = \sum_{k=1}^n \frac{\partial f_i}{\partial x_k}(\mathbf{g}(\mathbf{a})) \frac{\partial g_k}{\partial t_j}(\mathbf{a})$$

**Proof.** By differentiability of $\mathbf{g}$ at $\mathbf{a}$:

$$\mathbf{g}(\mathbf{a} + \mathbf{h}) = \mathbf{g}(\mathbf{a}) + D\mathbf{g}(\mathbf{a}) \mathbf{h} + \|\mathbf{h}\| \boldsymbol{\epsilon}_1(\mathbf{h})$$

where $\boldsymbol{\epsilon}_1(\mathbf{h}) \to \mathbf{0}$ as $\mathbf{h} \to \mathbf{0}$. Let $\mathbf{k} = \mathbf{g}(\mathbf{a} + \mathbf{h}) - \mathbf{g}(\mathbf{a})$. By differentiability of $f$ at $\mathbf{g}(\mathbf{a})$:

$$f(\mathbf{g}(\mathbf{a}) + \mathbf{k}) = f(\mathbf{g}(\mathbf{a})) + Df(\mathbf{g}(\mathbf{a})) \mathbf{k} + \|\mathbf{k}\| \boldsymbol{\epsilon}_2(\mathbf{k})$$

where $\boldsymbol{\epsilon}_2(\mathbf{k}) \to \mathbf{0}$ as $\mathbf{k} \to \mathbf{0}$. Substituting $\mathbf{k} = D\mathbf{g}(\mathbf{a}) \mathbf{h} + \|\mathbf{h}\| \boldsymbol{\epsilon}_1(\mathbf{h})$:

$$f(\mathbf{g}(\mathbf{a} + \mathbf{h})) = f(\mathbf{g}(\mathbf{a})) + Df(\mathbf{g}(\mathbf{a})) [D\mathbf{g}(\mathbf{a}) \mathbf{h} + \|\mathbf{h}\| \boldsymbol{\epsilon}_1(\mathbf{h})] + \|\mathbf{k}\| \boldsymbol{\epsilon}_2(\mathbf{k})$$

Since $\|\mathbf{k}\| \le C \|\mathbf{h}\|$ for some constant $C$ when $\mathbf{h}$ is small (by continuity of $\mathbf{g}$), the error term $\|\mathbf{k}\| \boldsymbol{\epsilon}_2(\mathbf{k})$ is $O(\|\mathbf{h}\|)$. Collecting terms linear in $\mathbf{h}$:

$$f(\mathbf{g}(\mathbf{a} + \mathbf{h})) = f(\mathbf{g}(\mathbf{a})) + [Df(\mathbf{g}(\mathbf{a})) D\mathbf{g}(\mathbf{a})] \mathbf{h} + o(\|\mathbf{h}\|)$$

This establishes that $D(f \circ \mathbf{g})(\mathbf{a}) = Df(\mathbf{g}(\mathbf{a})) D\mathbf{g}(\mathbf{a})$. $\square$

**Example (Change of Variables).** Express the partial derivatives of $f(x, y)$ with respect to polar coordinates $r, \theta$, where $x = r \cos \theta$ and $y = r \sin \theta$. Define $\mathbf{g}(r, \theta) = (r \cos \theta, r \sin \theta)$. The Jacobian is:

$$D\mathbf{g} = \begin{pmatrix} \frac{\partial x}{\partial r} & \frac{\partial x}{\partial \theta} \\ \frac{\partial y}{\partial r} & \frac{\partial y}{\partial \theta} \end{pmatrix} = \begin{pmatrix} \cos \theta & -r \sin \theta \\ \sin \theta & r \cos \theta \end{pmatrix}$$

By the chain rule:

$$\begin{pmatrix} \frac{\partial f}{\partial r} \\ \frac{\partial f}{\partial \theta} \end{pmatrix} = (D\mathbf{g})^T \begin{pmatrix} \frac{\partial f}{\partial x} \\ \frac{\partial f}{\partial y} \end{pmatrix} = \begin{pmatrix} \cos \theta & \sin \theta \\ -r \sin \theta & r \cos \theta \end{pmatrix} \begin{pmatrix} \frac{\partial f}{\partial x} \\ \frac{\partial f}{\partial y} \end{pmatrix}$$

Thus:

$$\frac{\partial f}{\partial r} = \cos \theta \frac{\partial f}{\partial x} + \sin \theta \frac{\partial f}{\partial y}, \quad \frac{\partial f}{\partial \theta} = -r \sin \theta \frac{\partial f}{\partial x} + r \cos \theta \frac{\partial f}{\partial y}$$

This technique is indispensable for solving partial differential equations in non-Cartesian coordinate systems.

### Implicit Differentiation and the Implicit Function Theorem

In single-variable calculus, an equation $F(x, y) = 0$ defines $y$ implicitly as a function of $x$ when $F_y \neq 0$. We compute $\frac{dy}{dx}$ by differentiating both sides: $F_x + F_y \frac{dy}{dx} = 0$, so $\frac{dy}{dx} = -\frac{F_x}{F_y}$. The multivariable generalization is the **Implicit Function Theorem**, which guarantees when an equation $F(\mathbf{x}, \mathbf{y}) = \mathbf{0}$ defines $\mathbf{y}$ locally as a function of $\mathbf{x}$.

**Theorem (Implicit Function Theorem, Single Equation).** Let $F: \mathbb{R}^{n+1} \to \mathbb{R}$ be continuously differentiable in a neighborhood of $(\mathbf{a}, b)$, where $\mathbf{a} = (a_1, \ldots, a_n) \in \mathbb{R}^n$ and $b \in \mathbb{R}$. Suppose $F(\mathbf{a}, b) = 0$ and $\frac{\partial F}{\partial y}(\mathbf{a}, b) \neq 0$. Then there exists a neighborhood $U$ of $\mathbf{a}$ and a unique continuously differentiable function $g: U \to \mathbb{R}$ such that $g(\mathbf{a}) = b$ and $F(\mathbf{x}, g(\mathbf{x})) = 0$ for all $\mathbf{x} \in U$. Moreover:

$$\frac{\partial g}{\partial x_i}(\mathbf{a}) = -\frac{\frac{\partial F}{\partial x_i}(\mathbf{a}, b)}{\frac{\partial F}{\partial y}(\mathbf{a}, b)}$$

**Proof Sketch.** The condition $\frac{\partial F}{\partial y}(\mathbf{a}, b) \neq 0$ ensures that $F$ is strictly monotone in the $y$-direction near $(\mathbf{a}, b)$. By the Inverse Function Theorem (to be stated shortly), the map $y \mapsto F(\mathbf{a}, y)$ is locally invertible. For $\mathbf{x}$ near $\mathbf{a}$, define $g(\mathbf{x})$ as the unique $y$ satisfying $F(\mathbf{x}, y) = 0$. Differentiating $F(\mathbf{x}, g(\mathbf{x})) = 0$ by the chain rule:

$$\frac{\partial F}{\partial x_i} + \frac{\partial F}{\partial y} \frac{\partial g}{\partial x_i} = 0$$

Solving for $\frac{\partial g}{\partial x_i}$ yields the formula. Continuity of $g$ and its derivatives follows from the Inverse Function Theorem. $\square$

**Example.** The equation $x^2 + y^2 + z^2 = 1$ defines the unit sphere. Near any point $(a, b, c)$ on the sphere where $c \neq 0$, we can solve for $z$ as a function of $x$ and $y$: $z = g(x, y) = \pm\sqrt{1 - x^2 - y^2}$. Set $F(x, y, z) = x^2 + y^2 + z^2 - 1$. Then $\frac{\partial F}{\partial z} = 2z \neq 0$ when $z \neq 0$, so the Implicit Function Theorem applies. The partial derivatives of $g$ are:

$$\frac{\partial z}{\partial x} = -\frac{\frac{\partial F}{\partial x}}{\frac{\partial F}{\partial z}} = -\frac{2x}{2z} = -\frac{x}{z}, \quad \frac{\partial z}{\partial y} = -\frac{y}{z}$$

These formulas give the slope of the tangent plane to the sphere at $(a, b, c)$.

The **Inverse Function Theorem** is the special case where $F(\mathbf{x}, y) = f(\mathbf{x}) - y$ for a given function $f$. It states conditions under which $f$ is locally invertible.

**Theorem (Inverse Function Theorem).** Let $f: \mathbb{R}^n \to \mathbb{R}^n$ be continuously differentiable in a neighborhood of $\mathbf{a}$, and suppose the Jacobian determinant $\det Df(\mathbf{a}) \neq 0$. Then there exists a neighborhood $U$ of $\mathbf{a}$ and a neighborhood $V$ of $f(\mathbf{a})$ such that $f: U \to V$ is a bijection with a continuously differentiable inverse $f^{-1}: V \to U$. Moreover, the Jacobian of $f^{-1}$ at $f(\mathbf{a})$ is:

$$Df^{-1}(f(\mathbf{a})) = [Df(\mathbf{a})]^{-1}$$

The proof relies on the Contraction Mapping Theorem and is beyond our scope, but the geometric content is clear: when the Jacobian is invertible, the function $f$ is locally a linear isomorphism, and nonlinear perturbations do not destroy invertibility in a small neighborhood.

**Example.** The transformation from Cartesian to polar coordinates $(x, y) = (r \cos \theta, r \sin \theta)$ has Jacobian determinant $r$. When $r \neq 0$, the map is locally invertible, recovering $(r, \theta)$ from $(x, y)$ via $r = \sqrt{x^2 + y^2}$ and $\theta = \arctan(y/x)$ (with appropriate branch cuts).

## 3. High-Performance Optimization & Failure Modes

### Critical Points and the Second Derivative Test

Optimization is the search for maximum or minimum values of a function. A point $\mathbf{a}$ is a **local maximum** of $f$ if $f(\mathbf{x}) \le f(\mathbf{a})$ for all $\mathbf{x}$ in some neighborhood of $\mathbf{a}$. It is a **local minimum** if $f(\mathbf{x}) \ge f(\mathbf{a})$ locally. If $f$ is differentiable at a local extremum $\mathbf{a}$, then necessarily $\nabla f(\mathbf{a}) = \mathbf{0}$ (first-order necessary condition). Such a point is called a **critical point** or **stationary point**.

**Proof.** If $\nabla f(\mathbf{a}) \neq \mathbf{0}$, then the directional derivative in the direction $\mathbf{u} = \nabla f(\mathbf{a}) / \|\nabla f(\mathbf{a})\|$ is $D_{\mathbf{u}} f(\mathbf{a}) = \|\nabla f(\mathbf{a})\| > 0$, so $f$ increases in the direction $\mathbf{u}$, contradicting the assumption that $\mathbf{a}$ is a local maximum. Similarly, in the direction $-\mathbf{u}$, $f$ decreases, contradicting local minimum. $\square$

However, $\nabla f(\mathbf{a}) = \mathbf{0}$ does not guarantee an extremum. The point could be a **saddle point**, where $f$ increases in some directions and decreases in others. The second-order information is encoded in the **Hessian matrix** of second partial derivatives:

$$Hf(\mathbf{a}) = \begin{pmatrix} \frac{\partial^2 f}{\partial x_1^2} & \frac{\partial^2 f}{\partial x_1 \partial x_2} & \cdots & \frac{\partial^2 f}{\partial x_1 \partial x_n} \\ \frac{\partial^2 f}{\partial x_2 \partial x_1} & \frac{\partial^2 f}{\partial x_2^2} & \cdots & \frac{\partial^2 f}{\partial x_2 \partial x_n} \\ \vdots & \vdots & \ddots & \vdots \\ \frac{\partial^2 f}{\partial x_n \partial x_1} & \frac{\partial^2 f}{\partial x_n \partial x_2} & \cdots & \frac{\partial^2 f}{\partial x_n^2} \end{pmatrix}_{\mathbf{a}}$$

By Clairaut's Theorem, if $f$ has continuous second partials, then $Hf$ is symmetric. The Hessian encodes the local curvature: near $\mathbf{a}$, the Taylor expansion is:

$$f(\mathbf{a} + \mathbf{h}) \approx f(\mathbf{a}) + \nabla f(\mathbf{a}) \cdot \mathbf{h} + \frac{1}{2} \mathbf{h}^T Hf(\mathbf{a}) \mathbf{h}$$

At a critical point where $\nabla f(\mathbf{a}) = \mathbf{0}$, the behavior is determined by the quadratic form $Q(\mathbf{h}) = \mathbf{h}^T Hf(\mathbf{a}) \mathbf{h}$.

**Theorem (Second Derivative Test).** Let $f$ have continuous second partial derivatives near $\mathbf{a}$, and suppose $\nabla f(\mathbf{a}) = \mathbf{0}$. Then:

1. If $Hf(\mathbf{a})$ is **positive definite** (all eigenvalues positive), then $\mathbf{a}$ is a strict local minimum.
2. If $Hf(\mathbf{a})$ is **negative definite** (all eigenvalues negative), then $\mathbf{a}$ is a strict local maximum.
3. If $Hf(\mathbf{a})$ is **indefinite** (has both positive and negative eigenvalues), then $\mathbf{a}$ is a saddle point.
4. If $Hf(\mathbf{a})$ is **semidefinite** (nonnegative or nonpositive, with at least one zero eigenvalue), the test is inconclusive.

**Proof.** Since $Hf(\mathbf{a})$ is symmetric, it has real eigenvalues and an orthonormal eigenbasis. In this basis, the quadratic form diagonalizes: $Q(\mathbf{h}) = \lambda_1 h_1^2 + \cdots + \lambda_n h_n^2$. If all $\lambda_i > 0$, then $Q(\mathbf{h}) > 0$ for all $\mathbf{h} \neq \mathbf{0}$, so $f(\mathbf{a} + \mathbf{h}) > f(\mathbf{a})$ for small $\|\mathbf{h}\|$, establishing a local minimum. If all $\lambda_i < 0$, then $Q(\mathbf{h}) < 0$, yielding a local maximum. If $\lambda_1 > 0$ and $\lambda_2 < 0$, then $Q$ is positive along the first eigenvector and negative along the second, so $f$ increases in one direction and decreases in another, defining a saddle. $\square$

In practice, determining definiteness is achieved via Sylvester's criterion: a symmetric matrix is positive definite if and only if all leading principal minors are positive. For $n = 2$:

$$Hf = \begin{pmatrix} f_{xx} & f_{xy} \\ f_{xy} & f_{yy} \end{pmatrix}$$

The determinant is $D = f_{xx} f_{yy} - f_{xy}^2$ (the **discriminant**). The matrix is positive definite if $f_{xx} > 0$ and $D > 0$, negative definite if $f_{xx} < 0$ and $D > 0$, and indefinite if $D < 0$. If $D = 0$, the test fails.

**Example.** Find and classify the critical points of $f(x, y) = x^3 - 3x + y^2$. Compute:

$$\nabla f = (3x^2 - 3, 2y) = (0, 0) \implies x^2 = 1, \, y = 0$$

Critical points: $(1, 0)$ and $(-1, 0)$. The Hessian is:

$$Hf = \begin{pmatrix} 6x & 0 \\ 0 & 2 \end{pmatrix}$$

At $(1, 0)$: $Hf = \begin{pmatrix} 6 & 0 \\ 0 & 2 \end{pmatrix}$, eigenvalues $6, 2 > 0$, so $(1, 0)$ is a local minimum.

At $(-1, 0)$: $Hf = \begin{pmatrix} -6 & 0 \\ 0 & 2 \end{pmatrix}$, eigenvalues $-6, 2$, so $(-1, 0)$ is a saddle point.

### Constrained Optimization and Lagrange Multipliers

Real-world optimization problems often involve constraints. For instance, maximize profit $f(\mathbf{x})$ subject to resource constraints $g(\mathbf{x}) = c$. The method of **Lagrange multipliers** converts this into an unconstrained problem by introducing auxiliary variables.

**Theorem (Lagrange Multipliers, Single Constraint).** Let $f, g: \mathbb{R}^n \to \mathbb{R}$ be continuously differentiable. Suppose $\mathbf{a}$ is a local extremum of $f$ subject to the constraint $g(\mathbf{x}) = c$, and suppose $\nabla g(\mathbf{a}) \neq \mathbf{0}$. Then there exists a scalar $\lambda$ (the **Lagrange multiplier**) such that:

$$\nabla f(\mathbf{a}) = \lambda \nabla g(\mathbf{a})$$

**Proof.** The constraint $g(\mathbf{x}) = c$ defines a level set, which is an $(n-1)$-dimensional surface $S$ near $\mathbf{a}$ (by the Implicit Function Theorem, since $\nabla g(\mathbf{a}) \neq \mathbf{0}$). If $\mathbf{a}$ is an extremum of $f$ on $S$, then for any curve $\mathbf{r}(t)$ in $S$ with $\mathbf{r}(0) = \mathbf{a}$, the function $h(t) = f(\mathbf{r}(t))$ has a local extremum at $t = 0$, so $h'(0) = 0$. By the chain rule:

$$h'(0) = \nabla f(\mathbf{a}) \cdot \mathbf{r}'(0) = 0$$

This holds for all tangent vectors $\mathbf{r}'(0)$ to $S$ at $\mathbf{a}$. Thus $\nabla f(\mathbf{a})$ is orthogonal to the tangent space of $S$. But $\nabla g(\mathbf{a})$ is also orthogonal to $S$ (since $S$ is a level set of $g$). Therefore, $\nabla f(\mathbf{a})$ and $\nabla g(\mathbf{a})$ are parallel, so $\nabla f(\mathbf{a}) = \lambda \nabla g(\mathbf{a})$ for some scalar $\lambda$. $\square$

The practical algorithm is to form the **Lagrangian** $L(\mathbf{x}, \lambda) = f(\mathbf{x}) - \lambda[g(\mathbf{x}) - c]$ and solve the system:

$$\nabla_{\mathbf{x}} L = \mathbf{0}, \quad \frac{\partial L}{\partial \lambda} = 0$$

This yields $n + 1$ equations in $n + 1$ unknowns $(\mathbf{x}, \lambda)$.

**Example.** Maximize $f(x, y) = xy$ subject to $x^2 + y^2 = 1$. The Lagrangian is $L(x, y, \lambda) = xy - \lambda(x^2 + y^2 - 1)$. Setting partial derivatives to zero:

$$\frac{\partial L}{\partial x} = y - 2\lambda x = 0, \quad \frac{\partial L}{\partial y} = x - 2\lambda y = 0, \quad \frac{\partial L}{\partial \lambda} = -(x^2 + y^2 - 1) = 0$$

From the first two equations, $y = 2\lambda x$ and $x = 2\lambda y$, so $y = 4\lambda^2 y$. If $y \neq 0$, then $\lambda = \pm \frac{1}{2}$. For $\lambda = \frac{1}{2}$: $y = x$, so $2x^2 = 1$, yielding $x = y = \pm \frac{1}{\sqrt{2}}$. For $\lambda = -\frac{1}{2}$: $y = -x$, so $x = -y$, yielding $x = \pm \frac{1}{\sqrt{2}}, y = \mp \frac{1}{\sqrt{2}}$. Evaluating $f$ at these four points:

$$f\left(\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}}\right) = \frac{1}{2}, \quad f\left(-\frac{1}{\sqrt{2}}, -\frac{1}{\sqrt{2}}\right) = \frac{1}{2}, \quad f\left(\frac{1}{\sqrt{2}}, -\frac{1}{\sqrt{2}}\right) = -\frac{1}{2}, \quad f\left(-\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}}\right) = -\frac{1}{2}$$

The maximum is $\frac{1}{2}$, attained at $\left(\pm \frac{1}{\sqrt{2}}, \pm \frac{1}{\sqrt{2}}\right)$.

For multiple constraints $g_1(\mathbf{x}) = c_1, \ldots, g_m(\mathbf{x}) = c_m$, the generalization introduces $m$ multipliers:

$$\nabla f(\mathbf{a}) = \lambda_1 \nabla g_1(\mathbf{a}) + \cdots + \lambda_m \nabla g_m(\mathbf{a})$$

The Lagrangian is $L(\mathbf{x}, \boldsymbol{\lambda}) = f(\mathbf{x}) - \sum_{i=1}^m \lambda_i [g_i(\mathbf{x}) - c_i]$, and we solve $\nabla_{\mathbf{x}} L = \mathbf{0}$ together with the constraint equations.

### Computational Workflow and Numerical Stability

In applications, we rarely solve optimization problems analytically. Numerical methods dominate. Gradient descent iteratively moves in the direction of steepest descent: $\mathbf{x}_{k+1} = \mathbf{x}_k - \alpha \nabla f(\mathbf{x}_k)$, where $\alpha > 0$ is the learning rate. Convergence is guaranteed for convex $f$ with appropriate $\alpha$, but can be slow. Newton's method uses second-order information: $\mathbf{x}_{k+1} = \mathbf{x}_k - [Hf(\mathbf{x}_k)]^{-1} \nabla f(\mathbf{x}_k)$, converging quadratically near a minimum when the Hessian is positive definite.

For constrained optimization, the **KKT (Karush-Kuhn-Tucker) conditions** generalize Lagrange multipliers to inequality constraints. For the problem minimize $f(\mathbf{x})$ subject to $g_i(\mathbf{x}) \le 0$ and $h_j(\mathbf{x}) = 0$, the KKT conditions state that at an optimum $\mathbf{x}^*$:

$$\nabla f(\mathbf{x}^*) + \sum_i \mu_i \nabla g_i(\mathbf{x}^*) + \sum_j \lambda_j \nabla h_j(\mathbf{x}^*) = \mathbf{0}$$

with $\mu_i \ge 0$, $\mu_i g_i(\mathbf{x}^*) = 0$ (complementary slackness), $g_i(\mathbf{x}^*) \le 0$, and $h_j(\mathbf{x}^*) = 0$.

Numerical pitfalls include ill-conditioned Hessians (large condition number, causing instability), flat regions where $\nabla f \approx \mathbf{0}$ but no extremum exists (plateaus), and saddle points where gradient-based methods stall. Regularization techniques, such as adding $\epsilon I$ to the Hessian, improve stability. Stochastic gradient descent (SGD) replaces the full gradient with a noisy estimate from a data subset, enabling scalability to high-dimensional problems like deep learning.

### Failure Modes and Edge Cases

**Discontinuous Functions.** If $f$ is not continuous, it may have no extrema even on a compact domain. For instance, $f(x, y) = \begin{cases} 1 & x^2 + y^2 < 1 \\ 0 & x^2 + y^2 = 1 \end{cases}$ on the closed unit disk has no maximum, as $f < 1$ everywhere on the boundary.

**Boundary Extrema.** When optimizing over a closed and bounded domain $D$, extrema can occur either at critical points in the interior (where $\nabla f = \mathbf{0}$) or on the boundary $\partial D$. The Extreme Value Theorem guarantees that a continuous function on a compact set attains its maximum and minimum, but they may lie on the boundary. To find boundary extrema, parameterize the boundary and optimize the resulting function of fewer variables.

**Degenerate Critical Points.** If the Hessian is singular at a critical point (zero determinant), the second derivative test is inconclusive. Higher-order derivatives or topological methods (Morse theory) are needed. For instance, $f(x, y) = x^4 + y^4$ has $\nabla f(0, 0) = (0, 0)$ and $Hf(0, 0) = 0$, yet $(0, 0)$ is a strict global minimum.

**Constraint Qualification Failures.** Lagrange multipliers require $\nabla g(\mathbf{a}) \neq \mathbf{0}$. If the constraint gradient vanishes, the constraint surface may have a cusp or singularity, and the method fails. For example, minimize $f(x, y) = x$ subject to $(x - 1)^2 + y^2 = 0$. The constraint forces $(x, y) = (1, 0)$, but $\nabla g(1, 0) = (0, 0)$.

**Non-Existence of Smooth Solutions.** The Implicit Function Theorem requires $\frac{\partial F}{\partial y} \neq 0$. If this fails, the level set may fold or become multivalued. The curve $x^2 + y^2 = 0$ consists only of the origin, not a smooth manifold. The equation $y^2 = x$ defines two branches $y = \pm\sqrt{x}$ for $x > 0$, neither smooth at $x = 0$.

**Computational Sensitivity.** Evaluating mixed partials numerically via finite differences $\frac{f(x+h, y+k) - f(x+h, y) - f(x, y+k) + f(x, y)}{hk}$ is highly sensitive to roundoff error when $h, k$ are small. Clairaut's theorem holds in exact arithmetic but may fail numerically if $f_{xy}$ and $f_{yx}$ are computed at different grid points or with different step sizes. Automatic differentiation (AD) avoids these issues by computing derivatives symbolically during execution.

The mastery of multivariable calculus is not merely symbolic manipulation but geometric intuition. The gradient as a normal vector, the Hessian as a curvature detector, the Jacobian as a local linear map—these are the conceptual primitives underlying fluid dynamics, general relativity, machine learning, and economic theory. By establishing rigorous foundations and explicit computational recipes, we equip ourselves to navigate the vast landscape where calculus meets the continuous geometry of the real world.
