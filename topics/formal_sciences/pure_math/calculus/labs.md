# Operational Verification Labs: Calculus

## Objective & Mathematical Computing Setup

Calculus verification demands symbolic computation engines capable of exact algebraic manipulation, numerical boundary testing at machine precision limits, and formal theorem proving to validate analytic properties. The modern practitioner operates at the intersection of classical analysis and computational verification, wielding symbolic algebra systems to validate limit operations, differentiation rules, and integration theorems against rigorous axiomatic foundations. This laboratory guide constructs a verification workflow grounded in SymPy's symbolic core for exact computation, NumPy's numerical precision testing for boundary behavior, and SageMath's integration of algebraic geometry and theorem proving capabilities.

The calculus verification environment operates as a three-tier system. At the foundational layer, SymPy provides symbolic representation of functions, limits, derivatives, and integrals through abstract syntax trees that preserve mathematical structure without premature numerical evaluation. The intermediate layer employs NumPy's floating-point arithmetic to stress-test asymptotic behavior at singularities, poles, and removable discontinuities where symbolic methods encounter algebraic obstructions. The verification layer uses automated theorem proving to validate fundamental theorems—the Fundamental Theorem of Calculus linking differentiation and integration, the Mean Value Theorem's guarantee of derivative existence, and the chain rule's compositional structure.

Begin by establishing a Python 3.11+ environment with the requisite symbolic and numerical computation libraries. Install SymPy 1.12+ for symbolic calculus operations, NumPy 1.24+ for vectorized numerical computation, and optionally SageMath 10.0+ for advanced algebraic manipulation and integration with proof assistants. Verify installation integrity by importing each library and confirming version compatibility. Execute `python -c 'import sympy; print(sympy.__version__)'` to confirm SymPy is operational, then repeat for NumPy with `import numpy; print(numpy.__version__)`. For SageMath verification, launch the Sage interpreter with `sage` and execute `version()` to confirm build information.

The working directory structure organizes verification scripts by calculus subdomain. Create a root directory `calculus_verification/` containing subdirectories `limits/`, `derivatives/`, `integrals/`, and `theorems/`. Within each subdirectory, maintain separate Python modules for symbolic verification, numerical boundary testing, and formal proof sketches. This separation isolates symbolic manipulation from numerical approximation, preventing floating-point contamination of exact algebraic results while enabling direct comparison between symbolic predictions and numerical observations.

Configure SymPy's global assumptions system to enforce real-valued analysis throughout verification workflows. Import the library with `from sympy import *` and immediately set `x, y, z = symbols('x y z', real=True)` to declare primary variables as real numbers. This assumption propagates through all subsequent symbolic operations, enabling SymPy to apply real-analysis simplification rules that fail in the complex domain. For functions requiring complex analysis, explicitly declare complex variables with `w = symbols('w', complex=True)` to activate branch-cut handling and multivalued function disambiguation.

Initialize NumPy with double-precision floating-point arithmetic by importing as `import numpy as np` and verifying default dtype with `np.finfo(np.float64)`. This configuration provides approximately 15 decimal digits of precision, sufficient for detecting numerical instabilities at singularities while exposing catastrophic cancellation in poorly conditioned computations. For higher precision boundary testing, invoke Python's `decimal` module with contexts set to 50 or 100 decimal places, enabling detection of convergence failures invisible at machine precision.

## Exercise 1: Computational Verification of Core Theorems

The Fundamental Theorem of Calculus establishes the inverse relationship between differentiation and integration, asserting that for a continuous function $f$ on $[a, b]$, the integral $F(x) = \int_a^x f(t) \, dt$ satisfies $F'(x) = f(x)$ for all $x \in (a, b)$. Computational verification proceeds by constructing explicit antiderivatives symbolically, differentiating the result, and confirming algebraic equivalence to the original integrand. This process exposes implementation correctness of SymPy's integration algorithms and validates the symbolic differentiation engine against known analytic results.

Begin with polynomial verification to establish baseline correctness. Define a polynomial function $f(x) = 3x^2 - 5x + 7$ and compute its indefinite integral symbolically. Execute the following Python verification script:

```python
from sympy import symbols, integrate, diff, simplify, expand

x = symbols('x', real=True)
f = 3*x**2 - 5*x + 7

F = integrate(f, x)
f_recovered = diff(F, x)
verification = simplify(f_recovered - f)

print(f"Original function: {f}")
print(f"Antiderivative: {F}")
print(f"Recovered function: {f_recovered}")
print(f"Verification residual: {verification}")
assert verification == 0, "Fundamental Theorem verification failed for polynomial"
```

The antiderivative yields $F(x) = x^3 - \frac{5x^2}{2} + 7x$, and differentiation recovers the original polynomial exactly with zero residual. This confirms SymPy's polynomial integration operates correctly through the power rule $\int x^n \, dx = \frac{x^{n+1}}{n+1} + C$ for $n \neq -1$.

