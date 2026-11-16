# Lesson 3: Analytic Methods in Coordinate Geometry

## 1. First-Principles Intuition & Invariants

The birth of analytic geometry in the seventeenth century represented a conceptual revolution whose magnitude cannot be overstated: the unification of algebraic manipulation with geometric intuition through the medium of coordinate systems. René Descartes and Pierre de Fermat independently discovered that geometric objects—curves, surfaces, and their intersections—could be faithfully encoded as algebraic equations, thereby importing the full arsenal of algebraic techniques into the investigation of spatial relationships. This lesson dissects the machinery of coordinate geometry from first principles, establishing both the classical Cartesian framework and its extensions into parametric, polar, and vector formulations.

At its core, analytic geometry rests on a simple but profound bijection: every point in Euclidean space $\mathbb{R}^n$ corresponds to a unique ordered $n$-tuple of real numbers, and conversely, every such $n$-tuple determines a unique point. In the plane, we establish this correspondence by selecting an origin $O$ and two perpendicular directed lines (the $x$-axis and $y$-axis) passing through $O$. Any point $P$ in the plane determines a unique ordered pair $(x, y)$ where $x$ measures signed distance along the horizontal axis and $y$ measures signed distance along the vertical axis. This coordinate assignment transforms geometric questions into algebraic ones: a locus of points satisfying a geometric constraint becomes the solution set of an equation or system of equations.

The distance metric inherited from Euclidean geometry provides the foundational invariant under which all analytic methods operate. For two points $P_1 = (x_1, y_1)$ and $P_2 = (x_2, y_2)$ in the plane, the Euclidean distance is given by the Pythagorean formula

$$d(P_1, P_2) = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}.$$

This metric extends naturally to $\mathbb{R}^n$ as

$$d(\mathbf{p}, \mathbf{q}) = \sqrt{\sum_{i=1}^n (q_i - p_i)^2} = \|\mathbf{q} - \mathbf{p}\|_2,$$

where $\|\cdot\|_2$ denotes the Euclidean norm. The metric induces a topology on $\mathbb{R}^n$ and provides the geometric foundation for optimization, approximation, and convergence arguments throughout mathematical analysis.

Conic sections—ellipses, parabolas, and hyperbolas—emerge as the locus of points satisfying quadratic polynomial equations in two variables. The general second-degree equation

$$Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0$$

encodes all non-degenerate conics, with the discriminant $\Delta = B^2 - 4AC$ determining the conic type: $\Delta < 0$ yields an ellipse (or circle when $A = C$ and $B = 0$), $\Delta = 0$ yields a parabola, and $\Delta > 0$ yields a hyperbola. The algebraic classification mirrors the classical geometric definition via cutting planes through a double cone, but the coordinate approach permits direct calculation of geometric invariants—foci, directrices, eccentricity, asymptotes—through purely algebraic manipulation.

Parametric representations introduce time as an auxiliary variable, expressing coordinates as functions of a parameter $t$. A parametric curve in the plane takes the form $\mathbf{r}(t) = (x(t), y(t))$ where $t$ ranges over some interval $I \subseteq \mathbb{R}$. This formulation proves indispensable for curves that fail the vertical line test (and thus cannot be expressed as $y = f(x)$), for describing motion and velocity, and for computing arc length and curvature through differential calculus. The cycloid, the parametric curve $(x(t), y(t)) = (r(t - \sin t), r(1 - \cos t))$ traced by a point on the rim of a rolling circle, exemplifies a curve whose elegant geometric definition becomes computationally tractable only through parametric coordinates.

Polar coordinates $(r, \theta)$ provide an alternative coordinate system particularly suited to problems exhibiting rotational symmetry. The conversion formulas

$$x = r\cos\theta, \quad y = r\sin\theta$$

relate Cartesian and polar representations, with the inverse transformation given by

$$r = \sqrt{x^2 + y^2}, \quad \theta = \arctan\left(\frac{y}{x}\right)$$

