# Hands-On Operational Lab: Complex Analysis

## Objective & Prerequisites

**Objective**: To develop rigorous operational proficiency in visualizing and computing complex functions through interactive exploration, with emphasis on *mathematical intuition* and *formal verification* of complex analytic properties. This lab bridges theoretical understanding with computational practice in the formal sciences domain.

**Prerequisites**:
1. Proficiency in basic complex numbers ($z = x + iy$)
2. Understanding of analytic functions, contour integration, and singularities
3. Python 3.x environment with `numpy` and `matplotlib` installed
4. Familiarity with LaTeX notation for mathematical expressions

> **Why this matters in formal sciences**: Complex analysis provides the foundation for advanced topics in quantum mechanics, fluid dynamics, and number theory. This lab ensures you can *operationally verify* theoretical properties through computational means while maintaining rigorous mathematical integrity.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify the computational environment and observe basic complex function behavior through explicit verification commands.

**Step-by-Step**:
1. Initialize a minimal Python environment with complex number operations:
```bash
python -c "import numpy as np; z = np.complex(1, 1); print(f'z = {z} | |z| = {np.abs(z)} | arg(z) = {np.angle(z)}')"
```

2. Generate a grid of complex numbers and compute real/imaginary parts:
```bash
python -c "import numpy as np; x = np.linspace(-2, 2, 100); y = np.linspace(-2, 2, 100); X, Y = np.meshgrid(x, y); Z = X + 1j*Y; U = np.real(Z**2); V = np.imag(Z**2); print(f'U shape: {U.shape} | V shape: {V.shape}')"
```

**Expected Output**:
```
z = (1+1j) | |z| = 1.4142135623730951 | arg(z) = 0.7853981633974483
U shape: (100, 100) | V shape: (100, 100)
```

**Verification & Why It Matters**:
- The output confirms:
  - Complex modulus $|z| = \sqrt{x^2 + y^2}$
  - Argument $\arg(z) = \tan^{-1}(y/x)$
  - Grid dimensions match expected 2D complex plane representation
- **Formal significance**: This verifies the computational environment adheres to the *algebraic structure* of $\mathbb{C}$, ensuring subsequent visualizations maintain mathematical validity.

> **Critical Insight**: The output demonstrates that complex arithmetic operations in Python *strictly follow* the formal axioms of complex numbers (field properties), which is essential for reliable modeling.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Construct a visual model of $f(z) = e^z$ with interactive exploration capabilities.

**Step-by-Step Workflow**:

1. Create `complex_analysis_model.py` with the following content:
```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Generate complex grid
x = np.linspace(-2, 2, 100)
y = np.linspace(-2, 2, 100)
X, Y = np.meshgrid(x, y)
Z = X + 1j * Y

# Compute function values
F = np.exp(Z)  # f(z) = e^z
U = np.real(F)  # Real part
V = np.imag(F)  # Imaginary part

# Plot real part with color mapping
plt.figure(figsize=(10, 8))
plt.imshow(U, extent=[-2, 2, -2, 2], cmap='plasma', aspect='auto')
plt.colorbar(label=r'Re(e^z)')
plt.title(r'Real Part of $e^z$')
plt.xlabel(r'Re(z)')
plt.ylabel(r'Im(z)')
plt.tight_layout()
plt.savefig('real_part_ez.png')

# Plot imaginary part with contour lines
plt.figure(figsize=(10, 8))
plt.contourf(X, Y, V, levels=20, cmap=cm.viridis)
plt.colorbar(label=r'Im(e^z)')
plt.title(r'Imaginary Part of $e^z$')
plt.xlabel(r'Re(z)')
plt.ylabel(r'Im(z)')
plt.tight_layout()
plt.savefig('imag_part_ez.png')

print("Model built successfully. Output files saved: real_part_ez.png, imag_part_ez.png")
```

2. Deploy the model:
```bash
python complex_analysis_model.py
```

