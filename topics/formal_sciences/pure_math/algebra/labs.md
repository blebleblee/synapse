# Operational Verification Labs: Algebra

## Objective & Mathematical Computing Setup

These operational verification labs bridge the gap between abstract algebraic theory and computational reality. You will execute symbolic computations to verify fundamental algebraic theorems, stress-test boundary cases that expose structural singularities, and implement concrete algorithmic representations of formal algebraic structures. The goal is not merely to accept algebraic propositions on authority, but to construct computational proofs that mechanically verify group homomorphisms, ring ideals, field extensions, and polynomial factorizations through symbolic execution engines.

The verification environment demands Python 3.11 or higher with a robust symbolic algebra stack. Install SymPy for symbolic computation, NumPy for numerical linear algebra support, and optionally SageMath for advanced number-theoretic operations. The SymPy library provides a pure-Python computer algebra system capable of symbolic manipulation, equation solving, polynomial arithmetic, and abstract algebraic structure definitions. SageMath extends this with GAP integration for group theory and PARI/GP for number-theoretic computations. For formal proof verification beyond symbolic computation, Lean 4 or Coq provide dependent type systems where algebraic propositions become provable theorems through constructive logic.

Install the core symbolic algebra environment with the following sequence. First, ensure Python 3.11+ is active in your shell environment. Execute `python --version` to confirm. Then install SymPy and NumPy through the package manager: `pip install sympy numpy matplotlib`. Verify the installation by launching a Python interpreter and importing the core modules: `python -c 'import sympy; import numpy; print(f"SymPy {sympy.__version__}, NumPy {numpy.__version__}")'`. You should observe version strings indicating SymPy 1.12+ and NumPy 1.24+. For SageMath, the installation depends on your operating system. On Linux, use the distribution package manager: `sudo apt install sagemath` on Debian-based systems or `brew install --cask sage` on macOS. On Windows, download the SageMath Windows installer from the official repository. Verify SageMath installation by executing `sage --version` in your terminal.

For formal proof assistant integration, install Lean 4 through the elan version manager. Execute `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh` on Unix-like systems, then restart your shell to activate the environment. Create a new Lean project with `lake new algebra_verification` and navigate into the directory. Open the `lakefile.lean` configuration and add the Mathlib dependency: `require mathlib from git "https://github.com/leanprover-community/mathlib4"`. Build the project with `lake build` to fetch and compile Mathlib, which provides formalized definitions of groups, rings, fields, and verified theorems. Coq installation follows a similar pattern: install through OPAM with `opam install coq` and verify with `coqc --version`. The Mathematical Components library provides formalized algebra: `opam install coq-mathcomp-ssreflect coq-mathcomp-algebra`.

The verification workflow alternates between symbolic computation in SymPy for exploratory calculations and formal proof construction in Lean or Coq for mechanized verification. Use SymPy to compute examples, test conjectures, and identify counterexamples. Once a property is computationally verified across test cases, translate the mathematical statement into a formal theorem in Lean or Coq and construct a proof term that the type checker mechanically verifies. This dual approach builds intuition through computation while maintaining the rigor of formal proof.

## Exercise 1: Computational Verification of Core Theorems

The first exercise establishes computational workflows for verifying fundamental algebraic theorems through symbolic execution. You will mechanically verify Lagrange's theorem for finite groups, the First Isomorphism Theorem for group homomorphisms, and the Fundamental Theorem of Algebra for polynomial roots. Each verification translates abstract mathematical propositions into executable code that computes explicit instances and checks structural invariants.

### Lagrange's Theorem: Subgroup Order Divides Group Order

Lagrange's theorem states that for any finite group $G$ and subgroup $H \subseteq G$, the order of $H$ divides the order of $G$: $|H| \mid |G|$. The proof constructs a partition of $G$ into left cosets of $H$, each having cardinality $|H|$, yielding $|G| = |H| \cdot [G : H]$ where $[G : H]$ denotes the index. Computationally verify this by constructing explicit finite groups and their subgroups, then checking divisibility.

Begin by importing SymPy's combinatorics module, which provides permutation group implementations. The symmetric group $S_n$ and dihedral group $D_n$ serve as concrete test cases. Launch a Python interactive session and execute the following verification script:

```python
from sympy.combinatorics import PermutationGroup, Permutation
from sympy.combinatorics.named_groups import SymmetricGroup, DihedralGroup, AlternatingGroup
from math import gcd

def verify_lagrange_theorem(group, subgroup):
    """
    Verify Lagrange's theorem: |H| divides |G|
    """
    group_order = group.order()
    subgroup_order = subgroup.order()
    
    # Check divisibility
    quotient, remainder = divmod(group_order, subgroup_order)
    
    print(f"Group order: {group_order}")
    print(f"Subgroup order: {subgroup_order}")
    print(f"Index [G:H]: {quotient}")
    print(f"Remainder: {remainder}")
    print(f"Lagrange satisfied: {remainder == 0}")
    
    # Verify by coset partition
    left_cosets = []
    elements_covered = set()
    
    for g in group.elements:
        if g not in elements_covered:
            # Construct left coset gH
            coset = set()
            for h in subgroup.elements:
                coset.add(g * h)
            left_cosets.append(coset)
            elements_covered.update(coset)
    
    print(f"Number of distinct left cosets: {len(left_cosets)}")
    print(f"Each coset has size: {len(left_cosets[0])}")
    print(f"Partition verified: {len(elements_covered) == group_order}")
    
    return remainder == 0

# Test Case 1: Symmetric group S_4 and alternating subgroup A_4
print("=" * 60)
print("Test Case 1: S_4 and A_4")
print("=" * 60)
S4 = SymmetricGroup(4)
A4 = AlternatingGroup(4)
verify_lagrange_theorem(S4, A4)

print("\n" + "=" * 60)
print("Test Case 2: Dihedral group D_6 and rotation subgroup")
print("=" * 60)
D6 = DihedralGroup(6)
# Rotation subgroup: generated by single rotation
r = D6.generators[0]  # rotation generator
rotation_subgroup = PermutationGroup([r])
verify_lagrange_theorem(D6, rotation_subgroup)

print("\n" + "=" * 60)
print("Test Case 3: S_3 and cyclic subgroup of order 3")
print("=" * 60)
S3 = SymmetricGroup(3)
# Cyclic subgroup generated by (0 1 2)
cyclic_gen = Permutation([1, 2, 0])
cyclic_subgroup = PermutationGroup([cyclic_gen])
verify_lagrange_theorem(S3, cyclic_subgroup)
```

Execute this script by saving it to `lagrange_verification.py` and running `python lagrange_verification.py`. The output displays the group and subgroup orders, computes the index as the quotient, and verifies that the remainder is zero. The coset partition construction explicitly builds left cosets $gH$ for each element $g \in G$ not yet covered, confirming that the group decomposes into disjoint cosets of equal size.

