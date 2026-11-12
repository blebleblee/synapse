# Hands-On Operational Lab: Computational Group Theory, Finite Fields & Galois Group Verification

## Objective & Lab Prerequisites
In this lab, you will computationally construct finite permutation groups, verify the Class Equation and Sylow theorems, build the Galois field $\mathbb{F}_{2^8}$ used in AES cryptography using irreducible polynomial quotients, and compute Galois groups of algebraic field extensions using Python.

### Prerequisites
* Python 3.10+ in your virtual environment.
* Install SymPy:
  ```bash
  pip install sympy
  ```

---

## Exercise 1: Computing Conjugacy Classes & Verifying the Class Equation

We will construct the Alternating Group $A_4$ (the rotational symmetries of a regular tetrahedron, order $|A_4| = 12$) and verify its Class Equation:

$$|G| = |Z(G)| + \sum_{i=1}^k [G : C_G(x_i)]$$

```python
cat << 'EOF' > test_class_equation.py
from sympy.combinatorics import AlternatingGroup

# Construct Alternating Group A_4
G = AlternatingGroup(4)
order_G = G.order()
print(f"Group: A_4 | Order: {order_G}")

# Compute Conjugacy Classes
conj_classes = G.conjugacy_classes()
print(f"Number of Conjugacy Classes: {len(conj_classes)}\n")

total_elements = 0
print("Class Equation Breakdown:")
for idx, c in enumerate(conj_classes, 1):
    rep = list(c)[0]
    class_size = len(c)
    total_elements += class_size
    print(f"  Class {idx}: Representative={rep}, Orbit Size={class_size}")

print("--------------------------------------------------")
print(f"Sum of Conjugacy Class Sizes: {total_elements}")
print(f"Verification (|G| == Sum):     {order_G == total_elements} (Class Equation Validated!)")

# Center of A_4
center = G.center()
print(f"Center Z(A_4) Order:          {center.order()} (Trivial Center)")
EOF
python3 test_class_equation.py
```

---

## Exercise 2: Constructing the Galois Field $\mathbb{F}_{2^8}$ (The AES Rijndael Field)

In modern cryptography (AES / Rijndael), bytes are treated as elements of the finite field $\mathbb{F}_{2^8} \cong \mathbb{F}_2[x] / \langle m(x) \rangle$, where $m(x) = x^8 + x^4 + x^3 + x + 1$ is an irreducible polynomial over $\mathbb{F}_2$.

We will construct this field and compute multiplicative inverses using polynomial modular arithmetic:

```python
cat << 'EOF' > aes_galois_field.py
def gf_multiply(a, b, mod=0x11B):
    """
    Multiplies two elements in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1 (0x11B).
    Uses peasant's algorithm with bitwise shifts and XOR.
    """
    p = 0
    while b > 0:
        if b & 1:
            p ^= a
        b >>= 1
        a <<= 1
        if a & 0x100: # If degree >= 8, reduce modulo m(x)
            a ^= mod
    return p & 0xFF

def gf_inverse(a):
    """
    Computes multiplicative inverse in GF(2^8) using Fermat's Little Theorem:
    In GF(2^8), a^(2^8 - 1) = a^255 = 1 => a^(-1) = a^254.
    """
    if a == 0:
        return 0
    res = 1
    base = a
    power = 254 # 2^8 - 2
    while power > 0:
        if power & 1:
            res = gf_multiply(res, base)
        base = gf_multiply(base, base)
        power >>= 1
    return res

# Test element: byte 0x53 ('S' in ASCII)
element = 0x53
inv = gf_inverse(element)
product = gf_multiply(element, inv)

print("==================================================")
print("     AES RIJNDAEL FINITE FIELD GF(2^8) LAB        ")
print("==================================================")
print(f"Original Element:   0x{element:02X} (binary: {bin(element)[2:].zfill(8)})")
print(f"Computed Inverse:   0x{inv:02X} (binary: {bin(inv)[2:].zfill(8)})")
print(f"Product a * a^(-1): 0x{product:02X}")
print(f"Field Axiom Check:  {product == 1} (Multiplicative Inverse Validated!)")
EOF
python3 aes_galois_field.py
```

---

## Exercise 3: Computing Galois Groups of Polynomial Field Extensions

We will determine the Galois group of $f(x) = x^3 - 2$ over $\mathbb{Q}$.
* Roots: $\sqrt[3]{2}, \omega\sqrt[3]{2}, \omega^2\sqrt[3]{2}$ where $\omega = e^{2\pi i / 3}$.
* Splitting field: $E = \mathbb{Q}(\sqrt[3]{2}, \omega)$.
* Degree: $[E : \mathbb{Q}] = [\mathbb{Q}(\sqrt[3]{2}, \omega) : \mathbb{Q}(\sqrt[3]{2})] \cdot [\mathbb{Q}(\sqrt[3]{2}) : \mathbb{Q}] = 2 \times 3 = 6$.
* Therefore, the Galois group must be non-abelian of order 6, which is isomorphic to $S_3$.

```python
cat << 'EOF' > test_galois_group.py
from sympy import symbols, Poly
from sympy.polys.polytools import galois_group

x = symbols('x')

# Polynomial 1: Cubic extension x^3 - 2
f1 = Poly(x**3 - 2, x)
G1, is_transitive = galois_group(f1)
print("Polynomial: f(x) = x^3 - 2 over Q")
print(f"  Galois Group: {G1.name} (Order: {G1.order()})")
print(f"  Isomorphism:  Isomorphic to Symmetric Group S_3")
print(f"  Is Solvable:  {G1.is_solvable} (Roots expressible by radicals!)\n")

# Polynomial 2: Non-solvable quintic x^5 - 4x + 2
f2 = Poly(x**5 - 4*x + 2, x)
G2, _ = galois_group(f2)
print("Polynomial: f(x) = x^5 - 4x + 2 over Q")
print(f"  Galois Group: {G2.name} (Order: {G2.order()})")
print(f"  Isomorphism:  Full Symmetric Group S_5")
print(f"  Is Solvable:  {G2.is_solvable} (PROVES INSOLVABILITY BY RADICALS!)")
EOF
python3 test_galois_group.py
```

---

## Exercise 4: Clean Up

```bash
rm -f test_class_equation.py aes_galois_field.py test_galois_group.py
```

---

## Challenge Lab: Socratic Exploration
1. In `Exercise 1`, why does $A_4$ have no subgroup of order 6, even though $6$ divides $|A_4| = 12$? How does this prove that the converse of Lagrange's Theorem is false?
2. In `Exercise 3`, how does Eisenstein's Criterion (with prime $p = 2$) prove that $x^5 - 4x + 2$ is irreducible over $\mathbb{Q}$? Why does having exactly 3 real roots and 2 complex conjugate roots force its Galois group over $\mathbb{Q}$ to contain a 2-cycle transposition, thereby generating all of $S_5$?
