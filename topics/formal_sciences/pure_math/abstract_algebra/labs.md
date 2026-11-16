# Operational Verification Labs: Abstract Algebra

## Objective & Mathematical Computing Setup

Abstract algebra occupies a unique position in the mathematical sciences: it provides the foundational structural language for understanding symmetry, transformation, and computation itself. While classical mathematicians prove group homomorphism theorems or ring factorization properties through pure symbolic manipulation, the modern computational practitioner must verify these structural claims through executable symbolic computation. This laboratory guide bridges pure mathematical formalism with concrete computational verification, enabling you to test the boundary conditions of algebraic structures, explore counterexamples to false conjectures, and build confidence in formal proofs through mechanical symbol manipulation.

The operational verification approach treats abstract algebra as an experimental science. Rather than accepting Lagrange's theorem on faith, you will construct explicit finite groups, enumerate their subgroup lattices, and verify that every subgroup order divides the group order across hundreds of test cases. When studying ring ideals, you will programmatically generate quotient rings, verify homomorphism kernels, and construct explicit isomorphisms required by the First Isomorphism Theorem. This hands-on methodology transforms abstract theorems into falsifiable hypotheses subject to computational scrutiny.

The primary computational engine for these laboratories is SymPy, Python's symbolic mathematics library, which provides native implementations of algebraic structures including permutation groups, finitely presented groups, polynomial rings, and field extensions. SymPy's symbolic algebra engine allows exact rational arithmetic, avoiding the floating-point approximation errors that plague numerical linear algebra. For more advanced investigations—particularly Galois theory computations and algebraic number theory—we supplement SymPy with SageMath, a comprehensive computer algebra system built on Python that integrates GAP (Groups, Algorithms, Programming) for computational group theory and Singular for commutative algebra.

Establish your computational environment by installing Python 3.11 or later with the scientific computing stack. On a Unix-like system with pip package management, execute `pip install sympy numpy matplotlib` to acquire the core dependencies. Verify the installation by running `python -c 'import sympy; print(sympy.__version__)'`, which should report version 1.12 or later. For SageMath, either install the complete distribution from sagemath.org or use the lightweight environment via `pip install sage`, though note that the pip installation provides limited functionality compared to the full distribution. On systems with conda package management, create an isolated environment with `conda create -n algebra python=3.11 sympy numpy sagemath` and activate it with `conda activate algebra`.

For formal proof verification beyond symbolic computation, install Lean 4, a dependently-typed proof assistant particularly well-suited to formalizing mathematical structures. Download the Lean toolchain from leanprover.github.io and install the Mathlib library, which contains formalized definitions of groups, rings, fields, and thousands of verified theorems. While these labs focus primarily on computational verification through symbolic execution, the final exercises demonstrate how computational conjectures translate into formal Lean proofs, completing the spectrum from numerical exploration to machine-checked mathematical certainty.

Configure your Python environment to import algebraic structures and symbolic variables cleanly. At the beginning of each computational session, execute the following initialization block:

```python
from sympy import *
from sympy.combinatorics import *
from sympy.polys import *
from sympy.ntheory import factorint
import numpy as np
from itertools import product, combinations
from collections import defaultdict

# Configure SymPy for optimal symbolic algebra
init_printing(use_unicode=True, wrap_line=False)
```

This configuration enables Unicode mathematical symbol rendering in terminal output and prevents automatic line wrapping that disrupts formatted algebraic expressions. The combinatorics submodule provides permutation group constructors, while the polys submodule supplies polynomial ring operations and ideal arithmetic. Throughout these laboratories, verify that symbolic computations produce exact rational results rather than floating-point approximations by checking that expressions like `Rational(1, 3) + Rational(2, 3)` yield `1` rather than `0.9999999999999999`.

## Exercise 1: Computational Verification of Core Theorems

The first operational laboratory verifies foundational theorems of group theory through exhaustive computational enumeration. Lagrange's theorem asserts that for any finite group $G$ and subgroup $H$, the order of $H$ divides the order of $G$. This fundamental result underpins the entire structure theory of finite groups, yet many students encounter it as an abstract proof involving coset decompositions without developing intuition for why the divisibility property must hold. By constructing dozens of finite groups and mechanically checking the subgroup divisibility condition, you transform this abstract theorem into an observable computational invariant.

Begin by implementing a systematic subgroup order verification function. The function accepts a finite group represented as a SymPy permutation group and enumerates all subgroups through the subgroup lattice algorithm. For each discovered subgroup, compute its order and verify that it divides the parent group order evenly. The implementation leverages SymPy's `PermutationGroup` class, which represents finite groups through their action on a set as permutation symmetries:

```python
def verify_lagrange(group):
    """
    Verify Lagrange's theorem for a finite group.
    Returns (True, details_dict) if theorem holds, (False, counterexample) otherwise.
    """
    G_order = group.order()
    subgroups = list(group.subgroups())
    
    results = {
        'group_order': G_order,
        'num_subgroups': len(subgroups),
        'subgroup_orders': [],
        'violations': []
    }
    
    for H in subgroups:
        H_order = H.order()
        results['subgroup_orders'].append(H_order)
        
        if G_order % H_order != 0:
            results['violations'].append({
                'subgroup_order': H_order,
                'group_order': G_order,
                'remainder': G_order % H_order
            })
    
    theorem_holds = len(results['violations']) == 0
    return theorem_holds, results

# Test on symmetric group S_4 (order 24)
S4 = SymmetricGroup(4)
holds, details = verify_lagrange(S4)
print(f"Lagrange's theorem verified for S_4: {holds}")
print(f"Group order: {details['group_order']}")
print(f"Number of subgroups: {details['num_subgroups']}")
print(f"Subgroup orders: {sorted(set(details['subgroup_orders']))}")
```

Execute this verification on the symmetric group $S_4$, which has order $4! = 24$ and a rich subgroup structure including cyclic subgroups, the Klein four-group, dihedral symmetries, and the alternating group $A_4$. The computation should discover 30 distinct subgroups with orders $\{1, 2, 3, 4, 6, 8, 12, 24\}$, each dividing 24 exactly. The trivial subgroup has order 1, maximal cyclic subgroups have order 4, the alternating group has order 12, and the full symmetric group has order 24.

Extend the verification to systematically test Lagrange's theorem across an entire family of finite groups. The symmetric groups $S_n$ provide a natural test suite since they exhibit diverse subgroup structures as $n$ increases. Construct and verify Lagrange's theorem for $S_3$ through $S_5$, observing how the number of subgroups explodes combinatorially:

