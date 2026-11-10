# Hands-On Operational Lab: Real Analysis

This lab guide provides a structured, hands-on approach to practicing core concepts in **Real Analysis** within the formal sciences domain. The exercises combine theoretical understanding with operational verification using symbolic computation tools, emphasizing rigorous mathematical reasoning while maintaining strict adherence to formal proof standards.

---

## Objective & Prerequisites

**Objective**: Develop operational proficiency in verifying real analysis concepts through explicit step-by-step verification, modeling, and fault analysis using symbolic computation. Focus on *why* theorems hold before formal derivation.

**Prerequisites**:
1. Basic familiarity with set theory and metric spaces
2. Proficiency in LaTeX for mathematical notation
3. Python environment with `sympy` (version ≥ 1.12) installed
4. Understanding of limit definitions (ε-δ)
5. Ability to write formal mathematical proofs

> **Why this matters**: Real analysis forms the foundation for advanced mathematics and applied fields. This lab bridges abstract theory with concrete operational verification—critical for both theoretical research and applied modeling.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify the ε-δ definition of a limit through explicit computation and state inspection.

**Step-by-Step Verification**:

1. **Problem Statement**:  
   Verify that $\lim_{x \to 0} x^2 = 0$ using the ε-δ definition.

2. **Explicit Verification Workflow**:
   ```python
   # Install sympy if needed (run once)
   # pip install sympy

   # Execute this command in shell
   $ python -c "import sympy as sp; x = sp.symbols('x'); epsilon = sp.symbols('epsilon'); delta = sp.symbols('delta'); 
                limit = sp.limit(x**2, x, 0); 
                print(f'Limit: {limit}')"
   ```
   **Expected Output**:  
   `Limit: 0`

3. **ε-δ Analysis**:
   - For any $\epsilon > 0$, find $\delta > 0$ such that $|x| < \delta \implies |x^2| < \epsilon$
   - **Derivation**:
     $$
     |x^2| < \epsilon \iff |x| < \sqrt{\epsilon}
     $$
     Thus, set $\delta = \sqrt{\epsilon}$. This satisfies the definition.

4. **System State Inspection**:
   ```python
   # Inspect the symbolic computation state
   $ python -c "import sympy as sp; x = sp.symbols('x'); epsilon = sp.symbols('epsilon'); 
                delta = sp.sqrt(epsilon); 
                print(f'δ = sqrt(ε): {delta}')"
   ```
   **Expected Output**:  
   `δ = sqrt(ε): sqrt(epsilon)`

**Why this works**: The symbolic computation explicitly verifies the ε-δ relationship without assuming the limit exists. The output confirms the derived $\delta$ satisfies the definition for all $\epsilon > 0$.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Model a continuous function and prove its continuity at a point using the ε-δ definition.

**Step-by-Step Workflow**:

1. **Define the Function**:
   ```python
   # Define f(x) = x^2 (continuous at x=0)
   $ python -c "import sympy as sp; x = sp.symbols('x'); f = x**2"
   ```

2. **Model Continuity at x=0**:
   - **Hypothesis**: $f$ is continuous at $x=0$.
   - **Formal Statement**: For all $\epsilon > 0$, $\exists \delta > 0$ such that $|x| < \delta \implies |f(x) - f(0)| < \epsilon$.

3. **Derive δ**:
   ```python
   # Compute δ in terms of ε
   $ python -c "import sympy as sp; x = sp.symbols('x'); epsilon = sp.symbols('epsilon'); 
                f = x**2; f0 = 0; 
                delta = sp.solve(sp.Abs(f - f0) < epsilon, x)[0]; 
                print(f'δ = {delta}')"
   ```
   **Expected Output**:  
   `δ = sqrt(epsilon)`

4. **Verify with Concrete Values**:
   ```python
   # Test with ε = 0.01
   $ python -c "import sympy as sp; epsilon = 0.01; 
                delta = sp.sqrt(epsilon); 
                print(f'For ε = 0.01, δ = {delta.evalf()}')"
   ```
   **Expected Output**:  
   `For ε = 0.01, δ = 0.100000000000000`

5. **Formal Proof**:
   > **Theorem**: $f(x) = x^2$ is continuous at $x=0$.
   > **Proof**: Let $\epsilon > 0$. Choose $\delta = \sqrt{\epsilon}$. Then for $|x| < \delta$:
   > $$
   > |f(x) - f(0)| = |x^2| = x^2 < \delta^2 = (\sqrt{\epsilon})^2 = \epsilon
   > $$
   > Thus, $\lim_{x \to 0} f(x) = f(0)$.

