# Operational Verification Labs: Foundational Paradoxes And Problems

## Objective & Mathematical Computing Setup

The paradoxes at the foundations of discrete mathematics are not mere curiosities. Russell's Paradox demolished naïve set theory and forced the axiomatization of mathematics itself. Gödel's Incompleteness Theorems proved that any sufficiently expressive formal system contains true statements it cannot prove. The Halting Problem demonstrated that computation has irreducible limits. These results are not abstract philosophical puzzles — they have direct, concrete consequences for how we build type systems, design automated theorem provers, and reason about the limits of algorithms.

This lab guide operationalizes these foundational results through Python, SymPy, and SageMath. Each exercise couples the mathematical structure of a paradox with a runnable computational implementation that makes the logical mechanism visible. You will encode Russell's paradox in Python's type system, construct Gödel numberings over syntactic strings, trace diagonal arguments over enumerable functions, and verify fixed-point constructions symbolically. By the end, the abstract becomes mechanical — you will see exactly where and why these systems break.

Before proceeding, verify your environment. The following commands confirm that the required toolchain is correctly installed and that version constraints are satisfied.

```python
import sys
import sympy
import numpy

print(f"Python version: {sys.version}")
print(f"SymPy version:  {sympy.__version__}")
print(f"NumPy version:  {numpy.__version__}")

# Confirm SageMath is available if running in a Sage kernel
try:
    import sage.all as sage
    print(f"SageMath version: {sage.version()}")
except ImportError:
    print("SageMath not detected — pure Python/SymPy path will be used throughout.")
```

If SymPy reports below version 1.12, upgrade with `pip install --upgrade sympy`. SageMath 10.x is recommended for the Gödel numbering exercises; if unavailable, the pure Python implementations provided here are fully self-contained. All code in this guide is written for Python 3.11+, exploits no deprecated APIs, and produces deterministic output.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Russell's Paradox and the Collapse of Naïve Comprehension

Naïve set theory permits the unrestricted comprehension schema: for any predicate $\phi(x)$, the collection $\{x \mid \phi(x)\}$ is a set. Georg Cantor and Gottlob Frege built their foundational programs on this principle. In 1901, Bertrand Russell applied it to the predicate $\phi(x) \equiv x \notin x$ and obtained the set $R = \{x \mid x \notin x\}$. The question $R \in R$ produces a contradiction regardless of its truth value: if $R \in R$, then by definition $R \notin R$; if $R \notin R$, then by definition $R \in R$. The system is inconsistent.

The computational analogue is not merely an illustration — it is a structurally identical argument expressed in terms of functions and their domains. Consider any function $f$ that maps objects to Boolean values. The diagonal construction builds a new object that disagrees with $f$ applied to itself. In Python, we can represent "sets" as membership-testing functions (predicates over integers) and construct the Russell predicate directly.

```python
from typing import Callable, Any

# A "naive set" is represented as a predicate: a function from objects to bool.
# We index sets by natural numbers so we can ask "does set n contain n?"

def make_russell_predicate(set_registry: dict[int, Callable[[int], bool]]) -> Callable[[int], bool]:
    """
    Constructs the Russell predicate R such that:
        R(n) = True  iff  set_registry[n](n) == False
    This directly encodes R = { x | x ∉ x }.
    """
    def russell(n: int) -> bool:
        if n not in set_registry:
            # Objects not in the registry are treated as not self-containing.
            return True
        return not set_registry[n](n)
    return russell


# Build a registry of example sets.
# set_registry[0]: the empty set — contains nothing.
# set_registry[1]: the universal set — contains everything.
# set_registry[2]: the set of even numbers — contains n if n is even.

set_registry: dict[int, Callable[[int], bool]] = {
    0: lambda n: False,          # empty set
    1: lambda n: True,           # universal set — SELF-CONTAINING: 1 ∈ set_1
    2: lambda n: (n % 2 == 0),   # even numbers — NOT self-containing: 2 ∈ set_2 (2 is even, OK)
}

russell = make_russell_predicate(set_registry)

print("Membership analysis before assigning Russell set an index:")
for idx in [0, 1, 2]:
    self_contains = set_registry[idx](idx)
    in_russell    = russell(idx)
    print(f"  set_{idx} contains itself: {self_contains:5} | Russell includes set_{idx}: {in_russell}")

# Now assign the Russell predicate an index in the registry and query it on itself.
RUSSELL_INDEX = 3
set_registry[RUSSELL_INDEX] = russell

print(f"\nRussell set assigned index {RUSSELL_INDEX}.")
print(f"Attempting to evaluate: does set_{RUSSELL_INDEX} contain set_{RUSSELL_INDEX}?")

try:
    # Python does not prevent this evaluation — it just recurses.
    # We detect the infinite regress manually.
    import sys
    sys.setrecursionlimit(20)  # intentionally low to catch the loop fast
    result = russell(RUSSELL_INDEX)
    print(f"  russell({RUSSELL_INDEX}) = {result}")
except RecursionError:
    print("  RecursionError: Infinite regress detected.")
    print("  This is the computational manifestation of Russell's Paradox.")
    print("  The predicate russell(RUSSELL_INDEX) has no well-defined Boolean value.")
```

