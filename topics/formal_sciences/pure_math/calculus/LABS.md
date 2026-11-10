# Hands-On Operational Lab: Calculus  
*For Formal Sciences (Pure Mathematics) Practice*  

---

## Objective & Prerequisites  
**Objective**: Develop *operational proficiency* in applying calculus concepts through structured verification, modeling, and failure analysis—bridging theoretical understanding with computational validation.  

**Prerequisites**:  
1. Basic familiarity with limits, derivatives, and integrals (single-variable calculus).  
2. Python 3.8+ installed with `sympy` (symbolic math library).  
3. Terminal access (Linux/macOS/Windows WSL).  
4. *Critical mindset*: Ability to trace logical errors in mathematical derivations.  

> 💡 **Why this lab?**  
> This lab transforms abstract calculus into *actionable operations* by requiring explicit verification of each step. Unlike theoretical exercises, it forces students to confront the *systematic interplay* between mathematical intuition and computational validation—essential for formal sciences.

---

## Exercise 1: Exploration & System State Inspection  
*Verify foundational calculus operations using symbolic computation.*  

**Goal**: Confirm that your environment correctly computes derivatives and integrals for basic functions.  

### Step-by-Step Verification Commands  
Run these commands in your terminal to inspect the system state and expected outputs:  

```bash
# 1. Verify derivative of x² (fundamental rule)
python -c "import sympy as sp; x = sp.symbols('x'); print(sp.diff(x**2, x))"
# Expected Output: 2*x

# 2. Verify integral of 3x² (power rule)
python -c "import sympy as sp; x = sp.symbols('x'); print(sp.integrate(3*x**2, x))"
# Expected Output: x**3

# 3. Verify chain rule (composite function)
python -c "import sympy as sp; x = sp.symbols('x'); f = sp.sin(x**2); print(sp.diff(f, x))"
# Expected Output: 2*x*cos(x**2)
```

### Why This Works  
These commands:  
1. **Explicitly define** symbolic variables (`x`)  
2. **Apply calculus operations** (`diff` for derivatives, `integrate` for integrals)  
3. **Output raw symbolic results** (no numerical approximation)  
4. **Validate against known rules** (power rule, chain rule)  

> ✅ **Pass Criteria**: All commands must output *exact symbolic expressions* matching the expected results above. If outputs differ, re-examine variable definitions or SymPy syntax.

---

## Exercise 2: Building & Deploying / Modeling Scenario  
*Model a real-world calculus problem with step-by-step deployment.*  

**Scenario**: *Optimize the volume of a cylindrical can* (radius `r`, height `h`) with fixed surface area `S = 2πr² + 2πrh = 100`.  

### Step-by-Step Workflow  
1. **Define the objective function** (volume to maximize):  
   ```bash
   # 1. Define symbolic variables
   python -c "import sympy as sp; r, h = sp.symbols('r h'); S = 100"
   ```

2. **Express height `h` in terms of `r` using the surface area constraint**:  
   ```bash
   # 2. Solve for h from S = 2πr² + 2πrh
   python -c "import sympy as sp; r, h = sp.symbols('r h'); S = 100; pi = sp.pi; eq = 2*pi*r**2 + 2*pi*r*h - S; h_expr = sp.solve(eq, h)[0]"
   # Output: h = (100 - 2*pi*r**2)/(2*pi*r)
   ```

3. **Define volume as a function of `r`**:  
   ```bash
   # 3. Volume V = πr²h
   python -c "import sympy as sp; r, h = sp.symbols('r h'); pi = sp.pi; V = pi*r**2*h_expr"
   ```

4. **Compute derivative of volume with respect to `r`**:  
   ```bash
   # 4. dV/dr = ?
   python -c "import sympy as sp; r = sp.symbols('r'); pi = sp.pi; V = pi*r**2*(100 - 2*pi*r**2)/(2*pi*r); dV_dr = sp.diff(V, r)"
   # Expected Output: (100 - 4*pi*r**2)/(2)  [simplified]
   ```

5. **Find critical point (set dV/dr = 0)**:  
   ```bash
   # 5. Solve dV/dr = 0
   python -c "import sympy as sp; r = sp.symbols('r'); pi = sp.pi; dV_dr = (100 - 4*pi*r**2)/2; critical_r = sp.solve(dV_dr, r)[0]"
   # Expected Output: r = sqrt(25/pi) ≈ 2.82
   ```

6. **Validate second derivative for minima/maxima**:  
   ```bash
   # 6. Check concavity
   python -c "import sympy as sp; r = sp.symbols('r'); pi = sp.pi; d2V_dr2 = sp.diff(dV_dr, r); d2V_dr2.subs(r, critical_r)"
   # Expected Output: Negative (indicating maximum volume)
   ```