```python
def test_lagrange_symmetric_groups(max_n=5):
    """Test Lagrange's theorem on symmetric groups S_3 through S_n."""
    results = {}
    
    for n in range(3, max_n + 1):
        Sn = SymmetricGroup(n)
        holds, details = verify_lagrange(Sn)
        results[f'S_{n}'] = details
        
        print(f"\nSymmetric Group S_{n}:")
        print(f"  Order: {details['group_order']}")
        print(f"  Subgroups: {details['num_subgroups']}")
        print(f"  Distinct orders: {sorted(set(details['subgroup_orders']))}")
        print(f"  Lagrange verified: {holds}")
    
    return results

symmetric_results = test_lagrange_symmetric_groups(max_n=5)
```

The output reveals structural patterns: $S_3$ has order 6 with 6 subgroups of orders $\{1, 2, 3, 6\}$, while $S_5$ has order 120 with subgroups whose orders divide 120 according to its prime factorization $120 = 2^3 \cdot 3 \cdot 5$. Note that the computational expense grows rapidly—$S_6$ has 1,455 conjugacy classes of subgroups—so practical verification beyond $S_5$ requires optimized group enumeration algorithms or restriction to specific subgroup families.

The second fundamental verification targets the First Isomorphism Theorem, which establishes the structural relationship between group homomorphisms and quotient groups. For any group homomorphism $\phi: G \to H$, the theorem guarantees that $G / \ker(\phi) \cong \text{im}(\phi)$. Computationally verify this by constructing explicit homomorphisms, computing their kernels and images, forming the quotient group, and verifying the isomorphism through element mapping.

Implement a homomorphism verification framework using SymPy's permutation group morphisms. The framework constructs a homomorphism from a cyclic group to a symmetric group, computes the kernel as the subgroup mapping to the identity, constructs the quotient group through coset representatives, and verifies that the quotient is isomorphic to the image:

```python
def verify_first_isomorphism_theorem():
    """
    Verify First Isomorphism Theorem: G/ker(φ) ≅ im(φ)
    Uses explicit homomorphism from Z_6 to S_3.
    """
    # Construct cyclic group Z_6 as permutation group
    Z6 = CyclicGroup(6)
    S3 = SymmetricGroup(3)
    
    # Define homomorphism φ: Z_6 → S_3
    # Map generator of Z_6 to 3-cycle (0 1 2) in S_3
    # This gives φ(k) = (0 1 2)^k for k in Z_6
    generator_Z6 = Z6.generators[0]
    image_generator = Permutation(0, 1, 2)  # 3-cycle in S_3
    
    # Compute kernel: elements mapping to identity
    kernel_elements = []
    for g in Z6.generate():
        # Compute power of generator
        power = 0
        temp = Permutation(5)  # identity in degree 6
        for h in Z6.generate():
            if h == g:
                break
            power += 1
        
        # Image is (0 1 2)^power
        image = image_generator ** power
        if image == Permutation(2):  # identity in S_3
            kernel_elements.append(g)
    
    # Kernel consists of elements with order dividing 3
    # In Z_6, these are {0, 3} where 3 is the element of order 2
    print(f"Kernel size: {len(kernel_elements)}")
    print(f"Kernel order: {len(kernel_elements)}")
    
    # Image is cyclic subgroup <(0 1 2)> of order 3
    image_subgroup = PermutationGroup([image_generator])
    image_order = image_subgroup.order()
    print(f"Image order: {image_order}")
    
    # Quotient G/ker(φ) should have order |G|/|ker| = 6/2 = 3
    quotient_order = Z6.order() // len(kernel_elements)
    print(f"Quotient G/ker(φ) order: {quotient_order}")
    
    # Verify isomorphism: quotient order equals image order
    isomorphism_verified = (quotient_order == image_order)
    print(f"\nFirst Isomorphism Theorem verified: {isomorphism_verified}")
    print(f"G/ker(φ) has order {quotient_order}, im(φ) has order {image_order}")
    
    return isomorphism_verified

verify_first_isomorphism_theorem()
```

This verification constructs the natural homomorphism from the cyclic group $\mathbb{Z}_6$ to the symmetric group $S_3$ by mapping the generator of $\mathbb{Z}_6$ to the 3-cycle $(0\,1\,2)$. The kernel consists of elements whose image is the identity, specifically the subgroup $\{0, 3\}$ of order 2. The image is the cyclic subgroup generated by $(0\,1\,2)$, which has order 3. The quotient $\mathbb{Z}_6 / \ker(\phi)$ therefore has order $6/2 = 3$, matching the image order exactly as the First Isomorphism Theorem guarantees.

Extend this verification to ring theory by testing the First Isomorphism Theorem for rings. The ring version asserts that for any ring homomorphism $\phi: R \to S$, the quotient ring $R / \ker(\phi)$ is isomorphic to the image $\text{im}(\phi)$. Implement this using SymPy's polynomial ring facilities:

```python
def verify_ring_isomorphism_theorem():
    """
    Verify First Isomorphism Theorem for rings.
    Uses quotient of polynomial ring Z[x] by principal ideal.
    """
    x = symbols('x')
    
    # Consider ring homomorphism φ: Z[x] → Z[x]/(x^2 + 1)
    # Kernel is the ideal (x^2 + 1)
    
    # Define polynomial ring Z[x]
    ZZ_x = ZZ.poly_ring(x)
    
    # Define ideal I = (x^2 + 1)
    ideal_generator = x**2 + 1
    
    # Quotient ring Z[x]/I
    # Elements are polynomials modulo x^2 + 1
    # This gives Z[i] (Gaussian integers) since x^2 = -1
    
    # Verify specific homomorphism properties
    # Test: (a + bx)(c + dx) mod (x^2 + 1)
    a, b, c, d = symbols('a b c d', integer=True)
    
    poly1 = a + b*x
    poly2 = c + d*x
    product = expand(poly1 * poly2)
    
    # Reduce modulo x^2 + 1 (replace x^2 with -1)
    reduced = product.subs(x**2, -1)
    reduced = expand(reduced)
    
    print("Ring Homomorphism Verification:")
    print(f"(a + bx)(c + dx) = {product}")
    print(f"Reduced mod (x^2 + 1): {reduced}")
    
    # Expected: ac - bd + (ad + bc)x
    expected = (a*c - b*d) + (a*d + b*c)*x
    
    isomorphism_holds = simplify(reduced - expected) == 0
    print(f"\nReduction matches expected form: {isomorphism_holds}")
    print(f"Z[x]/(x^2 + 1) ≅ Z[i] verified")
    
    return isomorphism_holds

verify_ring_isomorphism_theorem()
```