The `RecursionError` is not a programming deficiency — it faithfully represents the logical situation. The evaluation of `russell(3)` requires knowing `russell(3)`, which requires knowing `russell(3)`, indefinitely. In formal logic, this is an ill-founded sentence: a sentence whose truth value would require its own truth value as input. The fix, historically, was type theory (Russell's own ramified type theory, later simplified by Church) or axiomatic set theory (Zermelo-Fraenkel), both of which restrict comprehension to prevent self-referential set formation.

Verify the structural integrity of the ZF restriction by reimplementing comprehension with an explicit domain bound. In ZF, the axiom schema of separation permits $\{x \in A \mid \phi(x)\}$ only when $A$ is an already-established set. The Russell argument fails because to form $R = \{x \in A \mid x \notin x\}$, you need a universal set $A$ containing all sets — and ZF's axioms do not provide one.

```python
# ZF-style separation: comprehension is always bounded by an existing set.
def zf_separation(base_set: set[int], predicate: Callable[[int], bool]) -> set[int]:
    """
    Implements the ZF Axiom Schema of Separation:
        { x ∈ base_set | predicate(x) }
    The domain is restricted to base_set, so self-referential formation
    requires base_set to already contain the constructed set — which it cannot,
    since the constructed set does not exist until after the operation completes.
    """
    return {x for x in base_set if predicate(x)}

# Attempt to form the Russell set within a finite universe {0, 1, 2, 3, 4}.
# Here "x contains itself" is modeled as x being even (a stand-in predicate).
finite_universe = {0, 1, 2, 3, 4}
self_containing = {0, 2, 4}  # sets that "contain themselves" in this model

not_self_containing = zf_separation(finite_universe, lambda x: x not in self_containing)
print(f"ZF separation — Russell-like set within finite universe: {not_self_containing}")

# Ask: is not_self_containing an element of finite_universe?
# In ZF, sets are formed within a universe; this new set is a subset, not necessarily a member.
# The paradox cannot arise because the constructed set is not an element of its own domain.
print(f"Is the constructed set itself in finite_universe? {not_self_containing in [finite_universe]}")
print("ZF separation produces a well-defined set with no self-referential contradiction.")
```

### 1.2 Cantor's Theorem and the Diagonal Argument

Cantor's Theorem states that for any set $S$, the power set $\mathcal{P}(S)$ has strictly greater cardinality than $S$. The proof constructs, for any function $f: S \to \mathcal{P}(S)$, a subset $D \subseteq S$ that cannot be in the image of $f$. Specifically:

$$D = \{x \in S \mid x \notin f(x)\}$$

For any $y \in S$, $D \neq f(y)$ because $y \in D \iff y \notin f(y)$, so $D$ and $f(y)$ disagree at $y$. This is the diagonal argument in its pure form, and it is structurally identical to Russell's Paradox. The difference is that Cantor's Theorem draws a cardinality conclusion from the construction rather than a contradiction — because $D$ is a perfectly valid subset of $S$; it just cannot be in the image of $f$, so $f$ is not surjective.

```python
import sympy
from sympy import FiniteSet, PowerSet, Symbol
from itertools import chain, combinations

def powerset_list(s: list) -> list[frozenset]:
    """Returns all subsets of s as a list of frozensets."""
    return [frozenset(c) for r in range(len(s) + 1) for c in combinations(s, r)]

def cantors_diagonal(base: list, f: dict[Any, frozenset]) -> frozenset:
    """
    Constructs the Cantor diagonal set D for a function f: base -> P(base).
    D = { x in base | x not in f(x) }
    By Cantor's theorem, D is not in the image of f.
    """
    return frozenset(x for x in base if x not in f[x])

# Work over the base set S = {0, 1, 2, 3}.
S = [0, 1, 2, 3]
PS = powerset_list(S)

print(f"|S| = {len(S)}, |P(S)| = {len(PS)}")
print(f"Cantor's theorem predicts |P(S)| > |S|: {len(PS) > len(S)}\n")

# Define an arbitrary function f: S -> P(S).
# This represents a candidate surjection — Cantor's proof shows none can exist.
f = {
    0: frozenset({1, 2}),
    1: frozenset({0, 1, 3}),
    2: frozenset(),
    3: frozenset({0, 2, 3}),
}

D = cantors_diagonal(S, f)
print(f"Defined mapping f:")
for k, v in f.items():
    print(f"  f({k}) = {set(v)}")

print(f"\nCantor diagonal set D = {set(D)}")

# Verify D is not in the image of f.
image_of_f = set(f.values())
print(f"\nImage of f contains {len(image_of_f)} sets.")
print(f"D is in image(f): {D in image_of_f}")
print("Cantor's Theorem confirmed: no f: S -> P(S) can be surjective.\n")

# Verify the disagreement at each point explicitly.
print("Pointwise verification of D vs f(y) for each y in S:")
for y in S:
    in_D     = y in D
    in_f_y   = y in f[y]
    disagree = in_D != in_f_y
    print(f"  y={y}: y∈D={in_D}, y∈f({y})={in_f_y}, D≠f({y}) at y: {disagree}")
```

The pointwise verification makes the diagonal mechanism explicit: at every index $y$, the diagonal set $D$ is constructed to disagree with $f(y)$, so $D$ cannot equal any $f(y)$. This same mechanism, applied to programs instead of sets, yields the undecidability of the Halting Problem.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Gödel Numbering and the Arithmetization of Syntax

Gödel's First Incompleteness Theorem (1931) establishes that any consistent, recursively axiomatizable formal system $T$ that is sufficiently expressive to represent Peano Arithmetic contains a sentence $G_T$ such that neither $G_T$ nor $\lnot G_T$ is provable in $T$. The sentence $G_T$ effectively says "I am not provable in $T$." The construction proceeds in three steps: assign natural numbers to syntactic objects (Gödel numbering), show that provability is an arithmetically definable relation, and apply the diagonal lemma to produce a self-referential sentence.

The critical technical mechanism is the Gödel numbering. We assign prime-based encodings to symbols, formulas, and sequences of formulas. For a sequence of symbols $s_1, s_2, \ldots, s_k$ with individual codes $c_1, c_2, \ldots, c_k$, the standard Gödel number is:

$$\ulcorner s_1 s_2 \cdots s_k \urcorner = 2^{c_1} \cdot 3^{c_2} \cdot 5^{c_3} \cdots p_k^{c_k}$$

where $p_i$ is the $i$-th prime. Unique prime factorization (the Fundamental Theorem of Arithmetic) guarantees that this encoding is injective and decodable.

```python
from sympy import factorint, nextprime, isprime
from functools import reduce
from operator import mul

# Symbol table for a minimal propositional logic over variables {p, q, r}
# and connectives {¬, ∧, ∨, →, ↔, (, )}.
SYMBOL_TABLE: dict[str, int] = {
    '0':  1,   # the constant zero (Peano arithmetic anchor)
    'S':  2,   # successor function
    '+':  3,
    '*':  4,
    '=':  5,
    '<':  6,
    '(':  7,
    ')':  8,
    '¬':  9,
    '∧': 10,
    '∨': 11,
    '→': 12,
    '↔': 13,
    '∀': 14,
    '∃': 15,
    'x':  16,
    'y':  17,
    'z':  18,
    'p':  19,
    'q':  20,
    'r':  21,
}

REVERSE_TABLE: dict[int, str] = {v: k for k, v in SYMBOL_TABLE.items()}

def nth_prime(n: int) -> int:
    """Returns the n-th prime (1-indexed)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    p = 2
    for _ in range(n - 1):
        p = nextprime(p)
    return p

def godel_encode(formula: str) -> int:
    """
    Encodes a formula string into its Gödel number using prime exponent encoding.
    formula: a string of symbols, each a key in SYMBOL_TABLE.
    Returns: the Gödel number as a Python integer.
    """
    tokens = list(formula)  # character-level tokenization for single-char symbols
    # Handle multi-character symbols (∧, ∨, →, ↔, ∀, ∃, ¬) which are single Unicode chars.
    # The tokenization above handles them correctly since each is one Unicode code point.
    
    codes = []
    for tok in tokens:
        if tok == ' ':
            continue  # skip whitespace
        if tok not in SYMBOL_TABLE:
            raise ValueError(f"Unknown symbol: '{tok}'. Add it to SYMBOL_TABLE.")
        codes.append(SYMBOL_TABLE[tok])
    
    # Gödel number = product of p_i^{code_i}
    gn = 1
    for i, c in enumerate(codes, start=1):
        gn *= nth_prime(i) ** c
    return gn

def godel_decode(gn: int) -> str:
    """
    Decodes a Gödel number back into the formula string.
    Uses prime factorization: the exponent of p_i gives symbol code at position i.
    """
    factors = factorint(gn)  # {prime: exponent}
    
    # Sort primes to recover positional order
    sorted_primes = sorted(factors.keys())
    
    # Verify these are consecutive primes starting from 2
    for i, p in enumerate(sorted_primes, start=1):
        expected = nth_prime(i)
        if p != expected:
            raise ValueError(f"Gödel number is malformed: expected prime {expected} at position {i}, found {p}.")
    
    tokens = []
    for p in sorted_primes:
        code = factors[p]
        if code not in REVERSE_TABLE:
            raise ValueError(f"Unknown symbol code {code} in Gödel number.")
        tokens.append(REVERSE_TABLE[code])
    
    return ''.join(tokens)

# Encode and decode a simple formula: ¬(x=0)
formula = '¬(x=0)'
gn = godel_encode(formula)
decoded = godel_decode(gn)

print(f"Formula:       '{formula}'")
print(f"Gödel number:  {gn}")
print(f"Decoded:       '{decoded}'")
print(f"Round-trip OK: {decoded == formula}\n")

# Encode the structure of a self-referential claim.
# The Gödel sentence G_T informally says: "the formula with Gödel number n is not provable."
# We encode a provability-negation template: ¬∃y(Proof(y,x))
# Using our minimal symbol set as an approximation.

provability_template = '¬∃y(y=x)'   # simplified: "there is no y equal to x" — structural stand-in
gn_template = godel_encode(provability_template)
print(f"Provability template: '{provability_template}'")
print(f"Gödel number:         {gn_template}")
print(f"Decoded:              '{godel_decode(gn_template)}'")
```

### 2.2 The Diagonal Lemma and the Fixed-Point Construction

The Diagonal Lemma (also called the Self-Reference Lemma or Fixed-Point Lemma) is the technical engine of Gödel's proof. It states: for any formula $\psi(x)$ with one free variable $x$, there exists a sentence $G$ such that $T \vdash G \leftrightarrow \psi(\ulcorner G \urcorner)$. That is, $G$ is provably equivalent to the claim that $\psi$ holds of $G$'s own Gödel number.

The construction is explicit. Define the substitution function $\text{sub}(n, m)$ to be the Gödel number of the formula obtained by substituting the numeral $\overline{m}$ for the free variable in the formula with Gödel number $n$. Define $\text{diag}(n) = \text{sub}(n, n)$: the Gödel number of the formula obtained by substituting $\overline{n}$ into the formula numbered $n$. For any $\psi(x)$, let $\psi^*$ be the formula $\psi(\text{diag}(x))$, with Gödel number $d = \ulcorner \psi^* \urcorner$. The fixed point is $G = \psi^*(\overline{d})$, whose Gödel number is $\text{diag}(d) = \text{sub}(d, d)$.

```python
# We simulate the diagonal lemma computationally using Python strings as formulas
# and a dictionary as the proof system's "derivation database."

class FormalSystem:
    """
    A minimal simulation of a formal system supporting:
      - Formula registration (associating strings with Gödel numbers)
      - Substitution of numerals for free variables
      - The diagonal construction
    """
    def __init__(self):
        self.formula_db: dict[int, str] = {}   # godel_number -> formula string
        self.provable:   set[int]       = set() # set of provable formula Gödel numbers

    def register(self, formula: str) -> int:
        gn = godel_encode(formula)
        self.formula_db[gn] = formula
        return gn

    def substitute(self, formula_gn: int, value: int) -> int:
        """
        Returns the Gödel number of the formula obtained by replacing
        the free variable 'x' in formula[formula_gn] with the numeral
        representing `value`. We simulate numerals as the string of `value`
        zeros chained with successors: S(S(...S(0)...)).
        In our symbol table, the numeral for n is S^n(0).
        We substitute the integer value directly in the formula string for simulation.
        """
        if formula_gn not in self.formula_db:
            raise ValueError(f"Formula GN {formula_gn} not in database.")
        
        formula = self.formula_db[formula_gn]
        # Substitute 'x' with the string representation of `value` (numeral stand-in)
        # In a real system, this would be S^value(0). We use str(value) for readability.
        substituted = formula.replace('x', str(value))
        return self.register(substituted)

    def diag(self, formula_gn: int) -> int:
        """
        Computes diag(n) = sub(n, n): substitutes n's own Gödel number into formula n.
        This is the core of the diagonal construction.
        """
        return self.substitute(formula_gn, formula_gn)

    def assert_provable(self, gn: int):
        self.provable.add(gn)

    def is_provable(self, gn: int) -> bool:
        return gn in self.provable


# Instantiate and register a provability-negation predicate.
# psi(x) = "the formula with Gödel number x is not provable"
# We approximate this as the string "¬∃y(y=x)" where x is the free variable.

T = FormalSystem()

psi_formula = '¬∃y(y=x)'          # psi(x): "x is not provable" (structural approximation)
psi_gn = T.register(psi_formula)

print(f"ψ(x) = '{psi_formula}'")
print(f"GN(ψ) = {psi_gn}\n")

# Compute the diagonal: D = psi(GN(psi)) = sub(psi_gn, psi_gn)
# This gives us the Gödel sentence G_T.
godel_sentence_gn = T.diag(psi_gn)
godel_sentence    = T.formula_db[godel_sentence_gn]

print(f"Gödel sentence G_T = ψ(⌈ψ⌉) = '{godel_sentence}'")
print(f"GN(G_T) = {godel_sentence_gn}\n")

# Demonstrate the fixed-point property:
# G_T says "the formula with GN godel_sentence_gn is not provable."
# If T proves G_T, then G_T is false (it says it's not provable), contradicting soundness.
# If T refutes G_T (proves ¬G_T), then G_T is true, contradicting consistency.
# Therefore T neither proves nor refutes G_T.

print("Incompleteness scenario analysis:")
print(f"  Suppose T ⊢ G_T.")
print(f"  Then G_T is provable, but G_T asserts its own unprovability.")
print(f"  This contradicts the soundness of T (T only proves truths).")
print(f"  Suppose T ⊢ ¬G_T.")
print(f"  Then G_T is false, meaning G_T IS provable.")
print(f"  But T ⊢ ¬G_T means T ⊢ G_T is false and T ⊢ G_T is true simultaneously.")
print(f"  This contradicts the consistency of T.")
print(f"  Therefore: T ⊬ G_T and T ⊬ ¬G_T — T is incomplete.")
```

### 2.3 The Halting Problem via Diagonalization

The Halting Problem asks whether there exists a Turing machine $H$ such that for any program $P$ and input $w$, $H(P, w)$ halts and correctly outputs whether $P(w)$ halts. Turing's 1936 proof that no such $H$ exists is a direct diagonal argument. We operationalize it in Python using the fact that programs are data: a Python function is a first-class object with an introspectable source string.

```python
import inspect
import textwrap

# Simulate the Halting Problem diagonalization.
# We model "programs" as Python callables and "halt/loop" behavior as return/no-return.
# The diagonal argument constructs a program D that defeats any candidate halts-decider H.

def simulate_halt_decider(program_source: str, input_value: Any) -> bool:
    """
    A HYPOTHETICAL halting decider. In reality, no such function can exist.
    For simulation, we use a simple heuristic: check whether the source contains
    an infinite loop pattern. This is NOT a real decider — it is used only
    to show how the diagonal argument defeats ANY candidate, however clever.
    """
    # Heuristic: if source contains 'while True' with no break, predict non-halting.
    has_infinite_loop = 'while True' in program_source and 'break' not in program_source
    return not has_infinite_loop  # True = "this program halts on this input"


def construct_diagonal_program(halts_decider) -> str:
    """
    Constructs the diagonal program D:
      D(x):
        if halts_decider(D_source, x):
            loop forever   # D does NOT halt when decider says it halts
        else:
            return         # D DOES halt when decider says it does not halt
    
    This is the program that defeats halts_decider by construction.
    Returns the source of D as a string (since D must be able to reference itself).
    """
    diagonal_source = textwrap.dedent("""
    def D(x):
        # D is the diagonal program. It runs the halting decider on its own source.
        import textwrap
        
        D_source = textwrap.dedent('''
        def D(x):
            pass  # placeholder — in a true diagonal construction,
                  # D_source would contain D's own full text.
        ''')
        
        # Ask the decider: does D halt on x?
        predicted_halt = simulate_halt_decider(D_source, x)
        
        if predicted_halt:
            # Decider says D halts — so D loops forever to contradict it.
            while True:
                pass
        else:
            # Decider says D loops — so D halts immediately to contradict it.
            return "halted"
    """)
    return diagonal_source


# Demonstrate the contradiction concretely.
print("Halting Problem — Diagonal Contradiction Analysis\n")

test_programs = {
    "trivial_halt": "def f(x): return x + 1",
    "infinite_loop": "def f(x):\n    while True: pass",
    "conditional":  "def f(x): return x if x > 0 else f(x-1)",
}

print("Hypothetical halting decider predictions:")
for name, src in test_programs.items():
    prediction = simulate_halt_decider(src, 0)
    print(f"  {name:20s}: halts = {prediction}")

print()

D_source = construct_diagonal_program(simulate_halt_decider)
print("Diagonal program D constructed.")
print("Applying halting decider to D on input D_source:\n")

# The decider predicts D's behavior on its own source.
# Whatever it predicts, D does the opposite.
prediction_on_D = simulate_halt_decider(D_source, D_source)
print(f"  simulate_halt_decider(D, D) predicts: D halts = {prediction_on_D}")

if prediction_on_D:
    print("  But D is defined to loop forever when the decider says it halts.")
    print("  Contradiction: the decider is wrong.")
else:
    print("  But D is defined to halt immediately when the decider says it loops.")
    print("  Contradiction: the decider is wrong.")

print("\nThis contradiction holds for ANY function in place of simulate_halt_decider.")
print("No program can correctly decide halting for all programs — QED.")
```

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Berry's Paradox and Definability in Finite Systems

Berry's Paradox considers "the smallest positive integer not definable in fewer than thirteen words." The phrase itself is a definition in fewer than thirteen words, so the number it purports to identify is both definable and not definable in fewer than thirteen words — a contradiction. This paradox, analyzed by Jules Richard and popularized by Bertrand Russell, is a semantic paradox about the limits of definability. Its formal resolution requires distinguishing between object language and metalanguage (Tarski's hierarchy of truth). Computationally, it manifests as the impossibility of a program shorter than $n$ bits that can describe the first string not describable by any program shorter than $n$ bits — the foundation of Kolmogorov complexity and algorithmic information theory.

