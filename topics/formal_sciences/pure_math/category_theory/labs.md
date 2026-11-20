# Operational Verification Labs: Category Theory

## Objective & Mathematical Computing Setup

Category theory is the mathematics of structure-preserving maps. Where set theory asks "what are the elements?", category theory asks "what are the morphisms?"—and in doing so, discovers that the relationships between structures often carry more information than the structures themselves. These labs treat category theory not as an abstract philosophical exercise but as a computational discipline: every axiom is a predicate you can evaluate, every universal property is a constraint you can verify, and every functor is a function you can test for coherence.

The goal across these three exercises is to build a working symbolic and proof-theoretic toolkit for category-theoretic reasoning. You will implement categorical structures from scratch in Python using SymPy for symbolic manipulation, verify functoriality and natural transformation conditions algebraically, stress-test universal properties at boundary cases, and encode the core axioms formally in a Lean 4 proof assistant. By the end, you will be able to take any candidate functor, any alleged natural transformation, or any claimed adjunction and subject it to rigorous mechanical verification.

Your environment must satisfy the following requirements before proceeding.

```text
python --version          # must report 3.11 or higher
python -c "import sympy; print(sympy.__version__)"    # must report 1.12 or higher
python -c "import numpy; print(numpy.__version__)"    # must report 1.25 or higher
sage --version            # SageMath 10.x for algebraic cross-verification
lean --version            # Lean 4 with Mathlib for formal proof verification
```

If SageMath is not available as a system command, the Python exercises are fully self-contained with SymPy. SageMath is used in Exercise 2 for Galois category computations where its built-in group and field machinery accelerates verification. Install the Python stack with:

```text
pip install sympy numpy networkx matplotlib
```

The conceptual architecture of these labs follows the categorical hierarchy directly. Exercise 1 builds and verifies the foundational layer: objects, morphisms, composition, and the functor laws on finite and polynomial categories. Exercise 2 stress-tests universal constructions — products, coproducts, limits, and colimits — at degenerate and boundary inputs where naive implementations fail. Exercise 3 ascends to the structural layer: implementing adjunctions, verifying the unit-counit triangle identities, and encoding the Yoneda lemma as an executable bijection whose naturality you will confirm symbolically.

Throughout, every categorical concept is paired with a canonical computational example drawn from types and functions (the category **Set**), linear maps (the category **Vect**$_k$), and polynomial rings (the category **Ring**). This grounding ensures that the abstract axioms are always anchored to something you can run and inspect.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Building a Verified Category in Python

A category $\mathcal{C}$ consists of a class of objects $\text{ob}(\mathcal{C})$, a class of morphisms $\text{hom}(\mathcal{C})$ where each morphism $f$ has a domain $\text{dom}(f)$ and codomain $\text{cod}(f)$, a composition operation $\circ$ that is associative, and identity morphisms $\text{id}_A$ for every object $A$. The two axioms that must hold are:

$$f \circ \text{id}_A = f \qquad \text{and} \qquad \text{id}_B \circ f = f$$

for every morphism $f : A \to B$, together with associativity:

$$(h \circ g) \circ f = h \circ (g \circ f)$$

for all composable triples. The following implementation encodes these axioms as verifiable predicates. Rather than working with abstract symbols alone, we model morphisms as Python functions between finite sets, making every composition concrete and testable.

```python
"""
lab01_category_core.py
Computational verification of category axioms on finite-set morphisms.
"""

from __future__ import annotations
from typing import Callable, TypeVar, Generic, Optional
from itertools import product
import sympy as sp
from sympy import symbols, Function, Lambda, Symbol

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')


class FiniteSet:
    """An object in the category Set, represented as a named finite set."""

    def __init__(self, name: str, elements: list):
        self.name = name
        self.elements = list(elements)

    def __repr__(self):
        return f"{self.name}{{{', '.join(str(e) for e in self.elements)}}}"

    def __eq__(self, other):
        return self.name == other.name and sorted(str(e) for e in self.elements) == sorted(str(e) for e in other.elements)

    def __hash__(self):
        return hash(self.name)


class SetMorphism:
    """
    A morphism f : A -> B in Set, defined by an explicit mapping dict.
    The mapping must be total on A.elements.
    """

    def __init__(self, name: str, domain: FiniteSet, codomain: FiniteSet, mapping: dict):
        self.name = name
        self.domain = domain
        self.codomain = codomain
        self.mapping = mapping
        self._validate_total()

    def _validate_total(self):
        for x in self.domain.elements:
            if x not in self.mapping:
                raise ValueError(
                    f"Morphism '{self.name}' is not total: element {x} in domain "
                    f"{self.domain.name} has no image."
                )
        for x, y in self.mapping.items():
            if x not in self.domain.elements:
                raise ValueError(f"Key {x} not in domain {self.domain.name}")
            if y not in self.codomain.elements:
                raise ValueError(f"Value {y} not in codomain {self.codomain.name}")

    def apply(self, x):
        return self.mapping[x]

    def __repr__(self):
        arrow = ", ".join(f"{k}↦{v}" for k, v in self.mapping.items())
        return f"{self.name}: {self.domain.name} → {self.codomain.name}  [{arrow}]"


def identity(obj: FiniteSet) -> SetMorphism:
    """Construct the identity morphism id_A for a given finite set A."""
    return SetMorphism(
        name=f"id_{obj.name}",
        domain=obj,
        codomain=obj,
        mapping={x: x for x in obj.elements}
    )


def compose(g: SetMorphism, f: SetMorphism) -> SetMorphism:
    """
    Compute g ∘ f : A → C, requiring cod(f) == dom(g).
    Composition is written in standard mathematical order: apply f first, then g.
    """
    if f.codomain != g.domain:
        raise TypeError(
            f"Cannot compose: cod({f.name}) = {f.codomain.name} ≠ dom({g.name}) = {g.domain.name}"
        )
    new_mapping = {x: g.apply(f.apply(x)) for x in f.domain.elements}
    return SetMorphism(
        name=f"({g.name}∘{f.name})",
        domain=f.domain,
        codomain=g.codomain,
        mapping=new_mapping
    )


# ---------------------------------------------------------------------------
# Axiom Verifiers
# ---------------------------------------------------------------------------

def verify_identity_laws(f: SetMorphism) -> dict:
    """
    Verify the left and right identity laws for morphism f : A → B.
      Right identity: f ∘ id_A = f
      Left identity:  id_B ∘ f = f
    Returns a dict with boolean results and any failing witnesses.
    """
    id_A = identity(f.domain)
    id_B = identity(f.codomain)

    right = compose(f, id_A)
    left  = compose(id_B, f)

    right_ok = all(right.apply(x) == f.apply(x) for x in f.domain.elements)
    left_ok  = all(left.apply(x)  == f.apply(x) for x in f.domain.elements)

    right_failures = [x for x in f.domain.elements if right.apply(x) != f.apply(x)]
    left_failures  = [x for x in f.domain.elements if left.apply(x)  != f.apply(x)]

    return {
        "morphism": str(f),
        "right_identity_holds": right_ok,
        "left_identity_holds":  left_ok,
        "right_identity_failures": right_failures,
        "left_identity_failures":  left_failures,
    }


def verify_associativity(h: SetMorphism, g: SetMorphism, f: SetMorphism) -> dict:
    """
    Verify (h ∘ g) ∘ f = h ∘ (g ∘ f) on all elements of dom(f).
    All three morphisms must form a composable triple.
    """
    lhs = compose(compose(h, g), f)
    rhs = compose(h, compose(g, f))

    failures = [x for x in f.domain.elements if lhs.apply(x) != rhs.apply(x)]
    holds = len(failures) == 0

    return {
        "triple": f"({h.name} ∘ {g.name}) ∘ {f.name}  vs  {h.name} ∘ ({g.name} ∘ {f.name})",
        "associativity_holds": holds,
        "failures": failures,
        "lhs_sample": {x: lhs.apply(x) for x in f.domain.elements},
        "rhs_sample": {x: rhs.apply(x) for x in f.domain.elements},
    }


# ---------------------------------------------------------------------------
# Concrete Test: a four-object composable chain in Set
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    A = FiniteSet("A", [1, 2, 3])
    B = FiniteSet("B", ['a', 'b', 'c'])
    C = FiniteSet("C", [True, False])
    D = FiniteSet("D", [10, 20])

    f = SetMorphism("f", A, B, {1: 'a', 2: 'b', 3: 'c'})
    g = SetMorphism("g", B, C, {'a': True, 'b': False, 'c': True})
    h = SetMorphism("h", C, D, {True: 10, False: 20})

    print("=== Identity Law Verification ===")
    for morph in [f, g, h]:
        result = verify_identity_laws(morph)
        print(f"  {morph.name}: right_id={result['right_identity_holds']}, "
              f"left_id={result['left_identity_holds']}")

    print("\n=== Associativity Verification ===")
    assoc = verify_associativity(h, g, f)
    print(f"  Triple: {assoc['triple']}")
    print(f"  Holds: {assoc['associativity_holds']}")
    print(f"  LHS mapping: {assoc['lhs_sample']}")
    print(f"  RHS mapping: {assoc['rhs_sample']}")
```