For the symmetric group $S_4$ with order 24 and alternating subgroup $A_4$ with order 12, Lagrange's theorem predicts index $[S_4 : A_4] = 2$, which the computation confirms. The dihedral group $D_6$ has order 12, and its rotation subgroup has order 6, yielding index 2. The symmetric group $S_3$ has order 6, and the cyclic subgroup generated by the 3-cycle $(0\ 1\ 2)$ has order 3, yielding index 2. In each case, the divisibility condition holds, and the coset partition covers the group exactly.

### First Isomorphism Theorem: Quotient Structure

The First Isomorphism Theorem states that for any group homomorphism $\phi: G \to H$, the quotient group $G / \ker\phi$ is isomorphic to the image $\text{im}\phi$. The canonical isomorphism maps each coset $g \ker\phi$ to $\phi(g)$. Computationally verify this by constructing an explicit homomorphism, computing its kernel and image, and checking that the quotient group structure matches the image.

Define a homomorphism from the additive group $\mathbb{Z}_{12}$ to $\mathbb{Z}_4$ given by $\phi(x) = x \mod 4$. The kernel consists of elements mapping to zero: $\ker\phi = \{0, 4, 8\}$, forming a subgroup of order 3. The image is all of $\mathbb{Z}_4$, with order 4. The quotient $\mathbb{Z}_{12} / \ker\phi$ should have order $12 / 3 = 4$ and be isomorphic to $\mathbb{Z}_4$.

```python
from sympy import symbols, Mod, simplify
from collections import defaultdict

def first_isomorphism_verification():
    """
    Verify First Isomorphism Theorem for Z_12 -> Z_4
    phi(x) = x mod 4
    """
    n = 12
    m = 4
    
    # Define the homomorphism
    def phi(x):
        return x % m
    
    # Compute kernel: {x in Z_12 : phi(x) = 0}
    kernel = [x for x in range(n) if phi(x) == 0]
    print(f"Kernel: {kernel}")
    print(f"Kernel order: {len(kernel)}")
    
    # Compute image
    image = sorted(set(phi(x) for x in range(n)))
    print(f"Image: {image}")
    print(f"Image order: {len(image)}")
    
    # Construct quotient group G/ker(phi)
    # Left cosets: x + ker(phi) for x in G
    cosets = []
    coset_representatives = []
    elements_covered = set()
    
    for x in range(n):
        if x not in elements_covered:
            # Build coset x + ker(phi)
            coset = set((x + k) % n for k in kernel)
            cosets.append(coset)
            coset_representatives.append(x)
            elements_covered.update(coset)
    
    print(f"\nQuotient group G/ker(phi) has {len(cosets)} cosets")
    print(f"Coset representatives: {coset_representatives}")
    
    # Verify isomorphism: map each coset to phi(representative)
    quotient_to_image = {}
    for rep in coset_representatives:
        quotient_to_image[rep] = phi(rep)
    
    print("\nIsomorphism verification:")
    print(f"Coset representative -> Image element")
    for rep, img in quotient_to_image.items():
        print(f"{rep} + ker(phi) -> {img}")
    
    # Verify bijection
    image_values = list(quotient_to_image.values())
    is_injective = len(image_values) == len(set(image_values))
    is_surjective = set(image_values) == set(image)
    
    print(f"\nInjective: {is_injective}")
    print(f"Surjective: {is_surjective}")
    print(f"Bijective: {is_injective and is_surjective}")
    
    # Verify homomorphism property on quotient
    print("\nVerifying multiplication table isomorphism:")
    print("(a + ker(phi)) * (b + ker(phi)) -> phi(a) * phi(b)")
    
    for i, rep_a in enumerate(coset_representatives[:3]):  # Sample check
        for j, rep_b in enumerate(coset_representatives[:3]):
            # Quotient multiplication: (a + ker) * (b + ker) = (a+b) + ker
            product_quotient = (rep_a + rep_b) % n
            # Find which coset this belongs to
            product_coset_rep = None
            for rep in coset_representatives:
                if product_quotient in set((rep + k) % n for k in kernel):
                    product_coset_rep = rep
                    break
            
            # Image multiplication: phi(a) * phi(b) = phi(a+b)
            product_image = (phi(rep_a) + phi(rep_b)) % m
            mapped_product = phi(product_coset_rep)
            
            match = (mapped_product == product_image)
            print(f"  ({rep_a} + ker) * ({rep_b} + ker) = {product_coset_rep} + ker -> {mapped_product}, "
                  f"phi({rep_a}) + phi({rep_b}) = {product_image}, Match: {match}")

print("=" * 60)
print("First Isomorphism Theorem Verification")
print("=" * 60)
first_isomorphism_verification()
```

Execute this script with `python first_isomorphism.py`. The output displays the kernel $\{0, 4, 8\}$ with order 3, the image $\{0, 1, 2, 3\}$ with order 4, and the four cosets of the quotient group. The isomorphism maps each coset representative to its image under $\phi$, and the verification confirms bijectivity. The multiplication table check samples several coset products and verifies that the quotient group operation matches the image group operation under the isomorphism.

### Fundamental Theorem of Algebra: Polynomial Root Existence

The Fundamental Theorem of Algebra states that every non-constant polynomial $p(z)$ with complex coefficients has at least one complex root. Equivalently, a polynomial of degree $n$ factors completely into $n$ linear factors over $\mathbb{C}$. Computationally verify this by constructing polynomials of varying degrees, computing their roots using SymPy's symbolic solver, and confirming that the number of roots (counting multiplicity) equals the degree.

```python
from sympy import symbols, poly, roots, expand, I, Poly
from sympy.abc import x

def fundamental_theorem_verification():
    """
    Verify Fundamental Theorem of Algebra:
    Every polynomial of degree n has exactly n complex roots (counting multiplicity)
    """
    test_polynomials = [
        ("x^2 - 1", x**2 - 1),
        ("x^2 + 1", x**2 + 1),
        ("x^3 - 1", x**3 - 1),
        ("x^4 - 16", x**4 - 16),
        ("x^5 + x^4 + x^3 + x^2 + x + 1", x**5 + x**4 + x**3 + x**2 + x + 1),
        ("(x - 1)^3 (x + 2)^2", expand((x - 1)**3 * (x + 2)**2)),
        ("x^6 + 1", x**6 + 1),
    ]
    
    for name, p in test_polynomials:
        print("=" * 60)
        print(f"Polynomial: {name}")
        print("=" * 60)
        
        # Convert to Poly object
        poly_obj = Poly(p, x)
        degree = poly_obj.degree()
        print(f"Degree: {degree}")
        
        # Compute roots
        root_dict = roots(p, x)
        print(f"Roots (with multiplicity):")
        
        total_roots = 0
        for root, multiplicity in root_dict.items():
            print(f"  {root} with multiplicity {multiplicity}")
            total_roots += multiplicity
        
        print(f"Total roots (counting multiplicity): {total_roots}")
        print(f"Fundamental Theorem satisfied: {total_roots == degree}")
        
        # Verify factorization
        factorization = 1
        for root, mult in root_dict.items():
            factorization *= (x - root)**mult
        
        difference = expand(p - factorization)
        print(f"Factorization reconstructs polynomial: {difference == 0}")
        print()

print("Fundamental Theorem of Algebra Verification")
print()
fundamental_theorem_verification()
```