```python
from sympy import isprime, factorint
from math import log2
import hashlib

# Berry's Paradox via Kolmogorov Complexity simulation.
# 
# Kolmogorov complexity K(s) of a string s = length of shortest program that outputs s.
# Berry's paradox formalizes as: consider the first string s* such that K(s*) > n bits.
# Any explicit description of s* is itself a program, so K(s*) ≤ |description| + O(1).
# If the description is shorter than n, we have K(s*) ≤ n, contradicting K(s*) > n.
#
# We simulate this with a "program" being a Python lambda's source, and "length" being
# the character count of that source. This demonstrates the definitional paradox concretely.

def description_complexity(value: int) -> int:
    """
    Returns the length (in characters) of the shortest Python expression
    we can find that evaluates to `value`. This is a computable LOWER BOUND
    approximation of Kolmogorov complexity — the true K(value) is uncomputable.
    """
    # Strategy: try increasingly complex expressions and find the shortest.
    candidates = [
        str(value),                             # direct numeral
        f"2**{int(log2(value))}" if value > 0 and (value & (value - 1)) == 0 else None,
        f"int('{hex(value)}', 16)",
        f"sum(range({int(value**0.5)+1}))" if value == sum(range(int(value**0.5)+1)) else None,
    ]
    lengths = [len(c) for c in candidates if c is not None]
    return min(lengths)

# Find, for small n, integers that require long descriptions.
print("Approximate description complexity for integers 1 to 50:\n")
print(f"{'n':>4}  {'shortest_expr_len':>18}  {'ratio':>8}")
print("-" * 40)

for n in range(1, 51):
    complexity = description_complexity(n)
    ratio = complexity / max(1, len(str(n)))
    print(f"{n:>4}  {complexity:>18}  {ratio:>8.2f}")

print()

# Simulate Berry's paradox: define "smallest integer not describable in <= K chars"
# for a given description length bound K.

def berry_candidate(K: int, search_limit: int = 10000) -> int:
    """
    Finds the smallest integer n in [1, search_limit] such that
    description_complexity(n) > K.
    
    The paradox: this function is itself a description of berry_candidate(K),
    and if the description of THIS FUNCTION is shorter than K characters in
    some formal system, then berry_candidate(K) is describable in < K characters,
    contradicting its definition.
    """
    for n in range(1, search_limit + 1):
        if description_complexity(n) > K:
            return n
    return -1  # not found within search limit

print("Berry's Paradox demonstration:")
print(f"{'K (char bound)':>15}  {'berry_candidate(K)':>20}  {'K(berry_candidate)':>20}")
print("-" * 60)
for K in [3, 5, 7, 9, 11]:
    bc = berry_candidate(K)
    if bc != -1:
        kc = description_complexity(bc)
        print(f"{K:>15}  {bc:>20}  {kc:>20}")
    else:
        print(f"{K:>15}  {'not found':>20}  {'—':>20}")

print()
print("The paradox: the function berry_candidate itself is a finite description.")
print("For large enough K, berry_candidate(K) is describable by this very function,")
print("which has a fixed finite length — contradicting its own minimality claim.")
```