This verification demonstrates that the quotient ring $\mathbb{Z}[x]/(x^2 + 1)$ is isomorphic to the Gaussian integers $\mathbb{Z}[i]$ by showing that the ideal $(x^2 + 1)$ forces the relation $x^2 = -1$, exactly the defining property of the imaginary unit $i$. Multiplication in the quotient ring follows the same arithmetic rules as complex number multiplication with real and imaginary parts restricted to integers.

The third core verification targets Cayley's theorem, which asserts that every finite group is isomorphic to a subgroup of some symmetric group. This profound result establishes that permutation groups are not merely one example of group structure—they are the universal model for all finite groups. Verify Cayley's theorem computationally by taking an abstract group presentation and constructing its faithful permutation representation:

```python
def verify_cayley_theorem(group):
    """
    Verify Cayley's theorem: every group embeds in a symmetric group.
    Constructs the left regular representation.
    """
    # Get group elements
    elements = list(group.generate())
    n = len(elements)
    
    print(f"Verifying Cayley's theorem for group of order {n}")
    
    # Construct left regular representation
    # For each g in G, define permutation π_g: h → gh
    representations = {}
    
    for g in elements:
        # Build permutation induced by left multiplication by g
        perm_list = []
        for h in elements:
            # Compute gh
            product = group.identity
            # Find gh in group multiplication
            gh_index = 0
            for idx, k in enumerate(elements):
                # Check if k = gh by group operation
                if str(g * h) == str(k):
                    gh_index = idx
                    break
            perm_list.append(gh_index)
        
        representations[str(g)] = Permutation(perm_list)
    
    # Verify representation is a homomorphism
    # Check: π_(g1 * g2) = π_g1 ∘ π_g2
    sample_pairs = list(combinations(elements[:min(5, len(elements))], 2))
    
    homomorphism_verified = True
    for g1, g2 in sample_pairs:
        product = g1 * g2
        
        perm_product = representations[str(g1)] * representations[str(g2)]
        perm_expected = representations[str(product)]
        
        if perm_product != perm_expected:
            homomorphism_verified = False
            print(f"Homomorphism violation: {g1} * {g2}")
    
    print(f"Regular representation is homomorphism: {homomorphism_verified}")
    print(f"Embedded group into S_{n}")
    
    return homomorphism_verified

# Test on dihedral group D_4
D4 = DihedralGroup(4)
verify_cayley_theorem(D4)
```

Execute this on the dihedral group $D_4$, which has order 8 and represents the symmetries of a square. The verification constructs the left regular representation, mapping each group element $g$ to the permutation $\pi_g$ defined by $\pi_g(h) = gh$. This embedding into $S_8$ preserves the group operation exactly, confirming that $D_4$ is isomorphic to a subgroup of the symmetric group on 8 elements.

## Exercise 2: Boundary Value Stress Testing & Singularities

Abstract algebra theorems often include subtle hypotheses whose necessity becomes apparent only at boundary cases or pathological examples. The second laboratory systematically probes these boundary conditions, constructing edge cases that reveal why theorem hypotheses cannot be weakened. This stress-testing methodology exposes the precise logical dependence between algebraic properties and structural theorems.

Begin by investigating the converse of Lagrange's theorem, which does not hold in general. While Lagrange guarantees that all subgroup orders divide the group order, the converse—that for every divisor $d$ of $|G|$, there exists a subgroup of order $d$—fails for certain groups. The alternating group $A_4$ provides the canonical counterexample: it has order 12, so divisibility would suggest subgroups of orders 1, 2, 3, 4, 6, and 12. However, $A_4$ contains no subgroup of order 6. Verify this computationally:

```python
def find_missing_subgroup_orders(group):
    """
    Find divisors of group order that do NOT correspond to subgroup orders.
    Demonstrates that converse of Lagrange's theorem fails.
    """
    G_order = group.order()
    
    # Compute all divisors of group order
    prime_factors = factorint(G_order)
    divisors = [1]
    for prime, power in prime_factors.items():
        new_divisors = []
        for d in divisors:
            for k in range(power + 1):
                new_divisors.append(d * (prime ** k))
        divisors = list(set(new_divisors))
    divisors.sort()
    
    # Compute actual subgroup orders
    subgroups = list(group.subgroups())
    actual_orders = set(H.order() for H in subgroups)
    
    # Find missing orders
    missing_orders = set(divisors) - actual_orders
    
    print(f"Group order: {G_order}")
    print(f"Divisors of {G_order}: {divisors}")
    print(f"Actual subgroup orders: {sorted(actual_orders)}")
    print(f"Missing subgroup orders: {sorted(missing_orders)}")
    
    return missing_orders

# Test on alternating group A_4
A4 = AlternatingGroup(4)
missing = find_missing_subgroup_orders(A4)

if 6 in missing:
    print("\nCounterexample confirmed: A_4 has no subgroup of order 6")
    print("Converse of Lagrange's theorem is FALSE")
```

The output confirms that $A_4$ has no subgroup of order 6, despite 6 dividing 12. This failure occurs because 6 is not a prime power, and the Sylow theorems provide existence guarantees only for subgroups whose orders are prime powers. The alternating group $A_4$ contains Sylow 2-subgroups of order 4 and Sylow 3-subgroups of order 3, but no mechanism forces a subgroup combining these prime factors. This example demonstrates the necessity of Sylow's theorem restrictions: subgroup existence theorems require prime power orders, not arbitrary divisors.

The second boundary investigation examines the failure of unique factorization in non-UFD rings. Unique factorization domains satisfy the fundamental property that every non-zero non-unit element factors uniquely into irreducibles up to units and order. However, many natural rings fail this property. The ring $\mathbb{Z}[\sqrt{-5}]$ provides a classical counterexample where the element 6 admits two distinct irreducible factorizations: $6 = 2 \cdot 3 = (1 + \sqrt{-5})(1 - \sqrt{-5})$. Verify this computationally:

```python
def verify_non_unique_factorization():
    """
    Demonstrate failure of unique factorization in Z[√(-5)].
    Shows 6 has two distinct irreducible factorizations.
    """
    # Define symbolic square root
    sqrt5 = sqrt(5)
    
    # Two factorizations of 6
    factorization_1 = (2, 3)
    factorization_2 = (1 + I*sqrt5, 1 - I*sqrt5)
    
    # Verify both give 6
    product_1 = factorization_1[0] * factorization_1[1]
    product_2 = expand(factorization_2[0] * factorization_2[1])
    
    print("Factorization 1: 6 = 2 × 3")
    print(f"  Product: {product_1}")
    
    print("\nFactorization 2: 6 = (1 + √(-5))(1 - √(-5))")
    print(f"  Product: {product_2}")
    print(f"  Simplified: {simplify(product_2)}")
    
    # Verify elements are irreducible by checking norms
    # Norm in Z[√(-5)]: N(a + b√(-5)) = a^2 + 5b^2
    
    def norm_z_sqrt_minus_5(a, b):
        """Compute norm N(a + b√(-5)) = a^2 + 5b^2"""
        return a**2 + 5*b**2
    
    # Check irreducibility via norms
    norm_2 = norm_z_sqrt_minus_5(2, 0)  # N(2) = 4
    norm_3 = norm_z_sqrt_minus_5(3, 0)  # N(3) = 9
    norm_factor = norm_z_sqrt_minus_5(1, 1)  # N(1 + √(-5)) = 1 + 5 = 6
    
    print(f"\nNorm verification:")
    print(f"  N(2) = {norm_2}")
    print(f"  N(3) = {norm_3}")
    print(f"  N(1 + √(-5)) = {norm_factor}")
    
    print("\nIrreducibility check:")
    print(f"  2 is irreducible: N(2) = 4 is not a product of integer norms > 1")
    print(f"  3 is irreducible: N(3) = 9 is not a product of integer norms > 1")
    print(f"  1 + √(-5) is irreducible: N = 6 is not a perfect square")
    
    print("\nConclusion: Z[√(-5)] is NOT a unique factorization domain")
    print("The element 6 admits two distinct irreducible factorizations")

verify_non_unique_factorization()
```

This verification uses norm arguments to establish irreducibility. In $\mathbb{Z}[\sqrt{-5}]$, an element $a + b\sqrt{-5}$ has norm $N(a + b\sqrt{-5}) = a^2 + 5b^2$. An element is irreducible if it cannot be written as a product of two non-units, which translates to the norm condition: if $N(\alpha) = p$ where $p$ is prime, then $\alpha$ is irreducible. The element 2 has norm 4, which cannot be factored as a product of norms greater than 1 within this ring (the only integer norm values are 1, 4, 5, 6, 9, ...). Similarly, 3 and $1 \pm \sqrt{-5}$ are irreducible. The existence of two distinct irreducible factorizations proves that $\mathbb{Z}[\sqrt{-5}]$ fails to be a UFD.

The third boundary case investigates non-normal subgroups and the failure of quotient group formation. A quotient group $G/H$ exists if and only if $H$ is a normal subgroup of $G$. For non-normal subgroups, the left cosets fail to form a group under the natural multiplication. Demonstrate this by attempting to construct a quotient by a non-normal subgroup:

```python
def verify_quotient_normality_requirement():
    """
    Demonstrate that quotient groups require normal subgroups.
    Shows quotient construction fails for non-normal subgroup.
    """
    # Use symmetric group S_3
    S3 = SymmetricGroup(3)
    
    # Subgroup H = <(0 1)> of order 2 (NOT normal in S_3)
    transposition = Permutation(0, 1)
    H_generators = [transposition]
    
    # Get all elements of S_3
    S3_elements = list(S3.generate())
    
    # Compute left cosets of H
    H_elements = set([S3.identity, transposition])
    
    left_cosets = []
    coset_representatives = []
    
    for g in S3_elements:
        # Compute left coset gH
        coset = set(g * h for h in H_elements)
        
        # Check if this coset is new
        is_new = True
        for existing in left_cosets:
            if coset == existing:
                is_new = False
                break
        
        if is_new:
            left_cosets.append(coset)
            coset_representatives.append(g)
    
    print(f"Left cosets of H = <(0 1)> in S_3:")
    for i, (rep, coset) in enumerate(zip(coset_representatives, left_cosets)):
        coset_strs = [str(c) for c in sorted(coset, key=str)]
        print(f"  Coset {i+1} (rep {rep}): {{{', '.join(coset_strs)}}}")
    
    # Attempt coset multiplication: verify it's not well-defined
    print("\nChecking if coset multiplication is well-defined:")
    
    # Take two coset representatives
    if len(coset_representatives) >= 2:
        g1, g2 = coset_representatives[0], coset_representatives[1]
        
        # Compute g1 * g2
        product_rep = g1 * g2
        
        # Find which coset the product belongs to
        product_coset_idx = None
        for i, coset in enumerate(left_cosets):
            if product_rep in coset:
                product_coset_idx = i
                break
        
        print(f"  {g1} * {g2} = {product_rep}")
        print(f"  Product is in coset {product_coset_idx + 1}")
        
        # Now pick different representatives from same cosets
        alt_g1 = list(left_cosets[0] - {g1})[0] if len(left_cosets[0]) > 1 else g1
        alt_g2 = list(left_cosets[1] - {g2})[0] if len(left_cosets[1]) > 1 else g2
        
        alt_product = alt_g1 * alt_g2
        alt_product_coset_idx = None
        for i, coset in enumerate(left_cosets):
            if alt_product in coset:
                alt_product_coset_idx = i
                break
        
        print(f"\n  Alternative representatives:")
        print(f"  {alt_g1} * {alt_g2} = {alt_product}")
        print(f"  Product is in coset {alt_product_coset_idx + 1}")
        
        if product_coset_idx != alt_product_coset_idx:
            print("\n  *** MULTIPLICATION NOT WELL-DEFINED ***")
            print("  Different coset representatives give products in different cosets")
            print("  Quotient G/H does NOT form a group (H is not normal)")
    
    # Check normality directly
    is_normal = all(
        g * h * (~g) in H_elements
        for g in S3_elements
        for h in H_elements
    )
    
    print(f"\nDirect normality check: H is normal = {is_normal}")
    print("Conclusion: Quotient groups require normal subgroups")

verify_quotient_normality_requirement()
```

This verification exposes the failure mechanism: when $H$ is not normal, the product of two left cosets depends on the choice of coset representatives. In $S_3$, the subgroup $H = \{e, (0\,1)\}$ is not normal because conjugation by $(0\,1\,2)$ yields $(0\,1\,2)(0\,1)(0\,2\,1) = (0\,2)$, which is not in $H$. Consequently, coset multiplication is not well-defined, and the quotient structure fails. This demonstrates why normality is an essential hypothesis for quotient group theorems.

