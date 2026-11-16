# Operational Verification Labs: Geometry

## Objective & Mathematical Computing Setup

This lab guide treats geometry as a computational discipline: every theorem is a proposition to be verified by symbolic execution or formal proof, and every geometric object is a data structure to be queried and stress-tested. The target here is not rote application of formulas but rather the construction of a verification pipeline in which classical results, from Euclid's parallel postulate consequences through projective duality and differential curvature, are held accountable to machine-checkable evidence.

The practitioner will work across two complementary environments. The first is Python with SymPy and NumPy, which provides a symbolic computer algebra system (CAS) capable of exact rational and algebraic arithmetic, polynomial ideal computation, and parametric differentiation. The second is SageMath, which wraps a broad ecosystem including Singular for Gröbner bases, Maxima for symbolic integration, and native geometric constructions over exact fields. For formal proof verification, the exercises include Lean 4 proof sketches that illustrate how classical Euclidean propositions are stated as types and discharged by tactic proof.

Before proceeding to the exercises, establish the environment and confirm all dependencies are present and version-consistent.

```
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "from sympy.geometry import *; print('sympy.geometry OK')"
sage --version
```

The expected output confirms SymPy 1.12 or later, NumPy 1.26 or later, and SageMath 10.x. If SageMath is unavailable, every SageMath block in this guide has a pure SymPy alternative provided inline. Install the Python stack via:

```
pip install sympy==1.12 numpy==1.26.4 scipy==1.13.0
```