with appropriate quadrant adjustments. Curves such as the Archimedean spiral $r = a\theta$, the cardioid $r = a(1 + \cos\theta)$, and the rose curves $r = a\cos(k\theta)$ admit compact polar representations while their Cartesian forms involve unwieldy algebraic equations. The polar distance formula between points $(r_1, \theta_1)$ and $(r_2, \theta_2)$ becomes

$$d = \sqrt{r_1^2 + r_2^2 - 2r_1 r_2 \cos(\theta_2 - \theta_1)},$$

a direct consequence of the law of cosines applied to the triangle formed by the origin and the two points.

Vector formulations elevate coordinate geometry into a coordinate-free framework by treating points as position vectors $\mathbf{p} = \langle x, y \rangle = x\mathbf{i} + y\mathbf{j}$ where $\mathbf{i}$ and $\mathbf{j}$ denote standard basis vectors. Lines become affine subspaces parameterized by $\mathbf{r}(t) = \mathbf{p}_0 + t\mathbf{v}$ where $\mathbf{p}_0$ is a point on the line and $\mathbf{v}$ is a direction vector. The dot product $\mathbf{u} \cdot \mathbf{v} = u_1 v_1 + u_2 v_2$ encodes orthogonality (when zero), computes projections, and measures angles through

$$\cos\theta = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}.$$

The cross product in $\mathbb{R}^3$ provides signed area and normal vectors, enabling efficient computation of distances from points to lines and planes. Vector methods reveal geometric relationships through algebraic identities: the parallelogram law $\|\mathbf{u} + \mathbf{v}\|^2 + \|\mathbf{u} - \mathbf{v}\|^2 = 2(\|\mathbf{u}\|^2 + \|\mathbf{v}\|^2)$ and the polarization identity $\mathbf{u} \cdot \mathbf{v} = \frac{1}{4}(\|\mathbf{u} + \mathbf{v}\|^2 - \|\mathbf{u} - \mathbf{v}\|^2)$ connect inner products to norms.

Duality principles in coordinate geometry manifest through the correspondence between points and lines. In the projective plane, a point $(a, b)$ corresponds to the line $ax + by = 1$ (when $a^2 + b^2 \neq 0$), and a line $px + qy = 1$ corresponds to the point $(p, q)$. This duality exchanges incidence with collinearity: three points lying on a common line correspond to three lines meeting at a common point. The principle extends to conics through polarity: for a conic $C$, each point $P$ determines a unique polar line $\ell_P$, and conversely, each line $\ell$ determines a unique pole point $P_\ell$. When $P$ lies on $C$, its polar $\ell_P$ coincides with the tangent line at $P$. Duality transforms theorems into dual theorems: Pascal's theorem (six points on a conic) dualizes to Brianchon's theorem (six tangent lines to a conic), and Desargues' theorem is self-dual.

The synthetic-analytic dichotomy in geometry—the contrast between pure geometric reasoning and coordinate-based calculation—dissolves in mature mathematical practice. Analytic methods provide algorithmic clarity and computational tractability, transforming existence proofs into constructive procedures and enabling optimization through calculus and linear algebra. Yet geometric intuition guides problem formulation, suggests coordinate system choices, and validates results. The interplay between geometric insight and algebraic technique constitutes the essence of analytic geometry.

## 2. Core Architecture & Mechanics

The Cartesian coordinate system in the plane establishes an isomorphism between $\mathbb{R}^2$ and the geometric plane, encoding geometric structure through algebraic operations. We begin by deriving the equation of a line from first principles. A non-vertical line passing through $(x_0, y_0)$ with slope $m$ satisfies the point-slope equation

$$y - y_0 = m(x - x_0).$$

This rearranges to the slope-intercept form $y = mx + b$ where $b = y_0 - mx_0$ is the $y$-intercept. For vertical lines where slope is undefined, we write $x = c$ for some constant $c$. A more symmetric and general representation is the implicit form $ax + by + c = 0$ where $(a, b) \neq (0, 0)$. The vector $(a, b)$ is normal to the line, and we obtain the explicit form by solving for $y$ when $b \neq 0$.