Extend verification to transcendental functions requiring substitution and integration by parts. Consider $f(x) = x e^{x^2}$, which demands the substitution $u = x^2$, yielding $du = 2x \, dx$ and the integral $\frac{1}{2} \int e^u \, du = \frac{1}{2} e^{x^2} + C$. Verify this symbolically:

```python
f_transcendental = x * exp(x**2)
F_transcendental = integrate(f_transcendental, x)
f_recovered_transcendental = diff(F_transcendental, x)
verification_transcendental = simplify(f_recovered_transcendental - f_transcendental)

print(f"Transcendental function: {f_transcendental}")
print(f"Antiderivative: {F_transcendental}")
print(f"Verification residual: {verification_transcendental}")
assert verification_transcendental == 0, "FTC verification failed for transcendental"
```

SymPy automatically applies the substitution rule and returns $F(x) = \frac{e^{x^2}}{2}$. Differentiation via the chain rule recovers $f(x) = x e^{x^2}$ with zero residual, validating both the integration algorithm and the differentiation chain rule implementation.

The Mean Value Theorem asserts that for a continuous function $f$ on $[a, b]$ differentiable on $(a, b)$, there exists $c \in (a, b)$ such that $f'(c) = \frac{f(b) - f(a)}{b - a}$. Computational verification constructs the derivative symbolically, solves for critical points where the derivative equals the secant slope, and confirms solutions lie within the open interval. Apply this to $f(x) = x^3 - 3x$ on $[0, 2]$:

```python
from sympy import solve

f_mvt = x**3 - 3*x
a, b = 0, 2

f_a = f_mvt.subs(x, a)
f_b = f_mvt.subs(x, b)
secant_slope = (f_b - f_a) / (b - a)

f_prime = diff(f_mvt, x)
critical_points = solve(f_prime - secant_slope, x)

print(f"Function: {f_mvt}")
print(f"Secant slope on [{a}, {b}]: {secant_slope}")
print(f"Derivative: {f_prime}")
print(f"Critical points: {critical_points}")

valid_points = [c for c in critical_points if a < c < b]
print(f"MVT witness points in ({a}, {b}): {valid_points}")
assert len(valid_points) > 0, "Mean Value Theorem verification failed"
```

The derivative $f'(x) = 3x^2 - 3$ and secant slope $(2 - 0) / 2 = 1$ yield the equation $3x^2 - 3 = 1$, giving $x^2 = \frac{4}{3}$ and $x = \pm \frac{2}{\sqrt{3}} \approx \pm 1.1547$. The positive root lies in $(0, 2)$, confirming the Mean Value Theorem. Numerical evaluation at this point verifies $f'(1.1547) \approx 1.0000$ within floating-point tolerance.

The chain rule for composite functions states $(f \circ g)'(x) = f'(g(x)) \cdot g'(x)$. Verify this symbolically by constructing an explicit composition, computing the derivative directly, and comparing against the chain rule expansion. Let $f(u) = \sin(u)$ and $g(x) = x^2 + 1$, so $(f \circ g)(x) = \sin(x^2 + 1)$:

```python
u = symbols('u', real=True)
f_outer = sin(u)
g_inner = x**2 + 1

composite = f_outer.subs(u, g_inner)
direct_derivative = diff(composite, x)

f_prime_at_g = diff(f_outer, u).subs(u, g_inner)
g_prime = diff(g_inner, x)
chain_rule_derivative = f_prime_at_g * g_prime

verification_chain = simplify(direct_derivative - chain_rule_derivative)

print(f"Composite function: {composite}")
print(f"Direct derivative: {direct_derivative}")
print(f"Chain rule derivative: {chain_rule_derivative}")
print(f"Verification residual: {verification_chain}")
assert verification_chain == 0, "Chain rule verification failed"
```

SymPy computes the direct derivative as $2x \cos(x^2 + 1)$ and the chain rule expansion as $\cos(x^2 + 1) \cdot 2x$, which simplify to identical expressions, confirming chain rule correctness.

Extend verification to the product rule $(fg)' = f'g + fg'$ and quotient rule $\left(\frac{f}{g}\right)' = \frac{f'g - fg'}{g^2}$. For product rule validation, choose $f(x) = x^2$ and $g(x) = \cos(x)$:

```python
f_product = x**2
g_product = cos(x)
product = f_product * g_product

direct_product_derivative = diff(product, x)
product_rule_derivative = diff(f_product, x) * g_product + f_product * diff(g_product, x)
verification_product = simplify(direct_product_derivative - product_rule_derivative)

print(f"Product: {product}")
print(f"Direct derivative: {direct_product_derivative}")
print(f"Product rule derivative: {product_rule_derivative}")
print(f"Verification residual: {verification_product}")
assert verification_product == 0, "Product rule verification failed"
```