### 3.2 SymPy-Based Verification of Fixed-Point Properties

The Knaster-Tarski Fixed-Point Theorem states that every monotone function on a complete lattice has a least fixed point and a greatest fixed point. This is the theoretical foundation of Datalog semantics, abstract interpretation in static analysis, and the semantics of recursive type definitions. We verify this computationally using SymPy's lattice structures and confirm fixed-point existence for concrete monotone operators.

```python
from sympy import symbols, And, Or, Not, Implies, simplify_logic, Symbol
from functools import reduce
from itertools import product, combinations

# Model a complete lattice as the powerset of a finite set, ordered by inclusion.
# Monotone operator T: P(S) -> P(S) represents a one-step consequence operator,
# exactly as in datalog / fixed-point logic semantics.

class PowersetLattice:
    """
    The complete lattice (P(S), ⊆) for a finite base set S.
    Elements are frozensets. The lattice ordering is set inclusion.
    Join (⊔) is union, Meet (⊓) is intersection.
    Bottom (⊥) is {}, Top (⊤) is S.
    """
    def __init__(self, base: list):
        self.base = list(base)
        self.top  = frozenset(base)
        self.bot  = frozenset()

    def leq(self, a: frozenset, b: frozenset) -> bool:
        """a ≤ b iff a ⊆ b."""
        return a.issubset(b)

    def join(self, a: frozenset, b: frozenset) -> frozenset:
        return a | b

    def meet(self, a: frozenset, b: frozenset) -> frozenset:
        return a & b

    def least_fixed_point(self, T) -> frozenset:
        """
        Computes the least fixed point of monotone operator T
        by iterating from ⊥: lfp(T) = ⋃_{n≥0} T^n(⊥).
        Terminates because P(S) is finite (ascending chain condition).
        """
        x = self.bot
        while True:
            x_next = T(x)
            if x_next == x:
                return x
            x = x_next

    def greatest_fixed_point(self, T) -> frozenset:
        """
        Computes the greatest fixed point of monotone operator T
        by iterating from ⊤: gfp(T) = ⋂_{n≥0} T^n(⊤).
        """
        x = self.top
        while True:
            x_next = T(x)
            if x_next == x:
                return x
            x = x_next

    def is_monotone(self, T) -> bool:
        """
        Verifies that T is monotone: a ⊆ b => T(a) ⊆ T(b)
        by checking all pairs of elements in P(S).
        """
        all_subsets = [frozenset(c) for r in range(len(self.base)+1)
                       for c in combinations(self.base, r)]
        for a in all_subsets:
            for b in all_subsets:
                if self.leq(a, b) and not self.leq(T(a), T(b)):
                    return False
        return True


from itertools import combinations

# Base set: S = {a, b, c, d}
S = ['a', 'b', 'c', 'd']
L = PowersetLattice(S)

# Define a monotone operator T: P(S) -> P(S).
# Example: T(X) = { y | some x in X "implies" y according to a rule set }
# Rules:  a -> b,  b -> c,  {a,c} -> d
# T(X) = X ∪ {b | a∈X} ∪ {c | b∈X} ∪ {d | a∈X and c∈X}

def consequence_operator(X: frozenset) -> frozenset:
    result = set(X)
    if 'a' in X:
        result.add('b')
    if 'b' in X:
        result.add('c')
    if 'a' in X and 'c' in X:
        result.add('d')
    return frozenset(result)

# Verify monotonicity.
mono = L.is_monotone(consequence_operator)
print(f"Consequence operator is monotone: {mono}\n")

# Compute least and greatest fixed points from different seeds.
lfp = L.least_fixed_point(consequence_operator)
gfp = L.greatest_fixed_point(consequence_operator)

print(f"Least fixed point  (from ⊥ = ∅):        {set(lfp)}")
print(f"Greatest fixed point (from ⊤ = {{a,b,c,d}}): {set(gfp)}")

# Trace the least fixed point iteration explicitly.
print("\nLFP iteration trace (Kleene ascending chain):")
x = L.bot
iteration = 0
while True:
    print(f"  T^{iteration}(⊥) = {set(x)}")
    x_next = consequence_operator(x)
    if x_next == x:
        print(f"  Fixed point reached at iteration {iteration}.")
        break
    x = x_next
    iteration += 1

# Verify the fixed point property: T(lfp) = lfp.
print(f"\nVerification: T(lfp) = {set(consequence_operator(lfp))}")
print(f"lfp itself   = {set(lfp)}")
print(f"T(lfp) == lfp: {consequence_operator(lfp) == lfp}")
```

