# Hands-On Operational Lab: Trigonometry  
*Formal Sciences | Pure Mathematics*  

---

## Objective & Prerequisites  
**Objective**: Develop rigorous operational proficiency in trigonometric identities, geometric modeling, and error analysis through structured computational verification. Students will transform abstract mathematical concepts into executable workflows while maintaining formal precision.  

**Prerequisites**:  
1. Basic familiarity with Python programming (version ≥ 3.8)  
2. Understanding of Euclidean geometry and trigonometric functions (sine, cosine, tangent)  
3. Proficiency in symbolic manipulation (e.g., `sympy` library)  
4. Access to a Unix-like shell (or WSL for Windows) with `python3` installed  

> 💡 *Why this matters*: Trigonometry bridges abstract geometry and computational modeling. This lab operationalizes formal proofs through executable verification—critical for fields like computational physics, cryptography, and algorithmic geometry.

---

## Exercise 1: Exploration & System State Inspection  
*Verify foundational trigonometric identities using symbolic computation*  

**Goal**: Confirm core identities via direct symbolic evaluation to establish a consistent computational baseline.  

**Step-by-Step Workflow**:  
1. Create a Python script `trig_base.py` with the following content:  
```python
import sympy as sp

# Define symbolic variables
theta = sp.symbols('theta')

# Core identities to verify
identity1 = sp.sin(theta)**2 + sp.cos(theta)**2 - 1
identity2 = sp.tan(theta) - sp.sin(theta)/sp.cos(theta)
identity3 = sp.sin(2*theta) - 2*sp.sin(theta)*sp.cos(theta)

# Evaluate identities (should return 0 for all)
results = {
    "Identity 1 (Pythagorean)": sp.simplify(identity1),
    "Identity 2 (Tangent definition)": sp.simplify(identity2),
    "Identity 3 (Double-angle)": sp.simplify(identity3)
}

# Print results in LaTeX format for formal verification
print("Verified identities (symbolic simplification):")
for name, expr in results.items():
    print(f"\\[ {sp.latex(expr)} \\]")
```

2. Execute the script in the shell:  
```bash
python3 trig_base.py
```

**Expected Output** (with LaTeX formatting):  
```
Verified identities (symbolic simplification):
\[ 0 \]
\[ 0 \]
\[ 0 \]
```

**Why this works**:  
- `sympy` performs symbolic simplification (not numerical evaluation) to maintain mathematical rigor.  
- The output confirms all identities reduce to `0`—a formal proof that the identities hold *for all* `θ` (where defined).  
- **Critical insight**: This avoids numerical approximation errors (e.g., `sin(0.1) ≈ 0.0998` vs. exact `0.1`).

> ✅ *System State Check*: Your environment is ready if the output matches the LaTeX expressions above. If not, reinstall `sympy` with `pip install sympy`.

---

## Exercise 2: Building & Deploying / Modeling Scenario  
*Model a triangle using the Law of Cosines and validate with the Law of Sines*  

**Goal**: Construct a geometric model of a triangle with known sides and verify angle relationships through formal computation.  

**Step-by-Step Workflow**:  
1. Create a Python script `triangle_model.py` with:  
```python
import sympy as sp

# Define symbolic variables
a, b, c, theta = sp.symbols('a b c theta')

# Given: Triangle with sides a=3, b=4, angle θ=60° (radians: π/3)
a_val = 3
b_val = 4
theta_val = sp.pi / 3

# Law of Cosines: c² = a² + b² - 2ab·cos(θ)
c_expr = sp.sqrt(a_val**2 + b_val**2 - 2*a_val*b_val*sp.cos(theta_val))

# Law of Sines: sin(α)/a = sin(β)/b = sin(γ)/c
alpha = sp.symbols('alpha')
beta = sp.symbols('beta')
gamma = sp.symbols('gamma')

# Solve for angle α using Law of Sines
sin_alpha = (a_val * sp.sin(theta_val)) / c_expr
alpha_expr = sp.asin(sin_alpha)

# Print results in LaTeX
print(f"Side c (Law of Cosines): \\[ c = {sp.latex(c_expr)} \\]")
print(f"Angle α (Law of Sines): \\[ \\alpha = {sp.latex(alpha_expr)} \\]")
```

2. Execute the script:  
```bash
python3 triangle_model.py
```

**Expected Output**:  
```
Side c (Law of Cosines): [ c = \sqrt{7} ]
Angle α (Law of Sines): [ \alpha = \arcsin\left(\frac{3}{\sqrt{7}}\right) ]
```