Both methods yield $2x \cos(x) - x^2 \sin(x)$ with zero residual. For the quotient rule, use $f(x) = \sin(x)$ and $g(x) = x$:

```python
f_quotient = sin(x)
g_quotient = x
quotient = f_quotient / g_quotient

direct_quotient_derivative = diff(quotient, x)
quotient_rule_derivative = (diff(f_quotient, x) * g_quotient - f_quotient * diff(g_quotient, x)) / g_quotient**2
verification_quotient = simplify(direct_quotient_derivative - quotient_rule_derivative)

print(f"Quotient: {quotient}")
print(f"Direct derivative: {direct_quotient_derivative}")
print(f"Quotient rule derivative: {quotient_rule_derivative}")
print(f"Verification residual: {verification_quotient}")
assert verification_quotient == 0, "Quotient rule verification failed"
```

Both methods produce $\frac{x \cos(x) - \sin(x)}{x^2}$, validating the quotient rule implementation.

## Exercise 2: Boundary Value Stress Testing & Singularities

Limits at singularities expose the boundary between symbolic manipulation and numerical approximation. The canonical example $\lim_{x \to 0} \frac{\sin(x)}{x} = 1$ involves a removable singularity where direct substitution yields the indeterminate form $\frac{0}{0}$. L'Hôpital's rule resolves this by differentiating numerator and denominator, giving $\lim_{x \to 0} \frac{\cos(x)}{1} = 1$. Verify this symbolically and numerically:

```python
from sympy import limit, sin, cos

f_limit = sin(x) / x
symbolic_limit = limit(f_limit, x, 0)

print(f"Function: {f_limit}")
print(f"Symbolic limit as x→0: {symbolic_limit}")
assert symbolic_limit == 1, "Symbolic limit verification failed"

# Numerical stress test
import numpy as np

x_values = np.logspace(-15, -1, 50)  # 10^-15 to 10^-1
numerical_limits = np.sin(x_values) / x_values

print(f"Numerical limit at x=10^-15: {numerical_limits[0]}")
print(f"Numerical limit at x=10^-1: {numerical_limits[-1]}")
print(f"Mean numerical limit: {np.mean(numerical_limits)}")

assert np.abs(numerical_limits[0] - 1.0) < 1e-10, "Numerical limit diverges at machine precision"
```

The symbolic limit returns exactly $1$. Numerically, evaluating at $x = 10^{-15}$ yields approximately $1.0$ within double-precision tolerance, but further reduction toward $x = 10^{-16}$ triggers catastrophic cancellation as $\sin(x) \approx x$ and floating-point subtraction loses significance. The numerical limits array should remain near $1.0$ throughout the range, confirming stable evaluation.

Poles and vertical asymptotes occur where denominators vanish. Consider $f(x) = \frac{1}{x - 2}$, which has a pole at $x = 2$. Verify that left and right limits diverge to $-\infty$ and $+\infty$ respectively:

```python
f_pole = 1 / (x - 2)

limit_left = limit(f_pole, x, 2, '-')
limit_right = limit(f_pole, x, 2, '+')

print(f"Function with pole: {f_pole}")
print(f"Left limit as x→2⁻: {limit_left}")
print(f"Right limit as x→2⁺: {limit_right}")

assert limit_left == -oo, "Left limit at pole incorrect"
assert limit_right == oo, "Right limit at pole incorrect"

# Numerical approach
x_left = 2.0 - np.logspace(-10, -1, 20)
x_right = 2.0 + np.logspace(-10, -1, 20)

f_left = 1.0 / (x_left - 2.0)
f_right = 1.0 / (x_right - 2.0)

print(f"Numerical left approach at x=2-10^-10: {f_left[0]}")
print(f"Numerical right approach at x=2+10^-10: {f_right[0]}")

assert f_left[0] < -1e9, "Left numerical approach did not diverge"
assert f_right[0] > 1e9, "Right numerical approach did not diverge"
```

SymPy correctly identifies the infinite limits. Numerically, approaching from $x = 2 - 10^{-10}$ yields values exceeding $-10^{10}$ in magnitude, confirming divergence.

Essential singularities exhibit chaotic behavior at the singularity point. The function $f(z) = e^{1/z}$ has an essential singularity at $z = 0$, where the limit does not exist (neither finite nor infinite). Test this by approaching zero along the real and imaginary axes:

```python
z = symbols('z', complex=True)
f_essential = exp(1/z)

limit_real = limit(f_essential.subs(z, x), x, 0, '+')
print(f"Limit along real axis as z→0⁺: {limit_real}")

# Numerical spiral approach
theta = np.linspace(0, 4*np.pi, 100)
r = np.logspace(-2, -0.1, 100)
z_spiral = r * np.exp(1j * theta)
f_spiral = np.exp(1.0 / z_spiral)

print(f"Max magnitude in spiral approach: {np.max(np.abs(f_spiral))}")
print(f"Min magnitude in spiral approach: {np.min(np.abs(f_spiral))}")
print(f"Variance in spiral approach: {np.var(np.abs(f_spiral))}")

assert np.var(np.abs(f_spiral)) > 1e10, "Essential singularity did not exhibit chaotic behavior"
```

Approaching along the real axis from the positive side yields $\lim_{x \to 0^+} e^{1/x} = +\infty$, but approaching along the imaginary axis produces oscillatory behavior. The numerical spiral approach shows extreme variance in magnitude, characteristic of essential singularities where the function takes on all complex values infinitely often in any neighborhood of the singularity.

Discontinuities partition into removable, jump, and infinite types. A removable discontinuity occurs when $\lim_{x \to c} f(x)$ exists but $f(c)$ is either undefined or differs from the limit. Construct $f(x) = \frac{x^2 - 1}{x - 1}$ with a removable discontinuity at $x = 1$:

```python
f_removable = (x**2 - 1) / (x - 1)
f_simplified = simplify(f_removable)

limit_at_discontinuity = limit(f_removable, x, 1)

print(f"Function with removable discontinuity: {f_removable}")
print(f"Simplified form: {f_simplified}")
print(f"Limit at x=1: {limit_at_discontinuity}")

assert f_simplified == x + 1, "Simplification failed"
assert limit_at_discontinuity == 2, "Limit at removable discontinuity incorrect"

# Define piecewise continuous extension
from sympy import Piecewise
f_extended = Piecewise((f_simplified, x != 1), (2, x == 1))

print(f"Continuous extension: {f_extended}")
```

Algebraic simplification yields $f(x) = x + 1$ for $x \neq 1$, and the limit as $x \to 1$ equals $2$. Defining the piecewise extension with $f(1) = 2$ removes the discontinuity.

Jump discontinuities occur when left and right limits exist but differ. The Heaviside step function $H(x) = \begin{cases} 0 & x < 0 \\ 1 & x \geq 0 \end{cases}$ has a jump discontinuity at $x = 0$:

```python
from sympy import Heaviside

H = Heaviside(x)

limit_left_jump = limit(H, x, 0, '-')
limit_right_jump = limit(H, x, 0, '+')

print(f"Heaviside function: {H}")
print(f"Left limit at x=0: {limit_left_jump}")
print(f"Right limit at x=0: {limit_right_jump}")
print(f"Jump magnitude: {limit_right_jump - limit_left_jump}")

assert limit_left_jump == 0, "Left limit at jump incorrect"
assert limit_right_jump == 1, "Right limit at jump incorrect"
```

The left limit is $0$ and the right limit is $1$, confirming a jump of magnitude $1$.

Infinite discontinuities occur at poles. Verify this for $f(x) = \tan(x)$ at $x = \frac{\pi}{2}$:

```python
from sympy import tan, pi

f_tangent = tan(x)

limit_left_tan = limit(f_tangent, x, pi/2, '-')
limit_right_tan = limit(f_tangent, x, pi/2, '+')

print(f"Tangent function: {f_tangent}")
print(f"Left limit at x=π/2: {limit_left_tan}")
print(f"Right limit at x=π/2: {limit_right_tan}")

assert limit_left_tan == oo, "Left limit at pole incorrect"
assert limit_right_tan == -oo, "Right limit at pole incorrect"
```

The left limit diverges to $+\infty$ and the right limit to $-\infty$, characteristic of an odd-order pole.

## Exercise 3: Algorithmic Implementation of Formal Structures

The derivative is the fundamental operator of differential calculus, defined as the limit $f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$. Implement a numerical differentiation function using finite differences and compare against symbolic differentiation. The forward difference approximation uses $f'(x) \approx \frac{f(x+h) - f(x)}{h}$, the backward difference uses $f'(x) \approx \frac{f(x) - f(x-h)}{h}$, and the central difference uses $f'(x) \approx \frac{f(x+h) - f(x-h)}{2h}$:

```python
def finite_difference_derivative(f_func, x_val, h=1e-5, method='central'):
    """
    Compute numerical derivative using finite differences.
    
    Parameters:
    - f_func: callable, function to differentiate
    - x_val: float, point at which to evaluate derivative
    - h: float, step size
    - method: str, 'forward', 'backward', or 'central'
    
    Returns:
    - float, approximate derivative
    """
    if method == 'forward':
        return (f_func(x_val + h) - f_func(x_val)) / h
    elif method == 'backward':
        return (f_func(x_val) - f_func(x_val - h)) / h
    elif method == 'central':
        return (f_func(x_val + h) - f_func(x_val - h)) / (2 * h)
    else:
        raise ValueError("Method must be 'forward', 'backward', or 'central'")

# Test against symbolic derivative
from sympy import lambdify

f_test = x**3 - 2*x**2 + 3*x - 1
f_prime_symbolic = diff(f_test, x)

f_test_func = lambdify(x, f_test, 'numpy')
f_prime_func = lambdify(x, f_prime_symbolic, 'numpy')

x_test = 2.5
symbolic_derivative_val = f_prime_func(x_test)

forward_diff = finite_difference_derivative(f_test_func, x_test, method='forward')
backward_diff = finite_difference_derivative(f_test_func, x_test, method='backward')
central_diff = finite_difference_derivative(f_test_func, x_test, method='central')

print(f"Function: {f_test}")
print(f"Symbolic derivative: {f_prime_symbolic}")
print(f"Symbolic derivative at x={x_test}: {symbolic_derivative_val}")
print(f"Forward difference: {forward_diff}, error: {abs(forward_diff - symbolic_derivative_val)}")
print(f"Backward difference: {backward_diff}, error: {abs(backward_diff - symbolic_derivative_val)}")
print(f"Central difference: {central_diff}, error: {abs(central_diff - symbolic_derivative_val)}")

assert abs(central_diff - symbolic_derivative_val) < 1e-8, "Central difference error exceeds tolerance"
```

The symbolic derivative $f'(x) = 3x^2 - 4x + 3$ evaluates to $11.75$ at $x = 2.5$. The central difference method achieves error below $10^{-8}$, while forward and backward differences show error around $10^{-5}$, demonstrating the superior accuracy of central differences through cancellation of first-order error terms.

Definite integration computes the signed area under a curve. The trapezoidal rule approximates $\int_a^b f(x) \, dx$ by partitioning $[a, b]$ into $n$ subintervals of width $h = \frac{b-a}{n}$ and summing trapezoidal areas: $\int_a^b f(x) \, dx \approx \frac{h}{2} \left[ f(x_0) + 2 \sum_{i=1}^{n-1} f(x_i) + f(x_n) \right]$. Implement this and compare against symbolic integration:

```python
def trapezoidal_integration(f_func, a, b, n=1000):
    """
    Compute definite integral using trapezoidal rule.
    
    Parameters:
    - f_func: callable, integrand
    - a, b: float, integration bounds
    - n: int, number of subintervals
    
    Returns:
    - float, approximate integral
    """
    h = (b - a) / n
    x_vals = np.linspace(a, b, n + 1)
    y_vals = f_func(x_vals)
    
    integral = (h / 2.0) * (y_vals[0] + 2 * np.sum(y_vals[1:-1]) + y_vals[-1])
    return integral

# Test against symbolic integration
f_integrate = x**2 * exp(-x)
a_bound, b_bound = 0, 5

symbolic_integral = integrate(f_integrate, (x, a_bound, b_bound))

f_integrate_func = lambdify(x, f_integrate, 'numpy')
numerical_integral = trapezoidal_integration(f_integrate_func, a_bound, b_bound, n=10000)

print(f"Function: {f_integrate}")
print(f"Symbolic integral from {a_bound} to {b_bound}: {symbolic_integral}")
print(f"Symbolic integral (float): {float(symbolic_integral)}")
print(f"Numerical integral: {numerical_integral}")
print(f"Absolute error: {abs(numerical_integral - float(symbolic_integral))}")
print(f"Relative error: {abs(numerical_integral - float(symbolic_integral)) / float(symbolic_integral)}")

assert abs(numerical_integral - float(symbolic_integral)) < 1e-6, "Trapezoidal integration error exceeds tolerance"
```

The symbolic integral evaluates to $2 - 7e^{-5} \approx 1.9953$. The trapezoidal rule with $n = 10000$ subintervals achieves absolute error below $10^{-6}$, validating the numerical integration algorithm.

Taylor series expansion represents analytic functions as infinite polynomials. The Taylor series of $f(x)$ about $x = a$ is $f(x) = \sum_{n=0}^\infty \frac{f^{(n)}(a)}{n!} (x - a)^n$. Implement a function to compute Taylor series symbolically to arbitrary order and verify against SymPy's built-in series expansion:

```python
from sympy import series, factorial

def taylor_series_manual(f_expr, var, point, order):
    """
    Compute Taylor series expansion manually.
    
    Parameters:
    - f_expr: sympy expression, function to expand
    - var: sympy symbol, variable
    - point: float, expansion point
    - order: int, maximum order
    
    Returns:
    - sympy expression, Taylor series
    """
    taylor_sum = 0
    for n in range(order + 1):
        derivative_n = diff(f_expr, var, n)
        coefficient = derivative_n.subs(var, point) / factorial(n)
        taylor_sum += coefficient * (var - point)**n
    
    return taylor_sum

# Test with exponential function
f_taylor = exp(x)
point_expansion = 0
order_expansion = 5

manual_taylor = taylor_series_manual(f_taylor, x, point_expansion, order_expansion)
sympy_taylor = series(f_taylor, x, point_expansion, n=order_expansion+1).removeO()

print(f"Function: {f_taylor}")
print(f"Manual Taylor series (order {order_expansion}): {manual_taylor}")
print(f"SymPy Taylor series: {sympy_taylor}")

verification_taylor = simplify(manual_taylor - sympy_taylor)
print(f"Verification residual: {verification_taylor}")

assert verification_taylor == 0, "Taylor series manual computation differs from SymPy"

# Numerical convergence test
x_eval = 0.5
exact_value = float(exp(x_eval))
taylor_orders = [1, 2, 3, 5, 10, 20]

print(f"\nTaylor series convergence at x={x_eval}:")
print(f"Exact value: {exact_value}")

for order in taylor_orders:
    taylor_approx = taylor_series_manual(f_taylor, x, point_expansion, order)
    numerical_approx = float(taylor_approx.subs(x, x_eval))
    error = abs(numerical_approx - exact_value)
    print(f"Order {order}: {numerical_approx}, error: {error}")
```

The exponential function's Taylor series $e^x = \sum_{n=0}^\infty \frac{x^n}{n!}$ converges rapidly. At $x = 0.5$, the 20th-order approximation achieves machine precision, confirming exponential convergence.

Newton's method finds roots of equations through iterative linearization. Given an initial guess $x_0$ and a function $f(x)$, the iteration $x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}$ converges quadratically to a root when $f'(x) \neq 0$ near the root. Implement Newton's method and verify convergence on test functions:

```python
def newton_method(f_expr, f_prime_expr, var, x0, tolerance=1e-10, max_iterations=100):
    """
    Find root using Newton's method.
    
    Parameters:
    - f_expr: sympy expression, function
    - f_prime_expr: sympy expression, derivative
    - var: sympy symbol
    - x0: float, initial guess
    - tolerance: float, convergence tolerance
    - max_iterations: int
    
    Returns:
    - float, approximate root
    - list, iteration history
    """
    f_func = lambdify(var, f_expr, 'numpy')
    f_prime_func = lambdify(var, f_prime_expr, 'numpy')
    
    x_current = x0
    history = [x_current]
    
    for iteration in range(max_iterations):
        f_val = f_func(x_current)
        f_prime_val = f_prime_func(x_current)
        
        if abs(f_val) < tolerance:
            print(f"Converged in {iteration} iterations")
            return x_current, history
        
        if abs(f_prime_val) < 1e-15:
            raise ValueError("Derivative too close to zero, Newton's method fails")
        
        x_next = x_current - f_val / f_prime_val
        history.append(x_next)
        x_current = x_next
    
    raise ValueError("Newton's method did not converge within max iterations")

# Find root of x^2 - 2 (square root of 2)
f_newton = x**2 - 2
f_prime_newton = diff(f_newton, x)

root, history_newton = newton_method(f_newton, f_prime_newton, x, x0=1.5)

print(f"Function: {f_newton}")
print(f"Newton's method root: {root}")
print(f"True value: {np.sqrt(2)}")
print(f"Error: {abs(root - np.sqrt(2))}")
print(f"Iteration history: {history_newton}")

# Verify quadratic convergence
errors = [abs(h - np.sqrt(2)) for h in history_newton]
convergence_ratios = [errors[i+1] / errors[i]**2 for i in range(len(errors)-1) if errors[i] > 1e-15]

print(f"Convergence ratios (error_{n+1} / error_n^2): {convergence_ratios}")
assert all(r < 10 for r in convergence_ratios), "Quadratic convergence not achieved"
```

Newton's method converges to $\sqrt{2} \approx 1.4142135623730951$ in approximately 4 iterations from the initial guess $x_0 = 1.5$. The convergence ratio $\frac{e_{n+1}}{e_n^2}$ remains bounded, confirming quadratic convergence.

Partial derivatives extend differentiation to multivariable functions. For $f(x, y) = x^2 y + \sin(xy)$, compute $\frac{\partial f}{\partial x}$ and $\frac{\partial f}{\partial y}$ symbolically and verify Schwarz's theorem on equality of mixed partials $\frac{\partial^2 f}{\partial x \partial y} = \frac{\partial^2 f}{\partial y \partial x}$:

```python
y = symbols('y', real=True)
f_multivar = x**2 * y + sin(x * y)

df_dx = diff(f_multivar, x)
df_dy = diff(f_multivar, y)

d2f_dxdy = diff(df_dx, y)
d2f_dydx = diff(df_dy, x)

print(f"Function: {f_multivar}")
print(f"∂f/∂x: {df_dx}")
print(f"∂f/∂y: {df_dy}")
print(f"∂²f/∂x∂y: {d2f_dxdy}")
print(f"∂²f/∂y∂x: {d2f_dydx}")

verification_schwarz = simplify(d2f_dxdy - d2f_dydx)
print(f"Schwarz theorem verification: {verification_schwarz}")

assert verification_schwarz == 0, "Mixed partial derivatives are not equal"
```

The mixed partial derivatives both equal $2x + \cos(xy) - xy \sin(xy)$, confirming Schwarz's theorem for this smooth function.

The gradient vector $\nabla f = \left( \frac{\partial f}{\partial x}, \frac{\partial f}{\partial y}, \frac{\partial f}{\partial z} \right)$ points in the direction of maximum increase. Compute the gradient of $f(x, y, z) = x^2 + y^2 + z^2$ and verify it points radially outward:

```python
z = symbols('z', real=True)
f_gradient = x**2 + y**2 + z**2

gradient = [diff(f_gradient, var) for var in (x, y, z)]

print(f"Function: {f_gradient}")
print(f"Gradient: {gradient}")

# Verify gradient at point (1, 2, 3)
point = {x: 1, y: 2, z: 3}
gradient_at_point = [g.subs(point) for g in gradient]

print(f"Gradient at (1, 2, 3): {gradient_at_point}")
assert gradient_at_point == [2, 4, 6], "Gradient computation incorrect"
```

The gradient $\nabla f = (2x, 2y, 2z)$ at $(1, 2, 3)$ equals $(2, 4, 6) = 2(1, 2, 3)$, confirming radial direction.

## Formal Axioms Cheat Sheet & Verification Reference

The foundations of calculus rest on the completeness axiom of real numbers, epsilon-delta definitions of limits, and the structure theorems connecting differentiation and integration. This reference consolidates formal definitions, key theorems, and computational verification patterns.

**Completeness Axiom of Real Numbers**: Every nonempty set of real numbers that is bounded above has a least upper bound (supremum). This axiom distinguishes the real numbers from the rationals and underlies the convergence of Cauchy sequences, the intermediate value theorem, and the existence of limits.

**Epsilon-Delta Definition of Limit**: The limit $\lim_{x \to c} f(x) = L$ holds if for every $\epsilon > 0$, there exists $\delta > 0$ such that $0 < |x - c| < \delta$ implies $|f(x) - L| < \epsilon$. Computational verification translates this into numerical testing: for a sequence of $\epsilon$ values decreasing toward zero, compute corresponding $\delta$ values and verify the implication holds.

**Continuity at a Point**: A function $f$ is continuous at $c$ if $\lim_{x \to c} f(x) = f(c)$. This requires three conditions: $f(c)$ is defined, the limit exists, and they are equal. Verify continuity by checking that symbolic limit evaluation matches function evaluation at the point.

**Differentiability Implies Continuity**: If $f$ is differentiable at $c$, then $f$ is continuous at $c$. The contrapositive states that discontinuity at a point precludes differentiability there. Computational verification: if a symbolic derivative exists at a point, confirm the limit equals the function value.

**Fundamental Theorem of Calculus (Part I)**: If $f$ is continuous on $[a, b]$ and $F(x) = \int_a^x f(t) \, dt$, then $F'(x) = f(x)$ for all $x \in (a, b)$. Verification pattern: compute $F$ symbolically via integration, differentiate the result, and confirm algebraic equivalence to $f$.

**Fundamental Theorem of Calculus (Part II)**: If $F$ is an antiderivative of $f$ on $[a, b]$, then $\int_a^b f(x) \, dx = F(b) - F(a)$. Verification pattern: compute the indefinite integral to obtain $F$, evaluate at bounds, and compare against direct definite integration.

**Mean Value Theorem**: If $f$ is continuous on $[a, b]$ and differentiable on $(a, b)$, then there exists $c \in (a, b)$ such that $f'(c) = \frac{f(b) - f(a)}{b - a}$. Verification pattern: compute the secant slope, set it equal to the derivative, solve for critical points, and confirm at least one lies in the open interval.

**Chain Rule**: If $g$ is differentiable at $x$ and $f$ is differentiable at $g(x)$, then $(f \circ g)'(x) = f'(g(x)) \cdot g'(x)$. Verification pattern: compute the composite derivative directly and via the chain rule expansion, then confirm algebraic equivalence.