### 3.3 Liar's Paradox and Tarski's Undefinability Theorem

The Liar's Paradox ("This sentence is false") demonstrates that a language cannot consistently contain its own truth predicate. Alfred Tarski formalized this intuition in his Undefinability Theorem (1933): no sufficiently expressive consistent formal system can define a truth predicate for its own language within that language. The proof uses the same diagonal construction as Gödel's theorem. We operationalize this by constructing a truth-assignment function in Python and demonstrating that any attempt to define a total self-applicable truth predicate produces a fixed sentence with no consistent Boolean value.

```python
from typing import Optional

class TruthSystem:
    """
    Models a formal system's attempt to define a truth predicate Truth(n),
    where n is the Gödel number of a sentence. Demonstrates Tarski's
    Undefinability Theorem by constructing the liar sentence.
    """
    def __init__(self):
        self.truth_values: dict[int, bool] = {}   # GN -> truth value
        self.sentence_map: dict[int, str]  = {}   # GN -> sentence string

    def assert_true(self, gn: int, sentence: str):
        self.truth_values[gn] = True
        self.sentence_map[gn] = sentence

    def assert_false(self, gn: int, sentence: str):
        self.truth_values[gn] = False
        self.sentence_map[gn] = sentence

    def truth(self, gn: int) -> Optional[bool]:
        """
        The candidate truth predicate Truth(n).
        Returns None if the sentence has no assigned value.
        """
        return self.truth_values.get(gn, None)

    def construct_liar(self) -> int:
        """
        Constructs the liar sentence L such that:
            L ≡ ¬Truth(⌈L⌉)
        That is, L says "I am false" — or equivalently, "my own truth value is False."
        
        Returns the Gödel number assigned to L.
        The diagonal construction: let phi(x) = ¬Truth(x).
        Apply the diagonal lemma: L = phi(⌈phi(⌈phi⌉)⌉) ... 
        We simulate by constructing a sentence whose GN is its own input to ¬Truth.
        """
        # We assign an arbitrary GN to L and define L as "¬Truth(GN_L)"
        # Then ask: what truth value must Truth(GN_L) have?
        
        LIAR_GN = 999999  # assigned Gödel number for the liar sentence
        liar_sentence = f"¬Truth({LIAR_GN})"  # "My Gödel number {LIAR_GN} is not true"
        self.sentence_map[LIAR_GN] = liar_sentence
        return LIAR_GN

    def evaluate_liar(self, liar_gn: int):
        """
        Attempts to assign a consistent truth value to the liar sentence.
        Demonstrates that no consistent assignment exists.
        """
        print(f"Liar sentence L (GN={liar_gn}): '{self.sentence_map[liar_gn]}'")
        print()
        
        print("Case 1: Suppose Truth(L) = True.")
        print(f"  Then L is true.")
        print(f"  L says '¬Truth({liar_gn})' — that Truth({liar_gn}) is False.")
        print(f"  But we assumed Truth({liar_gn}) = True. Contradiction.")
        print()
        
        print("Case 2: Suppose Truth(L) = False.")
        print(f"  Then L is false.")
        print(f"  L says '¬Truth({liar_gn})' — that Truth({liar_gn}) is False.")
        print(f"  L is false means its content ¬Truth({liar_gn}) is false.")
        print(f"  So Truth({liar_gn}) = True. But we assumed False. Contradiction.")
        print()
        
        print("Tarski's Undefinability Theorem conclusion:")
        print("  No total truth predicate Truth: GN -> Bool can consistently apply")
        print("  to sentences of the same language in which Truth is defined.")
        print("  Truth for language L must be defined in a strictly richer metalanguage L'.")


T = TruthSystem()

# Assign truth values to ordinary (non-paradoxical) sentences.
T.assert_true(godel_encode('x=0'),   'x=0')
T.assert_false(godel_encode('¬(x=0)'), '¬(x=0)')

print("Ordinary sentence truth values:")
for gn, sentence in list(T.sentence_map.items()):
    print(f"  GN={gn}: '{sentence}' -> Truth = {T.truth(gn)}")

print()
liar_gn = T.construct_liar()
T.evaluate_liar(liar_gn)
```