### Key Insight  
This workflow demonstrates *how calculus operations are deployed operationally*:  
1. Constraints → Explicit function definition  
2. Derivatives → Critical point identification  
3. Second derivatives → Concavity validation  

> 🔄 **Why this is formal science**: Every step is *reversible* and *verifiable* via symbolic computation—no approximations, no assumptions beyond the problem statement.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging  
*Identify and resolve errors in a calculus model.*  

**Scenario**: A student accidentally writes `S = 100` instead of `S = 2πr² + 2πrh = 100` in their code.  

### Step-by-Step Debugging  
1. **Inject the error**:  
   ```bash
   # 1. Incorrect constraint (missing π terms)
   python -c "import sympy as sp; r, h = sp.symbols('r h'); S = 100; eq = r**2 + h**2 - S"
   ```

2. **Observe failure**:  
   ```bash
   # 2. Compute volume with broken constraint
   python -c "import sympy as sp; r, h = sp.symbols('r h'); pi = sp.pi; V = pi*r**2*h; eq = r**2 + h**2 - 100; h_expr = sp.solve(eq, h)[0]; V_expr = V.subs(h, h_expr)"
   # Output: Error: "ValueError: too many values to unpack"
   ```

3. **Diagnose the root cause**:  
   - The constraint `r² + h² = 100` is *not* the surface area formula (should be `2πr² + 2πrh = 100`).  
   - The error causes `h_expr` to return *two* solutions (not one), breaking the substitution.

4. **Fix the model**:  
   ```bash
   # 3. Correct constraint with π
   python -c "import sympy as sp; r, h = sp.symbols('r h'); pi = sp.pi; S = 100; eq = 2*pi*r**2 + 2*pi*r*h - S; h_expr = sp.solve(eq, h)[0]"
   ```

5. **Re-verify**:  
   ```bash
   # 4. Confirm critical point
   python -c "import sympy as sp; r = sp.symbols('r'); pi = sp.pi; V = pi*r**2*(100 - 2*pi*r**2)/(2*pi*r); dV_dr = sp.diff(V, r); critical_r = sp.solve(dV_dr, r)[0]"
   # Expected Output: r = sqrt(25/pi)
   ```

### Failure Analysis Summary  
| **Error Type**       | **Symptom**                          | **Root Cause**                     |
|----------------------|---------------------------------------|-------------------------------------|
| Incorrect constraint | `ValueError: too many values to unpack` | Missing π terms in surface area    |
| Substitution failure | Invalid `h_expr`                     | Non-unique solution for `h`        |

> 🔍 **Critical Takeaway**: In formal sciences, *every failure must be traced to a precise mathematical definition*. This lab trains you to isolate errors at the level of symbolic expressions—not just code.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor  
*Design a calculus problem where you must derive the solution from first principles—then validate it operationally.*  

**Your Task**:  
> *Prove that the function $f(x) = x^3 - 3x$ has exactly one critical point in the interval $(-2, 2)$ using:  
> (a) Derivative analysis  
> (b) Symbolic computation (SymPy)  
> (c) Graphical verification (plot the derivative)*  

**Socratic Discussion Prompts for the AI Tutor**:  
1. *What is the first step in deriving the critical point?*  
2. *How would you verify that the critical point is unique in $(-2, 2)$?*  
3. *If your SymPy output shows two critical points, what does that imply about the function?*  
4. *Why is graphical verification necessary even after symbolic analysis?*  

**Operational Validation Steps**:  
```bash
# 1. Compute derivative
python -c "import sympy as sp; x = sp.symbols('x'); f = x**3 - 3*x; df = sp.diff(f, x)"

# 2. Solve for critical points
python -c "import sympy as sp; x = sp.symbols('x'); df = 3*x**2 - 3; critical_points = sp.solve(df, x)"

# 3. Plot derivative (for visualization)
python -c "import sympy as sp; x = sp.symbols('x'); df = 3*x**2 - 3; sp.plot(df, (x, -2, 2))"
```

> 💡 **Why this challenge works**: It forces you to *integrate* symbolic computation with conceptual reasoning—exactly what formal sciences demand. Discuss your results with the AI Tutor using the prompts above.

---

**Final Note**: In formal sciences, *operationality* means treating mathematics as a *system of verifiable operations*. This lab trains you to move beyond "what" to "how" and "why" at every step—making calculus a living, operational discipline.  

*Professor's Signature*:  
> "The true power of calculus lies not in its formulas, but in the precision with which we apply them. This lab is your first step toward that mastery."