The distance from a point $(x_0, y_0)$ to the line $ax + by + c = 0$ is computed by projecting the vector from any point on the line to $(x_0, y_0)$ onto the unit normal vector $\mathbf{n} = \frac{1}{\sqrt{a^2 + b^2}}(a, b)$. Let $(x_1, y_1)$ be any point satisfying $ax_1 + by_1 + c = 0$. The vector from $(x_1, y_1)$ to $(x_0, y_0)$ is $\mathbf{w} = (x_0 - x_1, y_0 - y_1)$, and the signed distance is $d = \mathbf{w} \cdot \mathbf{n}$. Computing this dot product yields

$$d = \frac{(x_0 - x_1)a + (y_0 - y_1)b}{\sqrt{a^2 + b^2}} = \frac{ax_0 + by_0 - (ax_1 + by_1)}{\sqrt{a^2 + b^2}} = \frac{ax_0 + by_0 + c}{\sqrt{a^2 + b^2}},$$

where we used $ax_1 + by_1 = -c$. The unsigned distance is the absolute value of this expression. This formula extends to hyperplanes in $\mathbb{R}^n$: the distance from $\mathbf{x}_0$ to the hyperplane $\mathbf{a}^T \mathbf{x} + c = 0$ is $\frac{|\mathbf{a}^T \mathbf{x}_0 + c|}{\|\mathbf{a}\|}$.

Conic sections emerge from the general quadratic equation. To classify and analyze conics, we employ matrix formulations and eigenvalue decomposition. The general conic

$$Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0$$

can be written in matrix form as

$$\mathbf{x}^T Q \mathbf{x} + \mathbf{d}^T \mathbf{x} + F = 0$$

where $\mathbf{x} = \begin{pmatrix} x \\ y \end{pmatrix}$, $Q = \begin{pmatrix} A & B/2 \\ B/2 & C \end{pmatrix}$, and $\mathbf{d} = \begin{pmatrix} D \\ E \end{pmatrix}$. The matrix $Q$ is symmetric, hence diagonalizable with real eigenvalues $\lambda_1, \lambda_2$. The discriminant $\Delta = B^2 - 4AC = -4\det(Q) = -4\lambda_1\lambda_2$ determines the conic type through the signs of the eigenvalues. When $\lambda_1$ and $\lambda_2$ have the same sign ($\Delta < 0$), the conic is an ellipse; when one eigenvalue is zero ($\Delta = 0$), a parabola; when they have opposite signs ($\Delta > 0$), a hyperbola.

To eliminate the $xy$ cross term, we perform a rotation of axes. Let $P$ be the orthogonal matrix diagonalizing $Q$, so $P^T Q P = \Lambda = \text{diag}(\lambda_1, \lambda_2)$. Setting $\mathbf{x} = P\mathbf{x}'$ transforms the equation to

$$\mathbf{x}'^T \Lambda \mathbf{x}' + \mathbf{d}^T P \mathbf{x}' + F = 0$$

or equivalently

$$\lambda_1 x'^2 + \lambda_2 y'^2 + D' x' + E' y' + F = 0$$

where $(D', E')^T = P^T \mathbf{d}$. Completing the square in $x'$ and $y'$ reduces this to canonical form. For an ellipse with $\lambda_1, \lambda_2 > 0$, we obtain

$$\frac{(x' - h)^2}{a^2} + \frac{(y' - k)^2}{b^2} = 1$$

after appropriate translation and scaling. The semi-major axis $a$ and semi-minor axis $b$ are determined by the eigenvalues and the constant term, and the foci lie at $(\pm c, 0)$ in the rotated frame where $c = \sqrt{a^2 - b^2}$ for $a > b$.

Consider the specific example of the conic $5x^2 + 6xy + 5y^2 - 8 = 0$. We have $Q = \begin{pmatrix} 5 & 3 \\ 3 & 5 \end{pmatrix}$, which has eigenvalues $\lambda_1 = 8$ and $\lambda_2 = 2$ with corresponding orthonormal eigenvectors $\mathbf{v}_1 = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix}$ and $\mathbf{v}_2 = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ -1 \end{pmatrix}$. The rotation matrix is $P = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$, corresponding to a $45°$ rotation. In the rotated coordinates $(x', y')$, the equation becomes $8x'^2 + 2y'^2 = 8$, or $\frac{x'^2}{1} + \frac{y'^2}{4} = 1$, an ellipse with semi-axes $a = 2$ and $b = 1$ along the rotated axes.