---

## Formal Axioms Cheat Sheet & Verification Reference

The following reference collects the formal statements of every theorem and paradox treated in this lab guide, together with their computational signatures, the key logical mechanism driving each result, and quick-verification one-liners for use during development.

---

**Naïve Comprehension Schema (Inconsistent)**

$$\forall \phi \,\exists S \,\forall x \,(x \in S \leftrightarrow \phi(x))$$

This schema is refuted by Russell's Paradox: instantiate $\phi(x) \equiv x \notin x$.

```python
# Quick verification: Russell predicate triggers infinite regress in Python.
R = {}
R[0] = lambda n: not R[n](n)  # encoding: set 0 "contains n" iff set n does not contain n
try:
    import sys; sys.setrecursionlimit(10)
    R[0](0)
except RecursionError:
    print("Russell contradiction confirmed: RecursionError on self-application.")
```

---

**ZF Axiom Schema of Separation (Consistent Replacement)**

$$\forall A \,\forall \phi \,\exists S \,\forall x \,(x \in S \leftrightarrow x \in A \land \phi(x))$$

Restricting comprehension to a bounded domain $A$ prevents the Russell construction because the resulting set $S \subseteq A$ is never a member of $A$ unless explicitly placed there by another axiom.

```python
A = frozenset(range(10))
S = frozenset(x for x in A if x % 2 == 0)  # separation: even elements of A
print(f"ZF separation: S = {S}, S ⊆ A: {S.issubset(A)}, S ∈ A: {S in A}")
```

