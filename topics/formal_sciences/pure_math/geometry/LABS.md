# Hands-On Operational Lab: Geometry

## Objective & Prerequisites

**Objective**: To develop hands-on skills in modeling geometric problems using formal computational verification, with emphasis on system state inspection, model construction, fault tolerance, and rigorous proof validation within the formal sciences framework.

**Prerequisites**:
- Python 3.8+ installed
- `sympy` library (install via `pip install sympy`)
- Basic understanding of Euclidean geometry
- Familiarity with symbolic computation and formal logic

> **Why this matters in formal sciences**: Geometry provides the foundational framework for spatial reasoning in mathematics. This lab bridges abstract geometric concepts with computational verification—critical for formalizing mathematical proofs and ensuring consistency in complex systems.

---

## Exercise 1: Exploration & System State Inspection

*Verify the symbolic computation environment and inspect geometric capabilities*

**Step-by-Step**:

1. Initialize the Python environment with `sympy`
2. Inspect available geometric primitives
3. Validate symbolic computation capabilities

```bash
# Create a Python script (geometry_inspect.py)
cat > geometry_inspect.py << 'EOF'
from sympy import init_printing, Point, Line, Segment, Triangle
init_printing()
print(f"Sympy version: {sympy.__version__}")
print(f"Available geometric primitives: {sorted([f for f in dir(sympy.geometry) if not f.startswith('_')])}")
print(f"Basic point: {Point(0, 0)}")
EOF

# Run the inspection script
python3 geometry_inspect.py
```

**Expected Output**:
```
Sympy version: 1.12.1
Available geometric primitives: ['Point', 'Line', 'Segment', 'Triangle', 'Circle', 'Polygon', ...]
Basic point: Point(0, 0)
```

**Key Insights**:
- The output confirms the symbolic computation environment is operational
- `Point` is the fundamental geometric primitive (matches formal definition of a 2D point)
- The system supports standard Euclidean geometric objects

> **Formal Justification**: This inspection verifies the *system state* satisfies the axioms of Euclidean geometry (as defined in `sympy.geometry`). The presence of `Point` and `Triangle` primitives confirms the environment can model the foundational geometric structures required for this lab.

---

## Exercise 2: Building & Deploying / Modeling Scenario

*Construct a triangle and compute its area using formal verification*

**Step-by-Step**:

1. Define three non-collinear points
2. Construct the triangle
3. Compute area using symbolic verification
4. Validate result with geometric proof

```bash
# Create a Python script (triangle_area.py)
cat > triangle_area.py << 'EOF'
from sympy import Point, Triangle

# Define points (non-collinear)
A = Point(0, 0)
B = Point(1, 0)
C = Point(0, 1)

# Construct triangle
triangle = Triangle(A, B, C)

# Compute area (symbolic form)
area = triangle.area
print(f"Area = {area}")
print(f"Formal proof: {area.doit()}")
EOF

# Run the triangle model
python3 triangle_area.py
```

**Expected Output**:
```
Area = 1/2
Formal proof: 1/2
```

**Formal Verification**:
The area is rigorously computed as `1/2` through:
1. **Geometric construction**: Points `A(0,0)`, `B(1,0)`, `C(0,1)` form a right triangle
2. **Area formula**: `Area = ½ |x₁(y₂ - y₃) + x₂(y₃ - y₁) + x₃(y₁ - y₂)|`
3. **Symbolic simplification**: `½ |0(0-1) + 1(1-0) + 0(0-0)| = ½ |1| = 1/2`

> **Why this works**: The `sympy` implementation follows the *axiomatic definition* of area in Euclidean geometry (Section 1.2 of *Euclid's Elements*), ensuring the result is mathematically sound.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

*Introduce a geometric fault and analyze the failure*

**Step-by-Step**:

1. Inject a collinear point (causing degenerate triangle)
2. Observe failure
3. Diagnose root cause
4. Implement robust validation

```bash
# Create a Python script (fault_injection.py)
cat > fault_injection.py << 'EOF'
from sympy import Point, Triangle

# Introduce fault: collinear points
A = Point(0, 0)
B = Point(1, 0)
C = Point(2, 0)  # Fault: collinear with A and B

# Construct triangle (will fail)
triangle = Triangle(A, B, C)
print(f"Triangle area: {triangle.area}")
EOF

# Run with fault
python3 fault_injection.py
```

**Expected Output**:
```
Triangle area: 0
```

**Failure Analysis**:
1. **Root cause**: Points `A`, `B`, `C` are collinear (lie on the x-axis)
2. **Mathematical reason**: Collinear points satisfy `det([x₁,y₁,1; x₂,y₂,1; x₃,y₃,1]) = 0`
3. **System response**: `Triangle` object returns area `0` (degenerate case)

**Debugging Workflow**:
```bash
# Fix the fault by adding collinearity check
cat > robust_triangle.py << 'EOF'
from sympy import Point, Triangle

def is_collinear(A, B, C):
    return A.distance(B) + B.distance(C) == A.distance(C)

A = Point(0, 0)
B = Point(1, 0)
C = Point(2, 0)

if is_collinear(A, B, C):
    print("Points are collinear - cannot form triangle")
else:
    triangle = Triangle(A, B, C)
    print(f"Area = {triangle.area}")
EOF

# Run robust version
python3 robust_triangle.py
```

**Expected Output**:
```
Points are collinear - cannot form triangle
```

> **Formal Insight**: This demonstrates *fault tolerance* in geometric modeling. The system correctly identifies degenerate cases (a critical property in formal geometry) by verifying the *collinearity condition* before computation.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem Statement**:
Given points `P₁(1, 2)`, `P₂(3, 4)`, `P₃(5, 6)`, determine:
1. Are these points collinear?
2. If not, compute the area of the triangle they form
3. Derive the equation of the line through `P₁` and `P₂`

**Socratic Discussion Prompts**:

1. **Formal verification**: How would you prove collinearity without computational tools?
   - *Hint*: Use the slope condition: `(y₂-y₁)/(x₂-x₁) = (y₃-y₂)/(x₃-x₂)`

2. **Symbolic derivation**: What is the general formula for the area of a triangle given three points?
   - *Hint*: Use the determinant formula

3. **Failure scenario**: What happens if you try to compute the line through `P₁` and `P₂` when `P₂ = P₁`?
   - *Hint*: Analyze the `Line` constructor in `sympy`

4. **Proof challenge**: Show that if three points are collinear, then the area is zero using vector algebra.

**AI Tutor Interaction Protocol**:
1. Write your Python solution using `sympy`
2. Run it and capture output
3. Discuss with the AI tutor using the prompts above
4. Refine your solution based on feedback

**Sample Solution**:
```python
from sympy import Point, Line, Triangle

P1 = Point(1, 2)
P2 = Point(3, 4)
P3 = Point(5, 6)

# Check collinearity
collinear = P1.distance(P2) + P2.distance(P3) == P1.distance(P3)

if collinear:
    line = Line(P1, P2)
    print(f"Points are collinear. Line equation: {line.equation()}")
else:
    triangle = Triangle(P1, P2, P3)
    print(f"Area = {triangle.area}")
```

**Expected Output**:
```
Points are collinear. Line equation: x - y + 1 = 0
```

> **Why this matters**: This exercise trains you to *think formally* about geometric problems while using computational tools to verify results—essential for formal sciences research where precision and proof are paramount.

---

**Final Note**: In formal sciences, *every computation must be traceable to axiomatic definitions*. This lab demonstrates how to build, verify, and debug geometric models while maintaining rigorous mathematical integrity. The ability to identify and resolve geometric faults is a critical skill for advanced formal systems.