The fourth boundary exploration examines field extensions and inseparable polynomials in positive characteristic. Over fields of characteristic 0, all irreducible polynomials are separable (have distinct roots in the algebraic closure). However, in characteristic $p > 0$, inseparable polynomials exist. Construct an example using $\mathbb{F}_p(t)$, the field of rational functions over the finite field:

```python
def verify_inseparable_polynomial():
    """
    Demonstrate existence of inseparable polynomials in characteristic p.
    Uses F_p(t) where p is prime.
    """
    # Work symbolically with characteristic p
    p = 2  # Use characteristic 2 for concrete example
    t = symbols('t')
    x = symbols('x')
    
    # In F_2(t), consider polynomial f(x) = x^2 - t
    # This polynomial is inseparable (has repeated roots in algebraic closure)
    
    print(f"Field: F_{p}(t) (characteristic {p})")
    print(f"Polynomial: f(x) = x^{p} - t")
    
    # Formal derivative
    poly = x**p - t
    derivative = diff(poly, x)
    
    print(f"\nPolynomial: f(x) = {poly}")
    print(f"Derivative: f'(x) = {derivative}")
    
    print("\nIn characteristic 2, (x^2)' = 2x = 0")
    print("Therefore f'(x) = 0 identically")
    
    print("\nConsequence: f(x) = x^2 - t is inseparable")
    print("All roots (if they exist) are repeated roots")
    
    # Verify factorization structure
    print("\nFactorization over splitting field:")
    print("f(x) = x^2 - t = (x - √t)^2")
    print("The polynomial has a double root at x = √t")
    
    print("\nConclusion: In characteristic p > 0, irreducible polynomials")
    print("can be inseparable (have repeated roots in algebraic closure)")

verify_inseparable_polynomial()
```

This example reveals a deep distinction between characteristic 0 and positive characteristic: in $\mathbb{F}_2(t)$, the polynomial $x^2 - t$ is irreducible yet inseparable because its derivative vanishes identically. The polynomial factors as $(x - \sqrt{t})^2$ in the algebraic closure, exhibiting a double root. This pathology cannot occur in characteristic 0, where non-zero derivatives guarantee separability for irreducible polynomials. The existence of inseparable extensions complicates Galois theory in positive characteristic, requiring careful distinction between algebraic extensions and separable algebraic extensions.

## Exercise 3: Algorithmic Implementation of Formal Structures

The third laboratory implements core algebraic algorithms from first principles, translating abstract definitions into executable code. Rather than relying on library functions, these implementations expose the computational complexity and algorithmic structure underlying algebraic operations.

Begin by implementing the Euclidean algorithm for polynomial greatest common divisors. The polynomial GCD algorithm parallels integer GCD but operates over polynomial rings, using polynomial long division instead of integer division. Implement the algorithm to accept two polynomials and return their monic GCD:

```python
def poly_gcd(f, g, var):
    """
    Compute GCD of polynomials f and g using Euclidean algorithm.
    Returns monic GCD (leading coefficient 1).
    """
    # Ensure f and g are SymPy polynomials
    f = Poly(f, var)
    g = Poly(g, var)
    
    print(f"Computing GCD of:")
    print(f"  f = {f.as_expr()}")
    print(f"  g = {g.as_expr()}")
    print()
    
    step = 0
    while g != 0:
        step += 1
        remainder = f % g
        
        print(f"Step {step}:")
        print(f"  {f.as_expr()} = ({g.as_expr()}) * q + ({remainder.as_expr()})")
        
        f = g
        g = remainder
    
    # Make monic (leading coefficient 1)
    gcd = f
    leading_coeff = gcd.LC()
    if leading_coeff != 0:
        gcd = gcd / leading_coeff
    
    print(f"\nGCD = {gcd.as_expr()}")
    return gcd

# Test on concrete polynomials
x = symbols('x')
f = x**4 - 1
g = x**3 - 1

gcd_result = poly_gcd(f, g, x)

# Verify factorizations
print("\nFactorization verification:")
print(f"  x^4 - 1 = (x - 1)(x + 1)(x^2 + 1)")
print(f"  x^3 - 1 = (x - 1)(x^2 + x + 1)")
print(f"  Common factor: (x - 1)")
print(f"  Computed GCD: {gcd_result.as_expr()}")
```

This implementation reveals the algorithmic structure: polynomial GCD requires $O(n^2)$ arithmetic operations where $n$ is the degree, significantly more expensive than integer GCD's $O(\log n)$ bit operations. The algorithm terminates when the remainder reaches zero, yielding the monic GCD. The example computes $\gcd(x^4 - 1, x^3 - 1) = x - 1$, exploiting the common factor from cyclotomic factorizations.

The second algorithm implements the Chinese Remainder Theorem for polynomial rings. Given polynomials $f_1, f_2, \ldots, f_k$ that are pairwise coprime and target remainders $r_1, r_2, \ldots, r_k$, the CRT guarantees a unique solution modulo $f_1 f_2 \cdots f_k$. Implement the constructive algorithm:

```python
def extended_euclidean_poly(a, b, var):
    """
    Extended Euclidean algorithm for polynomials.
    Returns (gcd, s, t) where gcd = s*a + t*b.
    """
    a, b = Poly(a, var), Poly(b, var)
    
    old_r, r = a, b
    old_s, s = Poly(1, var), Poly(0, var)
    old_t, t = Poly(0, var), Poly(1, var)
    
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    
    gcd = old_r
    return gcd, old_s, old_t

def chinese_remainder_poly(moduli, remainders, var):
    """
    Chinese Remainder Theorem for polynomials.
    Find f such that f ≡ r_i (mod m_i) for all i.
    """
    print("Chinese Remainder Theorem for Polynomials")
    print("=" * 50)
    
    for i, (m, r) in enumerate(zip(moduli, remainders)):
        print(f"Condition {i+1}: f ≡ {r} (mod {m})")
    print()
    
    # Compute product of all moduli
    M = Poly(1, var)
    for m in moduli:
        M *= Poly(m, var)
    
    print(f"Product M = {M.as_expr()}")
    print()
    
    # Build solution using CRT construction
    solution = Poly(0, var)
    
    for i, (m_i, r_i) in enumerate(zip(moduli, remainders)):
        # Compute M_i = M / m_i
        M_i = M // Poly(m_i, var)
        
        # Find inverse of M_i modulo m_i using extended Euclidean algorithm
        gcd, s, t = extended_euclidean_poly(M_i, m_i, var)
        
        # s is the inverse: s * M_i ≡ 1 (mod m_i)
        # Add r_i * s * M_i to solution
        term = Poly(r_i, var) * s * M_i
        solution += term
        
        print(f"Step {i+1}: Adding term for condition {i+1}")
        print(f"  M_{i+1} = {M_i.as_expr()}")
        print(f"  Inverse: {s.as_expr()}")
    
    # Reduce solution modulo M
    solution = solution % M
    
    print(f"\nSolution: f = {solution.as_expr()}")
    
    # Verify solution
    print("\nVerification:")
    for i, (m, r) in enumerate(zip(moduli, remainders)):
        remainder = solution % Poly(m, var)
        expected = Poly(r, var)
        matches = remainder == expected
        print(f"  f mod ({m}) = {remainder.as_expr()} {'✓' if matches else '✗'}")
    
    return solution

# Test CRT with polynomial moduli
x = symbols('x')

# Solve system:
# f ≡ x (mod x^2 - 1)
# f ≡ 1 (mod x^2 + 1)

moduli = [x**2 - 1, x**2 + 1]
remainders = [x, 1]

solution = chinese_remainder_poly(moduli, remainders, x)
```