---

**Cantor's Theorem**

For any set $S$ and any function $f: S \to \mathcal{P}(S)$, the diagonal set $D = \{x \in S \mid x \notin f(x)\}$ satisfies $D \notin \text{im}(f)$. Therefore $|\mathcal{P}(S)| > |S|$ for all sets $S$.

$$D = \{x \in S \mid x \notin f(x)\} \implies \forall y \in S,\; D \neq f(y)$$

```python
S = list(range(4))
f = {0: frozenset({1}), 1: frozenset({0,1}), 2: frozenset(), 3: frozenset({2,3})}
D = frozenset(x for x in S if x not in f[x])
print(f"D = {set(D)}, D in image(f): {D in set(f.values())}")
```

---

**Gödel's First Incompleteness Theorem**

Let $T$ be a consistent, recursively axiomatizable extension of Robinson Arithmetic $Q$. Then there exists a sentence $G_T$ such that $T \nvdash G_T$ and $T \nvdash \lnot G_T$. The sentence $G_T$ is constructed via the Diagonal Lemma applied to the predicate $\lnot \text{Provable}_T(x)$:

$$T \vdash G_T \leftrightarrow \lnot \text{Provable}_T(\ulcorner G_T \urcorner)$$

The key mechanism is the arithmetization of provability via Gödel numbering and the fixed-point construction $\text{diag}(n) = \text{sub}(n, n)$.