Parametric representations provide explicit constructions of curves. A circle of radius $r$ centered at $(h, k)$ has parametric equations

$$x(t) = h + r\cos t, \quad y(t) = k + r\sin t, \quad t \in [0, 2\pi).$$

The ellipse $\frac{(x-h)^2}{a^2} + \frac{(y-k)^2}{b^2} = 1$ is parametrized by

$$x(t) = h + a\cos t, \quad y(t) = k + b\sin t.$$

The hyperbola $\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1$ admits the parametrization

$$x(t) = a\sec t, \quad y(t) = b\tan t, \quad t \in [0, 2\pi) \setminus \{\pi/2, 3\pi/2\}$$

for the right branch, or alternatively using hyperbolic functions

$$x(t) = a\cosh t, \quad y(t) = b\sinh t, \quad t \in \mathbb{R},$$

which covers the right branch as $t$ ranges over all reals and the left branch as $t$ ranges over negatives. The parabola $y = x^2$ has the natural parametrization $x(t) = t, y(t) = t^2$.

Parametric curves enable computation of tangent vectors, velocities, and arc lengths. The velocity vector at parameter value $t$ is $\mathbf{v}(t) = \frac{d\mathbf{r}}{dt} = \left(\frac{dx}{dt}, \frac{dy}{dt}\right)$, and the speed is $\|\mathbf{v}(t)\| = \sqrt{(dx/dt)^2 + (dy/dt)^2}$. The arc length from $t = a$ to $t = b$ is

$$L = \int_a^b \|\mathbf{v}(t)\| \, dt = \int_a^b \sqrt{\left(\frac{dx}{dt}\right)^2 + \left(\frac{dy}{dt}\right)^2} \, dt.$$

For the circle $x(t) = r\cos t, y(t) = r\sin t$, we have $\mathbf{v}(t) = (-r\sin t, r\cos t)$ and $\|\mathbf{v}(t)\| = r$, yielding $L = \int_0^{2\pi} r \, dt = 2\pi r$, confirming the familiar circumference formula.

Polar coordinates $(r, \theta)$ convert algebraic equations through the substitution $x = r\cos\theta, y = r\sin\theta$. The line $y = mx + b$ becomes $r\sin\theta = m r\cos\theta + b$, or $r = \frac{b}{\sin\theta - m\cos\theta}$. The circle $x^2 + y^2 = a^2$ simplifies to $r = a$. A circle passing through the origin with diameter along a ray at angle $\alpha$ has equation $r = 2a\cos(\theta - \alpha)$. The conic sections admit a unified polar representation with focus at the origin:

$$r = \frac{ed}{1 + e\cos\theta}$$

where $e$ is the eccentricity and $d$ is the semi-latus rectum. For $e < 1$, this is an ellipse; $e = 1$, a parabola; $e > 1$, a hyperbola. This form directly encodes the focus-directrix definition: a conic is the locus of points whose distance to a focus is $e$ times the distance to the corresponding directrix.

The area enclosed by a polar curve $r = f(\theta)$ from $\theta = \alpha$ to $\theta = \beta$ is computed by integration:

$$A = \frac{1}{2} \int_\alpha^\beta r^2 \, d\theta.$$

This formula follows from considering an infinitesimal sector of angle $d\theta$ as approximately triangular with area $\frac{1}{2} r^2 d\theta$. For the cardioid $r = a(1 + \cos\theta)$, the total enclosed area is

$$A = \frac{1}{2} \int_0^{2\pi} a^2(1 + \cos\theta)^2 \, d\theta = \frac{a^2}{2} \int_0^{2\pi} (1 + 2\cos\theta + \cos^2\theta) \, d\theta.$$

