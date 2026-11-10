# Hands-On Operational Lab: Algebra

## Objective & Prerequisites

**Objective**: To develop rigorous algebraic manipulation skills through systematic exploration, model construction, fault injection, and debugging in a formal mathematical context. Students will practice verifying algebraic identities, constructing symbolic models, and diagnosing errors in algebraic reasoning.

**Prerequisites**:
1. Basic understanding of algebraic structures (rings, fields, polynomials)
2. Familiarity with symbolic computation environments (Python with `sympy` library)
3. Proficiency in LaTeX for mathematical notation
4. Ability to trace logical dependencies in mathematical systems

> **Note**: Install `sympy` via `pip install sympy` before starting. All commands execute in a terminal environment.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify fundamental algebraic identities using symbolic computation.

**Verification Commands**:
```bash
python -c "from sympy import symbols, expand; a, b = symbols('a b'); expr = (a + b)**2; print(f'Expanded: {expand(expr)}')"
```

**Expected Output**:
```
Expanded: a**2 + 2*a*b + b**2
```

**Verification Commands** (for identity verification):
```bash
python -c "from sympy import symbols, expand; a, b = symbols('a b'); expr = (a + b)**3; print(f'Expanded: {expand(expr)}')"
```

**Expected Output**:
```
Expanded: a**3 + 3*a**2*b + 3*a*b**2 + b**3
```

**Why This Works**:  
The `expand()` function in `sympy` systematically applies the distributive property to polynomials. The output confirms the binomial theorem for $n=2$ and $n=3$ through explicit symbolic manipulation. This demonstrates how algebraic identities can be verified without prior assumptions.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Construct and solve a quadratic equation model with symbolic parameters.

**Step-by-Step Workflow**:

1. **Define symbolic variables**:
   ```bash
   python -c "from sympy import symbols; a, b, c, x = symbols('a b c x')"
   ```

2. **Build quadratic model**:
   ```bash
   python -c "from sympy import symbols, solve; a, b, c, x = symbols('a b c x'); equation = a*x**2 + b*x + c; print(f'Equation: {equation} = 0')"
   ```

3. **Solve for roots**:
   ```bash
   python -c "from sympy import symbols, solve; a, b, c, x = symbols('a b c x'); equation = a*x**2 + b*x + c; solutions = solve(equation, x); print(f'Solutions: {solutions}')"
   ```

4. **Deploy with concrete example** (solve $x^2 - 5x + 6 = 0$):
   ```bash
   python -c "from sympy import symbols, solve; x = symbols('x'); equation = x**2 - 5*x + 6; solutions = solve(equation, x); print(f'For x^2 - 5x + 6 = 0: {solutions}')"
   ```

**Expected Outputs**:
```
Equation: a*x**2 + b*x + c = 0
Solutions: [-b/(2*a) - sqrt(b**2 - 4*a*c)/(2*a), -b/(2*a) + sqrt(b**2 - 4*a*c)/(2*a)]
For x^2 - 5x + 6 = 0: [2, 3]
```

**Why This Works**:  
The symbolic solver (`solve()`) expresses roots in terms of coefficients using the quadratic formula. The concrete example demonstrates how abstract algebraic models map to specific numerical solutions. This workflow validates the model's correctness through both symbolic and numerical verification.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce and resolve algebraic errors in a symbolic model.

**Step 1: Inject Fault** (typo in variable name)
```bash
python -c "from sympy import symbols, solve; x = symbols('x'); y = symbols('y'); equation = y**2 - 5*y + 6; solutions = solve(equation, x); print(f'Faulty output: {solutions}')"
```

**Expected Output**:
```
Faulty output: []
```

**Step 2: Failure Analysis**  
The empty list (`[]`) occurs because:
1. The equation is defined in terms of `y` (`y**2 - 5*y + 6`)
2. The solver attempts to find solutions for `x` (which does not appear in the equation)
3. This violates the **domain consistency principle**: Variables in the equation must match the target variable for solution

**Step 3: Debugging**  
Correct the variable mismatch:
```bash
python -c "from sympy import symbols, solve; x = symbols('x'); equation = x**2 - 5*x + 6; solutions = solve(equation, x); print(f'Corrected output: {solutions}')"
```

**Expected Output**:
```
Corrected output: [2, 3]
```

**Why This Works**:  
The fix restores domain consistency by ensuring:
- The equation uses the same variable (`x`) as the target
- The solver operates within the defined algebraic structure
- The model remains valid under the constraints of the problem

**Key Insight**:  
Algebraic errors often stem from **variable misalignment** rather than computational errors. This exercise demonstrates how formal verification catches inconsistencies before they propagate.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Prove that for all real numbers $a$ and $b$, the identity $(a + b)^3 = a^3 + 3a^2b + 3ab^2 + b^3$ holds using algebraic manipulation.

**Socratic Discussion Prompts** (for AI Tutor interaction):

1. **Initial Expansion**:  
   *What is the first step in expanding $(a + b)^3$ without using the binomial theorem?*

2. **Term Identification**:  
   *How do we systematically identify the coefficients of $a^2b$ and $ab^2$ in the expansion?*

3. **Verification Strategy**:  
   *Why is it sufficient to verify this identity for $a = 0$ and $b = 1$ to prove it for all real numbers?*

4. **Formal Proof Structure**:  
   *What mathematical principles must we invoke to ensure the proof holds for all real $a, b$?*

**Expected AI Tutor Response Structure**:
```markdown
1. **Initial Expansion**:  
   Start with $(a + b)^3 = (a + b)(a + b)^2$. First expand $(a + b)^2$ using distributive property, then multiply by $(a + b)$.

2. **Term Identification**:  
   The coefficient of $a^2b$ comes from $a \cdot a \cdot b$ (3 permutations), and $ab^2$ from $b \cdot a \cdot b$ (3 permutations).

3. **Verification Strategy**:  
   This is insufficient for full proof. The identity holds for all reals only when we use the distributive property over all combinations.

4. **Formal Proof Structure**:  
   We must invoke the distributive property of multiplication over addition in $\mathbb{R}$, and the commutativity of multiplication to ensure all terms are accounted for.
```

**Why This Challenge Works**:  
This problem requires students to:
- Move beyond computational verification to *structural* understanding
- Connect algebraic manipulation to foundational axioms
- Develop critical questioning skills through Socratic dialogue
- Validate proofs using formal mathematical principles rather than computational tools

> **Tutor Note**: The AI will guide students through the proof step-by-step using LaTeX notation and formal logic, ensuring the solution adheres to the axioms of real numbers.

---

This lab provides a rigorous, operational framework for algebraic practice that bridges formal theory with hands-on verification. By focusing on systematic error analysis and symbolic modeling, students develop the intuition and precision required for advanced formal sciences work.