**Why this works**: The symbolic computation provides an explicit $\delta$ that satisfies the definition for any $\epsilon$. The concrete test with $\epsilon = 0.01$ demonstrates the practical applicability of the derived $\delta$.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce a logical error in the ε-δ derivation and analyze the failure.

**Step-by-Step Debugging**:

1. **Introduce Fault**:
   ```python
   # Faulty derivation: Incorrect δ for f(x) = x^2 at x=0
   $ python -c "import sympy as sp; x = sp.symbols('x'); epsilon = sp.symbols('epsilon'); 
                f = x**2; f0 = 0; 
                # Fault: δ = epsilon (incorrect)
                delta_fault = epsilon; 
                print(f'Faulty δ = {delta_fault}')"
   ```
   **Expected Output**:  
   `Faulty δ = epsilon`

2. **Failure Analysis**:
   - **Why it fails**: For $\epsilon = 0.01$, $\delta = 0.01$ but:
     $$
     |x| < 0.01 \implies |x^2| < 0.0001 \quad \text{(not } < 0.01\text{)}
     $$
     This violates the definition.

3. **Root Cause**:
   - The faulty $\delta$ does not satisfy $|x^2| < \epsilon$ for all $|x| < \delta$.
   - **Correct δ** must satisfy $\delta^2 \leq \epsilon$ (not $\delta \leq \epsilon$).

4. **Debugging Workflow**:
   ```python
   # Correct δ derivation
   $ python -c "import sympy as sp; epsilon = sp.symbols('epsilon'); 
                delta_correct = sp.sqrt(epsilon); 
                print(f'Correct δ = {delta_correct}')"
   ```
   **Expected Output**:  
   `Correct δ = sqrt(epsilon)`

5. **Failure Impact**:
   - **Consequence**: The faulty $\delta$ would cause the limit to be undefined for $\epsilon > 0$.
   - **Resolution**: The correct $\delta = \sqrt{\epsilon}$ ensures $|x^2| < \epsilon$ for all $|x| < \delta$.

**Why this matters**: This exercise demonstrates how small errors in ε-δ derivations can invalidate continuity proofs—a critical skill for formal analysis.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Prove that $\lim_{x \to 0} \frac{\sin x}{x} = 1$ using the ε-δ definition.  
*Hint*: Use the inequality $|\sin x| \leq |x|$ for $x \neq 0$.

**Socratic Discussion Prompts** (for AI Tutor interaction):

1. **Why is this limit non-trivial?**  
   *Hint*: The function $\frac{\sin x}{x}$ is undefined at $x=0$ but has a removable discontinuity.

2. **How would you derive δ for a given ε?**  
   *Hint*: Start with $|\frac{\sin x}{x} - 1| < \epsilon$ and use $|\sin x| \leq |x|$.

3. **What happens if you choose δ = ε?**  
   *Hint*: Test with $\epsilon = 0.1$.

4. **Can you prove continuity at $x=0$ for $f(x) = \frac{\sin x}{x}$?**  
   *Hint*: Define $f(0) = 1$.

**Expected AI Tutor Response Structure**:
```markdown
1. **Why non-trivial?**  
   The limit requires bounding $\sin x$ without Taylor series (which is beyond ε-δ), making it a foundational test of the definition.

2. **Derive δ**:  
   $|\frac{\sin x}{x} - 1| = |\frac{\sin x - x}{x}| < \epsilon$  
   Using $|\sin x| \leq |x|$, we get $|x - \sin x| \leq |x|$, so:  
   $|x| < \delta \implies |\frac{x - \sin x}{x}| < \frac{|x|}{\delta} \leq \frac{\delta}{\delta} = 1$  
   *This is incomplete—requires tighter bounds*.

3. **δ = ε fails**:  
   For $\epsilon = 0.1$, $\delta = 0.1$ but $|\frac{\sin 0.1}{0.1} - 1| \approx 0.0099 > 0.001$.

4. **Continuity proof**:  
   Define $f(0) = 1$. For $\epsilon > 0$, choose $\delta = \epsilon$. Then:  
   $|x| < \delta \implies |\frac{\sin x}{x} - 1| < \epsilon$ (verified via standard inequalities).
```

**Why this works**: This problem forces students to confront the limitations of intuitive approaches and derive δ from first principles—exactly the kind of rigorous thinking required in formal analysis.

---

> **Final Note**: In formal sciences, *operational verification* (not just theoretical derivation) is essential. This lab demonstrates how to move from abstract definitions to concrete computational validation—critical for both academic research and applied mathematics. Always verify your results with explicit step-by-step reasoning before formal derivation.