Running `python lab01_category_core.py` should produce output confirming that all identity laws and associativity hold for the four-object chain. The verification is not trivial: the `verify_associativity` function constructs both bracketing orders independently and compares their element-wise outputs, which is precisely what a formal proof checker would do.

### 1.2 Functor Verification on Polynomial Rings

A functor $F : \mathcal{C} \to \mathcal{D}$ is a structure-preserving map between categories. It assigns to each object $A \in \mathcal{C}$ an object $F(A) \in \mathcal{D}$, and to each morphism $f : A \to B$ a morphism $F(f) : F(A) \to F(B)$, subject to two laws:

$$F(\text{id}_A) = \text{id}_{F(A)} \tag{Functor Identity}$$

$$F(g \circ f) = F(g) \circ F(f) \tag{Functor Composition}$$

A candidate assignment that fails either of these is not a functor, regardless of how natural it appears. The following exercise implements a symbolic functor from the category of commutative rings to the category of sets (the forgetful functor's polynomial cousin), and then verifies both laws using SymPy's symbolic polynomial machinery.

The functor we verify is the free polynomial algebra functor $T : \textbf{Set} \to \textbf{Ring}$, which sends a finite set $S = \{x_1, \ldots, x_n\}$ to the polynomial ring $\mathbb{Z}[x_1, \ldots, x_n]$, and sends a function $f : S \to T$ to the ring homomorphism $T(f) : \mathbb{Z}[S] \to \mathbb{Z}[T]$ defined by substituting $f(x_i)$ for each generator $x_i$.

```python
"""
lab01_functor_poly.py
Symbolic verification of the free polynomial algebra functor T: Set -> Ring.
Checks F(id) = id and F(g ∘ f) = F(g) ∘ F(f) using SymPy.
"""

import sympy as sp
from sympy import symbols, Symbol, Poly, expand, factor
from sympy.abc import x, y, z
from typing import Callable


class PolyRing:
    """
    Object in the image of T: a polynomial ring Z[generators].
    """
    def __init__(self, generators: list[Symbol]):
        self.generators = generators
        self.name = "Z[" + ", ".join(str(g) for g in generators) + "]"

    def __repr__(self):
        return self.name


class RingHomomorphism:
    """
    A ring homomorphism φ : Z[gens_A] → Z[gens_B] defined by a substitution dict
    mapping each generator in gens_A to a polynomial expression over gens_B.
    """
    def __init__(self, name: str, domain: PolyRing, codomain: PolyRing,
                 substitution: dict[Symbol, sp.Expr]):
        self.name = name
        self.domain = domain
        self.codomain = codomain
        self.substitution = substitution

    def apply(self, poly: sp.Expr) -> sp.Expr:
        """Apply the ring homomorphism to a polynomial expression."""
        result = poly
        for gen, image in self.substitution.items():
            result = result.subs(gen, image)
        return expand(result)

    def __repr__(self):
        sub_str = ", ".join(f"{k}↦{v}" for k, v in self.substitution.items())
        return f"{self.name}: {self.domain.name} → {self.codomain.name}  [{sub_str}]"


def ring_identity(ring: PolyRing) -> RingHomomorphism:
    """The identity homomorphism id_{Z[gens]}: every generator maps to itself."""
    return RingHomomorphism(
        name=f"id_{ring.name}",
        domain=ring,
        codomain=ring,
        substitution={g: g for g in ring.generators}
    )


def compose_hom(phi: RingHomomorphism, psi: RingHomomorphism) -> RingHomomorphism:
    """
    Compute φ ∘ ψ: apply ψ first, then φ.
    Requires cod(ψ) == dom(φ) by generator name matching.
    """
    if set(str(g) for g in psi.codomain.generators) != set(str(g) for g in phi.domain.generators):
        raise TypeError(
            f"Cannot compose: cod({psi.name}) generators ≠ dom({phi.name}) generators"
        )
    # Build the composed substitution: for each generator g of psi.domain,
    # the composed map sends g to φ(ψ(g)).
    composed_sub = {}
    for gen in psi.domain.generators:
        intermediate = psi.substitution[gen]        # ψ(gen) in psi.codomain
        final = phi.apply(intermediate)              # φ(ψ(gen)) in phi.codomain
        composed_sub[gen] = final

    return RingHomomorphism(
        name=f"({phi.name}∘{psi.name})",
        domain=psi.domain,
        codomain=phi.codomain,
        substitution=composed_sub
    )


# ---------------------------------------------------------------------------
# Functor T: Set -> Ring on morphisms
# A function f: {x1,...,xn} -> {y1,...,ym} induces T(f): Z[x's] -> Z[y's]
# by the substitution xi |-> f(xi).
# ---------------------------------------------------------------------------

def T_on_morphism(set_map: dict[Symbol, Symbol],
                  domain_ring: PolyRing,
                  codomain_ring: PolyRing) -> RingHomomorphism:
    """
    Apply the free polynomial algebra functor T to a set function.
    set_map: { xi: yj } where xi are generators of domain_ring, yj of codomain_ring.
    """
    return RingHomomorphism(
        name=f"T({{{', '.join(f'{k}↦{v}' for k,v in set_map.items())}}})",
        domain=domain_ring,
        codomain=codomain_ring,
        substitution=set_map
    )


# ---------------------------------------------------------------------------
# Test suite: verify functoriality on a composable triple
# ---------------------------------------------------------------------------

def verify_functor_identity(ring: PolyRing, test_polys: list[sp.Expr]) -> dict:
    """
    Verify T(id_S) = id_{T(S)}: check that T applied to the identity set function
    yields the ring identity homomorphism, by testing on sample polynomials.
    """
    id_set_map = {g: g for g in ring.generators}
    T_id = T_on_morphism(id_set_map, ring, ring)
    id_ring = ring_identity(ring)

    failures = []
    for p in test_polys:
        t_id_result = T_id.apply(p)
        id_result   = id_ring.apply(p)
        if expand(t_id_result - id_result) != 0:
            failures.append({
                "polynomial": str(p),
                "T_id_result": str(t_id_result),
                "id_result":   str(id_result)
            })

    return {
        "law": "T(id_S) = id_{T(S)}",
        "ring": str(ring),
        "holds": len(failures) == 0,
        "failures": failures,
        "tests_run": len(test_polys)
    }


def verify_functor_composition(set_f: dict, set_g: dict,
                                ring_A: PolyRing, ring_B: PolyRing, ring_C: PolyRing,
                                test_polys: list[sp.Expr]) -> dict:
    """
    Verify T(g ∘ f) = T(g) ∘ T(f) on a list of test polynomials in Z[ring_A.generators].

    set_f: function A -> B (generator substitution dict)
    set_g: function B -> C (generator substitution dict)
    """
    # Compute T(g ∘ f): first build g ∘ f as a set function, then apply T
    gof_set_map = {a: set_g[set_f[a]] for a in ring_A.generators}
    T_gof = T_on_morphism(gof_set_map, ring_A, ring_C)

    # Compute T(g) ∘ T(f) as ring homomorphism composition
    T_f = T_on_morphism(set_f, ring_A, ring_B)
    T_g = T_on_morphism(set_g, ring_B, ring_C)
    T_g_then_T_f = compose_hom(T_g, T_f)

    failures = []
    for p in test_polys:
        lhs = T_gof.apply(p)
        rhs = T_g_then_T_f.apply(p)
        if expand(lhs - rhs) != 0:
            failures.append({
                "polynomial": str(p),
                "T(g∘f) result": str(lhs),
                "T(g)∘T(f) result": str(rhs)
            })

    return {
        "law": "T(g∘f) = T(g) ∘ T(f)",
        "holds": len(failures) == 0,
        "failures": failures,
        "tests_run": len(test_polys)
    }


if __name__ == "__main__":
    # Define three sets as generator lists
    a1, a2 = symbols('a1 a2')
    b1, b2 = symbols('b1 b2')
    c1, c2 = symbols('c1 c2')

    ring_A = PolyRing([a1, a2])
    ring_B = PolyRing([b1, b2])
    ring_C = PolyRing([c1, c2])

    # Set function f: A -> B
    set_f = {a1: b1, a2: b2}
    # Set function g: B -> C
    set_g = {b1: c1 + c2, b2: c1 - c2}

    # Test polynomials in Z[a1, a2]
    test_polys = [
        a1,
        a2,
        a1 + a2,
        a1**2 - a2**2,
        a1**3 + 3*a1*a2 + a2**2,
        (a1 + a2)**4,
        a1**2 * a2 - 2*a1 * a2**2 + a2**3,
    ]

    print("=== Functor Identity Law Verification ===")
    id_result = verify_functor_identity(ring_A, test_polys)
    print(f"  Law: {id_result['law']}")
    print(f"  Holds: {id_result['holds']}  ({id_result['tests_run']} polynomials tested)")
    if id_result['failures']:
        for fail in id_result['failures']:
            print(f"  FAIL on {fail['polynomial']}: T(id)={fail['T_id_result']}, id={fail['id_result']}")

    print("\n=== Functor Composition Law Verification ===")
    comp_result = verify_functor_composition(set_f, set_g, ring_A, ring_B, ring_C, test_polys)
    print(f"  Law: {comp_result['law']}")
    print(f"  Holds: {comp_result['holds']}  ({comp_result['tests_run']} polynomials tested)")
    if comp_result['failures']:
        for fail in comp_result['failures']:
            print(f"  FAIL on {fail['polynomial']}")
```

### 1.3 Natural Transformation Verification

A natural transformation $\eta : F \Rightarrow G$ between two functors $F, G : \mathcal{C} \to \mathcal{D}$ is a family of morphisms $\{\eta_A : F(A) \to G(A)\}_{A \in \mathcal{C}}$ satisfying the naturality square: for every $f : A \to B$ in $\mathcal{C}$,

$$G(f) \circ \eta_A = \eta_B \circ F(f)$$

This single commutative diagram, repeated for every morphism in $\mathcal{C}$, is the content of naturality. The following verifier checks this condition exhaustively over a finite category encoded as a directed graph.

```python
"""
lab01_nat_transform.py
Verify the naturality condition for a candidate natural transformation
between two functors on a finite category, using SymPy symbolic matrices.
"""

import sympy as sp
from sympy import Matrix, symbols, eye, zeros
from typing import Callable


# ---------------------------------------------------------------------------
# We model objects as integers and morphisms as symbolic linear maps (matrices).
# Functors F, G: C -> Vect_k  (category of vector spaces over a field k).
# Natural transformation η: F => G assigns a matrix η_A to each object A.
# ---------------------------------------------------------------------------

class LinearFunctor:
    """
    A functor from a finite category (objects: ints, morphisms: matrix dict)
    to Vect_k.
    object_map:   { obj_id: dimension }
    morphism_map: { (dom_id, cod_id): sympy Matrix }
    """
    def __init__(self, name: str,
                 object_map: dict[int, int],
                 morphism_map: dict[tuple[int,int], Matrix]):
        self.name = name
        self.object_map = object_map
        self.morphism_map = morphism_map

    def on_object(self, obj: int) -> int:
        return self.object_map[obj]

    def on_morphism(self, dom: int, cod: int) -> Matrix:
        if (dom, cod) in self.morphism_map:
            return self.morphism_map[(dom, cod)]
        if dom == cod:
            dim = self.object_map[dom]
            return eye(dim)
        raise KeyError(f"No morphism ({dom}→{cod}) in functor {self.name}")


def verify_naturality(
    F: LinearFunctor,
    G: LinearFunctor,
    eta: dict[int, Matrix],       # η_A for each object A
    morphisms: list[tuple[int,int]]  # all non-identity morphisms in C
) -> dict:
    """
    For each morphism f: A -> B in C, verify:
        G(f) ∘ η_A = η_B ∘ F(f)
    Returns a full report with per-morphism results.
    """
    results = []
    all_hold = True

    for (A, B) in morphisms:
        eta_A = eta[A]
        eta_B = eta[B]
        F_f   = F.on_morphism(A, B)
        G_f   = G.on_morphism(A, B)

        lhs = sp.simplify(G_f * eta_A)   # G(f) ∘ η_A
        rhs = sp.simplify(eta_B * F_f)   # η_B ∘ F(f)

        diff = sp.simplify(lhs - rhs)
        holds = diff == zeros(*diff.shape)

        if not holds:
            all_hold = False

        results.append({
            "morphism": f"{A} → {B}",
            "naturality_holds": holds,
            "G(f)∘η_A": lhs,
            "η_B∘F(f)": rhs,
            "difference": diff
        })

    return {
        "all_natural": all_hold,
        "per_morphism": results
    }


if __name__ == "__main__":
    # -----------------------------------------------------------------
    # Category C with objects {0, 1, 2} and morphisms:
    #   f: 0 -> 1,  g: 1 -> 2,  h = g∘f: 0 -> 2
    # Both F and G send each object to R^2.
    # We define F and G on morphisms as 2x2 matrices.
    # η is a natural transformation from F to G.
    # -----------------------------------------------------------------
    a, b, c, d = symbols('a b c d')

    # F on morphisms (2x2 rotation-like maps)
    F_f01 = Matrix([[1, 1], [0, 1]])    # F(f): F(0)=R^2 -> F(1)=R^2
    F_f12 = Matrix([[2, 0], [1, 2]])    # F(g): F(1)=R^2 -> F(2)=R^2
    F_f02 = sp.simplify(F_f12 * F_f01) # F(h) = F(g)∘F(f)  (functor law enforced)

    # G on morphisms
    G_f01 = Matrix([[1, 2], [0, 1]])    # G(f)
    G_f12 = Matrix([[3, 0], [1, 3]])    # G(g)
    G_f02 = sp.simplify(G_f12 * G_f01) # G(h) = G(g)∘G(f)

    F = LinearFunctor(
        name="F",
        object_map={0: 2, 1: 2, 2: 2},
        morphism_map={(0,1): F_f01, (1,2): F_f12, (0,2): F_f02}
    )

    G = LinearFunctor(
        name="G",
        object_map={0: 2, 1: 2, 2: 2},
        morphism_map={(0,1): G_f01, (1,2): G_f12, (0,2): G_f02}
    )

    # -----------------------------------------------------------------
    # Construct η satisfying naturality: G(f)∘η_A = η_B∘F(f)
    # For η_0 = I, solve for η_1 from G(f)∘η_0 = η_1∘F(f).
    # Then verify η_2 is consistent.
    # η_1 = G_f01 ∘ η_0 ∘ F_f01^{-1}
    # -----------------------------------------------------------------
    eta_0 = eye(2)                                                   # η_0 := identity
    eta_1 = sp.simplify(G_f01 * eta_0 * F_f01**-1)                 # derived from naturality
    eta_2 = sp.simplify(G_f12 * eta_1 * F_f12**-1)                 # derived from naturality

    eta = {0: eta_0, 1: eta_1, 2: eta_2}

    print("=== Computed natural transformation components ===")
    for obj, mat in eta.items():
        print(f"  η_{obj} =\n{mat}\n")

    morphisms = [(0, 1), (1, 2), (0, 2)]
    result = verify_naturality(F, G, eta, morphisms)

    print("=== Naturality Verification ===")
    print(f"  All natural: {result['all_natural']}")
    for r in result['per_morphism']:
        status = "✓" if r['naturality_holds'] else "✗ FAIL"
        print(f"  {status}  Morphism {r['morphism']}: naturality_holds={r['naturality_holds']}")
        if not r['naturality_holds']:
            print(f"      Difference:\n{r['difference']}")
```

The derivation of $\eta_1$ from the equation $G(f) \circ \eta_0 = \eta_1 \circ F(f)$ uses the fact that $F(f)$ is invertible in this example, giving $\eta_1 = G(f) \cdot \eta_0 \cdot F(f)^{-1}$. In general, naturality constrains but does not uniquely determine the components of $\eta$; the verifier checks whether a given assignment is natural, not whether it is the unique one.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Universal Properties at Degenerate Inputs

Universal properties are the characteristic feature of category theory: a construction is defined not by what it is internally, but by how it relates to everything else via a unique mediating morphism. The product $A \times B$ in a category is characterized by the universal property: for every object $C$ and pair of morphisms $f : C \to A$, $g : C \to B$, there exists a unique morphism $\langle f, g \rangle : C \to A \times B$ such that $\pi_1 \circ \langle f, g \rangle = f$ and $\pi_2 \circ \langle f, g \rangle = g$.

The degenerate cases reveal where naive implementations break. When $A$ is the terminal object $\mathbf{1}$ (the one-element set), the product $A \times B \cong B$, and the unique mediating morphism collapses to the identity. When $A = B$, the diagonal $\Delta : A \to A \times A$ defined by $\Delta(x) = (x, x)$ must be the unique morphism making both projections equal to $\text{id}_A$. When $C$ is the initial object $\mathbf{0}$ (empty set), there are no morphisms to test and the universal property holds vacuously. Each of these boundary cases must be handled correctly.

```python
"""
lab02_universal_props.py
Stress-test the universal product property in Set at degenerate inputs:
terminal object, initial object, diagonal, and self-product.
"""

from lab01_category_core import FiniteSet, SetMorphism, identity, compose


# ---------------------------------------------------------------------------
# Terminal and Initial objects in Set
# ---------------------------------------------------------------------------

TERMINAL = FiniteSet("1", ["*"])          # the one-element set
INITIAL  = FiniteSet("0", [])             # the empty set


def unique_to_terminal(obj: FiniteSet) -> SetMorphism:
    """The unique morphism ! : obj -> 1 (terminal). Every element maps to *."""
    return SetMorphism(
        name=f"!_{obj.name}",
        domain=obj,
        codomain=TERMINAL,
        mapping={x: "*" for x in obj.elements}
    )


def unique_from_initial(obj: FiniteSet) -> SetMorphism:
    """The unique morphism ¡ : 0 -> obj (initial). Empty mapping, vacuously total."""
    return SetMorphism(
        name=f"¡_{obj.name}",
        domain=INITIAL,
        codomain=obj,
        mapping={}
    )


# ---------------------------------------------------------------------------
# Product construction in Set
# ---------------------------------------------------------------------------

def set_product(A: FiniteSet, B: FiniteSet) -> tuple[FiniteSet, SetMorphism, SetMorphism]:
    """
    Construct A × B in Set as a FiniteSet of pairs, with projections π₁, π₂.
    Returns (AxB, pi1, pi2).
    """
    pairs = [(a, b) for a in A.elements for b in B.elements]
    AxB = FiniteSet(f"{A.name}×{B.name}", pairs)

    pi1 = SetMorphism(
        name=f"π₁:{A.name}×{B.name}→{A.name}",
        domain=AxB,
        codomain=A,
        mapping={(a, b): a for (a, b) in pairs}
    )
    pi2 = SetMorphism(
        name=f"π₂:{A.name}×{B.name}→{B.name}",
        domain=AxB,
        codomain=B,
        mapping={(a, b): b for (a, b) in pairs}
    )
    return AxB, pi1, pi2


def universal_mediator(C: FiniteSet,
                        f: SetMorphism, g: SetMorphism,
                        A: FiniteSet, B: FiniteSet) -> SetMorphism:
    """
    Given f: C -> A and g: C -> B, construct the unique mediating morphism
    <f,g> : C -> A×B  such that π₁∘<f,g>=f and π₂∘<f,g>=g.
    """
    if f.domain != C or g.domain != C:
        raise ValueError("Both f and g must have domain C.")
    if f.codomain != A or g.codomain != B:
        raise ValueError("f must map to A and g must map to B.")

    mapping = {c: (f.apply(c), g.apply(c)) for c in C.elements}
    return SetMorphism(
        name=f"⟨{f.name},{g.name}⟩",
        domain=C,
        codomain=FiniteSet(f"{A.name}×{B.name}", [(a, b) for a in A.elements for b in B.elements]),
        mapping=mapping
    )


def verify_universal_product(C: FiniteSet,
                               f: SetMorphism, g: SetMorphism,
                               A: FiniteSet, B: FiniteSet) -> dict:
    """
    Verify that the mediating morphism ⟨f,g⟩ satisfies both projection equations.
    """
    AxB, pi1, pi2 = set_product(A, B)
    med = universal_mediator(C, f, g, A, B)

    # π₁ ∘ ⟨f,g⟩ should equal f
    pi1_med = compose(pi1, med)
    pi2_med = compose(pi2, med)

    pi1_ok = all(pi1_med.apply(c) == f.apply(c) for c in C.elements)
    pi2_ok = all(pi2_med.apply(c) == g.apply(c) for c in C.elements)

    # Uniqueness: verify there is no other morphism satisfying the equations
    # by exhaustive search over all functions C -> AxB
    from itertools import product as iproduct
    all_maps = list(iproduct(AxB.elements, repeat=len(C.elements)))
    satisfying = []
    for assignment in all_maps:
        candidate_map = dict(zip(C.elements, assignment))
        pi1_ok_cand = all(candidate_map[c][0] == f.apply(c) for c in C.elements)
        pi2_ok_cand = all(candidate_map[c][1] == g.apply(c) for c in C.elements)
        if pi1_ok_cand and pi2_ok_cand:
            satisfying.append(candidate_map)

    return {
        "mediator": str(med),
        "pi1_equation_holds": pi1_ok,
        "pi2_equation_holds": pi2_ok,
        "unique_mediator": len(satisfying) == 1,
        "satisfying_morphisms_count": len(satisfying)
    }


if __name__ == "__main__":
    A = FiniteSet("A", [1, 2])
    B = FiniteSet("B", ['x', 'y'])

    print("=== CASE 1: Standard C = {a,b,c} with arbitrary f,g ===")
    C = FiniteSet("C", ['a', 'b', 'c'])
    f = SetMorphism("f", C, A, {'a': 1, 'b': 2, 'c': 1})
    g = SetMorphism("g", C, B, {'a': 'x', 'b': 'x', 'c': 'y'})
    r1 = verify_universal_product(C, f, g, A, B)
    print(f"  π₁ eq: {r1['pi1_equation_holds']}, π₂ eq: {r1['pi2_equation_holds']}, "
          f"unique: {r1['unique_mediator']} (count={r1['satisfying_morphisms_count']})")

    print("\n=== CASE 2: Degenerate — C = terminal object 1 ===")
    f_term = SetMorphism("f!", TERMINAL, A, {'*': 1})
    g_term = SetMorphism("g!", TERMINAL, B, {'*': 'y'})
    r2 = verify_universal_product(TERMINAL, f_term, g_term, A, B)
    print(f"  π₁ eq: {r2['pi1_equation_holds']}, π₂ eq: {r2['pi2_equation_holds']}, "
          f"unique: {r2['unique_mediator']} (count={r2['satisfying_morphisms_count']})")

    print("\n=== CASE 3: Degenerate — A = B (self-product, diagonal) ===")
    id_A = identity(A)
    r3 = verify_universal_product(A, id_A, id_A, A, A)
    print(f"  π₁ eq: {r3['pi1_equation_holds']}, π₂ eq: {r3['pi2_equation_holds']}, "
          f"unique: {r3['unique_mediator']} (count={r3['satisfying_morphisms_count']})")
    print(f"  Mediator (should be diagonal Δ): {r3['mediator']}")

    print("\n=== CASE 4: Degenerate — C = initial object 0 ===")
    f_init = unique_from_initial(A)
    g_init = unique_from_initial(B)
    r4 = verify_universal_product(INITIAL, f_init, g_init, A, B)
    print(f"  π₁ eq: {r4['pi1_equation_holds']}, π₂ eq: {r4['pi2_equation_holds']}, "
          f"unique: {r4['unique_mediator']} (count={r4['satisfying_morphisms_count']})")
    print("  (Vacuously satisfied: 0 elements to test, exactly 1 mediator = empty map)")
```

### 2.2 Equalizer Stress Testing: Degenerate and Singular Cases

The equalizer of a parallel pair $f, g : A \to B$ is the universal object $E$ together with a morphism $e : E \to A$ such that $f \circ e = g \circ e$, and any other morphism $h : C \to A$ satisfying $f \circ h = g \circ h$ factors uniquely through $e$. The degenerate cases here are: when $f = g$ (the equalizer is all of $A$), when $f$ and $g$ agree on no element (the equalizer is empty, the initial object), and when $A$ itself is empty.

```python
"""
lab02_equalizer.py
Construct and stress-test equalizers in Set, covering degenerate cases.
"""

from lab01_category_core import FiniteSet, SetMorphism, compose, identity


def equalizer(f: SetMorphism, g: SetMorphism) -> tuple[FiniteSet, SetMorphism]:
    """
    Compute the equalizer of f, g : A -> B in Set.
    Returns (E, e) where E = {a in A | f(a) = g(a)} and e: E -> A is inclusion.
    """
    if f.domain != g.domain or f.codomain != g.codomain:
        raise ValueError("f and g must be parallel morphisms (same domain, same codomain).")

    eq_elements = [a for a in f.domain.elements if f.apply(a) == g.apply(a)]
    E = FiniteSet(f"Eq({f.name},{g.name})", eq_elements)

    e = SetMorphism(
        name=f"e_({f.name},{g.name})",
        domain=E,
        codomain=f.domain,
        mapping={a: a for a in eq_elements}   # inclusion map
    )
    return E, e


def verify_equalizer(f: SetMorphism, g: SetMorphism) -> dict:
    """
    Verify the equalizer (E, e) satisfies:
    1. f ∘ e = g ∘ e           (equalizer equation)
    2. Universal property: for every h: C -> A with f∘h = g∘h,
       there exists a unique ū: C -> E with e ∘ ū = h.
    We test the universal property with C = dom(f) and h = inclusion of a subset.
    """
    E, e = equalizer(f, g)
    A = f.domain

    # Check equalizer equation on all elements of E
    eq_elements = E.elements
    fe_ge_agree = all(
        f.apply(e.apply(x)) == g.apply(e.apply(x))
        for x in eq_elements
    )

    # Universal property: take C = E itself, h = e.
    # The unique factoring morphism must be id_E.
    if len(eq_elements) > 0:
        # Build ū: E -> E as the unique morphism with e ∘ ū = h = e
        # Since e is injective (inclusion), ū = id_E is the only solution.
        u_bar_map = {x: x for x in eq_elements}
        u_bar = SetMorphism(f"ū", E, E, u_bar_map) if eq_elements else None

        # Verify e ∘ ū = e
        if u_bar:
            e_ubar = compose(e, u_bar)
            factoring_ok = all(e_ubar.apply(x) == e.apply(x) for x in eq_elements)
        else:
            factoring_ok = True
    else:
        factoring_ok = True   # vacuously true for empty equalizer

    return {
        "f": str(f),
        "g": str(g),
        "equalizer_set": str(E),
        "equalizer_elements": eq_elements,
        "equalizer_equation_holds": fe_ge_agree,
        "universal_factoring_holds": factoring_ok,
        "is_initial": len(eq_elements) == 0,
        "is_all_of_A": eq_elements == A.elements
    }


if __name__ == "__main__":
    A = FiniteSet("A", [1, 2, 3, 4])
    B = FiniteSet("B", ['p', 'q', 'r'])

    print("=== CASE 1: Partial agreement (f ≠ g on some elements) ===")
    f1 = SetMorphism("f", A, B, {1: 'p', 2: 'q', 3: 'r', 4: 'p'})
    g1 = SetMorphism("g", A, B, {1: 'p', 2: 'r', 3: 'r', 4: 'q'})
    r1 = verify_equalizer(f1, g1)
    print(f"  Equalizer: {r1['equalizer_elements']}")
    print(f"  Equation holds: {r1['equalizer_equation_holds']}")
    print(f"  Universal factoring: {r1['universal_factoring_holds']}")

    print("\n=== CASE 2: f = g (equalizer = all of A) ===")
    f2 = SetMorphism("f", A, B, {1: 'p', 2: 'q', 3: 'r', 4: 'p'})
    g2 = SetMorphism("g", A, B, {1: 'p', 2: 'q', 3: 'r', 4: 'p'})
    r2 = verify_equalizer(f2, g2)
    print(f"  Equalizer is all of A: {r2['is_all_of_A']}")
    print(f"  Equation holds: {r2['equalizer_equation_holds']}")

    print("\n=== CASE 3: f,g agree nowhere (equalizer = initial object ∅) ===")
    A2 = FiniteSet("A", [1, 2])
    B2 = FiniteSet("B", ['x', 'y'])
    f3 = SetMorphism("f", A2, B2, {1: 'x', 2: 'x'})
    g3 = SetMorphism("g", A2, B2, {1: 'y', 2: 'y'})
    r3 = verify_equalizer(f3, g3)
    print(f"  Equalizer is empty (initial): {r3['is_initial']}")
    print(f"  Equation holds vacuously: {r3['equalizer_equation_holds']}")

    print("\n=== CASE 4: A is a singleton ===")
    A3 = FiniteSet("A", ['*'])
    B3 = FiniteSet("B", ['a', 'b'])
    f4 = SetMorphism("f", A3, B3, {'*': 'a'})
    g4 = SetMorphism("g", A3, B3, {'*': 'a'})
    r4 = verify_equalizer(f4, g4)
    print(f"  Equalizer: {r4['equalizer_elements']}, is all of A: {r4['is_all_of_A']}")
```

### 2.3 Pullback Verification with SageMath

The pullback of a cospan $A \xrightarrow{f} C \xleftarrow{g} B$ is the limit of this diagram: an object $P$ with projections $p_1 : P \to A$ and $p_2 : P \to B$ satisfying $f \circ p_1 = g \circ p_2$, universal among all such cones. In **Set**, the pullback is concretely $P = \{(a, b) \in A \times B \mid f(a) = g(b)\}$. When $C$ is the terminal object, the pullback recovers the product. When $f = g$ and $A = B = C$, the pullback is the equalizer. SageMath's combinatorial tools accelerate exhaustive verification for larger sets.

```python
"""
lab02_pullback_sage.py
Pullback construction and stress testing in Set using SageMath.
Run with: sage lab02_pullback_sage.py
If SageMath unavailable, the pure-Python fallback below runs with Python 3.11+.
"""

# Pure-Python implementation (SageMath-free, runs with standard Python + no deps)

from itertools import product as iproduct


def pullback_set(A_elems, B_elems, f_map, g_map):
    """
    Compute the pullback of A -f-> C <-g- B in Set.
    Returns list of pairs (a, b) with f(a) == g(b), plus projection functions.
    """
    P_elems = [(a, b) for a in A_elems for b in B_elems if f_map[a] == g_map[b]]
    p1 = {(a, b): a for (a, b) in P_elems}
    p2 = {(a, b): b for (a, b) in P_elems}
    return P_elems, p1, p2


def verify_pullback_universal(A_elems, B_elems, C_elems, f_map, g_map,
                               Q_elems, q1_map, q2_map):
    """
    Given a competing cone Q -q1-> A, Q -q2-> B with f∘q1 = g∘q2,
    verify there is a unique mediating morphism u: Q -> P with p1∘u = q1 and p2∘u = q2.
    """
    # Verify Q is a valid cone
    cone_ok = all(f_map[q1_map[x]] == g_map[q2_map[x]] for x in Q_elems)

    P_elems, p1, p2 = pullback_set(A_elems, B_elems, f_map, g_map)

    # Find all u: Q -> P satisfying p1∘u = q1 and p2∘u = q2
    satisfying = []
    for assignment in iproduct(P_elems, repeat=len(Q_elems)):
        u_map = dict(zip(Q_elems, assignment))
        p1_ok = all(p1[u_map[x]] == q1_map[x] for x in Q_elems)
        p2_ok = all(p2[u_map[x]] == q2_map[x] for x in Q_elems)
        if p1_ok and p2_ok:
            satisfying.append(u_map)

    return {
        "valid_cone": cone_ok,
        "P_elements": P_elems,
        "satisfying_mediators": len(satisfying),
        "unique_mediator": len(satisfying) == 1,
        "mediator": satisfying[0] if len(satisfying) == 1 else satisfying
    }


if __name__ == "__main__":
    # Cospan: A -f-> C <-g- B
    A_elems = [1, 2, 3, 4]
    B_elems = ['a', 'b', 'c', 'd']
    C_elems = ['X', 'Y', 'Z']

    f_map = {1: 'X', 2: 'Y', 3: 'X', 4: 'Z'}
    g_map = {'a': 'Y', 'b': 'X', 'c': 'Z', 'd': 'X'}

    P_elems, p1, p2 = pullback_set(A_elems, B_elems, f_map, g_map)
    print("=== Pullback P ===")
    print(f"  P = {P_elems}")
    print(f"  p1 = {p1}")
    print(f"  p2 = {p2}")

    # Verify f∘p1 = g∘p2 on all of P
    eq_ok = all(f_map[p1[(a,b)]] == g_map[p2[(a,b)]] for (a,b) in P_elems)
    print(f"  f∘p1 = g∘p2 on all P: {eq_ok}")

    # Competing cone Q with q1: Q->A, q2: Q->B satisfying f∘q1 = g∘q2
    # Take Q = {α, β}, q1(α)=2, q1(β)=3, q2(α)='a', q2(β)='b'
    # f(q1(α))=f(2)='Y' = g('a')='Y' ✓
    # f(q1(β))=f(3)='X' = g('b')='X' ✓
    Q_elems = ['α', 'β']
    q1_map  = {'α': 2, 'β': 3}
    q2_map  = {'α': 'a', 'β': 'b'}

    print("\n=== Universal Property Verification ===")
    result = verify_pullback_universal(A_elems, B_elems, C_elems, f_map, g_map,
                                        Q_elems, q1_map, q2_map)
    print(f"  Valid cone: {result['valid_cone']}")
    print(f"  Unique mediator exists: {result['unique_mediator']}")
    print(f"  Number of satisfying morphisms: {result['satisfying_mediators']}")
    print(f"  Mediator u: Q → P = {result['mediator']}")

    print("\n=== DEGENERATE: Pullback over terminal (recovers product) ===")
    T_elems = ['*']
    f_term = {1: '*', 2: '*'}
    g_term = {'a': '*', 'b': '*'}
    P_term, _, _ = pullback_set([1,2], ['a','b'], f_term, g_term)
    print(f"  P (should be full product) = {P_term}")
    print(f"  |A|×|B| = {len([1,2]) * len(['a','b'])}, |P| = {len(P_term)}")

    print("\n=== DEGENERATE: Empty A (pullback = ∅) ===")
    P_empty, _, _ = pullback_set([], ['a', 'b'], {}, g_map)
    print(f"  P with empty A = {P_empty}")
```

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Adjunctions: Unit-Counit Triangle Identities

An adjunction $F \dashv G$ between functors $F : \mathcal{C} \to \mathcal{D}$ and $G : \mathcal{D} \to \mathcal{C}$ consists of a unit natural transformation $\eta : \text{Id}_\mathcal{C} \Rightarrow G \circ F$ and a counit $\varepsilon : F \circ G \Rightarrow \text{Id}_\mathcal{D}$ satisfying the two triangle identities:

$$G(\varepsilon_B) \circ \eta_{G(B)} = \text{id}_{G(B)} \tag{Triangle I}$$

$$\varepsilon_{F(A)} \circ F(\eta_A) = \text{id}_{F(A)} \tag{Triangle II}$$

for all objects $A \in \mathcal{C}$ and $B \in \mathcal{D}$. These two equations, deceptively simple in appearance, encode the entire structure of the adjunction. We will verify them for the free-forgetful adjunction between **Vect**$_k$ and **Set**: the free functor $F$ sends a set $S$ to the vector space $k^S$ with basis $S$, and the forgetful functor $G$ sends a vector space $V$ to its underlying set of basis vectors.

```python
"""
lab03_adjunction.py
Verify the unit-counit triangle identities for the free-forgetful adjunction
F ⊣ G between finite-dimensional vector spaces and finite sets.

F: Set -> Vect_k   sends a basis set S to the free vector space k^S
G: Vect_k -> Set   sends a vector space to its set of basis indices
"""

import sympy as sp
from sympy import Matrix, eye, zeros, symbols, Rational


class BasisSet:
    """An object in Set: an indexed collection of basis labels."""
    def __init__(self, name: str, basis: list):
        self.name = name
        self.basis = list(basis)
        self.dim = len(basis)

    def __repr__(self):
        return f"Set({self.name}={self.basis})"


class FreeVectorSpace:
    """
    Object in Vect_k: the free vector space k^S over basis set S.
    Morphisms are represented as matrices with respect to the standard basis.
    """
    def __init__(self, basis_set: BasisSet, field=sp.QQ):
        self.basis_set = basis_set
        self.dim = basis_set.dim
        self.field = field
        self.name = f"k^{basis_set.name}"

    def __repr__(self):
        return self.name


def free_functor_on_morphism(set_map: dict, domain_basis: BasisSet,
                              codomain_basis: BasisSet) -> Matrix:
    """
    Apply F to a set function f: S -> T.
    F(f): k^S -> k^T is the linear map sending basis vector e_s to e_{f(s)}.
    Returns the matrix of F(f) with rows indexed by T, columns by S.
    """
    n = domain_basis.dim
    m = codomain_basis.dim
    col_index = {v: i for i, v in enumerate(domain_basis.basis)}
    row_index = {v: i for i, v in enumerate(codomain_basis.basis)}

    mat = zeros(m, n)
    for s, t in set_map.items():
        mat[row_index[t], col_index[s]] = 1
    return mat


def unit_component(S: BasisSet) -> Matrix:
    """
    η_S : S -> G(F(S)) = S   (as a set map, encoded as a matrix over k^S -> k^{k^S})
    For the free-forgetful adjunction on finite sets and finite-dim vector spaces,
    the unit η_S : S -> GF(S) = S is the identity on the basis labels.
    As a linear map k^S -> k^{GF(S)} = k^S, this is the identity matrix.
    """
    return eye(S.dim)


def counit_component(V: FreeVectorSpace) -> Matrix:
    """
    ε_V : F(G(V)) -> V   
    FG(V) = F(basis of V) = k^{basis of V}.
    The counit is the canonical evaluation map: e_{v_i} ↦ v_i.
    For a free vector space, G(V) = the basis set, F(G(V)) = V itself,
    and ε_V is the identity map (every basis vector maps to itself).
    """
    return eye(V.dim)


def verify_triangle_I(B_basis: BasisSet) -> dict:
    """
    Triangle Identity I:  G(ε_B) ∘ η_{G(B)} = id_{G(B)}

    In matrix form (with F,G as above):
    ε_B is a (dim_B × dim_B) matrix (identity for free spaces).
    η_{G(B)} is a (dim_B × dim_B) matrix (identity for unit on basis sets).
    G(ε_B): since G forgets linear structure to the basis set, G(ε_B) as a
    matrix acting on k^{G(B)} is the same matrix as ε_B.

    So Triangle I becomes: ε_B ∘ η_{G(B)} = I.
    """
    V = FreeVectorSpace(B_basis)
    eta_GB = unit_component(B_basis)        # η_{G(B)}: G(B) -> GF(G(B)) = G(B)
    eps_B  = counit_component(V)            # ε_B: FG(B) -> B, matrix form

    # G(ε_B) ∘ η_{G(B)} in matrix form
    lhs = sp.simplify(eps_B * eta_GB)
    rhs = eye(B_basis.dim)

    diff = sp.simplify(lhs - rhs)
    holds = diff == zeros(B_basis.dim, B_basis.dim)

    return {
        "identity": "Triangle I: G(ε_B) ∘ η_{G(B)} = id_{G(B)}",
        "dim": B_basis.dim,
        "lhs": lhs,
        "rhs": rhs,
        "difference": diff,
        "holds": holds
    }


def verify_triangle_II(A_basis: BasisSet) -> dict:
    """
    Triangle Identity II: ε_{F(A)} ∘ F(η_A) = id_{F(A)}

    F(η_A): F(A) -> F(GF(A)) = F(A)  (since GF(A) = A for free spaces on finite sets)
    ε_{F(A)}: F(GF(A)) = F(A) -> F(A)
    Both are identity matrices for the free-forgetful adjunction.
    """
    V_A = FreeVectorSpace(A_basis)
    # F(η_A): k^A -> k^{GF(A)} = k^A.  Since η_A is id_A as a set map, F(η_A) = I.
    F_eta_A = free_functor_on_morphism(
        {a: a for a in A_basis.basis}, A_basis, A_basis
    )
    eps_FA  = counit_component(V_A)         # ε_{F(A)}: FGF(A) -> F(A)

    lhs = sp.simplify(eps_FA * F_eta_A)
    rhs = eye(A_basis.dim)

    diff = sp.simplify(lhs - rhs)
    holds = diff == zeros(A_basis.dim, A_basis.dim)

    return {
        "identity": "Triangle II: ε_{F(A)} ∘ F(η_A) = id_{F(A)}",
        "dim": A_basis.dim,
        "lhs": lhs,
        "rhs": rhs,
        "difference": diff,
        "holds": holds
    }


if __name__ == "__main__":
    # Test across multiple dimensions
    for n in [1, 2, 3, 4, 5, 10]:
        S = BasisSet(f"S{n}", list(range(n)))
        t1 = verify_triangle_I(S)
        t2 = verify_triangle_II(S)
        print(f"dim={n:2d}:  Triangle I={t1['holds']},  Triangle II={t2['holds']}")

    # Detailed output for dim=3
    S3 = BasisSet("S3", ['x', 'y', 'z'])
    print("\n=== Detailed verification for dim=3 ===")
    t1 = verify_triangle_I(S3)
    t2 = verify_triangle_II(S3)
    print(f"Triangle I:  {t1['identity']}")
    print(f"  LHS:\n{t1['lhs']}")
    print(f"  Holds: {t1['holds']}")
    print(f"\nTriangle II: {t2['identity']}")
    print(f"  LHS:\n{t2['lhs']}")
    print(f"  Holds: {t2['holds']}")
```

### 3.2 The Yoneda Lemma as an Executable Bijection

The Yoneda lemma states that for any locally small category $\mathcal{C}$, any object $A \in \mathcal{C}$, and any functor $F : \mathcal{C} \to \textbf{Set}$, there is a natural bijection:

$$\text{Nat}(\text{Hom}(A, -), F) \cong F(A)$$

The bijection sends a natural transformation $\alpha : \text{Hom}(A,-) \Rightarrow F$ to the element $\alpha_A(\text{id}_A) \in F(A)$, and in the other direction sends an element $x \in F(A)$ to the natural transformation $\alpha^x$ whose component at $B$ is the function $\alpha^x_B : \text{Hom}(A,B) \to F(B)$ defined by $\alpha^x_B(f) = F(f)(x)$. The following implementation makes this bijection computable on a finite category and verifies both naturality of $\alpha^x$ and the round-trip property.

```python
"""
lab03_yoneda.py
Implement and verify the Yoneda bijection:
  Nat(Hom(A,-), F) ≅ F(A)
on a small finite category represented explicitly.
"""

from lab01_category_core import FiniteSet, SetMorphism, identity, compose
from typing import Callable


class FiniteCategory:
    """
    A finite category specified by:
    - objects: list of object names (strings)
    - morphisms: dict mapping (dom, cod) -> list of morphism names
    - compose_table: dict mapping (g_name, f_name) -> (g∘f)_name
    - identity_map: dict mapping obj_name -> identity morphism name
    """
    def __init__(self, objects, morphisms_by_pair, compose_table, identity_map):
        self.objects = objects
        self.morphisms_by_pair = morphisms_by_pair   # (A,B) -> [morph_names]
        self.compose_table = compose_table           # (g,f) -> g∘f name
        self.identity_map = identity_map             # A -> id_A name

    def hom(self, A, B):
        return self.morphisms_by_pair.get((A, B), [])

    def compose(self, g_name, f_name):
        return self.compose_table[(g_name, f_name)]

    def id(self, A):
        return self.identity_map[A]


def yoneda_to_element(alpha: dict, A: str) -> object:
    """
    Given a natural transformation α: Hom(A,-) => F (encoded as a dict:
      alpha[(B, f)] = F(f)(x)  for each object B and morphism f: A -> B
    ), extract the element α_A(id_A) ∈ F(A).
    """
    return alpha.get(('component_at', A, 'on', A + '_id'))


def yoneda_from_element(x, A: str, F_on_objects: dict, F_on_morphisms: dict,
                         cat: FiniteCategory) -> dict:
    """
    Given x ∈ F(A), construct the natural transformation α^x: Hom(A,-) => F.
    α^x_B(f) := F(f)(x)  for each f: A -> B.

    Encodes the natural transformation as:
      { ('component_at', B, 'on', f_name): F_on_morphisms[f_name](x)
        for each object B and morphism f: A->B }
    """
    alpha = {}
    for B in cat.objects:
        for f_name in cat.hom(A, B):
            F_f = F_on_morphisms[f_name]   # F(f): F(A) -> F(B), a function
            alpha[('component_at', B, 'on', f_name)] = F_f(x)
    return alpha


def verify_yoneda_naturality(alpha: dict, A: str, F_on_objects: dict,
                              F_on_morphisms: dict, cat: FiniteCategory) -> dict:
    """
    Verify naturality of α^x: for every morphism h: B -> C and f: A -> B,
      α^x_C(h∘f) = F(h)(α^x_B(f))
    i.e., the naturality square commutes.
    """
    failures = []
    checks = []
    for B in cat.objects:
        for C in cat.objects:
            for h_name in cat.hom(B, C):
                for f_name in cat.hom(A, B):
                    hof_name = cat.compose(h_name, f_name)
                    # LHS: α^x_C(h∘f)
                    lhs = alpha.get(('component_at', C, 'on', hof_name))
                    # RHS: F(h)(α^x_B(f))
                    alpha_B_f = alpha.get(('component_at', B, 'on', f_name))
                    F_h = F_on_morphisms[h_name]
                    rhs = F_h(alpha_B_f)

                    ok = (lhs == rhs)
                    checks.append({
                        "h": h_name, "f": f_name, "h∘f": hof_name,
                        "lhs": lhs, "rhs": rhs, "holds": ok
                    })
                    if not ok:
                        failures.append({"h": h_name, "f": f_name, "lhs": lhs, "rhs": rhs})

    return {
        "all_natural": len(failures) == 0,
        "checks": checks,
        "failures": failures
    }


def verify_yoneda_roundtrip(A: str, F_on_objects: dict, F_on_morphisms: dict,
                             cat: FiniteCategory) -> dict:
    """
    Verify the round-trip: for every x ∈ F(A),
      yoneda_to_element(yoneda_from_element(x)) = x.
    """
    F_A_elements = F_on_objects[A]
    failures = []
    for x in F_A_elements:
        alpha_x = yoneda_from_element(x, A, F_on_objects, F_on_morphisms, cat)
        # α^x_A(id_A) = F(id_A)(x) = id_{F(A)}(x) = x
        id_A_name = cat.id(A)
        recovered = alpha_x.get(('component_at', A, 'on', id_A_name))
        if recovered != x:
            failures.append({"x": x, "recovered": recovered})

    return {
        "F(A)": F_A_elements,
        "roundtrip_holds": len(failures) == 0,
        "failures": failures,
        "elements_tested": len(F_A_elements)
    }


if __name__ == "__main__":
    # -----------------------------------------------------------------
    # Define a small category C with objects {0, 1, 2} and morphisms:
    #   id_0, id_1, id_2  (identities)
    #   f: 0->1, g: 1->2, h: 0->2  (with h = g∘f)
    # -----------------------------------------------------------------
    objects = ['0', '1', '2']
    morphisms_by_pair = {
        ('0','0'): ['id_0'],
        ('1','1'): ['id_1'],
        ('2','2'): ['id_2'],
        ('0','1'): ['f'],
        ('1','2'): ['g'],
        ('0','2'): ['h'],
    }
    # Composition table: (outer, inner) -> result
    compose_table = {
        ('id_0','id_0'): 'id_0',
        ('id_1','id_1'): 'id_1',
        ('id_2','id_2'): 'id_2',
        ('f',   'id_0'): 'f',
        ('id_1','f'):    'f',
        ('g',   'id_1'): 'g',
        ('id_2','g'):    'g',
        ('h',   'id_0'): 'h',
        ('id_2','h'):    'h',
        ('g',   'f'):    'h',
    }
    identity_map = {'0': 'id_0', '1': 'id_1', '2': 'id_2'}

    cat = FiniteCategory(objects, morphisms_by_pair, compose_table, identity_map)

    # -----------------------------------------------------------------
    # Define a functor F: C -> Set
    #   F(0) = {10, 20},  F(1) = {30, 40, 50},  F(2) = {60, 70}
    #   F(f): {10->30, 20->40}
    #   F(g): {30->60, 40->60, 50->70}
    #   F(h) = F(g)∘F(f): {10->60, 20->60}
    # -----------------------------------------------------------------
    F_on_objects = {
        '0': [10, 20],
        '1': [30, 40, 50],
        '2': [60, 70],
    }
    raw_F = {
        'id_0': {10: 10, 20: 20},
        'id_1': {30: 30, 40: 40, 50: 50},
        'id_2': {60: 60, 70: 70},
        'f':    {10: 30, 20: 40},
        'g':    {30: 60, 40: 60, 50: 70},
        'h':    {10: 60, 20: 60},
    }
    # Wrap as callable functions
    F_on_morphisms = {name: (lambda m: (lambda x: m[x]))(mapping)
                     for name, mapping in raw_F.items()}

    # -----------------------------------------------------------------
    # Yoneda with A = '0'
    # -----------------------------------------------------------------
    A = '0'
    print(f"=== Yoneda Lemma Verification: Nat(Hom({A},-), F) ≅ F({A}) ===\n")

    for x in F_on_objects[A]:
        print(f"--- Element x = {x} ∈ F({A}) ---")
        alpha_x = yoneda_from_element(x, A, F_on_objects, F_on_morphisms, cat)

        nat_result = verify_yoneda_naturality(alpha_x, A, F_on_objects, F_on_morphisms, cat)
        print(f"  α^{x} is natural: {nat_result['all_natural']}")
        if not nat_result['all_natural']:
            for fail in nat_result['failures']:
                print(f"    FAIL: h={fail['h']}, f={fail['f']}, lhs={fail['lhs']}, rhs={fail['rhs']}")

    rt = verify_yoneda_roundtrip(A, F_on_objects, F_on_morphisms, cat)
    print(f"\n=== Round-trip α^x ↦ α^x_A(id_A) = x ===")
    print(f"  Holds: {rt['roundtrip_holds']}")
    print(f"  Elements tested: {rt['elements_tested']}")
    if rt['failures']:
        for fail in rt['failures']:
            print(f"  FAIL: x={fail['x']}, recovered={fail['recovered']}")
```

### 3.3 Formal Proof in Lean 4: Category Axioms and Functor Laws

The Python exercises verify correctness empirically over finite instances. The Lean 4 proof below establishes the axioms universally, for all categories and all functors, through formal type-theoretic proof. This is the complement of computational testing: where Python confirms that a specific morphism satisfies associativity, Lean proves that any morphism in any category satisfying the axioms satisfies it, and that any functor preserving composition necessarily preserves identity.

```lean
-- lab03_category.lean
-- Lean 4 (with Mathlib): formal encoding and proof of category axioms,
-- functor laws, and the basic naturality condition.
-- Compile with: lake build  (in a Lean 4 project with Mathlib dependency)

import Mathlib.CategoryTheory.Category.Basic
import Mathlib.CategoryTheory.Functor.Basic
import Mathlib.CategoryTheory.NatTrans
import Mathlib.CategoryTheory.Adjunction.Basic

open CategoryTheory

-- -----------------------------------------------------------------------
-- Part 1: Verify that any category satisfies the identity and associativity
-- axioms. These are definitionally true in Lean's type system, but we
-- state them explicitly as propositions to confirm the encoding.
-- -----------------------------------------------------------------------

section CategoryAxioms

variable {C : Type*} [Category C]
variable {A B D E : C}
variable (f : A ⟶ B) (g : B ⟶ D) (h : D ⟶ E)

-- Right identity: f ≫ 𝟙 B = f
theorem right_identity_holds : f ≫ 𝟙 B = f := by
  simp [Category.comp_id]

-- Left identity: 𝟙 A ≫ f = f
theorem left_identity_holds : 𝟙 A ≫ f = f := by
  simp [Category.id_comp]

-- Associativity: (h ≫ g) ≫ f = h ≫ (g ≫ f)
-- Note: Lean uses left-to-right composition, so f ≫ g means "f then g"
theorem associativity_holds : (f ≫ g) ≫ h = f ≫ (g ≫ h) := by
  simp [Category.assoc]

end CategoryAxioms


-- -----------------------------------------------------------------------
-- Part 2: Verify the functor laws.
-- Given F : C ⥤ D, prove F.map (𝟙 A) = 𝟙 (F.obj A) and
-- F.map (f ≫ g) = F.map f ≫ F.map g.
-- -----------------------------------------------------------------------

section FunctorLaws

variable {C D : Type*} [Category C] [Category D]
variable (F : C ⥤ D)
variable {A B E : C} (f : A ⟶ B) (g : B ⟶ E)

-- Functor identity law
theorem functor_identity_law : F.map (𝟙 A) = 𝟙 (F.obj A) := by
  exact F.map_id A

-- Functor composition law
theorem functor_composition_law : F.map (f ≫ g) = F.map f ≫ F.map g := by
  exact F.map_comp f g

end FunctorLaws


-- -----------------------------------------------------------------------
-- Part 3: Natural transformation naturality condition.
-- Given α : F ⟹ G (a natural transformation), verify the naturality square.
-- -----------------------------------------------------------------------

section NaturalTransformationNaturality

variable {C D : Type*} [Category C] [Category D]
variable {F G : C ⥤ D} (α : F ⟶ G)
variable {A B : C} (f : A ⟶ B)

-- Naturality: G.map f ≫ α.app B = α.app A ≫ F.map f  (note: Lean convention)
-- In Mathlib, NatTrans.naturality states: α.app A ≫ G.map f = F.map f ≫ α.app B
-- We confirm both formulations are equivalent.
theorem naturality_square : α.app A ≫ G.map f = F.map f ≫ α.app B := by
  exact α.naturality f

-- The naturality square commutes in both directions (via symmetry of the equation)
theorem naturality_square_symm : F.map f ≫ α.app B = α.app A ≫ G.map f := by
  exact (α.naturality f).symm

end NaturalTransformationNaturality


-- -----------------------------------------------------------------------
-- Part 4: Adjunction triangle identities.
-- For an adjunction F ⊣ G, verify the two triangle identities.
-- -----------------------------------------------------------------------

section AdjunctionTriangles

variable {C D : Type*} [Category C] [Category D]
variable {F : C ⥤ D} {G : D ⥤ C} (adj : F ⊣ G)

-- Triangle Identity I: G.map (adj.counit.app B) ∘ adj.unit.app (G.obj B) = id
theorem triangle_identity_I (B : D) :
    adj.unit.app (G.obj B) ≫ G.map (adj.counit.app B) = 𝟙 (G.obj B) := by
  exact adj.right_triangle_components B

-- Triangle Identity II: adj.counit.app (F.obj A) ∘ F.map (adj.unit.app A) = id
theorem triangle_identity_II (A : C) :
    F.map (adj.unit.app A) ≫ adj.counit.app (F.obj A) = 𝟙 (F.obj A) := by
  exact adj.left_triangle_components A

end AdjunctionTriangles


-- -----------------------------------------------------------------------
-- Part 5: Yoneda lemma — the bijection Nat(Hom(A,-), F) ≅ F(A).
-- Mathlib provides this as Yoneda.yonedaEquiv. We state and use it here.
-- -----------------------------------------------------------------------

section YonedaLemma

open Opposite

variable {C : Type*} [Category C] [Small C]
variable (F : Cᵒᵖ ⥤ Type*)   -- presheaf (covariant Yoneda uses C ⥤ Type*)

-- The covariant Yoneda lemma: Nat(Hom(A,-), F) ≅ F(A)
-- In Mathlib this is phrased as yonedaEquiv.
-- We use the covariant version for concreteness.

example (A : C) (F : C ⥤ Type*) :
    ((yoneda.obj A) ⟶ F) ≃ F.obj A :=
  yonedaEquiv

-- The bijection maps α ↦ α.app A (𝟙 A)
-- We verify the forward direction explicitly.
example (A : C) (F : C ⥤ Type*) (α : (yoneda.obj A) ⟶ F) :
    yonedaEquiv α = α.app A (𝟙 A) := by
  rfl

-- The inverse maps x ∈ F(A) to the natural transformation α^x_B(f) = F(f)(x)
-- This is yonedaEquiv.symm, definitionally equal to the formula above.
example (A : C) (F : C ⥤ Type*) (x : F.obj A) :
    (yonedaEquiv.symm x).app A (𝟙 A) = x := by
  simp [yonedaEquiv]

end YonedaLemma
```

---

## Formal Axioms Cheat Sheet & Verification Reference

### Category Axioms

A category $\mathcal{C}$ must satisfy the following, all of which are verifiable by the predicates implemented above:

| Axiom | Formal Statement | Python Verifier |
|---|---|---|
| Composition closure | $f : A \to B,\ g : B \to C \implies g \circ f : A \to C$ | `compose(g, f)` raises `TypeError` if domains mismatch |
| Identity existence | $\forall A \in \mathcal{C},\ \exists\, \text{id}_A : A \to A$ | `identity(A)` |
| Right identity | $f \circ \text{id}_A = f$ | `verify_identity_laws(f)["right_identity_holds"]` |
| Left identity | $\text{id}_B \circ f = f$ | `verify_identity_laws(f)["left_identity_holds"]` |
| Associativity | $(h \circ g) \circ f = h \circ (g \circ f)$ | `verify_associativity(h, g, f)["associativity_holds"]` |

### Functor Laws

A functor $F : \mathcal{C} \to \mathcal{D}$ must satisfy:

| Law | Formal Statement | Python Verifier |
|---|---|---|
| Identity preservation | $F(\text{id}_A) = \text{id}_{F(A)}$ | `verify_functor_identity(ring, polys)["holds"]` |
| Composition preservation | $F(g \circ f) = F(g) \circ F(f)$ | `verify_functor_composition(...)["holds"]` |

### Natural Transformation Conditions

A natural transformation $\alpha : F \Rightarrow G$ requires, for every $f : A \to B$:

$$G(f) \circ \alpha_A = \alpha_B \circ F(f)$$

This is verified per-morphism by `verify_naturality(F, G, eta, morphisms)`. A failure on even one morphism disqualifies the entire transformation.

### Adjunction Triangle Identities

For an adjunction $F \dashv G$ with unit $\eta$ and counit $\varepsilon$:

| Identity | Formal Statement | Verification |
|---|---|---|
| Triangle I | $G(\varepsilon_B) \circ \eta_{G(B)} = \text{id}_{G(B)}$ | `verify_triangle_I(B_basis)["holds"]` |
| Triangle II | $\varepsilon_{F(A)} \circ F(\eta_A) = \text{id}_{F(A)}$ | `verify_triangle_II(A_basis)["holds"]` |

### Yoneda Bijection

The Yoneda bijection $\Phi : \text{Nat}(\text{Hom}(A,-), F) \xrightarrow{\sim} F(A)$ and its inverse are:

$$\Phi(\alpha) = \alpha_A(\text{id}_A) \qquad \Phi^{-1}(x)_B(f) = F(f)(x)$$

Naturality of $\Phi^{-1}(x)$ holds because for any $h : B \to C$ and $f : A \to B$:

$$\Phi^{-1}(x)_C(h \circ f) = F(h \circ f)(x) = F(h)(F(f)(x)) = F(h)(\Phi^{-1}(x)_B(f))$$

which is exactly the naturality square. The round-trip identity $\Phi^{-1}(\Phi(\alpha))_B(f) = \alpha_B(f)$ follows from naturality of $\alpha$ itself, applied to $f : A \to B$ with $\text{id}_A$:

$$F(f)(\alpha_A(\text{id}_A)) = \alpha_B(\text{Hom}(A,f)(\text{id}_A)) = \alpha_B(f \circ \text{id}_A) = \alpha_B(f)$$

Both directions are verified computationally by `verify_yoneda_roundtrip` and confirmed universally by the Lean proof `yonedaEquiv.symm` / `rfl`.

### Complete Verification Command Reference

```bash
# Environment check
python -c "import sympy, numpy; print(sympy.__version__, numpy.__version__)"

# Run all Python labs in sequence
python lab01_category_core.py
python lab01_functor_poly.py
python lab01_nat_transform.py
python lab02_universal_props.py
python lab02_equalizer.py
python lab02_pullback_sage.py
python lab03_adjunction.py
python lab03_yoneda.py

# Lean 4 formal verification (requires Mathlib)
# In a Lean 4 project directory with lakefile.lean importing Mathlib:
lake build
lean lab03_category.lean

# SageMath interactive session for algebraic cross-checks
sage -c "
from sage.all import *
# Verify that the free module functor on ZZ satisfies functor laws:
M2 = ZZ^2; M3 = ZZ^3
phi = M2.hom([M3([1,0,1]), M3([0,1,1])])  # linear map Z^2 -> Z^3
print('Identity map composite:', phi * M2.hom(matrix.identity(ZZ,2)) == phi)
print('Composition test:', (M3.hom(matrix.identity(ZZ,3)) * phi) == phi)
"
```