**Taylor's Theorem with Remainder**: If $f$ is $(n+1)$-times differentiable on an interval containing $a$ and $x$, then $f(x) = \sum_{k=0}^n \frac{f^{(k)}(a)}{k!} (x-a)^k + R_n(x)$, where the Lagrange form of the remainder is $R_n(x) = \frac{f^{(n+1)}(\xi)}{(n+1)!} (x-a)^{n+1}$ for some $\xi$ between $a$ and $x$. Verification pattern: compute Taylor polynomial to order $n$, evaluate remainder numerically, and confirm convergence as $n \to \infty$.

**L'Hôpital's Rule**: If $\lim_{x \to c} f(x) = \lim_{x \to c} g(x) = 0$ (or both $\pm \infty$) and $\lim_{x \to c} \frac{f'(x)}{g'(x)}$ exists, then $\lim_{x \to c} \frac{f(x)}{g(x)} = \lim_{x \to c} \frac{f'(x)}{g'(x)}$. Verification pattern: identify indeterminate forms, compute derivatives, and confirm the derivative quotient limit matches the original limit.

**Intermediate Value Theorem**: If $f$ is continuous on $[a, b]$ and $N$ is any number between $f(a)$ and $f(b)$, then there exists $c \in (a, b)$ such that $f(c) = N$. Verification pattern: evaluate function at endpoints, choose an intermediate value, solve $f(x) = N$ symbolically, and confirm roots lie within the interval.

**Rolle's Theorem**: If $f$ is continuous on $[a, b]$, differentiable on $(a, b)$, and $f(a) = f(b)$, then there exists $c \in (a, b)$ such that $f'(c) = 0$. Verification pattern: confirm endpoint equality, solve $f'(x) = 0$ for critical points, and verify at least one lies in the open interval.

**Extreme Value Theorem**: If $f$ is continuous on a closed interval $[a, b]$, then $f$ attains both a maximum and minimum value on that interval. Verification pattern: compute critical points in $(a, b)$ via $f'(x) = 0$, evaluate $f$ at critical points and endpoints, and identify the maximum and minimum values.

**Integration by Parts**: $\int u \, dv = uv - \int v \, du$. Computational verification: choose $u$ and $dv$, compute $du$ and $v$, apply the formula symbolically, and confirm the result matches direct integration.

**Substitution Rule**: If $u = g(x)$ is differentiable with continuous derivative and $f$ is continuous, then $\int f(g(x)) g'(x) \, dx = \int f(u) \, du$. Verification pattern: perform substitution symbolically, integrate with respect to $u$, back-substitute, and confirm equivalence to direct integration.

**Leibniz Integral Rule**: If $f(x, t)$ and $\frac{\partial f}{\partial x}$ are continuous, then $\frac{d}{dx} \int_{a(x)}^{b(x)} f(x, t) \, dt = f(x, b(x)) b'(x) - f(x, a(x)) a'(x) + \int_{a(x)}^{b(x)} \frac{\partial f}{\partial x}(x, t) \, dt$. Verification pattern: compute the derivative of the integral using Leibniz rule, and compare against direct differentiation of the integrated result.

**Numerical Integration Error Bounds**: For the trapezoidal rule on $[a, b]$ with $n$ subintervals, the error is $E_T = -\frac{(b-a)^3}{12n^2} f''(\xi)$ for some $\xi \in (a, b)$. Verification pattern: compute symbolic second derivative, find its maximum on $[a, b]$, calculate theoretical error bound, and compare against actual numerical error.

**Numerical Differentiation Error**: Central difference error is $O(h^2)$, while forward/backward difference error is $O(h)$. Verification pattern: compute symbolic derivative, evaluate numerically with varying $h$, plot error versus $h$ on log-log scale, and confirm slope matches theoretical order.

**Cauchy Convergence Criterion**: A sequence converges if and only if for every $\epsilon > 0$, there exists $N$ such that $|a_m - a_n| < \epsilon$ for all $m, n > N$. Computational verification: generate sequence terms, compute pairwise differences for large indices, and confirm they decrease below all positive thresholds.

**Weierstrass M-Test**: If $|f_n(x)| \leq M_n$ for all $x$ in a set and $\sum M_n$ converges, then $\sum f_n(x)$ converges uniformly. Verification pattern: compute bounds $M_n$ symbolically, verify convergence of $\sum M_n$ numerically, and test uniform convergence by computing supremum of partial sum differences.

This verification framework transforms abstract calculus theorems into executable computational patterns. Each formal definition translates into symbolic manipulation procedures in SymPy, numerical stress tests in NumPy, and formal proof sketches in proof assistants. The boundary between symbolic exactness and numerical approximation becomes a diagnostic tool: when symbolic methods fail due to algebraic complexity, numerical methods expose asymptotic behavior; when numerical methods encounter precision limits, symbolic methods provide exact algebraic structure. The calculus practitioner wields both modes in concert, verifying theoretical predictions against computational reality.