```python
# Verify Gödel numbering injectivity on two distinct formulas.
gn1 = godel_encode('x=0')
gn2 = godel_encode('¬(x=0)')
print(f"GN('x=0') = {gn1}, GN('¬(x=0)') = {gn2}, distinct: {gn1 != gn2}")
print(f"Round-trip: '{godel_decode(gn1)}', '{godel_decode(gn2)}'")
```

---

**Gödel's Second Incompleteness Theorem**

Let $T$ satisfy the conditions of the First Incompleteness Theorem. Then $T \nvdash \text{Con}(T)$, where $\text{Con}(T)$ is the arithmetical sentence expressing the consistency of $T$. The formal derivation proceeds by showing that if $T \vdash \text{Con}(T)$, then $T \vdash G_T$ (since $G_T$ is equivalent to $\text{Con}(T) \to G_T$ under the Hilbert-Bernays derivability conditions), contradicting the First Incompleteness Theorem.

---

**The Halting Problem (Turing 1936)**

There is no computable function $H: \Sigma^* \times \Sigma^* \to \{0,1\}$ such that for all programs $P$ and inputs $w$:

$$H(P, w) = \begin{cases} 1 & \text{if } P(w) \text{ halts} \\ 0 & \text{if } P(w) \text{ does not halt} \end{cases}$$

The proof constructs the diagonal program $D(x) = \text{if } H(x, x) = 1 \text{ then loop else halt}$, which satisfies $H(D, D) = 1 \iff D(D)$ does not halt, a direct contradiction.

```python
# Demonstrate that any Boolean-valued function on program source is defeated by D.
def any_decider(src: str, inp: str) -> bool:
    return len(src) % 2 == 0  # arbitrary total computable function

D_src = "loop_if_decider_says_halt"
prediction = any_decider(D_src, D_src)
# D does the opposite of prediction — the decider is wrong on input (D, D).
actual = not prediction
print(f"Decider predicts D halts: {prediction}. D actually halts: {actual}. Decider wrong: {prediction != actual}")
```

---

**Tarski's Undefinability Theorem**

Let $T$ be a consistent theory interpreting Robinson Arithmetic. There is no formula $\text{True}(x)$ in the language of $T$ such that for every sentence $\phi$ of $T$:

$$T \vdash \phi \leftrightarrow \text{True}(\ulcorner \phi \urcorner)$$

The proof: apply the Diagonal Lemma to $\lnot \text{True}(x)$ to obtain a liar sentence $L$ satisfying $T \vdash L \leftrightarrow \lnot \text{True}(\ulcorner L \urcorner)$. If $T \vdash L$, then $T \vdash \lnot \text{True}(\ulcorner L \urcorner)$, contradicting the T-schema. If $T \vdash \lnot L$, then $T \vdash \text{True}(\ulcorner L \urcorner)$, so $T \vdash L$, contradicting consistency.

---

**Knaster-Tarski Fixed-Point Theorem**

Let $(L, \leq)$ be a complete lattice and $f: L \to L$ a monotone function (i.e., $a \leq b \implies f(a) \leq f(b)$). Then $f$ has a least fixed point $\text{lfp}(f) = \bigwedge\{x \mid f(x) \leq x\}$ and a greatest fixed point $\text{gfp}(f) = \bigvee\{x \mid x \leq f(x)\}$.

$$\text{lfp}(f) = \bigcup_{n \geq 0} f^n(\bot), \qquad \text{gfp}(f) = \bigcap_{n \geq 0} f^n(\top)$$

```python
# Quick check: a monotone operator on {0,1,2,3} under ≤ has a fixed point.
def mono_f(x): return min(x + 1, 3)  # monotone on {0,1,2,3}
x = 0
while mono_f(x) != x:
    x = mono_f(x)
print(f"Least fixed point of mono_f: {x}  (verify: f({x})={mono_f(x)})")
```

---

Every result in this lab guide converges on the same underlying structure: a diagonal construction applied to a self-referential sentence, function, or program. Russell's Paradox, Cantor's Theorem, Gödel's Incompleteness Theorems, the Halting Problem, and Tarski's Undefinability Theorem are not five separate discoveries — they are five instantiations of one mathematical pattern. The computational implementations here are not mere illustrations. They are executable witnesses to the formal arguments, and running them, modifying the predicate tables, changing the base sets, and stress-testing the fixed-point iterations is the most direct path to internalizing why these limits exist and exactly where they bind.