**Expected Output**:
- Two PNG files generated:
  - `real_part_ez.png`: Color plot showing exponential growth in the right half-plane
  - `imag_part_ez.png`: Contour plot revealing periodicity with period $2\pi$ in the imaginary direction

**Why This Works Mathematically**:
- $e^z = e^x (\cos y + i \sin y)$
- Real part: $e^x \cos y$ → *exponential growth* in $x$ direction
- Imaginary part: $e^x \sin y$ → *periodic oscillations* with period $2\pi$ in $y$
- **Formal verification**: The contour plot explicitly shows the periodicity $\sin(y + 2\pi) = \sin y$ for fixed $x$, confirming the analytic continuation properties of $e^z$.

> **Key Insight**: This model demonstrates how *computational visualization* directly reveals the *analytic structure* of complex functions – a critical skill for formal verification in complex analysis.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce a controlled failure in the model and analyze the root cause.

**Step-by-Step**:

1. Inject a fault into `complex_analysis_model.py` (line 7):
```python
# FAULT INJECTION: Incorrect complex grid generation
# Original: Z = X + 1j * Y
Z = X + 1j * Y.real  # Intentional error: using real part of Y
```

2. Run the model:
```bash
python complex_analysis_model.py
```

**Expected Failure Output**:
```
Traceback (most recent call last):
  File "complex_analysis_model.py", line 7, in <module>
    Z = X + 1j * Y.real
TypeError: 'numpy.ndarray' object is not callable
```

3. Analyze the failure:
- **Root Cause**: `Y.real` returns a 2D array of real values (not a function), but the code attempts to call it as a function (`1j * Y.real`).
- **Mathematical Implication**: This violates the *complex field axioms* – the grid must represent complex numbers, not real numbers.

4. Fix the error:
```python
# CORRECTED LINE
Z = X + 1j * Y  # Y is already a complex array
```

5. Verify the fix:
```bash
python complex_analysis_model.py
```

**Failure Analysis Summary**:
| Component          | Failure Mode                     | Mathematical Consequence                     |
|---------------------|-----------------------------------|----------------------------------------------|
| Complex Grid        | Real part used instead of complex | Loss of imaginary component → non-analytic function |
| Field Axioms        | Violation of $z = x + iy$       | Breaks complex linearity and additivity      |

> **Critical Lesson**: In formal sciences, *computational errors* often stem from *structural violations* of mathematical definitions. This exercise demonstrates how to trace failures back to foundational axioms.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Prove that the function $f(z) = \frac{1}{z}$ has a *simple pole* at $z=0$ and compute its residue.

**Socratic Discussion Prompts** (for AI Tutor interaction):

1. **Formal Verification**:  
   > "Show that $f(z)$ fails the Cauchy-Riemann equations at $z=0$ while satisfying them elsewhere. How does this relate to the pole type?"

2. **Series Expansion**:  
   > "Derive the Laurent series expansion of $f(z)$ around $z=0$. Why does this series *not* converge to $f(z)$ for all $z$?"

3. **Residue Significance**:  
   > "What is the physical interpretation of the residue in the context of contour integration? How does it connect to the *residue theorem*?"

4. **Formal Proof**:  
   > "Prove that $\text{Res}(f, 0) = 1$ using the definition of residue for simple poles. Show all steps with rigorous justification."

**Why This Matters**:  
This problem requires *operational verification* of complex analytic properties through both algebraic manipulation and series expansion – the core of complex analysis. The AI Tutor will guide you through formal proofs while maintaining mathematical rigor.

> **Professor's Note**: In formal sciences, the *most valuable insight* comes from understanding *why* a computational failure occurs at the level of mathematical definitions. This challenge forces you to bridge the gap between computation and theory.

---

**Final Verification**:  
All exercises maintain strict adherence to complex analysis axioms while providing actionable computational workflows. The lab demonstrates that *formal verification* in complex analysis requires both mathematical precision and computational discipline. 

> "The true power of complex analysis lies not in computation alone, but in the *operational verification* of mathematical truths through both symbolic reasoning and computational exploration."  
> — *Professor of Mathematics and Formal Logic*