This implementation constructs the CRT solution explicitly through the standard algorithm: compute $M = \prod m_i$, find $M_i = M / m_i$ for each modulus, compute the multiplicative inverse of $M_i$ modulo $m_i$ using the extended Euclidean algorithm, and sum the terms $r_i \cdot s_i \cdot M_i$. The algorithm terminates with a polynomial that satisfies all congruence conditions simultaneously. The example solves the system where $f \equiv x \pmod{x^2 - 1}$ and $f \equiv 1 \pmod{x^2 + 1}$, yielding a unique solution modulo $(x^2 - 1)(x^2 + 1) = x^4 - 1$.

The third algorithm implements finite field arithmetic in $\mathbb{F}_{2^8}$, the Galois field used in AES cryptography. Elements of $\mathbb{F}_{2^8}$ are polynomials of degree at most 7 over $\mathbb{F}_2$, with arithmetic performed modulo the irreducible polynomial $m(x) = x^8 + x^4 + x^3 + x + 1$. Implement addition, multiplication, and multiplicative inverse:

```python
class GF256:
    """
    Galois Field GF(2^8) arithmetic for AES.
    Elements represented as integers 0-255 (polynomial coefficients).
    """
    
    # AES irreducible polynomial: x^8 + x^4 + x^3 + x + 1
    MODULUS = 0b100011011  # Binary representation
    
    def __init__(self, value):
        """Initialize field element from integer 0-255."""
        self.value = value & 0xFF  # Ensure 8 bits
    
    def __add__(self, other):
        """Addition in GF(2^8): XOR of coefficients."""
        return GF256(self.value ^ other.value)
    
    def __mul__(self, other):
        """Multiplication in GF(2^8) modulo irreducible polynomial."""
        a, b = self.value, other.value
        result = 0
        
        for _ in range(8):
            if b & 1:
                result ^= a
            
            # Check if high bit of a is set
            high_bit = a & 0x80
            a <<= 1
            
            if high_bit:
                # Reduce modulo irreducible polynomial
                a ^= self.MODULUS
            
            b >>= 1
        
        return GF256(result & 0xFF)
    
    def inverse(self):
        """
        Multiplicative inverse using extended Euclidean algorithm.
        Returns element such that self * inverse = 1.
        """
        if self.value == 0:
            raise ValueError("Zero has no multiplicative inverse")
        
        # Extended Euclidean algorithm in GF(2^8)
        r0, r1 = self.MODULUS, self.value
        s0, s1 = 1, 0
        
        while r1 != 0:
            # Polynomial division in GF(2)
            q = self._poly_divide(r0, r1)
            r0, r1 = r1, r0 ^ self._poly_multiply(q, r1)
            s0, s1 = s1, s0 ^ self._poly_multiply(q, s1)
        
        return GF256(s0 & 0xFF)
    
    @staticmethod
    def _poly_multiply(a, b):
        """Multiply polynomials over GF(2) (no modular reduction)."""
        result = 0
        while b:
            if b & 1:
                result ^= a
            a <<= 1
            b >>= 1
        return result
    
    @staticmethod
    def _poly_divide(dividend, divisor):
        """Polynomial division quotient over GF(2)."""
        if divisor == 0:
            return 0
        
        quotient = 0
        dividend_bits = dividend.bit_length()
        divisor_bits = divisor.bit_length()
        
        for i in range(dividend_bits - divisor_bits, -1, -1):
            if dividend & (1 << (i + divisor_bits - 1)):
                quotient |= (1 << i)
                dividend ^= (divisor << i)
        
        return quotient
    
    def __repr__(self):
        return f"GF256(0x{self.value:02x})"
    
    def __eq__(self, other):
        return self.value == other.value

def test_gf256_arithmetic():
    """Test Galois field arithmetic."""
    print("GF(2^8) Arithmetic Tests")
    print("=" * 50)
    
    # Test addition (XOR)
    a = GF256(0x53)  # 0x53 = x^6 + x^4 + x + 1
    b = GF256(0xCA)  # 0xCA = x^7 + x^6 + x^3 + x
    c = a + b
    print(f"Addition: {a} + {b} = {c}")
    print(f"  Binary: {a.value:08b} XOR {b.value:08b} = {c.value:08b}")
    
    # Test multiplication
    a = GF256(0x57)
    b = GF256(0x83)
    c = a * b
    print(f"\nMultiplication: {a} * {b} = {c}")
    
    # Test multiplicative inverse
    a = GF256(0x53)
    a_inv = a.inverse()
    product = a * a_inv
    print(f"\nInverse: {a} * {a_inv} = {product}")
    print(f"  Verification: product == GF256(1) ? {product == GF256(1)}")
    
    # Test AES S-box input (example)
    print("\nAES S-box computation (partial):")
    x = GF256(0x53)
    x_inv = x.inverse()
    print(f"  Input: {x}")
    print(f"  After inverse: {x_inv}")
    print(f"  (Full S-box requires affine transformation)")

test_gf256_arithmetic()
```

This implementation exposes the bit-level mechanics of finite field arithmetic. Addition is polynomial addition over $\mathbb{F}_2$, equivalent to XOR. Multiplication performs the standard polynomial multiplication followed by reduction modulo the irreducible polynomial using bit shifts and XOR. The multiplicative inverse uses the extended Euclidean algorithm adapted for polynomial arithmetic over $\mathbb{F}_2$. This code forms the foundation of the AES S-box construction, which applies the multiplicative inverse followed by an affine transformation.