The integral of $\cos\theta$ over a full period vanishes, and using $\cos^2\theta = \frac{1 + \cos(2\theta)}{2}$, we compute

$$A = \frac{a^2}{2} \left[2\pi + 0 + \frac{1}{2}(2\pi)\right] = \frac{3\pi a^2}{2}.$$

Vector methods unify and generalize coordinate computations. A line in $\mathbb{R}^n$ through point $\mathbf{p}_0$ with direction $\mathbf{v}$ is parametrized as $\mathbf{r}(t) = \mathbf{p}_0 + t\mathbf{v}$. The distance from a point $\mathbf{q}$ to this line is computed by finding the projection of $\mathbf{q} - \mathbf{p}_0$ onto the direction perpendicular to $\mathbf{v}$. The projection of $\mathbf{w} = \mathbf{q} - \mathbf{p}_0$ onto $\mathbf{v}$ is

$$\text{proj}_{\mathbf{v}} \mathbf{w} = \frac{\mathbf{w} \cdot \mathbf{v}}{\mathbf{v} \cdot \mathbf{v}} \mathbf{v},$$

and the perpendicular component is $\mathbf{w}_\perp = \mathbf{w} - \text{proj}_{\mathbf{v}} \mathbf{w}$. The distance is $d = \|\mathbf{w}_\perp\|$. Using the identity $\|\mathbf{w}\|^2 = \|\text{proj}_{\mathbf{v}} \mathbf{w}\|^2 + \|\mathbf{w}_\perp\|^2$, we derive

$$d = \sqrt{\|\mathbf{w}\|^2 - \frac{(\mathbf{w} \cdot \mathbf{v})^2}{\|\mathbf{v}\|^2}}.$$

In $\mathbb{R}^3$, the cross product provides an alternative: $d = \frac{\|\mathbf{w} \times \mathbf{v}\|}{\|\mathbf{v}\|}$, since $\|\mathbf{w} \times \mathbf{v}\| = \|\mathbf{w}\| \|\mathbf{v}\| \sin\theta$ where $\theta$ is the angle between $\mathbf{w}$ and $\mathbf{v}$, and $\|\mathbf{w}\| \sin\theta$ is precisely the perpendicular distance.

A plane in $\mathbb{R}^3$ is determined by a point $\mathbf{p}_0$ and a normal vector $\mathbf{n}$. Any point $\mathbf{p}$ on the plane satisfies $(\mathbf{p} - \mathbf{p}_0) \cdot \mathbf{n} = 0$, yielding the implicit equation $\mathbf{n} \cdot \mathbf{p} = \mathbf{n} \cdot \mathbf{p}_0$. Writing $\mathbf{n} = (a, b, c)$ and $\mathbf{p} = (x, y, z)$, this becomes $ax + by + cz = d$ where $d = \mathbf{n} \cdot \mathbf{p}_0$. Alternatively, a plane is parametrized by two direction vectors $\mathbf{u}, \mathbf{v}$ spanning the plane: $\mathbf{r}(s, t) = \mathbf{p}_0 + s\mathbf{u} + t\mathbf{v}$. The normal vector is $\mathbf{n} = \mathbf{u} \times \mathbf{v}$.

The intersection of two planes is a line (when the planes are not parallel or coincident). Given planes $\mathbf{n}_1 \cdot \mathbf{p} = d_1$ and $\mathbf{n}_2 \cdot \mathbf{p} = d_2$, the direction vector of the intersection line is $\mathbf{v} = \mathbf{n}_1 \times \mathbf{n}_2$ (perpendicular to both normals). To find a point on the line, we solve the system of two equations in three unknowns by setting one coordinate (say $z = 0$ if possible) and solving for $x, y$ in the reduced system. This yields a point $\mathbf{p}_0$, and the line is $\mathbf{r}(t) = \mathbf{p}_0 + t\mathbf{v}$.

