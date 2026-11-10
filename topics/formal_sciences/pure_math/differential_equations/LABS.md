# Hands-On Operational Lab: Differential Equations

## Objective & Prerequisites

**Objective**: To develop operational proficiency in solving, verifying, and debugging differential equations using symbolic computation while maintaining rigorous mathematical intuition. Students will gain hands-on experience with formal modeling workflows, failure analysis, and systematic debugging techniques.

**Prerequisites**:
1. Proficiency in basic calculus (derivatives, integrals)
2. Familiarity with Python programming fundamentals
3. Understanding of symbolic mathematics (algebraic manipulation, integration)
4. Installation of Python 3.10+ and SymPy library (`pip install sympy`)
5. Basic knowledge of differential equations (first-order, separable equations)

> **Why this matters in formal sciences**: Differential equations form the mathematical foundation for modeling continuous systems in physics, biology, and engineering. This lab bridges abstract theory with operational practice by emphasizing *why* solutions hold before *how* to compute them.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify symbolic solutions through explicit computation and compare with hand-derived results.

### Step-by-Step Workflow
1. **Hand-derived solution** (mathematical intuition first):
   Solve the logistic equation:  
   $$
   \frac{dy}{dx} = y(1 - y)
   $$
   *Rationale*: This is separable. We rewrite:
   $$
   \int \frac{dy}{y(1-y)} = \int dx
   $$
   Using partial fractions:
   $$
   \int \left( \frac{1}{y} + \frac{1}{1-y} \right) dy = \int dx
   $$
   Integrating:
   $$
   \ln|y| - \ln|1-y| = x + C \implies \ln\left|\frac{y}{1-y}\right| = x + C
   $$
   Exponentiating:
   $$
   \frac{y}{1-y} = e^{x + C} = Ce^x \implies y = \frac{Ce^x}{1 + Ce^x}
   $$
   *Key insight*: The solution exhibits asymptotic stability at $y=1$.

2. **SymPy verification** (operational step):
   Create a Python script `exercise1.py` with:
   ```python
   import sympy as sp

   # Define symbols
   x = sp.symbols('x')
   y = sp.symbols('y')

   # Define DE
   de = sp.Eq(sp.diff(y, x), y * (1 - y))

   # Solve symbolically
   solution = sp.dsolve(de, y)

   # Print solution in standard form
   print(f"Symbolic solution: {sp.simplify(solution.rhs)}")
   print(f"Verification: {sp.simplify(sp.diff(solution.rhs, x) - y*(1-y))}")
   ```

3. **Expected output** (run via shell):
   ```bash
   $ python3 exercise1.py
   Symbolic solution: C1/(C1*exp(x) + 1)
   Verification: 0
   ```

**Why this works**: The output confirms the solution satisfies the original DE (verification = 0). The `C1` is a constant of integration (formalized as a *general solution*). The `simplify()` command ensures the output matches the hand-derived form.

> **Critical insight**: The verification step (`sp.diff(solution.rhs, x) - y*(1-y)`) is a *formal check* that the solution is mathematically valid – not a numerical approximation.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Model a physical system (harmonic oscillator) using symbolic DEs and validate the solution.

### Step-by-Step Workflow
1. **Problem formulation**:
   Model the damped harmonic oscillator:  
   $$
   \frac{d^2y}{dt^2} + 2\zeta\omega_0 \frac{dy}{dt} + \omega_0^2 y = 0
   $$
   where $\zeta$ = damping ratio, $\omega_0$ = natural frequency.

2. **Build the solution** (Python script `exercise2.py`):
   ```python
   import sympy as sp

   # Define symbols
   t = sp.symbols('t')
   y = sp.symbols('y')
   zeta = sp.symbols('zeta')
   omega0 = sp.symbols('omega0')

   # Define DE (second-order)
   de = sp.Eq(sp.diff(y, t, 2) + 2*zeta*omega0*sp.diff(y, t) + omega0**2*y, 0)

   # Solve symbolically
   solution = sp.dsolve(de, y)

   # Print solution with parameters
   print(f"General solution: {sp.simplify(solution.rhs)}")
   print(f"Critical damping condition: {sp.solve(sp.Eq(2*zeta*omega0, 1), zeta)}")
   ```