**Why this works**:  
- The Law of Cosines computes side `c` *exactly* (not numerically) using symbolic math.  
- The Law of Sines gives angle `α` as an inverse sine expression—preserving formal precision.  
- **Critical insight**: This workflow validates *both* laws simultaneously through a single computational model, avoiding ad-hoc approximations.

> 🔍 *System State Check*: If output shows numerical values (e.g., `c ≈ 2.6458`), your environment is using numerical evaluation instead of symbolic. Re-run with `sp.simplify()` on all expressions to enforce symbolic mode.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging  
*Introduce a common error and debug using formal verification*  

**Goal**: Identify and resolve a critical error in trigonometric modeling by analyzing symbolic inconsistencies.  

**Step-by-Step Workflow**:  
1. Create a broken script `triangle_fault.py` with a *known error*:  
```python
import sympy as sp

a, b, c = sp.symbols('a b c')
theta = sp.pi / 3  # 60 degrees (radians)

# Fault: Using degrees instead of radians (critical error!)
c_expr = sp.sqrt(a**2 + b**2 - 2*a*b*sp.cos(theta*180/sp.pi))  # ❌ Wrong unit conversion
```

2. Execute the script:  
```bash
python3 triangle_fault.py
```

**Expected Failure**:  
```
ValueError: The argument must be a number or a symbolic expression with a known value.
```

**Failure Analysis & Debugging**:  
1. **Identify the error**: `theta*180/sp.pi` converts radians to degrees—*but `sp.pi` is symbolic*, so `theta*180/sp.pi` evaluates to `60` (a number), not `π/3`.  
2. **Formal verification**:  
   - Correct unit: `theta` must remain in *radians* (e.g., `sp.pi/3`).  
   - Why it fails: `sp.cos` expects *radians* (not degrees). The error converts `θ` to degrees *before* trigonometric evaluation.  
3. **Fix the script**:  
   ```python
   c_expr = sp.sqrt(a**2 + b**2 - 2*a*b*sp.cos(theta))  # ✅ Radians preserved
   ```
4. **Re-run verification**:  
   ```bash
   python3 triangle_fault_fixed.py
   ```

**Why this matters**:  
- This error demonstrates how *unit consistency* breaks formal proofs in computational models.  
- **Formal lesson**: In pure mathematics, trigonometric functions are defined for *radians* (not degrees). Computational implementation must respect this domain constraint.

> 💡 *Debugging tip*: Always check the *domain* of trigonometric functions in symbolic contexts. Use `sp.simplify()` to validate expressions before numerical evaluation.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor  
*Design a problem requiring formal proof and computational verification*  

**Problem Statement**:  
> Prove that for any triangle with sides `a`, `b`, `c` and angles `α`, `β`, `γ` (opposite to sides `a`, `b`, `c`), the following identity holds:  
> $$\frac{a}{\sin \alpha} = \frac{b}{\sin \beta} = \frac{c}{\sin \gamma} = 2R$$  
> where `R` is the circumradius.  
>  
> **Your task**:  
> 1. Derive this identity using the Law of Sines.  
> 2. Implement a Python script that:  
>    - Takes `a`, `b`, `c` as inputs (in symbolic form)  
>    - Computes `R` using the formula $R = \frac{a}{2\sin \alpha}$  
>    - Verifies that $R$ is consistent across all three sides (i.e., $\frac{a}{2\sin \alpha} = \frac{b}{2\sin \beta} = \frac{c}{2\sin \gamma}$)  
> 3. Submit your script and expected output to the AI Tutor for analysis.  

**Socratic Discussion Prompts for the AI Tutor**:  
1. *Why does the circumradius `R` appear in the Law of Sines?*  
2. *How would you modify the script to handle degenerate triangles (e.g., `α = 0`)?*  
3. *What happens if the input angles don't satisfy the triangle inequality?*  

> 🌟 *Why this challenges you*: This problem forces you to bridge abstract geometry with computational constraints—exactly where formal sciences meet real-world implementation.

---

**Professor's Note**:  
> "Trigonometry is not merely a set of formulas—it is a language for describing relationships between quantities. In this lab, you've transformed that language into executable operations. Remember: *Every computational model is a formal proof in disguise*. When you debug a trigonometric error, you're not just fixing code—you're preserving mathematical truth."  

*— Dr. A. Thorne, Professor of Mathematics and Formal Logic*