The mathematical objects at the center of this guide are drawn from three layers of classical and modern geometry: Euclidean geometry (distances, angles, triangle centers, circle theorems), projective and affine geometry (cross-ratio, collinearity, Desargues's theorem), and differential geometry (curvature of parametric curves and surfaces, geodesics on the sphere). Each layer is treated not as an isolated domain but as a stratum in a coherent hierarchy, where Euclidean results appear as special cases of projective ones under a choice of absolute conic, and differential geometry generalizes Euclidean measurement to curved manifolds.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Euclid's Theorems via SymPy Geometry

The first battery of verifications targets fundamental Euclidean propositions: the Pythagorean theorem in its algebraic and geometric forms, the angle bisector theorem, and the nine-point circle. Rather than simply computing a numerical example, the approach here is to work with parametric coordinates so that the verification holds universally over the symbolic parameter space.

The Pythagorean theorem states that in a right triangle with legs $a$, $b$ and hypotenuse $c$, the relation $a^2 + b^2 = c^2$ holds. We will verify this by constructing a right triangle at an arbitrary point, computing all three side lengths symbolically, and confirming the algebraic identity.

```python
from sympy import symbols, sqrt, simplify, expand, Rational
from sympy.geometry import Point, Triangle, Circle, Segment

# Parametric right triangle: right angle at O, legs along axes
a, b = symbols('a b', positive=True)

O = Point(0, 0)
A = Point(a, 0)
B = Point(0, b)

t = Triangle(O, A, B)

leg_OA = Segment(O, A).length          # a
leg_OB = Segment(O, B).length          # b
hyp_AB = Segment(A, B).length          # sqrt(a^2 + b^2)

pythagorean_lhs = expand(leg_OA**2 + leg_OB**2)
pythagorean_rhs = expand(hyp_AB**2)

residual = simplify(pythagorean_lhs - pythagorean_rhs)
print(f"Legs: OA={leg_OA}, OB={leg_OB}")
print(f"Hypotenuse: AB={hyp_AB}")
print(f"a^2 + b^2 - c^2 = {residual}")   # Must print 0
assert residual == 0, "Pythagorean theorem violated"
print("Pythagorean theorem: VERIFIED")
```

The symbolic residual evaluates to exactly zero, which constitutes a universal algebraic proof over the parameter space $\{(a, b) \mid a, b > 0\}$. This is strictly stronger than a numerical spot-check.

### 1.2 Nine-Point Circle

The nine-point circle theorem asserts that for any triangle $ABC$, the following nine points are concyclic: the three midpoints of the sides, the three feet of the altitudes, and the three midpoints of the segments from each vertex to the orthocenter. The radius of the nine-point circle is exactly half the circumradius, and the nine-point center $N_9$ lies at the midpoint of the segment from the orthocenter $H$ to the circumcenter $O$.

We verify the concyclicity condition and the radius relation symbolically.

```python
from sympy import symbols, sqrt, simplify, Rational
from sympy.geometry import Point, Triangle, Circle, Segment, Line

# General triangle with symbolic coordinates (non-degenerate)
x1, y1, x2, y2 = symbols('x1 y1 x2 y2', real=True)

A = Point(0, 0)
B = Point(4, 0)
C = Point(x1, y1)   # Parametric apex

tri = Triangle(A, B, C)

# Midpoints of sides
M_AB = Segment(A, B).midpoint
M_BC = Segment(B, C).midpoint
M_CA = Segment(C, A).midpoint

# Circumcircle and circumradius
circumcircle = tri.circumcircle
R = circumcircle.radius

# Orthocenter
H = tri.orthocenter

# Nine-point center = midpoint of circumcenter and orthocenter
O_circ = circumcircle.center
N9 = Segment(O_circ, H).midpoint

# Nine-point circle passes through midpoints; its radius should be R/2
nine_pt_circle = Circle(M_AB, M_BC, M_CA)
r9 = nine_pt_circle.radius
r9_simplified = simplify(r9)
R_simplified = simplify(R)

ratio = simplify(r9_simplified / R_simplified)
print(f"Nine-point circle radius / Circumradius = {ratio}")
assert simplify(ratio - Rational(1, 2)) == 0, "Nine-point radius relation failed"

# Verify N9 equals the nine-point circle center
nine_pt_center = nine_pt_circle.center
center_diff_x = simplify(nine_pt_center.x - N9.x)
center_diff_y = simplify(nine_pt_center.y - N9.y)
print(f"Center discrepancy x: {center_diff_x}, y: {center_diff_y}")
assert center_diff_x == 0 and center_diff_y == 0, "Nine-point center mismatch"
print("Nine-point circle theorem: VERIFIED")
```

For the symbolic computation to terminate in finite time, SymPy operates on the triangle $(0,0), (4,0), (x_1, y_1)$ with one free apex. The ratio simplification confirms $r_9 = R/2$ exactly, and the center coincidence is confirmed by reducing both coordinate differences to zero.

### 1.3 Ceva's Theorem

Ceva's theorem provides the necessary and sufficient condition for three cevians of a triangle to be concurrent. Given triangle $ABC$ with points $D$ on $BC$, $E$ on $CA$, $F$ on $AB$, the cevians $AD$, $BE$, $CF$ are concurrent if and only if:

$$\frac{BD}{DC} \cdot \frac{CE}{EA} \cdot \frac{AF}{FB} = 1$$

The computational verification strategy is to parameterize $D$, $E$, $F$ by their ratio parameters $\lambda, \mu, \nu$ on the respective sides, compute the intersection of two cevians to obtain a candidate concurrence point $P$, verify that the third cevian also passes through $P$, and then confirm the product of ratios is unity.

```python
from sympy import symbols, simplify, solve, Rational
from sympy.geometry import Point, Triangle, Line, Segment

# Concrete triangle for Ceva verification
A = Point(0, 0)
B = Point(6, 0)
C = Point(2, 5)

# Parameters: D divides BC in ratio lam:(1-lam), etc.
lam, mu, nu = symbols('lambda mu nu', positive=True)

# Points on sides parameterized by convex combination
D = Point(B.x + lam*(C.x - B.x), B.y + lam*(C.y - B.y))  # D on BC
E = Point(C.x + mu*(A.x - C.x),  C.y + mu*(A.y - C.y))   # E on CA
F = Point(A.x + nu*(B.x - A.x),  A.y + nu*(B.y - A.y))   # F on AB

# Cevian lines
cevian_AD = Line(A, D)
cevian_BE = Line(B, E)
cevian_CF = Line(C, F)

# Concurrence condition: intersection of AD and BE
P = cevian_AD.intersection(cevian_BE)[0]

# Check P lies on CF
cf_contains_P = cevian_CF.contains(P)

# If concurrent, derive lam,mu,nu relation and verify Ceva product
# Use specific concurrent cevians: medians (lam=mu=nu=1/2)
lam_v, mu_v, nu_v = Rational(1,2), Rational(1,2), Rational(1,2)

D_m = Point(B.x + lam_v*(C.x - B.x), B.y + lam_v*(C.y - B.y))
E_m = Point(C.x + mu_v*(A.x - C.x),  C.y + mu_v*(A.y - C.y))
F_m = Point(A.x + nu_v*(B.x - A.x),  A.y + nu_v*(B.y - A.y))

# Signed ratios BD/DC, CE/EA, AF/FB for medians (all = 1)
BD = Segment(B, D_m).length
DC = Segment(D_m, C).length
CE = Segment(C, E_m).length
EA = Segment(E_m, A).length
AF = Segment(A, F_m).length
FB = Segment(F_m, B).length

ceva_product = simplify((BD/DC) * (CE/EA) * (AF/FB))
print(f"Ceva product (medians): {ceva_product}")
assert ceva_product == 1, "Ceva product not unity for medians"

# Verify all three medians are concurrent at centroid
L_AD = Line(A, D_m)
L_BE = Line(B, E_m)
L_CF = Line(C, F_m)
centroid_AB = L_AD.intersection(L_BE)[0]
print(f"Centroid from AD∩BE: {centroid_AB}")
print(f"CF contains centroid: {L_CF.contains(centroid_AB)}")
assert L_CF.contains(centroid_AB), "Medians not concurrent"
print("Ceva's theorem (medians): VERIFIED")
```

### 1.4 Cross-Ratio Invariance Under Projective Transformation

Projective geometry is organized around invariants: properties of configurations that survive arbitrary projective transformations. The cross-ratio is the fundamental projective invariant of four collinear points. For four distinct collinear points $A, B, C, D$ with coordinate values $a, b, c, d$ on a projective line, the cross-ratio is:

$$[A, B; C, D] = \frac{(C - A)(D - B)}{(D - A)(C - B)}$$

A projective transformation of the line has the form $x \mapsto (px + q)/(rx + s)$ with $ps - qr \neq 0$. The defining property is that the cross-ratio is preserved under such maps. We verify this symbolically for a general Möbius transformation.

```python
from sympy import symbols, simplify, Function, factor

# Four collinear points as symbols
a, b, c, d = symbols('a b c d', real=True)

def cross_ratio(A, B, C, D):
    return ((C - A)*(D - B)) / ((D - A)*(C - B))

CR_original = cross_ratio(a, b, c, d)

# General projective (Möbius) transformation
p, q, r, s = symbols('p q r s', real=True, nonzero=True)

def mobius(x):
    return (p*x + q) / (r*x + s)

a2 = mobius(a)
b2 = mobius(b)
c2 = mobius(c)
d2 = mobius(d)

CR_transformed = cross_ratio(a2, b2, c2, d2)
CR_transformed_simplified = simplify(CR_transformed)

invariance_residual = simplify(CR_transformed_simplified - CR_original)
print(f"Cross-ratio invariance residual: {invariance_residual}")
assert invariance_residual == 0, "Cross-ratio not invariant under Möbius transformation"
print("Cross-ratio projective invariance: VERIFIED")
```

The residual simplifies to zero regardless of the values of $p, q, r, s$ (subject to $ps - qr \neq 0$, which SymPy honors through the `nonzero=True` assumption on each variable and the structure of cancellation).

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Degenerate Triangle: Collinear Points and Area Collapse

Geometric algorithms frequently encounter degenerate configurations in which the defining objects collapse to lower-dimensional subsets. A triangle becomes degenerate when its three vertices are collinear, causing its area to vanish and its circumcircle to degenerate to a line (or a circle of infinite radius). Verifying that a computational system correctly detects and handles these boundary cases is as important as verifying theorems in the generic position.

The signed area of triangle $ABC$ with vertices $(x_A, y_A)$, $(x_B, y_B)$, $(x_C, y_C)$ is:

$$\text{Area} = \frac{1}{2} \det \begin{pmatrix} x_B - x_A & x_C - x_A \\ y_B - y_A & y_C - y_A \end{pmatrix}$$

When this determinant vanishes, the vertices are collinear and SymPy's `Triangle` constructor raises an exception. The practitioner must guard against this by testing collinearity before construction.

```python
from sympy import symbols, Rational, simplify, Matrix
from sympy.geometry import Point, Triangle, Line, Segment
import sympy

# Stress test 1: Exactly degenerate (collinear) triangle
A_deg = Point(0, 0)
B_deg = Point(3, 0)
C_deg = Point(6, 0)   # On the same line y=0

# Collinearity test via signed area determinant
def signed_area_2x(A, B, C):
    M = Matrix([
        [B.x - A.x, C.x - A.x],
        [B.y - A.y, C.y - A.y]
    ])
    return M.det()

area_degenerate = signed_area_2x(A_deg, B_deg, C_deg)
print(f"Signed 2*Area (collinear): {area_degenerate}")
assert area_degenerate == 0, "Expected degenerate area"

# Confirm SymPy raises GeometryError for degenerate Triangle
try:
    bad_tri = Triangle(A_deg, B_deg, C_deg)
    print("ERROR: SymPy accepted a degenerate triangle without error")
except sympy.geometry.exceptions.GeometryError as e:
    print(f"SymPy correctly raises GeometryError: {e}")

# Stress test 2: Nearly degenerate – epsilon perturbation
eps = symbols('epsilon', positive=True)
C_near = Point(6, eps)
area_near = signed_area_2x(A_deg, B_deg, C_near)
print(f"Signed 2*Area (epsilon perturbation): {area_near}")
# As eps -> 0, area -> 0
from sympy import limit
area_limit = limit(area_near, eps, 0)
print(f"Limit of area as eps->0: {area_limit}")
assert area_limit == 0, "Area limit at degeneracy should be 0"
print("Degenerate triangle boundary: VERIFIED")
```

### 2.2 Circle–Circle Intersection: Tangency and Non-Intersection Singularities

Circle intersection exhibits three qualitative regimes depending on the distance $d$ between centers and the radii $r_1, r_2$: two intersection points when $|r_1 - r_2| < d < r_1 + r_2$, tangency (one point) when $d = r_1 + r_2$ (external) or $d = |r_1 - r_2|$ (internal), and no real intersection when $d > r_1 + r_2$ or $d < |r_1 - r_2|$. Automated detection of these cases is a prerequisite for any robust geometric solver.

```python
from sympy import sqrt, Rational, symbols, simplify
from sympy.geometry import Point, Circle

def circle_intersection_analysis(c1, r1_val, c2, r2_val):
    circ1 = Circle(c1, r1_val)
    circ2 = Circle(c2, r2_val)
    d = c1.distance(c2)
    intersections = circ1.intersection(circ2)
    
    r1s, r2s = Rational(r1_val), Rational(r2_val)
    d_simplified = simplify(d)
    
    print(f"  d = {d_simplified}, r1+r2 = {r1s+r2s}, |r1-r2| = {abs(r1s-r2s)}")
    print(f"  Intersection points: {intersections}")
    return intersections

print("Case 1: Two intersection points (generic)")
circle_intersection_analysis(Point(0,0), 5, Point(6,0), 5)

print("\nCase 2: External tangency (d = r1 + r2 = 10)")
circle_intersection_analysis(Point(0,0), 5, Point(10,0), 5)

print("\nCase 3: Internal tangency (d = |r1 - r2| = 2)")
circle_intersection_analysis(Point(0,0), 5, Point(2,0), 3)

print("\nCase 4: No intersection (d > r1 + r2)")
circle_intersection_analysis(Point(0,0), 3, Point(10,0), 3)

print("\nCase 5: One circle inside the other (d < |r1 - r2|)")
circle_intersection_analysis(Point(0,0), 5, Point(1,0), 1)
```

The expected outputs for cases 2 and 3 (tangency) are single-element intersection lists containing one `Point`. Cases 4 and 5 return empty lists in SymPy's exact arithmetic, cleanly distinguishing them from the two-point case. This exact behavior is what makes SymPy preferable to floating-point geometry libraries for boundary verification, where numerical error could misclassify a tangency as a two-point intersection or a non-intersection as a tangency.

### 2.3 Curvature Singularities on Parametric Curves

For a smooth parametric curve $\gamma(t) = (x(t), y(t))$, the signed curvature is:

$$\kappa(t) = \frac{x'(t) y''(t) - y'(t) x''(t)}{\left( x'(t)^2 + y'(t)^2 \right)^{3/2}}$$

Curvature singularities (points where the formula is undefined or the curvature diverges) occur at inflection points where the numerator vanishes, and at cusps where both $x'(t) = 0$ and $y'(t) = 0$ simultaneously, making the denominator vanish. These are qualitatively different singularities requiring distinct diagnostic treatment.

We test the curvature formula on the semicubical parabola $\gamma(t) = (t^2, t^3)$, which has a cusp at $t = 0$.

```python
from sympy import symbols, diff, sqrt, simplify, limit, oo, Rational, factor

t = symbols('t', real=True)

# Semicubical parabola: cusp at t=0
x = t**2
y = t**3

dx  = diff(x, t)
dy  = diff(y, t)
ddx = diff(x, t, 2)
ddy = diff(y, t, 2)

numerator   = dx*ddy - dy*ddx
denominator = (dx**2 + dy**2)**Rational(3, 2)

kappa = numerator / denominator
kappa_simplified = simplify(kappa)
print(f"Curvature κ(t) = {kappa_simplified}")

# At t=0: denominator = 0, cusp singularity
# Examine curvature behavior near t=0
kappa_limit_right = limit(kappa_simplified, t, 0, '+')
kappa_limit_left  = limit(kappa_simplified, t, 0, '-')
print(f"lim_{{t→0+}} κ(t) = {kappa_limit_right}")
print(f"lim_{{t→0-}} κ(t) = {kappa_limit_left}")

# Circle (x=cos t, y=sin t): constant curvature = 1/r with r=1
from sympy import cos, sin
x_circ = cos(t)
y_circ = sin(t)

dx_c  = diff(x_circ, t)
dy_c  = diff(y_circ, t)
ddx_c = diff(x_circ, t, 2)
ddy_c = diff(y_circ, t, 2)

kappa_circle = simplify(
    (dx_c*ddy_c - dy_c*ddx_c) / (dx_c**2 + dy_c**2)**Rational(3,2)
)
print(f"\nCurvature of unit circle: κ = {kappa_circle}")
assert kappa_circle == -1 or kappa_circle == 1 or simplify(abs(kappa_circle) - 1) == 0
print("Circle constant curvature κ=1: VERIFIED")

# Inflection point: cubic y = x^3, parametrized as (t, t^3)
x_cub = t
y_cub = t**3
dx_cu  = diff(x_cub, t)
dy_cu  = diff(y_cub, t)
ddx_cu = diff(x_cub, t, 2)
ddy_cu = diff(y_cub, t, 2)

kappa_cubic = simplify(
    (dx_cu*ddy_cu - dy_cu*ddx_cu) / (dx_cu**2 + dy_cu**2)**Rational(3,2)
)
print(f"\nCurvature of y=x³: κ(t) = {kappa_cubic}")
kappa_cubic_at_0 = kappa_cubic.subs(t, 0)
print(f"κ(0) = {kappa_cubic_at_0}  ← inflection point, curvature = 0")
assert kappa_cubic_at_0 == 0, "Inflection curvature should be 0"
print("Inflection point curvature = 0: VERIFIED")
```

The semicubical parabola's curvature diverges to $+\infty$ from both sides of $t = 0$, confirming the cusp. The unit circle returns $\kappa = -1$ (the sign depending on orientation convention), and the inflection point of $y = x^3$ gives $\kappa(0) = 0$, all consistent with classical differential geometry.

### 2.4 Geodesic Curvature and Gaussian Curvature on the Sphere

The two-sphere $S^2$ of radius $R$ provides the canonical surface for curvature stress-testing because all relevant quantities are known exactly. The Gaussian curvature is $K = 1/R^2$ everywhere, the geodesics are great circles, and the Gauss–Bonnet theorem asserts:

$$\iint_{S^2} K \, dA = 4\pi \chi(S^2) = 4\pi \cdot 2 = 8\pi$$

We verify the Gaussian curvature of the unit sphere from the first and second fundamental forms.

```python
from sympy import symbols, sin, cos, diff, sqrt, Matrix, simplify, pi, integrate, Rational

u, v = symbols('u v', real=True)

R_sphere = 1  # Unit sphere

# Parametrization of S^2: x=sin(u)cos(v), y=sin(u)sin(v), z=cos(u)
# u in (0,pi), v in (0,2pi)
X = Matrix([sin(u)*cos(v), sin(u)*sin(v), cos(u)])

# First fundamental form coefficients
X_u = diff(X, u)
X_v = diff(X, v)

E = simplify(X_u.dot(X_u))
F = simplify(X_u.dot(X_v))
G = simplify(X_v.dot(X_v))

print(f"E = {E}")
print(f"F = {F}")
print(f"G = {G}")

# Normal vector (not necessarily unit)
N_unnorm = X_u.cross(X_v)
N_norm_sq = simplify(N_unnorm.dot(N_unnorm))
N_unit = simplify(N_unnorm / sqrt(N_norm_sq))

# Second fundamental form coefficients
X_uu = diff(X_u, u)
X_uv = diff(X_u, v)
X_vv = diff(X_v, v)

e_coeff = simplify(N_unit.dot(X_uu))
f_coeff = simplify(N_unit.dot(X_uv))
g_coeff = simplify(N_unit.dot(X_vv))

print(f"\ne = {e_coeff}")
print(f"f = {f_coeff}")
print(f"g = {g_coeff}")

# Gaussian curvature K = (eg - f^2) / (EG - F^2)
K_num = simplify(e_coeff*g_coeff - f_coeff**2)
K_den = simplify(E*G - F**2)
K = simplify(K_num / K_den)
print(f"\nGaussian curvature K = {K}")
assert simplify(K - 1) == 0, f"Expected K=1 for unit sphere, got {K}"
print("Gaussian curvature of S^2 = 1: VERIFIED")

# Gauss-Bonnet: integrate K * sqrt(EG-F^2) over S^2
# dA = sqrt(EG-F^2) du dv = sin(u) du dv
integrand = simplify(K * sqrt(K_den))
gauss_bonnet = integrate(
    integrate(integrand, (v, 0, 2*pi)),
    (u, 0, pi)
)
print(f"\nGauss-Bonnet integral = {gauss_bonnet}")
assert simplify(gauss_bonnet - 4*pi) == 0, f"Expected 4π, got {gauss_bonnet}"
print("Gauss-Bonnet theorem on S^2: VERIFIED (∫∫K dA = 4π)")
```

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Gröbner Basis Algorithm for Geometric Theorem Proving

The Wu–Ritt characteristic set method and the Buchberger algorithm for Gröbner bases provide the algebraic backbone of automated geometric theorem proving. The fundamental idea is to translate a geometric configuration into a system of polynomial equations (hypotheses), translate the conclusion into a polynomial equation or inequality, and then reduce the conclusion polynomial modulo the Gröbner basis of the hypothesis ideal. If the reduction yields zero, the conclusion is an algebraic consequence of the hypotheses.

We demonstrate this methodology on the classical theorem that the diagonals of a parallelogram bisect each other. The parallelogram $ABCD$ is defined by its vertex coordinates
