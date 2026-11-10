# Beginner Technical Lesson: Abstract Algebra 02 Normal Subgroups And Isomorphisms

## 1. Core Mechanics & Basic Principles

### Normal Subgroups

In group theory, a **normal subgroup** is a special type of subgroup that is invariant under conjugation by members of the group. Formally, a subgroup \( N \) of a group \( G \) is normal if for every element \( g \in G \) and every element \( n \in N \), the element \( gng^{-1} \) is also in \( N \). This can be written as:
\[ gNg^{-1} = N \]
for all \( g \in G \).

Normal subgroups are important because they allow us to define quotient groups, which are fundamental in understanding the structure of groups.

### Isomorphisms

An **isomorphism** is a bijective (one-to-one and onto) homomorphism between two groups. If there exists an isomorphism between two groups \( G \) and \( H \), then \( G \) and \( H \) are said to be isomorphic, denoted \( G \cong H \). An isomorphism preserves the group structure, meaning that the group operation is preserved under the mapping. Formally, if \( \phi: G \to H \) is an isomorphism, then:
\[ \phi(g_1 g_2) = \phi(g_1) \phi(g_2) \]
for all \( g_1, g_2 \in G \).

Isomorphisms are crucial because they allow us to classify groups up to structural equivalence.

## 2. Step-by-Step Component Breakdown

### Normal Subgroups

1. **Identify the Group and Subgroup:** Start by identifying the group \( G \) and the subgroup \( N \).
2. **Check Conjugation Invariance:** For each element \( g \in G \) and each element \( n \in N \), check if \( gng^{-1} \in N \).
3. **Verify Normality:** If the condition \( gNg^{-1} = N \) holds for all \( g \in G \), then \( N \) is a normal subgroup.

### Isomorphisms

1. **Define the Mapping:** Define a function \( \phi: G \to H \) that maps elements of \( G \) to elements of \( H \).
2. **Check Homomorphism Property:** Verify that \( \phi(g_1 g_2) = \phi(g_1) \phi(g_2) \) for all \( g_1, g_2 \in G \).
3. **Check Bijectivity:** Ensure that \( \phi \) is both injective (one-to-one) and surjective (onto).
4. **Verify Isomorphism:** If both the homomorphism property and bijectivity are satisfied, then \( \phi \) is an isomorphism.

## 3. First Working Implementation

Let's consider a simple example using Python and the `sympy` library to demonstrate normal subgroups and isomorphisms.

```python
from sympy.combinatorics import Permutation, PermutationGroup
from sympy.combinatorics.named_groups import SymmetricGroup

# Define the symmetric group S3
G = SymmetricGroup(3)

# Define a subgroup H of G
H = PermutationGroup([Permutation([0, 1, 2]), Permutation([1, 2, 0]), Permutation([2, 0, 1])])

# Check if H is a normal subgroup of G
is_normal = all(g * h * g**-1 in H for g in G for h in H)
print(f"H is a normal subgroup of G: {is_normal}")

# Define another group K (also S3)
K = SymmetricGroup(3)

# Define an isomorphism phi from G to K
phi = {g: K(g.array_form) for g in G}

# Check if phi is a homomorphism
is_homomorphism = all(phi[g1 * g2] == phi[g1] * phi[g2] for g1 in G for g2 in G)
print(f"phi is a homomorphism: {is_homomorphism}")

# Check if phi is bijective
is_bijective = len(phi) == len(G) and len(set(phi.values())) == len(K)
print(f"phi is bijective: {is_bijective}")

# Verify if phi is an isomorphism
is_isomorphism = is_homomorphism and is_bijective
print(f"phi is an isomorphism: {is_isomorphism}")
```

### Explanation

- **Symmetric Group \( S_3 \):** We define the symmetric group \( S_3 \) which consists of all permutations of three elements.
- **Subgroup \( H \):** We define a subgroup \( H \) of \( S_3 \) which is the cyclic group of order 3.
- **Normality Check:** We check if \( H \) is a normal subgroup of \( G \) by verifying the conjugation invariance.
- **Isomorphism Check:** We define an isomorphism \( \phi \) from \( G \) to \( K \) (which is also \( S_3 \)) and check if it is a homomorphism and bijective.

## 4. What Can Go Wrong

### Common Mistakes

- **Incorrect Conjugation:** When checking if a subgroup is normal, ensure that the conjugation \( gng^{-1} \) is correctly computed for all \( g \in G \) and \( n \in N \).
- **Homomorphism Property Violation:** When defining an isomorphism, ensure that the homomorphism property \( \phi(g_1 g_2) = \phi(g_1) \phi(g_2) \) holds.
- **Bijectivity Issues:** Ensure that the mapping is both injective and surjective to confirm it is an isomorphism.

### How to Spot Mistakes

- **Double-Check Calculations:** Verify all calculations, especially conjugations and group operations.
- **Use Software Tools:** Utilize software tools like `sympy` to automate and verify complex calculations.
- **Review Definitions:** Always refer back to the definitions of normal subgroups and isomorphisms to ensure all conditions are met.

## 5. Key Takeaways & Review Checklist

### Key Takeaways

- **Normal Subgroups:** A subgroup \( N \) of a group \( G \) is normal if \( gNg^{-1} = N \) for all \( g \in G \).
- **Isomorphisms:** An isomorphism \( \phi: G \to H \) is a bijective homomorphism that preserves the group structure.
- **Applications:** Normal subgroups and isomorphisms are fundamental in understanding group structure and classification.

### Review Checklist

- [ ] Understand the definition and properties of normal subgroups.
- [ ] Verify normality by checking conjugation invariance.
- [ ] Define and verify isomorphisms by checking the homomorphism property and bijectivity.
- [ ] Use software tools to automate and verify calculations.
- [ ] Review definitions and properties regularly to reinforce understanding.