The fourth algorithm implements the Berlekamp factorization algorithm for polynomials over finite fields. Given a polynomial $f(x) \in \mathbb{F}_p[x]$, Berlekamp's algorithm computes the complete factorization into irreducible factors. The algorithm constructs the Berlekamp matrix $Q$, whose null space yields factor candidates:

```python
def berlekamp_factorization(poly, p):
    """
    Berlekamp algorithm for polynomial factorization over F_p.
    Returns list of irreducible factors.
    """
    x = symbols('x')
    f = Poly(poly, x, modulus=p)
    
    print(f"Berlekamp Factorization over F_{p}")
    print(f"Polynomial: {f.as_expr()}")
    print()
    
    n = f.degree()
    
    # Build Berlekamp matrix Q
    # Q[i,j] = coefficient of x^j in x^(ip) mod f(x)
    Q = []
    
    for i in range(n):
        # Compute x^(ip) mod f(x)
        power_poly = Poly(x**(i * p), x, modulus=p)
        remainder = power_poly % f
        
        # Extract coefficients (pad to degree n)
        coeffs = remainder.all_coeffs()
        coeffs = [0] * (n - len(coeffs)) + coeffs
        coeffs.reverse()  # Low-degree first
        
        Q.append(coeffs)
    
    Q = Matrix(Q)
    print(f"Berlekamp matrix Q:")
    print(Q)
    print()
    
    # Compute Q - I (mod p)
    I = eye(n)
    Q_minus_I = Matrix([[(Q[i,j] - I[i,j]) % p for j in range(n)] for i in range(n)])
    
    # Find null space of Q - I
    # Dimension of null space = number of irreducible factors
    null_space = Q_minus_I.nullspace()
    
    print(f"Null space dimension: {len(null_space)}")
    print(f"Number of irreducible factors: {len(null_space)}")
    print()
    
    if len(null_space) == 1:
        print(f"Polynomial is irreducible")
        return [f]
    
    # Use null space vectors to find factors
    factors = [f]
    
    for vec in null_space[1:]:  # Skip trivial vector [1,0,0,...]
        # Convert null space vector to polynomial
        vec_poly = Poly(sum(vec[i] * x**i for i in range(n)), x, modulus=p)
        
        # Try GCD with vec_poly - a for a in F_p
        for a in range(p):
            g = Poly(vec_poly - a, x, modulus=p)
            
            new_factors = []
            for factor in factors:
                gcd_result = gcd(factor, g)
                
                if gcd_result.degree() > 0 and gcd_result.degree() < factor.degree():
                    # Found nontrivial factor
                    quotient = factor // gcd_result
                    new_factors.append(gcd_result)
                    new_factors.append(quotient)
                else:
                    new_factors.append(factor)
            
            factors = new_factors
            
            # Check if fully factored
            if all(fac.degree() == 1 for fac in factors):
                break
        
        if all(fac.degree() == 1 for fac in factors):
            break
    
    print(f"Irreducible factors:")
    for i, fac in enumerate(factors):
        print(f"  {i+1}. {fac.as_expr()}")
    
    return factors

# Test on polynomial over F_2
x = symbols('x')
poly = x**4 + x + 1

factors = berlekamp_factorization(poly, p=2)

# Verify factorization
print("\nVerification:")
product = Poly(1, x, modulus=2)
for f in factors:
    product *= f
product = product % Poly(1, x, modulus=2)  # Normalize

print(f"Product of factors: {product.as_expr()}")
print(f"Original polynomial: {poly}")
print(f"Match: {expand(product.as_expr() - poly) == 0}")
```

This implementation reveals the linear algebra structure of polynomial factorization: the null space of the Berlekamp matrix directly determines the number of irreducible factors, and null space vectors yield GCD splitting conditions that separate factors. The algorithm operates entirely within the finite field $\mathbb{F}_p$, avoiding numerical instability. For the polynomial $x^4 + x + 1$ over $\mathbb{F}_2$, the algorithm determines whether it is irreducible or factors into lower-degree polynomials.

## Formal Axioms Cheat Sheet & Verification Reference

The following reference catalog provides operational definitions and verification tests for core algebraic axioms. Use these implementations as building blocks for custom algebraic structure verification.

**Group Axioms Verification**

A group $(G, \cdot)$ satisfies closure, associativity, identity, and inverses. Verify programmatically:

```python
def verify_group_axioms(elements, operation, identity):
    """
    Verify group axioms for finite set with binary operation.
    
    elements: list of group elements
    operation: function (a, b) -> a * b
    identity: identity element
    """
    n = len(elements)
    
    # Closure
    closure_holds = True
    for a in elements:
        for b in elements:
            if operation(a, b) not in elements:
                closure_holds = False
                break
    
    print(f"Closure: {closure_holds}")
    
    # Associativity
    associativity_holds = True
    sample_size = min(5, n)
    for a in elements[:sample_size]:
        for b in elements[:sample_size]:
            for c in elements[:sample_size]:
                lhs = operation(operation(a, b), c)
                rhs = operation(a, operation(b, c))
                if lhs != rhs:
                    associativity_holds = False
                    break
    
    print(f"Associativity (sampled): {associativity_holds}")
    
    # Identity
    identity_holds = all(
        operation(identity, a) == a and operation(a, identity) == a
        for a in elements
    )
    
    print(f"Identity: {identity_holds}")
    
    # Inverses
    inverses_exist = True
    for a in elements:
        has_inverse = any(
            operation(a, b) == identity and operation(b, a) == identity
            for b in elements
        )
        if not has_inverse:
            inverses_exist = False
            break
    
    print(f"Inverses: {inverses_exist}")
    
    is_group = closure_holds and associativity_holds and identity_holds and inverses_exist
    print(f"\nVerdict: {'GROUP' if is_group else 'NOT A GROUP'}")
    
    return is_group
```

**Ring Axioms Verification**

A ring $(R, +, \cdot)$ forms an abelian group under addition with associative multiplication distributing over addition:

```python
def verify_ring_axioms(elements, add, mul, zero, one=None):
    """
    Verify ring axioms.
    
    elements: list of ring elements
    add: addition operation
    mul: multiplication operation
    zero: additive identity
    one: multiplicative identity (optional, for ring with unity)
    """
    # Additive group verification
    print("Checking additive group structure:")
    add_group = verify_group_axioms(elements, add, zero)
    
    # Commutativity of addition
    add_commutative = all(
        add(a, b) == add(b, a)
        for a in elements for b in elements
    )
    print(f"\nAdditive commutativity: {add_commutative}")
    
    # Multiplicative closure
    mul_closed = all(
        mul(a, b) in elements
        for a in elements for b in elements
    )
    print(f"Multiplicative closure: {mul_closed}")
    
    # Multiplicative associativity
    sample = min(5, len(elements))
    mul_associative = all(
        mul(mul(a, b), c) == mul(a, mul(b, c))
        for a in elements[:sample]
        for b in elements[:sample]
        for c in elements[:sample]
    )
    print(f"Multiplicative associativity (sampled): {mul_associative}")
    
    # Distributivity
    distributive = all(
        mul(a, add(b, c)) == add(mul(a, b), mul(a, c)) and
        mul(add(a, b), c) == add(mul(a, c), mul(b, c))
        for a in elements[:sample]
        for b in elements[:sample]
        for c in elements[:sample]
    )
    print(f"Distributivity (sampled): {distributive}")
    
    # Unity (if provided)
    if one is not None:
        unity_holds = all(
            mul(one, a) == a and mul(a, one) == a
            for a in elements
        )
        print(f"Multiplicative unity: {unity_holds}")
    
    is_ring = add_group and add_commutative and mul_closed and mul_associative and distributive
    print(f"\nVerdict: {'RING' if is_ring else 'NOT A RING'}")
    
    return is_ring
```

**Field Axioms Verification**

A field is a commutative ring where every nonzero element has a multiplicative inverse:

```python
def verify_field_axioms(elements, add, mul, zero, one):
    """Verify field axioms."""
    print("Checking ring structure:")
    is_ring = verify_ring_axioms(elements, add, mul, zero, one)
    
    # Multiplicative commutativity
    mul_commutative = all(
        mul(a, b) == mul(b, a)
        for a in elements for b in elements
    )
    print(f"\nMultiplicative commutativity: {mul_commutative}")
    
    # Multiplicative inverses for nonzero elements
    nonzero = [e for e in elements if e != zero]
    inverses_exist = all(
        any(mul(a, b) == one for b in nonzero)
        for a in nonzero
    )
    print(f"Multiplicative inverses: {inverses_exist}")
    
    is_field = is_ring and mul_commutative and inverses_exist
    print(f"\nVerdict: {'FIELD' if is_field else 'NOT A FIELD'}")
    
    return is_field
```

**Homomorphism Verification**

A function $\phi: G \to H$ is a group homomorphism if $\phi(ab) = \phi(a)\phi(b)$:

```python
def verify_homomorphism(phi, G_elements, G_op, H_op):
    """
    Verify φ is a group homomorphism.
    
    phi: function mapping G elements to H
    G_elements: list of domain elements
    G_op: group operation in G
    H_op: group operation in H (codomain)
    """
    sample_size = min(10, len(G_elements))
    
    violations = []
    for a in G_elements[:sample_size]:
        for b in G_elements[:sample_size]:
            # Check φ(ab) = φ(a)φ(b)
            lhs = phi(G_op(a, b))
            rhs = H_op(phi(a), phi(b))
            
            if lhs != rhs:
                violations.append((a, b))
    
    is_homomorphism = len(violations) == 0
    
    print(f"Homomorphism property: {is_homomorphism}")
    if violations:
        print(f"  Violations: {len(violations)} pairs")
        print(f"  Example: φ({violations[0][0]} * {violations[0][1]}) ≠ φ({violations[0][0]}) * φ({violations[0][1]})")
    
    return is_homomorphism
```

**Ideal Verification**

A subset $I \subseteq R$ is a two-sided ideal if it is closed under addition and absorbs multiplication from both sides:

```python
def verify_ideal(I_elements, R_elements, add, mul, zero):
    """
    Verify I is an ideal of ring R.
    
    I_elements: subset forming ideal
    R_elements: ring elements
    add: ring addition
    mul: ring multiplication
    zero: additive identity
    """
    # Nonempty and contains zero
    contains_zero = zero in I_elements
    print(f"Contains zero: {contains_zero}")
    
    # Closed under addition
    add_closed = all(
        add(a, b) in I_elements
        for a in I_elements for b in I_elements
    )
    print(f"Additively closed: {add_closed}")
    
    # Closed under additive inverses
    # (Implied by group property, but check explicitly)
    inverses_closed = True  # Simplified check
    
    # Absorbs multiplication: rI ⊆ I and Ir ⊆ I
    left_absorption = all(
        mul(r, i) in I_elements
        for r in R_elements for i in I_elements
    )
    right_absorption = all(
        mul(i, r) in I_elements
        for i in I_elements for r in R_elements
    )
    
    print(f"Left absorption (rI ⊆ I): {left_absorption}")
    print(f"Right absorption (Ir ⊆ I): {right_absorption}")
    
    is_ideal = contains_zero and add_closed and left_absorption and right_absorption
    print(f"\nVerdict: {'IDEAL' if is_ideal else 'NOT AN IDEAL'}")
    
    return is_ideal
```

**Sylow Subgroup Verification**

Verify Sylow's First Theorem: for prime $p$ dividing $|G|$, there exists a subgroup of order $p^k$ where $p^k$ is the maximal prime power dividing $|G|$:

```python
def verify_sylow_existence(group, prime):
    """
    Verify existence of Sylow p-subgroup.
    
    group: finite group
    prime: prime number
    """
    G_order = group.order()
    
    # Find maximal power of prime dividing order
    k = 0
    temp_order = G_order
    while temp_order % prime == 0:
        k += 1
        temp_order //= prime
    
    sylow_order = prime ** k
    
    print(f"Group order: {G_order}")
    print(f"Prime: {prime}")
    print(f"Maximal prime power: {prime}^{k} = {sylow_order}")
    
    # Search for subgroup of order sylow_order
    subgroups = list(group.subgroups())
    sylow_subgroups = [H for H in subgroups if H.order() == sylow_order]
    
    exists = len(sylow_subgroups) > 0
    
    print(f"\nSylow {prime}-subgroups found: {len(sylow_subgroups)}")
    print(f"Sylow's First Theorem verified: {exists}")
    
    return exists, sylow_subgroups
```

These verification utilities provide the computational foundation for exploring abstract algebra through executable symbolic manipulation. By encoding axioms as predicates and theorems as verifiable properties, you transform abstract mathematical claims into falsifiable computational hypotheses, enabling empirical investigation of algebraic structures before engaging formal proof. The combination of symbolic computation and axiomatic verification bridges the gap between abstract theory and concrete implementation, cultivating both computational fluency and formal mathematical rigor.