Duality in the projective plane enriches the theory. The real projective plane $\mathbb{RP}^2$ consists of equivalence classes of nonzero triples $(x, y, z) \sim (\lambda x, \lambda y, \lambda z)$ for $\lambda \neq 0$, denoted $[x:y:z]$ in homogeneous coordinates. A line in $\mathbb{RP}^2$ is determined by an equation $ax + by + cz = 0$ with $(a, b, c) \neq (0, 0, 0)$, also viewed as a point $[a:b:c]$ in the dual projective plane. Incidence is symmetric: point $[x_0:y_0:z_0]$ lies on line $[a:b:c]$ if and only if $ax_0 + by_0 + cz_0 = 0$, the same condition as line $[x_0:y_0:z_0]$ passing through point $[a:b:c]$ in the dual picture.

A conic in $\mathbb{RP}^2$ is given by a quadratic form $\mathbf{x}^T C \mathbf{x} = 0$ where $C$ is a symmetric $3 \times 3$ matrix and $\mathbf{x} = [x:y:z]^T$. The polar line of a point $\mathbf{p}$ with respect to conic $C$ is $\mathbf{\ell} = C\mathbf{p}$, meaning that point $\mathbf{q}$ lies on the polar if and only if $\mathbf{q}^T (C\mathbf{p}) = 0$, or equivalently $\mathbf{q}^T C \mathbf{p} = 0$. By symmetry of $C$, this is $\mathbf{p}^T C \mathbf{q} = 0$, showing that $\mathbf{p}$ lies on the polar of $\mathbf{q}$ if and only if $\mathbf{q}$ lies on the polar of $\mathbf{p}$. When $\mathbf{p}$ lies on the conic ($\mathbf{p}^T C \mathbf{p} = 0$), the polar is the tangent line at $\mathbf{p}$.

Pascal's theorem states that if six points lie on a conic, then the three intersection points of opposite sides of the hexagon formed by these points are collinear. In coordinates, let the six points be $\mathbf{p}_1, \ldots, \mathbf{p}_6$ on conic $C$. Define lines $\mathbf{\ell}_{12} = \mathbf{p}_1 \times \mathbf{p}_2$ (using cross product to construct the line through two points in homogeneous coordinates), and similarly for $\mathbf{\ell}_{23}, \mathbf{\ell}_{34}, \mathbf{\ell}_{45}, \mathbf{\ell}_{56}, \mathbf{\ell}_{61}$. Then opposite sides $\mathbf{\ell}_{12}, \mathbf{\ell}_{45}$ intersect at a point, as do $\mathbf{\ell}_{23}, \mathbf{\ell}_{56}$ and $\mathbf{\ell}_{34}, \mathbf{\ell}_{61}$, and these three intersection points lie on a common line called the Pascal line. The dual statement is Brianchon's theorem: if six lines are tangent to a conic, then the three lines joining opposite vertices of the hexagon formed by these tangents are concurrent.

## 3. High-Performance Optimization & Failure Modes

Computational implementations of analytic geometry demand careful attention to numerical stability, algorithmic complexity, and degenerate cases. Floating-point arithmetic introduces rounding errors that can corrupt geometric predicates—tests for collinearity, concyclicity, or orientation—leading to inconsistent topological determinations. Robust geometric computation employs exact arithmetic (through rational number representations or symbolic algebra systems), adaptive precision methods that escalate to higher precision only when needed, or carefully designed predicates using orientation tests and determinants.

The orientation test for three points $\mathbf{p}_1, \mathbf{p}_2, \mathbf{p}_3$ in the plane determines whether they form a left turn, right turn, or are collinear. This reduces to computing the sign of the determinant

$$\text{orient}(\mathbf{p}_1, \mathbf{p}_2, \mathbf{p}_3) = \det\begin{pmatrix} x_1 & y_1 & 1 \\ x_2 & y_2 & 1 \\ x_3 & y_3 & 1 \end{pmatrix} = (x_2 - x_1)(y_3 - y_1) - (x_3 - x_1)(y_2 - y_1).$$

Positive determinant indicates counterclockwise orientation, negative clockwise, and zero collinearity. Naive floating-point evaluation can yield incorrect zero tests when the true value is small but nonzero, destroying the correctness of algorithms like convex hull construction or Delaunay triangulation. Shewchuk's adaptive precision predicates compute the determinant using floating-point arithmetic with error bounds, escalating to exact arithmetic only when the error bounds overlap zero.