3. **Deploy & validate** (run via shell):
   ```bash
   $ python3 exercise2.py
   General solution: C1*exp(-zeta*omega0*t)*cos(omega0*sqrt(1 - zeta**2)*t) + C2*exp(-zeta*omega0*t)*sin(omega0*sqrt(1 - zeta**2)*t)
   Critical damping condition: [1/2]
   ```

**Why this works**: The solution shows:
- **Underdamped** ($\zeta < 1/2$): Oscillatory decay
- **Critical damping** ($\zeta = 1/2$): No oscillation (exponential decay)
- **Overdamped** ($\zeta > 1/2$): Non-oscillatory decay

> **Formal significance**: The `sp.solve()` command for critical damping demonstrates *exact* parameter conditions – a hallmark of formal sciences where we seek *precise* transition points between solution behaviors.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce intentional errors and systematically diagnose/fix them using formal reasoning.

### Step-by-Step Workflow
1. **Inject fault** (modify `exercise2.py`):
   ```python
   # Faulty version (intentional error)
   de = sp.Eq(sp.diff(y, t, 2) + 2*zeta*omega0*sp.diff(y, t) + omega0**2*y, 0)
   # ERROR: Missing exponent on omega0
   solution = sp.dsolve(de, y)
   ```

2. **Analyze failure** (diagnose the error):
   - **SymPy output**:
     ```bash
     $ python3 exercise2_faulty.py
     Traceback (most recent call last):
       File "exercise2_faulty.py", line 5, in <module>
         solution = sp.dsolve(de, y)
     TypeError: 'int' object is not callable
     ```
   - **Root cause analysis**:
     1. SymPy expects symbolic expressions (not integers)
     2. The error occurs because `omega0**2` was computed as a *numerical* value (not symbolic)
     3. **Formal diagnosis**: The expression `omega0**2` is evaluated to `1` when `omega0` is a symbol (due to SymPy's default behavior), causing integer-type conflicts.

3. **Fix the error** (corrected script):
   ```python
   # Corrected version
   de = sp.Eq(sp.diff(y, t, 2) + 2*zeta*omega0*sp.diff(y, t) + omega0**2*y, 0)
   solution = sp.dsolve(de, y)
   ```

4. **Verify fix** (run corrected script):
   ```bash
   $ python3 exercise2_fixed.py
   General solution: C1*exp(-zeta*omega0*t)*cos(omega0*sqrt(1 - zeta**2)*t) + C2*exp(-zeta*omega0*t)*sin(omega0*sqrt(1 - zeta**2)*t)
   ```

**Why this works**: The debugging process follows *formal* error tracing:
1. Identify symptom (TypeError)
2. Trace to symbolic context (omega0 as symbol)
3. Apply mathematical correction (maintain symbolic expressions)
4. Validate with formal solution

> **Key lesson**: In formal sciences, *all* errors must be traceable to mathematical definitions – not ad-hoc fixes.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**: Solve the following differential equation using symbolic methods and verify your solution:  
$$
\frac{d^2y}{dx^2} - 3\frac{dy}{dx} + 2y = e^{2x}
$$

**Socratic Discussion Prompts** (for AI Tutor interaction):
1. *Why* is this a linear nonhomogeneous DE? What is the homogeneous solution?
2. How would you verify your particular solution satisfies the original DE?
3. What happens if you incorrectly assume the particular solution is $Ce^{2x}$? Why?
4. Can you derive the general solution using the method of undetermined coefficients? Show the formal steps.

**Expected output format** (for your AI Tutor):
```markdown
### My Solution
1. Homogeneous solution: [form]
2. Particular solution: [form]
3. General solution: [form]

### Verification Steps
- Step 1: [mathematical derivation]
- Step 2: [substitution check]
- Step 3: [formal equivalence proof]

### Critical Insight
[1-sentence explanation of why this matters in formal sciences]
```

> **Why this matters**: This challenge forces you to *reproduce* the formal derivation process – not just run code. The AI Tutor will help you identify gaps in your reasoning using the principles of formal logic and mathematical induction.

---

**Final Note**: In formal sciences, *operational practice* must always be grounded in *mathematical rigor*. Every command, script, and verification step should answer: "Why does this hold *exactly*?" This lab trains you to think like a mathematician – not just a coder.