Run this verification with `python fundamental_theorem.py`. For the polynomial $x^2 - 1$, SymPy computes roots $\{1, -1\}$, matching the degree 2. For $x^2 + 1$, the roots are $\{i, -i\}$, the complex roots with multiplicity 1 each. The polynomial $x^3 - 1$ yields the three cube roots of unity: $1, -\frac{1}{2} + \frac{\sqrt{3}}{2}i, -\frac{1}{2} - \frac{\sqrt{3}}{2}i$. The polynomial $(x - 1)^3 (x + 2)^2$ expanded has degree 5, and SymPy correctly identifies root 1 with multiplicity 3 and root $-2$ with multiplicity 2, totaling 5 roots. The cyclotomic-like polynomial $x^6 + 1$ factors into six complex roots corresponding to the sixth roots of $-1$.

In every case, the total number of roots counted with multiplicity equals the polynomial degree, and the factorization into linear terms $(x - r_i)^{m_i}$ exactly reconstructs the original polynomial. This computational verification confirms the Fundamental Theorem of Algebra for explicit instances. For formal proof, the theorem requires complex analysis and topological arguments (compactness, Liouville's theorem, winding numbers), but the computational check validates the root count property across diverse polynomial structures.

## Exercise 2: Boundary Value Stress Testing & Singularities

The second exercise probes the boundary cases and singularities where algebraic structures exhibit degenerate or exceptional behavior. You will test the limits of group structure (trivial groups, groups of prime order), ring behavior (zero divisors, nilpotent elements, units in quotient rings), and field extensions (finite fields, splitting fields, inseparable extensions). These stress tests reveal the conditions under which algebraic theorems require careful hypothesis checking and expose computational edge cases that symbolic engines must handle gracefully.

### Trivial and Prime-Order Groups: Minimal Structure

The trivial group $\{e\}$ and cyclic groups of prime order $\mathbb{Z}_p$ represent the minimal non-trivial group structures. The trivial group contains only the identity element, and its only subgroup is itself. A cyclic group $\mathbb{Z}_p$ for prime $p$ has no non-trivial proper subgroups by Lagrange's theorem, since the only divisors of $p$ are 1 and $p$. Computationally verify these boundary cases and test whether standard group algorithms handle them correctly.

```python
from sympy.combinatorics import PermutationGroup, Permutation
from sympy.ntheory import isprime

def test_trivial_group():
    """
    Test trivial group {e}
    """
    print("=" * 60)
    print("Trivial Group")
    print("=" * 60)
    
    # Trivial group: identity permutation only
    e = Permutation([0])
    trivial = PermutationGroup([e])
    
    print(f"Order: {trivial.order()}")
    print(f"Elements: {list(trivial.elements)}")
    print(f"Is abelian: {trivial.is_abelian}")
    print(f"Center equals group: {trivial.center().order() == trivial.order()}")
    
    # All subgroups
    print(f"Number of subgroups: 1 (only itself)")
    print()

def test_prime_order_cyclic():
    """
    Test cyclic groups of prime order
    """
    primes = [2, 3, 5, 7, 11]
    
    for p in primes:
        print("=" * 60)
        print(f"Cyclic Group Z_{p}")
        print("=" * 60)
        
        # Represent Z_p as integers mod p under addition
        elements = list(range(p))
        print(f"Elements: {elements}")
        print(f"Order: {p}")
        print(f"Is prime: {isprime(p)}")
        
        # Check generator property: every non-identity element generates the group
        generators = []
        for g in elements[1:]:  # exclude identity 0
            generated = set()
            current = 0
            for _ in range(p):
                generated.add(current)
                current = (current + g) % p
            if len(generated) == p:
                generators.append(g)
        
        print(f"Generators: {generators}")
        print(f"Number of generators (phi(p)): {len(generators)} (expected {p - 1})")
        
        # Verify no non-trivial proper subgroups
        print(f"Only subgroups: {{0}}, Z_{p} (by Lagrange)")
        print()

test_trivial_group()
test_prime_order_cyclic()
```

Execute with `python boundary_groups.py`. The trivial group has order 1 and only the identity element. It is trivially abelian, and its center is itself. For each prime $p$, the cyclic group $\mathbb{Z}_p$ has exactly $\phi(p) = p - 1$ generators (all non-zero elements), confirming that every non-identity element generates the entire group. Lagrange's theorem guarantees no intermediate subgroups exist, since the only divisors of a prime are 1 and itself.

### Zero Divisors and Nilpotent Elements in Rings

In a commutative ring, a zero divisor is a non-zero element $a$ such that $ab = 0$ for some non-zero $b$. A nilpotent element satisfies $a^n = 0$ for some positive integer $n$. These elements exhibit degenerate multiplicative behavior that prevents the ring from being an integral domain. Test for zero divisors and nilpotents in quotient rings $\mathbb{Z}_n$ for composite $n$.

```python
from sympy import gcd

def test_zero_divisors_and_nilpotents():
    """
    Find zero divisors and nilpotent elements in Z_n for composite n
    """
    composite_moduli = [4, 6, 8, 9, 12, 15, 16]
    
    for n in composite_moduli:
        print("=" * 60)
        print(f"Ring Z_{n}")
        print("=" * 60)
        
        # Find zero divisors: non-zero a such that ab = 0 (mod n) for some non-zero b
        zero_divisors = set()
        for a in range(1, n):
            for b in range(1, n):
                if (a * b) % n == 0:
                    zero_divisors.add(a)
                    break
        
        print(f"Zero divisors: {sorted(zero_divisors)}")
        
        # Find nilpotent elements: a such that a^k = 0 (mod n) for some k
        nilpotents = set()
        for a in range(1, n):
            power = a
            for k in range(1, n + 1):
                if power % n == 0:
                    nilpotents.add(a)
                    print(f"  {a}^{k} ≡ 0 (mod {n})")
                    break
                power = (power * a) % n
        
        print(f"Nilpotent elements: {sorted(nilpotents)}")
        
        # Find units: a such that gcd(a, n) = 1
        units = [a for a in range(1, n) if gcd(a, n) == 1]
        print(f"Units: {units}")
        print(f"Number of units (phi({n})): {len(units)}")
        
        # Verify: zero divisors and units are disjoint
        overlap = set(zero_divisors) & set(units)
        print(f"Zero divisors ∩ Units: {overlap} (should be empty)")
        print()

test_zero_divisors_and_nilpotents()
```

Run with `python ring_boundary.py`. In $\mathbb{Z}_4$, the element 2 is a zero divisor since $2 \cdot 2 = 4 \equiv 0 \pmod{4}$, and it is also nilpotent with $2^2 \equiv 0$. In $\mathbb{Z}_6$, the elements 2, 3, and 4 are zero divisors: $2 \cdot 3 \equiv 0$, $3 \cdot 2 \equiv 0$, $4 \cdot 3 \equiv 0 \pmod{6}$. The element 3 is nilpotent in $\mathbb{Z}_9$ since $3^2 = 9 \equiv 0 \pmod{9}$. In $\mathbb{Z}_{16}$, the elements 2, 4, 6, 8, 10, 12, 14 are zero divisors, and powers of 2 are nilpotent: $2^4 = 16 \equiv 0$, $4^2 = 16 \equiv 0$, $8^2 = 64 \equiv 0 \pmod{16}$.

The verification confirms that zero divisors and units are disjoint sets: if $\gcd(a, n) = 1$, then $a$ is a unit with a multiplicative inverse, so $a$ cannot be a zero divisor. Conversely, if $\gcd(a, n) = d > 1$, then $a \cdot (n/d) \equiv 0 \pmod{n}$, making $a$ a zero divisor. This boundary testing reveals the structural differences between rings that are integral domains (no zero divisors, like $\mathbb{Z}_p$ for prime $p$) and rings with zero divisors (composite moduli).

### Finite Field Extensions and Splitting Fields

A finite field $\mathbb{F}_{p^n}$ is a field extension of the prime field $\mathbb{F}_p$ with degree $n$. The splitting field of a polynomial $f(x)$ over $\mathbb{F}_p$ is the smallest field extension in which $f$ factors completely into linear terms. Computationally construct finite fields and splitting fields using SymPy's galois module and verify the field axioms and extension degrees.

```python
from sympy import symbols, GF, Poly, factor
from sympy.abc import x

def test_finite_field_extensions():
    """
    Construct and verify finite field extensions
    """
    print("=" * 60)
    print("Finite Field F_4 = F_2[x]/(x^2 + x + 1)")
    print("=" * 60)
    
    # Construct F_4 as F_2[alpha] where alpha^2 + alpha + 1 = 0
    # Elements: {0, 1, alpha, alpha + 1}
    F2 = GF(2)
    
    # Represent F_4 elements as polynomials in alpha modulo the minimal polynomial
    # alpha^2 = alpha + 1
    elements_F4 = [
        (0, 0),  # 0
        (1, 0),  # 1
        (0, 1),  # alpha
        (1, 1),  # alpha + 1
    ]
    
    print("Elements (as (a, b) representing a + b*alpha):")
    for elem in elements_F4:
        print(f"  {elem}")
    
    # Addition table (component-wise mod 2)
    print("\nAddition table:")
    print("  ", end="")
    for e in elements_F4:
        print(f"{e} ", end="")
    print()
    
    for e1 in elements_F4:
        print(f"{e1} ", end="")
        for e2 in elements_F4:
            sum_elem = ((e1[0] + e2[0]) % 2, (e1[1] + e2[1]) % 2)
            print(f"{sum_elem} ", end="")
        print()
    
    # Multiplication table (with alpha^2 = alpha + 1)
    print("\nMultiplication table:")
    print("  ", end="")
    for e in elements_F4:
        print(f"{e} ", end="")
    print()
    
    for e1 in elements_F4:
        print(f"{e1} ", end="")
        for e2 in elements_F4:
            # (a + b*alpha)(c + d*alpha) = ac + (ad + bc)*alpha + bd*alpha^2
            # alpha^2 = alpha + 1, so bd*alpha^2 = bd*(alpha + 1) = bd*alpha + bd
            a, b = e1
            c, d = e2
            prod_0 = (a * c + b * d) % 2
            prod_1 = (a * d + b * c + b * d) % 2
            print(f"{(prod_0, prod_1)} ", end="")
        print()
    
    # Verify multiplicative inverses (excluding 0)
    print("\nMultiplicative inverses:")
    for e in elements_F4[1:]:  # exclude 0
        print(f"  {e}: ", end="")
        a, b = e
        for candidate in elements_F4[1:]:
            c, d = candidate
            prod_0 = (a * c + b * d) % 2
            prod_1 = (a * d + b * c + b * d) % 2
            if (prod_0, prod_1) == (1, 0):
                print(f"{candidate}")
                break
    
    print("\n" + "=" * 60)
    print("Splitting Field of x^3 - 2 over Q")
    print("=" * 60)
    
    # x^3 - 2 has roots: 2^(1/3), 2^(1/3) * omega, 2^(1/3) * omega^2
    # where omega = exp(2*pi*i/3) = (-1 + sqrt(3)*i)/2
    # Splitting field: Q(2^(1/3), omega)
    
    poly = x**3 - 2
    print(f"Polynomial: {poly}")
    
    from sympy import cbrt, exp, pi, I, simplify
    
    root1 = cbrt(2)
    omega = exp(2 * pi * I / 3)
    root2 = root1 * omega
    root3 = root1 * omega**2
    
    print(f"Roots:")
    print(f"  {root1}")
    print(f"  {simplify(root2)}")
    print(f"  {simplify(root3)}")
    
    # Extension degree: [Q(2^(1/3), omega) : Q] = [Q(2^(1/3), omega) : Q(2^(1/3))] * [Q(2^(1/3)) : Q]
    # [Q(2^(1/3)) : Q] = 3 (minimal polynomial x^3 - 2)
    # [Q(2^(1/3), omega) : Q(2^(1/3))] = 2 (minimal polynomial of omega over Q(2^(1/3)) is x^2 + x + 1)
    # Total degree: 3 * 2 = 6
    
    print(f"\nExtension degrees:")
    print(f"  [Q(2^(1/3)) : Q] = 3")
    print(f"  [Q(2^(1/3), omega) : Q(2^(1/3))] = 2")
    print(f"  [Q(2^(1/3), omega) : Q] = 6")

test_finite_field_extensions()
```

Execute with `python finite_fields.py`. The finite field $\mathbb{F}_4$ has four elements, represented as $\{0, 1, \alpha, \alpha + 1\}$ where $\alpha$ satisfies the irreducible polynomial $x^2 + x + 1$ over $\mathbb{F}_2$. The addition table shows component-wise addition modulo 2, and the multiplication table uses the relation $\alpha^2 = \alpha + 1$ to reduce products. Each non-zero element has a multiplicative inverse: $1^{-1} = 1$, $\alpha^{-1} = \alpha + 1$ (since $\alpha(\alpha + 1) = \alpha^2 + \alpha = 1$), and $(\alpha + 1)^{-1} = \alpha$.

For the splitting field of $x^3 - 2$ over $\mathbb{Q}$, the three roots are $\sqrt[3]{2}$, $\sqrt[3]{2} \omega$, and $\sqrt[3]{2} \omega^2$ where $\omega = e^{2\pi i / 3} = -\frac{1}{2} + \frac{\sqrt{3}}{2}i$ is a primitive cube root of unity. The splitting field is $\mathbb{Q}(\sqrt[3]{2}, \omega)$, which has degree 6 over $\mathbb{Q}$. The tower law gives $[\mathbb{Q}(\sqrt[3]{2}, \omega) : \mathbb{Q}] = [\mathbb{Q}(\sqrt[3]{2}, \omega) : \mathbb{Q}(\sqrt[3]{2})] \cdot [\mathbb{Q}(\sqrt[3]{2}) : \mathbb{Q}] = 2 \cdot 3 = 6$.

These boundary tests verify that algebraic structures behave correctly at the extremes: minimal groups, degenerate ring elements, and field extensions. The computational checks confirm that symbolic engines handle edge cases gracefully and that the theoretical predictions (Lagrange for prime-order groups, tower law for field extensions) match computed results.

## Exercise 3: Algorithmic Implementation of Formal Structures

The third exercise implements algorithmic representations of formal algebraic structures: group multiplication tables, polynomial arithmetic in quotient rings, and linear algebra over finite fields. These implementations translate abstract definitions into executable data structures and algorithms, enabling computational verification of algebraic properties and practical applications in cryptography and coding theory.

### Group Multiplication Tables and Cayley Tables

A finite group can be represented by its Cayley table: a multiplication table encoding the group operation for every pair of elements. Implement a class that constructs the Cayley table from a group generator set, verifies closure, associativity, identity, and inverses, and tests whether the group is abelian.

```python
from itertools import product

class FiniteGroup:
    """
    Finite group represented by Cayley table
    """
    def __init__(self, elements, operation, identity):
        """
        elements: list of group elements
        operation: binary operation function (a, b) -> a * b
        identity: identity element
        """
        self.elements = elements
        self.operation = operation
        self.identity = identity
        self.cayley_table = {}
        
        # Build Cayley table
        for a in elements:
            for b in elements:
                self.cayley_table[(a, b)] = operation(a, b)
    
    def verify_group_axioms(self):
        """
        Verify closure, associativity, identity, and inverses
        """
        print("Verifying Group Axioms")
        print("=" * 60)
        
        # Closure: operation result is in the group
        closure = all(self.cayley_table[(a, b)] in self.elements 
                     for a, b in product(self.elements, repeat=2))
        print(f"Closure: {closure}")
        
        # Associativity: (a * b) * c = a * (b * c)
        associativity = True
        for a, b, c in product(self.elements, repeat=3):
            ab = self.cayley_table[(a, b)]
            bc = self.cayley_table[(b, c)]
            ab_c = self.cayley_table[(ab, c)]
            a_bc = self.cayley_table[(a, bc)]
            if ab_c != a_bc:
                associativity = False
                print(f"  Associativity fails: ({a} * {b}) * {c} = {ab_c}, {a} * ({b} * {c}) = {a_bc}")
                break
        print(f"Associativity: {associativity}")
        
        # Identity: e * a = a * e = a for all a
        identity_check = all(
            self.cayley_table[(self.identity, a)] == a and 
            self.cayley_table[(a, self.identity)] == a 
            for a in self.elements
        )
        print(f"Identity element {self.identity}: {identity_check}")
        
        # Inverses: for each a, exists b such that a * b = b * a = e
        inverses = {}
        all_have_inverse = True
        for a in self.elements:
            found_inverse = False
            for b in self.elements:
                if (self.cayley_table[(a, b)] == self.identity and 
                    self.cayley_table[(b, a)] == self.identity):
                    inverses[a] = b
                    found_inverse = True
                    break
            if not found_inverse:
                all_have_inverse = False
                print(f"  Element {a} has no inverse")
        
        print(f"All elements have inverses: {all_have_inverse}")
        if all_have_inverse:
            print(f"Inverse map: {inverses}")
        
        # Abelian: a * b = b * a for all a, b
        abelian = all(
            self.cayley_table[(a, b)] == self.cayley_table[(b, a)]
            for a, b in product(self.elements, repeat=2)
        )
        print(f"Abelian: {abelian}")
        
        return closure and associativity and identity_check and all_have_inverse
    
    def print_cayley_table(self):
        """
        Print the Cayley table
        """
        print("\nCayley Table:")
        print("   |", " ".join(f"{e:3}" for e in self.elements))
        print("---+" + "----" * len(self.elements))
        for a in self.elements:
            row = " | ".join(f"{self.cayley_table[(a, b)]:3}" for b in self.elements)
            print(f"{a:3}| {row}")

# Test Case 1: Cyclic group Z_4 under addition mod 4
print("=" * 60)
print("Test: Cyclic Group Z_4")
print("=" * 60)
elements_Z4 = [0, 1, 2, 3]
operation_Z4 = lambda a, b: (a + b) % 4
identity_Z4 = 0

Z4 = FiniteGroup(elements_Z4, operation_Z4, identity_Z4)
Z4.verify_group_axioms()
Z4.print_cayley_table()

# Test Case 2: Klein four-group V_4
print("\n" + "=" * 60)
print("Test: Klein Four-Group V_4")
print("=" * 60)
elements_V4 = ['e', 'a', 'b', 'c']
# Multiplication table: e is identity, all elements are self-inverse, a*b=c, a*c=b, b*c=a
cayley_V4 = {
    ('e', 'e'): 'e', ('e', 'a'): 'a', ('e', 'b'): 'b', ('e', 'c'): 'c',
    ('a', 'e'): 'a', ('a', 'a'): 'e', ('a', 'b'): 'c', ('a', 'c'): 'b',
    ('b', 'e'): 'b', ('b', 'a'): 'c', ('b', 'b'): 'e', ('b', 'c'): 'a',
    ('c', 'e'): 'c', ('c', 'a'): 'b', ('c', 'b'): 'a', ('c', 'c'): 'e',
}
operation_V4 = lambda a, b: cayley_V4[(a, b)]
identity_V4 = 'e'

V4 = FiniteGroup(elements_V4, operation_V4, identity_V4)
V4.verify_group_axioms()
V4.print_cayley_table()

# Test Case 3: Symmetric group S_3
print("\n" + "=" * 60)
print("Test: Symmetric Group S_3")
print("=" * 60)
# Represent permutations as tuples: (sigma(0), sigma(1), sigma(2))
elements_S3 = [
    (0, 1, 2),  # identity
    (1, 0, 2),  # (01)
    (0, 2, 1),  # (12)
    (2, 1, 0),  # (02)
    (1, 2, 0),  # (012)
    (2, 0, 1),  # (021)
]

def compose_permutations(sigma, tau):
    """Compose permutations: (sigma ∘ tau)(i) = sigma(tau(i))"""
    return tuple(sigma[tau[i]] for i in range(len(sigma)))

operation_S3 = compose_permutations
identity_S3 = (0, 1, 2)

S3 = FiniteGroup(elements_S3, operation_S3, identity_S3)
S3.verify_group_axioms()
S3.print_cayley_table()
```

Run with `python cayley_tables.py`. For the cyclic group $\mathbb{Z}_4$, the verification confirms closure, associativity, the identity element 0, and inverses: $0^{-1} = 0$, $1^{-1} = 3$, $2^{-1} = 2$, $3^{-1} = 1$. The group is abelian since $(a + b) \mod 4 = (b + a) \mod 4$. The Cayley table displays the addition modulo 4 for all pairs.

The Klein four-group $V_4$ has four elements $\{e, a, b, c\}$ with the property that every non-identity element has order 2 (is self-inverse) and the product of any two distinct non-identity elements is the third. The verification confirms the group axioms and that $V_4$ is abelian. The symmetric group $S_3$ has six elements (the permutations of three objects), and the composition operation is non-abelian: $(0\ 1) \circ (1\ 2) = (0\ 1\ 2)$ but $(1\ 2) \circ (0\ 1) = (0\ 2\ 1)$.

### Polynomial Arithmetic in Quotient Rings

Implement polynomial arithmetic in the quotient ring $\mathbb{F}_p[x] / (m(x))$ where $m(x)$ is an irreducible polynomial over the finite field $\mathbb{F}_p$. This structure is fundamental to finite field constructions and cryptographic applications like AES, which uses $\mathbb{F}_{2^8} \cong \mathbb{F}_2[x] / (x^8 + x^4 + x^3 + x + 1)$.

```python
from sympy import Poly, GF, symbols, rem, quo
from sympy.abc import x

class QuotientRingPolynomial:
    """
    Polynomial arithmetic in F_p[x] / (m(x))
    """
    def __init__(self, poly, modulus_poly, field_char):
        """
        poly: polynomial in F_p[x]
        modulus_poly: irreducible modulus polynomial m(x)
        field_char: characteristic of base field F_p
        """
        self.field = GF(field_char)
        self.modulus = Poly(modulus_poly, x, domain=self.field)
        self.poly = Poly(poly, x, domain=self.field)
        self.reduce()
    
    def reduce(self):
        """Reduce polynomial modulo the modulus"""
        self.poly = self.poly.rem(self.modulus)
    
    def __add__(self, other):
        """Addition in quotient ring"""
        result_poly = self.poly + other.poly
        return QuotientRingPolynomial(result_poly, self.modulus, self.field.characteristic)
    
    def __mul__(self, other):
        """Multiplication in quotient ring"""
        result_poly = self.poly * other.poly
        return QuotientRingPolynomial(result_poly, self.modulus, self.field.characteristic)
    
    def __pow__(self, n):
        """Exponentiation in quotient ring"""
        if n == 0:
            return QuotientRingPolynomial(1, self.modulus, self.field.characteristic)
        result = self
        for _ in range(n - 1):
            result = result * self
        return result
    
    def multiplicative_inverse(self):
        """
        Compute multiplicative inverse using Extended Euclidean Algorithm
        """
        def extended_gcd_poly(a, b):
            """Extended GCD for polynomials"""
            if b.is_zero:
                return a, Poly(1, x, domain=self.field), Poly(0, x, domain=self.field)
            
            q, r = a.div(b)
            g, s, t = extended_gcd_poly(b, r)
            return g, t, s - q * t
        
        g, s, t = extended_gcd_poly(self.poly, self.modulus)
        
        if g.degree() > 0:
            raise ValueError(f"Element {self.poly} is not invertible")
        
        # Normalize: g should be constant polynomial 1
        inv = s / g.LC()
        return QuotientRingPolynomial(inv, self.modulus, self.field.characteristic)
    
    def __repr__(self):
        return f"{self.poly.as_expr()}"

# Test: F_2[x] / (x^8 + x^4 + x^3 + x + 1) - AES finite field F_{2^8}
print("=" * 60)
print("AES Finite Field: F_2[x] / (x^8 + x^4 + x^3 + x + 1)")
print("=" * 60)

aes_modulus = x**8 + x**4 + x**3 + x + 1
field_char = 2

# Test element: x^6 + x^4 + x^2 + x + 1 (represents byte 0x57 = 01010111)
a_poly = x**6 + x**4 + x**2 + x + 1
a = QuotientRingPolynomial(a_poly, aes_modulus, field_char)
print(f"Element a = {a}")

# Test element: x^7 + x + 1 (represents byte 0x83 = 10000011)
b_poly = x**7 + x + 1
b = QuotientRingPolynomial(b_poly, aes_modulus, field_char)
print(f"Element b = {b}")

# Addition (XOR in GF(2))
c = a + b
print(f"\na + b = {c}")

# Multiplication
d = a * b
print(f"a * b = {d}")

# Verify: (a * b) mod m(x)
product_unreduced = Poly(a_poly * b_poly, x, domain=GF(2))
product_reduced = product_unreduced.rem(Poly(aes_modulus, x, domain=GF(2)))
print(f"Verification: {product_reduced.as_expr()}")

# Multiplicative inverse
print(f"\nComputing multiplicative inverse of a...")
try:
    a_inv = a.multiplicative_inverse()
    print(f"a^(-1) = {a_inv}")
    
    # Verify: a * a^(-1) = 1
    verification = a * a_inv
    print(f"a * a^(-1) = {verification} (should be 1)")
except ValueError as e:
    print(f"Error: {e}")

# AES MixColumns operation: multiplication by fixed polynomial
print("\n" + "=" * 60)
print("AES MixColumns: Multiply by {02} = x")
print("=" * 60)

mix_poly = x  # The constant {02} in AES
mix = QuotientRingPolynomial(mix_poly, aes_modulus, field_char)

test_byte = x**7 + x**6 + x**5 + x**4  # 0xF0
test = QuotientRingPolynomial(test_byte, aes_modulus, field_char)
print(f"Input byte: {test}")

result = test * mix
print(f"Result after multiply by x: {result}")

# Test the reduction property: x^8 = x^4 + x^3 + x + 1
x8_test = QuotientRingPolynomial(x**8, aes_modulus, field_char)
print(f"\nx^8 mod m(x) = {x8_test} (should be x^4 + x^3 + x + 1)")
```

Execute with `python quotient_ring.py`. The script implements polynomial arithmetic in the AES finite field $\mathbb{F}_{2^8}$, where elements are polynomials of degree at most 7 with coefficients in $\mathbb{F}_2$, and operations are performed modulo the irreducible polynomial $m(x) = x^8 + x^4 + x^3 + x + 1$. Addition corresponds to XOR of polynomial coefficients, and multiplication uses polynomial multiplication followed by reduction modulo $m(x)$.

The multiplicative inverse computation uses the Extended Euclidean Algorithm adapted for polynomials: given $a(x)$ and $m(x)$, find $s(x)$ such that $a(x) s(x) \equiv 1 \pmod{m(x)}$. The verification confirms that $a \cdot a^{-1} = 1$ in the quotient ring. The AES MixColumns operation multiplies state bytes by fixed polynomials in $\mathbb{F}_{2^8}$, and the script demonstrates multiplication by the polynomial $x$ (representing the byte $\{02\}$ in AES notation).

### Linear Algebra over Finite Fields

Implement matrix operations over finite fields, including matrix multiplication, determinant computation, and solving linear systems. These operations are fundamental to coding theory (linear codes, syndrome decoding) and cryptography (Hill cipher, lattice-based cryptography).

```python
import numpy as np
from sympy import Matrix, GF

class FiniteFieldMatrix:
    """
    Matrix over finite field F_p
    """
    def __init__(self, matrix, field_char):
        """
        matrix: 2D list or numpy array
        field_char: characteristic of field F_p
        """
        self.field_char = field_char
        self.matrix = np.array(matrix, dtype=int) % field_char
        self.rows, self.cols = self.matrix.shape
    
    def __mul__(self, other):
        """Matrix multiplication over F_p"""
        if self.cols != other.rows:
            raise ValueError("Incompatible dimensions for multiplication")
        
        result = np.dot(self.matrix, other.matrix) % self.field_char
        return FiniteFieldMatrix(result, self.field_char)
    
    def determinant(self):
        """Compute determinant over F_p using SymPy"""
        sympy_matrix = Matrix(self.matrix)
        det = sympy_matrix.det()
        return int(det) % self.field_char
    
    def inverse(self):
        """Compute matrix inverse over F_p"""
        det = self.determinant()
        
        if det == 0:
            raise ValueError("Matrix is not invertible (determinant = 0)")
        
        # Use SymPy for inversion
        sympy_matrix = Matrix(self.matrix)
        sympy_inv = sympy_matrix.inv_mod(self.field_char)
        
        inv_array = np.array(sympy_inv.tolist(), dtype=int) % self.field_char
        return FiniteFieldMatrix(inv_array, self.field_char)
    
    def __repr__(self):
        return f"FiniteFieldMatrix(F_{self.field_char}):\n{self.matrix}"

# Test: Hill cipher over F_26 (alphabet)
print("=" * 60)
print("Hill Cipher: Matrix operations over F_26")
print("=" * 60)

# Key matrix (2x2)
key_matrix = [
    [3, 3],
    [2, 5]
]
field_char = 26

key = FiniteFieldMatrix(key_matrix, field_char)
print(f"Key matrix:\n{key.matrix}")
print(f"Determinant: {key.determinant()}")

# Compute inverse
try:
    key_inv = key.inverse()
    print(f"\nInverse matrix:\n{key_inv.matrix}")
    
    # Verify: K * K^(-1) = I
    identity_check = key * key_inv
    print(f"\nK * K^(-1):\n{identity_check.matrix}")
    print(f"Is identity: {np.allclose(identity_check.matrix, np.eye(2))}")
    
except ValueError as e:
    print(f"Error: {e}")

# Encrypt plaintext "HELP" -> [7, 4], [11, 15] (H=7, E=4, L=11, P=15)
print("\n" + "=" * 60)
print("Encryption: HELP")
print("=" * 60)

plaintext = np.array([[7, 11], [4, 15]], dtype=int)
print(f"Plaintext matrix:\n{plaintext}")

plaintext_obj = FiniteFieldMatrix(plaintext, field_char)
ciphertext_obj = key * plaintext_obj
print(f"Ciphertext matrix:\n{ciphertext_obj.matrix}")

# Decrypt
decrypted_obj = key_inv * ciphertext_obj
print(f"Decrypted matrix:\n{decrypted_obj.matrix}")
print(f"Matches plaintext: {np.array_equal(decrypted_obj.matrix, plaintext)}")

# Test: Linear code over F_2
print("\n" + "=" * 60)
print("Linear Code: Generator matrix over F_2")
print("=" * 60)

# [7,4] Hamming code generator matrix
generator = [
    [1, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 1, 0, 1],
    [0, 0, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1],
]

G = FiniteFieldMatrix(generator, field_char=2)
print(f"Generator matrix G:\n{G.matrix}")

# Encode message [1, 0, 1, 1]
message = np.array([[1], [0], [1], [1]], dtype=int)
message_obj = FiniteFieldMatrix(message, field_char=2)

# Transpose G for proper multiplication
G_T = FiniteFieldMatrix(G.matrix.T, field_char=2)
codeword_obj = G_T * message_obj

print(f"\nMessage: {message.T}")
print(f"Codeword: {codeword_obj.matrix.T}")
print(f"Codeword length: {len(codeword_obj.matrix)}")
```

Run with `python finite_field_linear_algebra.py`. The Hill cipher example demonstrates matrix encryption over $\mathbb{F}_{26}$ (the alphabet modulo 26). The key matrix has determinant 9 modulo 26, which is invertible (since $\gcd(9, 26) = 1$). The inverse matrix is computed, and encryption/decryption of the plaintext "HELP" verifies that $K K^{-1} = I$ and that decryption recovers the original plaintext.

The linear code example uses the $[7, 4]$ Hamming code over $\mathbb{F}_2$. The generator matrix $G$ is a $4 \times 7$ matrix where each row generates a codeword. Encoding a 4-bit message involves matrix-vector multiplication: $\mathbf{c} = G^T \mathbf{m}$, producing a 7-bit codeword. This construction ensures that the code has minimum distance 3, allowing single-error correction.

These algorithmic implementations provide concrete computational models of abstract algebraic structures, enabling verification of theoretical properties through execution and supporting practical applications in cryptography, coding theory, and computational algebra.

## Formal Axioms Cheat Sheet & Verification Reference

This reference section provides the formal axiomatic definitions of fundamental algebraic structures and verification procedures for checking these axioms computationally. Use this as a quick lookup when implementing algebraic structures or verifying their properties.

### Group Axioms

A group $(G, \cdot)$ consists of a set $G$ with a binary operation $\cdot: G \times G \to G$ satisfying:

1. **Closure**: For all $a, b \in G$, $a \cdot b \in G$.
2. **Associativity**: For all $a, b, c \in G$, $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.
3. **Identity**: There exists $e \in G$ such that for all $a \in G$, $e \cdot a = a \cdot e = a$.
4. **Inverses**: For each $a \in G$, there exists $b \in G$ such that $a \cdot b = b \cdot a = e$.

**Computational Verification**: For finite groups, verify closure by checking all pairs $(a, b)$ and ensuring $a \cdot b$ is in the element set. Verify associativity by checking all triples $(a, b, c)$ and comparing $(a \cdot b) \cdot c$ with $a \cdot (b \cdot c)$. Verify identity by testing $e \cdot a = a$ and $a \cdot e = a$ for all $a$. Verify inverses by finding $b$ such that $a \cdot b = e$ for each $a$.

**Abelian Group**: A group is abelian (commutative) if for all $a, b \in G$, $a \cdot b = b \cdot a$. Verify by checking all pairs.

### Ring Axioms

A ring $(R, +, \cdot)$ consists of a set $R$ with two binary operations $+$ and $\cdot$ satisfying:

1. **$(R, +)$ is an abelian group**: closure, associativity, identity (0), inverses (negation), commutativity.
2. **Multiplicative associativity**: For all $a, b, c \in R$, $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.
3. **Distributivity**: For all $a, b, c \in R$:
   - Left: $a \cdot (b + c) = a \cdot b + a \cdot c$
   - Right: $(a + b) \cdot c = a \cdot c + b \cdot c$

**Commutative Ring**: If $a \cdot b = b \cdot a$ for all $a, b \in R$.

**Ring with Unity**: If there exists $1 \in R$ such that $1 \cdot a = a \cdot 1 = a$ for all $a$.

**Integral Domain**: A commutative ring with unity having no zero divisors: if $a \cdot b = 0$, then $a = 0$ or $b = 0$.

**Computational Verification**: Verify additive group axioms first. Verify multiplicative associativity by checking triples. Verify distributivity by checking $(a \cdot (b + c)) = (a \cdot b) + (a \cdot c)$ for all triples. Check for zero divisors by testing all pairs $(a, b)$ with $a, b \neq 0$ and checking if $a \cdot b = 0$.

### Field Axioms

A field $(F, +, \cdot)$ is a commutative ring with unity where every non-zero element has a multiplicative inverse:

1. **$(F, +)$ is an abelian group** with identity 0.
2. **$(F \setminus \{0\}, \cdot)$ is an abelian group** with identity 1.
3. **Distributivity**: $a \cdot (b + c) = a \cdot b + a \cdot c$.

**Computational Verification**: Verify ring axioms and commutativity. For each non-zero element $a$, find $b$ such that $a \cdot b = 1$. The Extended Euclidean Algorithm provides inverse computation in $\mathbb{Z}_p$ for prime $p$.

### Homomorphism Properties

A group homomorphism $\phi: G \to H$ preserves the group operation: $\phi(a \cdot_G b) = \phi(a) \cdot_H \phi(b)$.

**Kernel**: $\ker\phi = \{g \in G : \phi(g) = e_H\}$ is a normal subgroup of $G$.

**Image**: $\text{im}\phi = \{\phi(g) : g \in G\}$ is a subgroup of $H$.

**First Isomorphism Theorem**: $G / \ker\phi \cong \text{im}\phi$ via the canonical map $g \ker\phi \mapsto \phi(g)$.

**Computational Verification**: For each pair $(a, b)$, verify $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$. Compute kernel by finding elements mapping to identity. Compute image by evaluating $\phi$ on all elements. Verify quotient group isomorphism by checking that coset representatives map bijectively to image elements and that operations are preserved.

### Lagrange's Theorem

For finite group $G$ and subgroup $H$, $|H|$ divides $|G|$: $|G| = |H| \cdot [G : H]$ where $[G : H]$ is the index (number of left cosets).

**Computational Verification**: Construct left cosets $gH = \{gh : h \in H\}$ for each $g \in G$. Verify that cosets partition $G$ (disjoint and cover all elements) and that each coset has cardinality $|H|$.

### Fundamental Theorem of Algebra

Every non-constant polynomial $p(z) \in \mathbb{C}[z]$ has at least one complex root. Equivalently, $p(z)$ of degree $n$ factors as $p(z) = c(z - r_1)^{m_1} \cdots (z - r_k)^{m_k}$ where $m_1 + \cdots + m_k = n$.

**Computational Verification**: Use symbolic root-finding (SymPy's `roots` function) to compute all roots with multiplicities. Verify that the sum of multiplicities equals the polynomial degree. Reconstruct the polynomial from its factorization and verify equality with the original.

### Finite Field Construction

The finite field $\mathbb{F}_{p^n}$ is constructed as $\mathbb{F}_p[x] / (m(x))$ where $m(x)$ is an irreducible polynomial of degree $n$ over $\mathbb{F}_p$. The field has $p^n$ elements, and the multiplicative group $\mathbb{F}_{p^n}^*$ is cyclic of order $p^n - 1$.

**Computational Verification**: Implement polynomial arithmetic modulo $m(x)$. Verify that every non-zero element has a multiplicative inverse using the Extended Euclidean Algorithm. Check that the multiplicative order of the field is $p^n - 1$ by verifying $a^{p^n - 1} = 1$ for non-zero $a$.

### Verification Command Templates

**SymPy Group Theory**:
```python
from sympy.combinatorics import PermutationGroup
G = PermutationGroup(generators)
print(f"Order: {G.order()}")
print(f"Is abelian: {G.is_abelian}")
print(f"Center: {G.center()}")
```

**SymPy Polynomial Roots**:
```python
from sympy import roots, Poly
from sympy.abc import x
p = Poly(x**n + ..., x)
root_dict = roots(p, x)
total_roots = sum(root_dict.values())  # sum of multiplicities
```

**Finite Field Matrix Inverse**:
```python
from sympy import Matrix
M = Matrix([[a, b], [c, d]])
M_inv = M.inv_mod(field_char)
```

**Extended GCD for Inverses in Z_n**:
```python
from sympy import gcd, gcdex
a, b = gcdex(element, modulus)  # a*element + b*modulus = gcd
if gcd(element, modulus) == 1:
    inverse = a % modulus
```

This reference provides the formal foundations and computational verification procedures for the core algebraic structures. Apply these axiom checks when implementing custom algebraic types or verifying properties of existing structures. The computational verification converts abstract mathematical definitions into executable predicates, enabling mechanized theorem checking and property-based testing of algebraic implementations.