Line-line intersection in two dimensions solves the system

$$\begin{cases} a_1 x + b_1 y + c_1 = 0 \\ a_2 x + b_2 y + c_2 = 0 \end{cases}$$

using Cramer's rule. The solution is

$$x = \frac{b_1 c_2 - b_2 c_1}{a_1 b_2 - a_2 b_1}, \quad y = \frac{a_2 c_1 - a_1 c_2}{a_1 b_2 - a_2 b_1},$$

provided the denominator $\Delta = a_1 b_2 - a_2 b_1 \neq 0$. When $\Delta = 0$, the lines are parallel (no intersection if $b_1 c_2 - b_2 c_1 \neq 0$) or coincident (infinitely many intersections if both numerators vanish). Robust implementation must handle these degenerate cases explicitly and avoid division by near-zero denominators, which amplify rounding errors catastrophically.

Parametric curve tracing for plotting or collision detection requires adaptive step sizing to balance resolution and efficiency. Uniform parameter sampling $t_i = t_0 + i\Delta t$ produces oversampling in low-curvature regions and undersampling in high-curvature regions. Adaptive methods monitor the curvature $\kappa(t)$ or the angular deviation between successive tangent vectors, refining the step size when curvature exceeds a threshold. For a parametric curve $\mathbf{r}(t) = (x(t), y(t))$, the curvature is

$$\kappa(t) = \frac{|x'(t)y''(t) - y'(t)x''(t)|}{(x'(t)^2 + y'(t)^2)^{3/2}}.$$

High curvature indicates tight bending requiring finer sampling. Subdivision methods recursively split a curve segment until a flatness criterion (maximum deviation from the chord connecting endpoints) is satisfied, yielding an adaptive polyline approximation.

Conic section fitting from data points arises in computer vision, orbit determination, and measurement noise filtering. Given $n$ points $(\mathbf{p}_i = (x_i, y_i))$, we seek coefficients $(A, B, C, D, E, F)$ minimizing the sum of squared algebraic distances

$$\sum_{i=1}^n (Ax_i^2 + Bx_i y_i + Cy_i^2 + Dx_i + Ey_i + F)^2$$

subject to a normalization constraint (e.g., $A^2 + B^2 + C^2 + D^2 + E^2 = 1$) to avoid the trivial zero solution. Formulating this as a least-squares problem $\min \|\mathbf{M}\mathbf{c}\|^2$ where $\mathbf{M}$ is the $n \times 6$ design matrix with rows $(x_i^2, x_i y_i, y_i^2, x_i, y_i, 1)$ and $\mathbf{c} = (A, B, C, D, E, F)^T$, the solution is the eigenvector corresponding to the smallest eigenvalue of $\mathbf{M}^T\mathbf{M}$. Alternatively, imposing the constraint $4AC - B^2 = 1$ enforces an ellipse and yields a generalized eigenvalue problem. Geometric distance minimization (perpendicular distance from points to the conic) requires nonlinear optimization via Levenberg-Marquardt or Gauss-Newton methods, using the algebraic fit as an initial guess.

Distance computations between geometric objects underpin collision detection, proximity queries, and computational geometry algorithms. The distance between a point $\mathbf{p}$ and a line segment from $\mathbf{a}$ to $\mathbf{b}$ requires projecting $\mathbf{p}$ onto the infinite line and clamping to the segment endpoints. The projection parameter is

$$t = \frac{(\mathbf{p} - \mathbf{a}) \cdot (\mathbf{b} - \mathbf{a})}{\|\mathbf{b} - \mathbf{a}\|^2},$$

and the closest point on the segment is

$$\mathbf{q} = \begin{cases} \mathbf{a} & \text{if } t \le 0 \\ \mathbf{a} + t(\mathbf{b} - \mathbf{a}) & \text{if } 0 < t < 1 \\ \mathbf{b} & \text{if } t \ge 1 \end{cases}.$$

The distance is $\|\mathbf{p} - \mathbf{q}\|$. Segment-segment distance in $\mathbb{R}^3$ is more involved: if the segments are skew (non-coplanar), the distance is realized between two unique points, found by solving a $2 \times 2$ linear system derived from minimizing $\|\mathbf{r}_1(s) - \mathbf{r}_2(t)\|^2$. Degenerate cases (parallel or intersecting segments) require separate handling.

Polar coordinate singularities arise at the origin where $r = 0$ and $\theta$ is undefined. Curves passing through the origin, such as the cardioid $r = a(1 + \cos\theta)$ at $\theta = \pi$, exhibit infinite curvature there. Numerical integration or differentiation in polar coordinates must handle the Jacobian factor: area integrals include the $r$ factor ($dA = r \, dr \, d\theta$), and the arc length differential is $ds = \sqrt{r^2 + (dr/d\theta)^2} \, d\theta$, which vanishes at the origin unless approached carefully via limits.

Coordinate system optimization involves choosing representations that exploit problem symmetry. Rotational symmetry suggests polar coordinates; translation symmetry suggests affine coordinates with origin at a natural center. For orbits and central force problems, polar coordinates with origin at the focus yield differential equations separable in $r$ and $\theta$. For linear transformations and matrix operations, Cartesian coordinates align with standard linear algebra machinery. Projective coordinates eliminate special cases for parallel lines (they intersect at infinity) and simplify duality, at the cost of an extra dimension and equivalence classes.

High-dimensional analytic geometry encounters the curse of dimensionality: Euclidean balls contain exponentially (in dimension) more volume near their surfaces, nearest neighbor search scales poorly, and intuition from low dimensions misleads. The volume of the unit $n$-ball is $V_n = \frac{\pi^{n/2}}{\Gamma(n/2 + 1)}$, which grows initially with $n$ but eventually decreases, becoming negligible for large $n$ despite the "sphere" having unit radius. Distance concentration occurs: all pairs of random points in high dimensions have nearly equal distances, degrading the discriminative power of distance-based algorithms. Dimensionality reduction via principal component analysis (PCA) or random projections (Johnson-Lindenstrauss lemma) mitigates these issues by embedding high-dimensional data into lower-dimensional spaces approximately preserving distances.

Matrix condition numbers affect the stability of coordinate transformations. A rotation matrix has condition number 1 (perfectly stable), but ill-conditioned change-of-basis matrices amplify rounding errors. When diagonalizing a matrix for conic classification, nearly equal eigenvalues (indicating nearly circular ellipses) yield eigenvectors sensitive to perturbations, making the rotation angle unstable. Singular value decomposition (SVD) provides more robust eigenvalue computation than naive characteristic polynomial methods, and incremental updates of decompositions (e.g., for tracking objects in video) avoid repeated full recomputation.

Failure modes in algorithmic geometry include topological inconsistencies (triangulations with overlapping faces due to rounding), missed edge cases (collinear or cocircular degeneracies), and infinite loops in iterative refinement (when convergence criteria are too strict relative to floating-point precision). Defensive programming employs epsilon-tolerance comparisons ($|x| < \epsilon$ rather than $x = 0$), explicit handling of all degenerate configurations, and assertions verifying geometric invariants (e.g., convex hull vertices maintain counterclockwise order). Symbolic perturbation schemes (simulation of simplicity) conceptually perturb inputs infinitesimally to eliminate degeneracies without actually modifying data, by defining tie-breaking rules based on input order or lexicographic coordinates.

The interplay of analytic methods with synthetic geometry emerges in optimization: a synthetic theorem suggesting equality or orthogonality becomes a constraint or objective function, solved via Lagrange multipliers or gradient descent. Fermat's principle (light travels the path of least time) translates to minimizing a functional subject to boundary conditions, yielding the eikonal equation via calculus of variations. The Euler-Lagrange equations, derived analytically, encode the synthetic condition that a curve is a geodesic (locally shortest path). This synthesis of analytic technique with geometric intuition pervades modern mathematical physics, optimization theory, and computational geometry, exemplifying the power of coordinate methods to unify, generalize, and compute.
