# Operational Verification Labs: Proof Theory

## Objective & Mathematical Computing Setup

Proof theory occupies the foundational strata of mathematical logic, treating proofs themselves as mathematical objects amenable to combinatorial analysis, structural transformation, and computational verification. Where model theory examines truth semantics through structures and interpretations, proof theory investigates the syntactic machinery of formal derivation: sequent calculi, natural deduction systems, cut elimination theorems, and normalization procedures. This laboratory guide establishes a computational framework for verifying fundamental proof-theoretic properties through symbolic execution, implementing formal derivation systems in Python with SymPy's logic module, and validating metatheorems through algorithmic construction and exhaustive case analysis.

The practitioner operating in this domain must cultivate dual competencies: rigorous symbolic manipulation of logical formulas within formal calculi, and the discipline to encode these syntactic transformations as verifiable computational procedures. Proof theory demands precision at the token level—every inference rule application, every structural transformation, every cut elimination step must preserve logical validity while respecting the combinatorial constraints of the formal system. Unlike semantic model checking, which appeals to truth tables and satisfiability solvers, proof-theoretic verification constructs explicit derivation trees, applies rewrite rules, and demonstrates syntactic properties through induction on proof structure.

Establish your computational environment by installing Python 3.11 or later with a complete symbolic computation stack. Execute `python -m pip install sympy numpy matplotlib` to acquire the primary algebraic engine. SymPy version 1.12 or later provides robust propositional and first-order logic manipulation through its `sympy.logic` module, supporting formula parsing, normal form conversion, and satisfiability checking. For advanced work involving automated theorem proving, install Z3 via `python -m pip install z3-solver`, which exposes satisfiability modulo theories (SMT) solving capabilities essential for verifying semantic consequences and countermodel construction. Practitioners requiring full proof assistant environments should install Lean 4 through `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh` or Coq via the platform package manager, though the core exercises in this guide target the more accessible Python ecosystem where proof objects are represented as structured data and manipulated through explicit algorithms.

Verify your installation by launching a Python REPL and executing the diagnostic sequence. Import SymPy's logic module and construct a simple propositional tautology: `from sympy.logic.boolalg import And, Or, Not, Implies; from sympy import symbols; p, q = symbols('p q'); formula = Implies(And(p, Implies(p, q)), q); print(formula)` should render the modus ponens schema in symbolic form. Test satisfiability checking with `from sympy.logic.inference import satisfiable; print(satisfiable(formula))` which should return a model dictionary or `True` indicating validity. For proof construction, we will implement sequent calculus rules and natural deduction inference patterns as Python functions operating on formula trees, tracking premise sets and conclusion formulas through explicit data structures. This computational substrate transforms abstract proof theory into executable verification procedures where metatheorems become testable hypotheses and structural properties emerge through algorithmic exploration.

## Exercise 1: Computational Verification of Core Theorems

### Sequent Calculus Implementation and Structural Properties

The sequent calculus, introduced by Gerhard Gentzen in 1934, formalizes logical inference through sequents of the form $\Gamma \vdash \Delta$, where $\Gamma$ and $\Delta$ are finite multisets of formulas representing antecedent assumptions and succedent conclusions respectively. Classical propositional sequent calculus LK admits structural rules (weakening, contraction, exchange) and logical rules (left and right introduction for each connective) that collectively characterize classical logic through a purely syntactic derivation system. The fundamental metatheorem of sequent calculus is Gentzen's cut elimination theorem: any provable sequent admits a cut-free derivation, where the cut rule—which allows modus ponens-style intermediate formula elimination—has been systematically removed through a constructive transformation algorithm.

Implement a sequent data structure as a Python class encapsulating antecedent and succedent formula lists. Begin by establishing the formula representation using SymPy's logic types, then construct the sequent container:

```python
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent
from sympy import symbols
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class Sequent:
    """Sequent Γ ⊢ Δ where Γ is antecedent list, Δ is succedent list."""
    antecedents: List = field(default_factory=list)
    succedents: List = field(default_factory=list)
    
    def __str__(self):
        ant_str = ", ".join(str(f) for f in self.antecedents) if self.antecedents else "∅"
        suc_str = ", ".join(str(f) for f in self.succedents) if self.succedents else "∅"
        return f"{ant_str} ⊢ {suc_str}"
    
    def is_axiom(self) -> bool:
        """Check if sequent is an axiom (formula appears in both sides)."""
        for ant in self.antecedents:
            if ant in self.succedents:
                return True
        return False

# Example: construct the sequent p, p → q ⊢ q (modus ponens)
p, q, r = symbols('p q r')
seq_mp = Sequent([p, Implies(p, q)], [q])
print(f"Modus Ponens Sequent: {seq_mp}")
print(f"Is Axiom: {seq_mp.is_axiom()}")
```

Axiom sequents form the base case of derivations, requiring no further justification. The axiomatic sequent $\Gamma, A \vdash A, \Delta$ holds for any formula $A$ and arbitrary contexts $\Gamma, \Delta$. Verify this property by constructing test cases where the same atomic proposition appears on both sides. The implementation above recognizes exact formula matches; in a complete system, one would extend this to handle formula equality modulo associativity and commutativity of multisets.

Now implement the fundamental sequent calculus rules for propositional logic. Each rule takes one or two premise sequents and produces a conclusion sequent, or operates as an axiom requiring no premises. The right conjunction rule $\land$R states that to prove $\Gamma \vdash A \land B, \Delta$, one must prove both $\Gamma \vdash A, \Delta$ and $\Gamma \vdash B, \Delta$. The left implication rule $\to$L states that from $\Gamma \vdash A, \Delta$ and $\Gamma, B \vdash \Delta$, one can derive $\Gamma, A \to B \vdash \Delta$. Encode these inference patterns:

```python
def apply_right_and(seq: Sequent, formula: And) -> Tuple[Sequent, Sequent]:
    """
    Right-And rule: Γ ⊢ A ∧ B, Δ requires proving Γ ⊢ A, Δ and Γ ⊢ B, Δ.
    Returns two premise sequents needed.
    """
    if formula not in seq.succedents:
        raise ValueError(f"Formula {formula} not in succedent")
    
    # Remove A ∧ B from succedent, add A in first premise, B in second
    new_succedents = [f for f in seq.succedents if f != formula]
    premise1 = Sequent(seq.antecedents[:], new_succedents + [formula.args[0]])
    premise2 = Sequent(seq.antecedents[:], new_succedents + [formula.args[1]])
    return premise1, premise2

def apply_left_implies(seq: Sequent, formula: Implies) -> Tuple[Sequent, Sequent]:
    """
    Left-Implies rule: Γ, A → B ⊢ Δ requires Γ ⊢ A, Δ and Γ, B ⊢ Δ.
    Returns two premise sequents.
    """
    if formula not in seq.antecedents:
        raise ValueError(f"Formula {formula} not in antecedent")
    
    new_antecedents = [f for f in seq.antecedents if f != formula]
    # First premise: prove antecedent A
    premise1 = Sequent(new_antecedents[:], seq.succedents[:] + [formula.args[0]])
    # Second premise: assume consequent B
    premise2 = Sequent(new_antecedents[:] + [formula.args[1]], seq.succedents[:])
    return premise1, premise2

# Test right-and decomposition
seq_test = Sequent([p], [And(q, r)])
p1, p2 = apply_right_and(seq_test, And(q, r))
print(f"\nRight-And Decomposition of {seq_test}:")
print(f"  Premise 1: {p1}")
print(f"  Premise 2: {p2}")

# Test left-implies decomposition
seq_impl = Sequent([Implies(p, q), p], [r])
pr1, pr2 = apply_left_implies(seq_impl, Implies(p, q))
print(f"\nLeft-Implies Decomposition of {seq_impl}:")
print(f"  Premise 1: {pr1}")
print(f"  Premise 2: {pr2}")
```

Execute this code to observe the syntactic decomposition of complex formulas into subgoals. The right-and rule creates two independent proof obligations—both conjuncts must be established separately. The left-implies rule manifests the computational content of implication elimination: to use an assumption $A \to B$, one must prove the antecedent $A$ holds (producing it in the succedent of the first premise) and then may assume the consequent $B$ (adding it to the antecedent of the second premise). This syntactic dance mirrors the semantic meaning while remaining purely structural, making no appeal to truth values or models.

Construct a complete proof tree for the sequent $p, p \to q \vdash q$ (modus ponens) by applying rules until reaching axioms. The strategy proceeds bottom-up: start with the goal sequent, apply left-implies to the implication in the antecedent, then verify both resulting premises are axioms:

```python
def prove_modus_ponens():
    """Construct explicit proof tree for p, p → q ⊢ q."""
    p, q = symbols('p q')
    goal = Sequent([p, Implies(p, q)], [q])
    print(f"Goal: {goal}")
    
    # Apply left-implies to p → q
    premise1, premise2 = apply_left_implies(goal, Implies(p, q))
    print(f"\nAfter applying →L:")
    print(f"  Premise 1: {premise1}")
    print(f"  Premise 1 is axiom: {premise1.is_axiom()}")
    print(f"  Premise 2: {premise2}")
    print(f"  Premise 2 is axiom: {premise2.is_axiom()}")
    
    return premise1.is_axiom() and premise2.is_axiom()

result = prove_modus_ponens()
print(f"\nModus ponens proof valid: {result}")
```

Both premises reduce to axioms: $p \vdash p, q$ (the antecedent $p$ appears in the succedent after being pushed right) and $p, q \vdash q$ (the consequent $q$ appears in both antecedent and succedent). This computational proof construction demonstrates that the sequent is derivable, confirming its validity through purely syntactic manipulation without semantic evaluation.

### Cut Elimination Verification

Gentzen's Hauptsatz (main theorem) asserts that the cut rule, which states that from $\Gamma \vdash A, \Delta$ and $\Gamma', A \vdash \Delta'$ one may derive $\Gamma, \Gamma' \vdash \Delta, \Delta'$, is admissible but not necessary: every provable sequent has a cut-free proof. The cut rule represents transitivity of entailment and mirrors modus ponens at the metalevel, allowing intermediate lemmas to be introduced and subsequently eliminated. Cut elimination is fundamental because cut-free proofs possess the subformula property—every formula appearing in the proof is a subformula of the conclusion sequent—which enables decision procedures and consistency proofs.

Implement the cut rule and then construct an algorithm that detects cuts in a proof tree and attempts elimination through rule permutation:

```python
def apply_cut(seq1: Sequent, seq2: Sequent, cut_formula) -> Sequent:
    """
    Cut rule: from Γ ⊢ A, Δ and Γ', A ⊢ Δ' derive Γ, Γ' ⊢ Δ, Δ'.
    cut_formula A must appear in seq1 succedent and seq2 antecedent.
    """
    if cut_formula not in seq1.succedents:
        raise ValueError(f"Cut formula {cut_formula} not in first sequent succedent")
    if cut_formula not in seq2.antecedents:
        raise ValueError(f"Cut formula {cut_formula} not in second sequent antecedent")
    
    # Remove cut formula from both sequents and merge
    new_ant = [f for f in seq1.antecedents] + [f for f in seq2.antecedents if f != cut_formula]
    new_suc = [f for f in seq1.succedents if f != cut_formula] + [f for f in seq2.succedents]
    return Sequent(new_ant, new_suc)

def has_subformula_property(proof_formulas: List, conclusion: Sequent) -> bool:
    """
    Check if all formulas in proof are subformulas of conclusion.
    """
    from sympy.logic.boolalg import BooleanFunction
    
    def get_subformulas(formula):
        """Extract all subformulas recursively."""
        subs = {formula}
        if isinstance(formula, BooleanFunction):
            for arg in formula.args:
                subs.update(get_subformulas(arg))
        return subs
    
    conclusion_subs = set()
    for f in conclusion.antecedents + conclusion.succedents:
        conclusion_subs.update(get_subformulas(f))
    
    for pf in proof_formulas:
        if pf not in conclusion_subs:
            return False
    return True

# Example: prove (p → q) ∧ (q → r) ⊢ p → r using cut on q
p, q, r = symbols('p q r')
# seq1: (p → q) ∧ (q → r), p ⊢ q (intermediate)
seq1 = Sequent([And(Implies(p, q), Implies(q, r)), p], [q])
# seq2: (p → q) ∧ (q → r), q ⊢ r (intermediate)
seq2 = Sequent([And(Implies(p, q), Implies(q, r)), q], [r])
# Apply cut on q
conclusion = apply_cut(seq1, seq2, q)
print(f"Cut application on q:")
print(f"  Premise 1: {seq1}")
print(f"  Premise 2: {seq2}")
print(f"  Conclusion: {conclusion}")

# Check subformula property violation
proof_formulas = list(set(seq1.antecedents + seq1.succedents + seq2.antecedents + seq2.succedents))
print(f"\nProof formulas: {proof_formulas}")
goal_sequent = Sequent([And(Implies(p, q), Implies(q, r))], [Implies(p, r)])
print(f"Subformula property holds: {has_subformula_property(proof_formulas, goal_sequent)}")
```

The cut on $q$ introduces an intermediate formula not appearing in the final sequent $(p \to q) \land (q \to r) \vdash p \to r$. A cut-free proof would decompose the conjunction and implications without explicitly materializing $q$ as an intermediate. Cut elimination algorithms systematically push cuts upward in the proof tree through rule permutations until they vanish or reduce to axioms. For propositional logic, this process always terminates, though it may cause exponential blowup in proof size—a complexity unavoidable in the worst case.

Implement a naive cut elimination checker that verifies whether a simple proof avoids cuts:

```python
def verify_cut_free_proof(proof_steps: List[Tuple[str, Sequent]]) -> bool:
    """
    Verify that a proof trace contains no cut applications.
    proof_steps is list of (rule_name, sequent) tuples.
    """
    for rule_name, seq in proof_steps:
        if rule_name == "cut":
            print(f"Cut detected at sequent: {seq}")
            return False
    return True

# Example cut-free proof trace for p ⊢ p ∨ q
proof_trace = [
    ("axiom", Sequent([p], [p])),
    ("right-or-1", Sequent([p], [Or(p, q)]))
]
print(f"\nCut-free verification: {verify_cut_free_proof(proof_trace)}")

proof_with_cut = proof_trace + [("cut", Sequent([p], [q]))]
print(f"Proof with cut: {verify_cut_free_proof(proof_with_cut)}")
```

This primitive checker identifies explicit cut rule applications in a proof trace. A complete cut elimination verifier would implement Gentzen's inductive algorithm, permuting cuts through logical rules and reducing cut rank (the complexity measure based on cut formula structure) until elimination. Such implementations exist in proof assistants like Coq and Isabelle, where the metatheorem itself is formalized and verified.

### Natural Deduction and Normalization

Natural deduction, also developed by Gentzen, provides an alternative proof calculus centered on introduction and elimination rules for each logical connective, more closely mirroring informal mathematical reasoning. Implication introduction ($\to$I) allows deriving $A \to B$ by assuming $A$ and proving $B$ under that assumption. Implication elimination ($\to$E) is modus ponens: from $A \to B$ and $A$, derive $B$. The fundamental metatheorem for natural deduction is normalization: every derivation can be transformed into normal form where no introduction rule is immediately followed by an elimination rule for the same connective, eliminating "detours" in reasoning.

Implement natural deduction proof trees as recursive structures where each node represents an inference rule application:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NDProof:
    """Natural deduction proof tree node."""
    conclusion: any  # Formula concluded at this node
    rule: str  # Rule name (implies-intro, implies-elim, and-intro, etc.)
    premises: List['NDProof'] = field(default_factory=list)
    assumption: Optional[any] = None  # For discharge in implies-intro
    
    def __str__(self, indent=0):
        prefix = "  " * indent
        result = f"{prefix}{self.rule}: {self.conclusion}"
        if self.assumption:
            result += f" [assuming {self.assumption}]"
        result += "\n"
        for prem in self.premises:
            result += prem.__str__(indent + 1)
        return result

def nd_implies_intro(assumption, proof_of_consequent: NDProof):
    """
    →I rule: If B is derivable from assumption A, conclude A → B.
    Discharges the assumption A.
    """
    implication = Implies(assumption, proof_of_consequent.conclusion)
    return NDProof(implication, "→I", [proof_of_consequent], assumption=assumption)

def nd_implies_elim(proof_of_impl: NDProof, proof_of_antecedent: NDProof):
    """
    →E rule (modus ponens): From A → B and A, derive B.
    """
    impl_formula = proof_of_impl.conclusion
    if not isinstance(impl_formula, Implies):
        raise ValueError(f"First premise must be implication, got {impl_formula}")
    if proof_of_antecedent.conclusion != impl_formula.args[0]:
        raise ValueError(f"Antecedent mismatch: {proof_of_antecedent.conclusion} vs {impl_formula.args[0]}")
    
    return NDProof(impl_formula.args[1], "→E", [proof_of_impl, proof_of_antecedent])

# Construct proof of p → p (identity function)
p, q = symbols('p q')
assumption_p = NDProof(p, "assumption")
proof_identity = nd_implies_intro(p, assumption_p)
print("Natural Deduction Proof of p → p:")
print(proof_identity)

# Construct proof of (p → q) → ((q → r) → (p → r)) (transitivity)
# Assume p → q
impl_pq = NDProof(Implies(p, q), "assumption")
# Assume q → r
impl_qr = NDProof(Implies(q, r), "assumption")
# Assume p
assumption_p2 = NDProof(p, "assumption")
# Apply p → q to p to get q
derived_q = nd_implies_elim(impl_pq, assumption_p2)
# Apply q → r to q to get r
derived_r = nd_implies_elim(impl_qr, derived_q)
# Discharge p to get p → r
impl_pr = nd_implies_intro(p, derived_r)
# Discharge q → r to get (q → r) → (p → r)
step2 = nd_implies_intro(Implies(q, r), impl_pr)
# Discharge p → q to get (p → q) → ((q → r) → (p → r))
proof_trans = nd_implies_intro(Implies(p, q), step2)
print("\nNatural Deduction Proof of Implication Transitivity:")
print(proof_trans)
```

Execute this to observe the hierarchical proof structure. Each implication introduction creates a subproof with an assumption scope, and elimination rules combine independent derivations. The transitivity proof exhibits nested assumption discharge, constructing a proof of the combinatorial type corresponding to function composition in the Curry-Howard correspondence.

Implement a detour detector that identifies β-redexes—patterns where an introduction immediately precedes an elimination—and performs normalization:

```python
def has_detour(proof: NDProof) -> bool:
    """
    Detect if proof contains detour: →I immediately followed by →E.
    This is a β-redex in proof terms.
    """
    if proof.rule == "→E":
        # Check if first premise (the implication) was derived by →I
        if proof.premises[0].rule == "→I":
            return True
    # Recursively check premises
    for prem in proof.premises:
        if has_detour(prem):
            return True
    return False

def normalize_step(proof: NDProof) -> NDProof:
    """
    Perform one step of β-reduction: eliminate →I/→E detours.
    """
    if proof.rule == "→E" and proof.premises[0].rule == "→I":
        # Detour detected: (λx.M) N reduces to M[x := N]
        impl_proof = proof.premises[0]  # The λx.M
        arg_proof = proof.premises[1]   # The N
        # Substitute arg_proof for assumption in impl_proof body
        # (Simplified: return the body of the →I proof)
        return impl_proof.premises[0]
    
    # Recursively normalize premises
    normalized_premises = [normalize_step(prem) for prem in proof.premises]
    return NDProof(proof.conclusion, proof.rule, normalized_premises, proof.assumption)

# Create a proof with detour: (λp.p) q reduces to q
q = symbols('q')
inner_assumption = NDProof(q, "assumption")
lambda_identity = nd_implies_intro(q, inner_assumption)  # q → q
arg = NDProof(q, "assumption")  # Prove q
detour_proof = nd_implies_elim(lambda_identity, arg)  # Apply identity to q

print("\nProof with Detour:")
print(detour_proof)
print(f"Has detour: {has_detour(detour_proof)}")

normalized = normalize_step(detour_proof)
print("\nAfter One Normalization Step:")
print(normalized)
print(f"Still has detour: {has_detour(normalized)}")
```

The detour $(q \to q)$ applied to $q$ normalizes to simply $q$, eliminating the unnecessary abstraction-application pair. Full normalization iterates this process until no redexes remain, producing the normal form where every formula is used exactly once in the most direct path from assumptions to conclusion. This corresponds to β-normal form in the lambda calculus, establishing the deep Curry-Howard connection between proofs and programs.

## Exercise 2: Boundary Value Stress Testing & Singularities

### Consistency and Completeness at the Metalevel

Proof-theoretic systems exhibit critical properties at their foundational boundaries: consistency (unprovability of contradictions), completeness (provability of all semantic truths), and decidability (algorithmic determination of provability). Gödel's incompleteness theorems establish that sufficiently expressive systems cannot simultaneously achieve consistency, completeness, and effective axiomatization. Testing these boundary conditions requires constructing minimal models, searching for contradictions, and analyzing the limits of provability.

Implement a consistency checker for propositional sequent calculus by attempting to derive the sequent $\vdash$ (empty antecedent, empty succedent), which represents falsehood. If this sequent is derivable, the system is inconsistent:

```python
def search_for_inconsistency(axioms: List[Sequent], max_depth: int = 5) -> Optional[Sequent]:
    """
    Breadth-first search for derivation of empty sequent ⊢ (inconsistency).
    Returns the inconsistency if found within max_depth steps.
    """
    from collections import deque
    
    target = Sequent([], [])  # The absurdity
    queue = deque([(ax, 0) for ax in axioms])
    visited = set()
    
    while queue:
        current, depth = queue.popleft()
        
        if depth > max_depth:
            continue
        
        # Convert to hashable form for visited check
        current_key = (tuple(current.antecedents), tuple(current.succedents))
        if current_key in visited:
            continue
        visited.add(current_key)
        
        # Check if we derived absurdity
        if not current.antecedents and not current.succedents:
            return current
        
        # Apply weakening and contraction (structural rules)
        # In practice, would apply all logical rules here
        # For demonstration, just check if axioms lead to empty sequent
        if not current.succedents and current.antecedents:
            # If we have only antecedents with no succedents, potential inconsistency
            # Try deriving contradiction from antecedents
            pass
    
    return None  # No inconsistency found

# Test with consistent axiom set
p, q = symbols('p q')
consistent_axioms = [
    Sequent([p], [p]),
    Sequent([q], [q])
]
result = search_for_inconsistency(consistent_axioms)
print(f"Inconsistency in consistent system: {result}")

# Test with explicitly inconsistent axiom set
inconsistent_axioms = [
    Sequent([p], []),  # p assumed but nothing provable
    Sequent([], [Not(p)])  # ¬p provable from nothing
]
# In classical logic, these together should derive absurdity
print(f"Checking inconsistent axioms: {inconsistent_axioms}")
```

Complete consistency checking requires implementing all sequent calculus rules and performing exhaustive proof search, which is decidable for propositional logic but computationally expensive (PSPACE-complete). For first-order logic, consistency becomes undecidable by the Church-Turing theorem, though automated theorem provers can detect many inconsistencies through saturation-based proof search.

Verify completeness for propositional logic by implementing a semantic evaluation function and checking that all tautologies are provable. The completeness theorem for classical propositional logic states that if $\vDash A$ (semantic validity), then $\vdash A$ (syntactic provability):

```python
from sympy.logic.boolalg import to_cnf, satisfiable
from sympy import simplify_logic

def is_tautology(formula) -> bool:
    """Check if formula is semantically valid (tautology)."""
    # Formula is tautology iff its negation is unsatisfiable
    negation = Not(formula)
    result = satisfiable(negation)
    return result is False

def attempt_proof(formula, max_steps: int = 10) -> bool:
    """
    Attempt to construct sequent calculus proof for ⊢ formula.
    Returns True if proof found within max_steps.
    """
    # Start with goal sequent ⊢ formula
    goal = Sequent([], [formula])
    
    # Check if already an axiom (trivially true)
    if goal.is_axiom():
        return True
    
    # For propositional tautologies, can use resolution method
    # Convert to CNF and check if all clauses are satisfied
    cnf = to_cnf(formula, simplify=True)
    
    # If CNF simplifies to True, formula is tautology
    if cnf == True:
        return True
    
    return False  # Proof search would continue here

# Test completeness: all tautologies should be provable
p, q = symbols('p q')
test_formulas = [
    Or(p, Not(p)),  # Law of excluded middle
    Implies(p, p),  # Identity
    Implies(And(p, Implies(p, q)), q),  # Modus ponens
    Or(Implies(p, q), Implies(q, p))  # Weak linearity (tautology)
]

print("\nCompleteness Testing:")
for formula in test_formulas:
    is_valid = is_tautology(formula)
    is_provable = attempt_proof(formula)
    status = "✓" if is_valid == is_provable else "✗"
    print(f"{status} {formula}: valid={is_valid}, provable={is_provable}")
```

Execute this to verify that semantic validity aligns with syntactic provability for the test cases. A complete implementation would use resolution theorem proving or tableau methods to construct actual proofs, but the SymPy satisfiability checker provides a semantic oracle for validation.

### Edge Cases in Rule Application

Proof systems contain corner cases where rule application becomes degenerate or where naive implementation choices lead to non-termination. Testing these boundaries exposes implementation bugs and clarifies the formal semantics of inference rules. Consider the weakening rule, which allows adding arbitrary formulas to antecedent or succedent: $\Gamma \vdash \Delta$ implies $\Gamma, A \vdash \Delta$ and $\Gamma \vdash A, \Delta$. Without restrictions, weakening enables infinite proof trees where formulas are added gratuitously.

Implement a proof search algorithm with cycle detection to prevent infinite weakening loops:

```python
def proof_search_with_cycle_detection(goal: Sequent, max_depth: int = 10) -> Optional[List[Sequent]]:
    """
    Backward proof search with visited state tracking.
    Returns proof trace if found, None otherwise.
    """
    from collections import deque
    
    visited = set()
    queue = deque([(goal, [goal], 0)])
    
    while queue:
        current, trace, depth = queue.popleft()
        
        if depth > max_depth:
            continue
        
        # Check if current sequent is axiom
        if current.is_axiom():
            return trace
        
        # Create hashable key for cycle detection
        key = (tuple(sorted(str(f) for f in current.antecedents)),
               tuple(sorted(str(f) for f in current.succedents)))
        
        if key in visited:
            continue  # Cycle detected
        visited.add(key)
        
        # Try applying rules (simplified: only try decomposition)
        # Right-And rule
        for formula in current.succedents:
            if isinstance(formula, And):
                try:
                    p1, p2 = apply_right_and(current, formula)
                    queue.append((p1, trace + [p1], depth + 1))
                    queue.append((p2, trace + [p2], depth + 1))
                except:
                    pass
        
        # Left-Implies rule
        for formula in current.antecedents:
            if isinstance(formula, Implies):
                try:
                    pr1, pr2 = apply_left_implies(current, formula)
                    queue.append((pr1, trace + [pr1], depth + 1))
                    queue.append((pr2, trace + [pr2], depth + 1))
                except:
                    pass
    
    return None  # No proof found

# Test with provable sequent
p, q, r = symbols('p q r')
test_goal = Sequent([p, Implies(p, q)], [q])
proof_trace = proof_search_with_cycle_detection(test_goal)
print("\nProof Search Result:")
if proof_trace:
    print("Proof found:")
    for step in proof_trace:
        print(f"  {step}")
else:
    print("No proof found (may be unprovable or requires deeper search)")

# Test with unprovable sequent
unprovable = Sequent([p], [q])
proof_trace2 = proof_search_with_cycle_detection(unprovable)
print(f"\nUnprovable sequent {unprovable}: {proof_trace2}")
```

The cycle detection mechanism prevents exploring identical proof states multiple times, enforcing termination for propositional logic. Without this, the search could enter infinite loops applying weakening or other structural rules that increase formula multisets without progressing toward axioms.

Test structural rule interactions by verifying the admissibility of contraction (replacing $A, A$ with $A$) in systems with and without explicit contraction rules:

```python
def verify_contraction_admissibility(seq_with_dup: Sequent, seq_contracted: Sequent) -> bool:
    """
    Verify that if seq_with_dup is provable, so is seq_contracted.
    Contraction: Γ, A, A ⊢ Δ implies Γ, A ⊢ Δ.
    """
    # Simulate proof search for both
    proof_dup = proof_search_with_cycle_detection(seq_with_dup, max_depth=5)
    proof_con = proof_search_with_cycle_detection(seq_contracted, max_depth=5)
    
    # Both should succeed or fail together for contraction to be admissible
    return (proof_dup is not None) == (proof_con is not None)

# Test contraction on antecedent
p = symbols('p')
seq_dup = Sequent([p, p], [p])
seq_con = Sequent([p], [p])
result = verify_contraction_admissibility(seq_dup, seq_con)
print(f"\nContraction admissibility test:")
print(f"  {seq_dup} vs {seq_con}: {result}")
```

In classical sequent calculus LK, contraction is a primitive rule, but in linear logic it is absent, making resource tracking explicit. Testing admissibility across different logical frameworks reveals the fine-grained distinctions between structural properties and their computational implications.

### Herbrand's Theorem and Skolemization

For first-order logic, proof-theoretic verification extends to quantifier handling through Herbrand's theorem: a first-order formula is valid if and only if some finite disjunction of its ground instances is propositionally valid. Skolemization eliminates existential quantifiers by introducing function symbols, transforming formulas into a form amenable to resolution theorem proving. Implement Skolemization and verify Herbrand expansion:

```python
from sympy import Function, Predicate
from sympy.logic.boolalg import And, Or, Implies
from sympy import symbols

def skolemize(formula):
    """
    Eliminate existential quantifiers by introducing Skolem functions.
    Simplified version handling prenex normal form ∀x∃y P(x,y).
    """
    # For ∃y P(y), replace y with Skolem constant c
    # For ∀x ∃y P(x,y), replace y with Skolem function f(x)
    
    # This is a stub; full implementation requires formula traversal
    # and context tracking for universal variables
    print(f"Skolemizing: {formula}")
    
    # Example transformation
    x, y = symbols('x y')
    if hasattr(formula, 'bound_symbols'):
        # Replace existential vars with Skolem terms
        skolem_func = Function('sk_f')
        # Return transformed formula with Skolem function
        return formula  # Placeholder
    
    return formula

# Example: ∀x ∃y (P(x) → Q(x, y))
x, y, z = symbols('x y z')
P = Predicate('P')
Q = Predicate('Q')

# In practice, would build formula using SymPy's quantifier support
# and apply Skolemization transformation
print("\nSkolemization example (conceptual):")
print("Original: ∀x ∃y (P(x) → Q(x, y))")
print("Skolemized: ∀x (P(x) → Q(x, f(x)))  where f is Skolem function")
```

Full implementation of Skolemization requires traversing formula syntax trees, tracking quantifier scopes, and substituting function terms. The Z3 SMT solver handles this automatically through its internal preprocessing pipeline. Verify Skolem normal form preservation by checking equisatisfiability (not equivalence, since Skolemization introduces new symbols):

```python
from sympy.logic.boolalg import to_cnf

def verify_skolem_equisatisfiability(original, skolemized):
    """
    Check that original and skolemized formulas are equisatisfiable.
    Original is valid iff skolemized is valid (in the expanded signature).
    """
    # Both should have same satisfiability status
    sat_orig = satisfiable(original)
    sat_skol = satisfiable(skolemized)
    
    # If original is unsatisfiable, skolemized should be too
    if sat_orig is False:
        return sat_skol is False
    # If original is satisfiable, skolemized should be (with possibly different model)
    return sat_skol is not False

# Test with propositional approximation
p, q = symbols('p q')
original = And(p, Implies(p, q))
skolemized = original  # No quantifiers, so identical
result = verify_skolem_equisatisfiability(original, skolemized)
print(f"\nEquisatisfiability check: {result}")
```

Herbrand's theorem enables first-order theorem proving through grounding: enumerate finite sets of ground instances and check propositional validity. Modern SMT solvers implement sophisticated Herbrand expansion strategies combined with congruence closure and theory reasoning, achieving decidability for specific first-order theories (e.g., linear arithmetic, uninterpreted functions).

## Exercise 3: Algorithmic Implementation of Formal Structures

### Resolution Theorem Proving

Resolution is a complete refutation procedure for first-order logic operating on clauses in conjunctive normal form. The resolution rule states that from clauses $C \lor A$ and $D \lor \neg A$, one may derive $C \lor D$ (the resolvent), eliminating complementary literals. Implement a propositional resolution prover that detects unsatisfiability by deriving the empty clause:

```python
from sympy.logic.boolalg import to_cnf, Or, And, Not
from sympy import symbols
from typing import Set, FrozenSet

def formula_to_clauses(formula) -> Set[FrozenSet]:
    """
    Convert formula to CNF and extract as set of clause sets.
    Each clause is a frozenset of literals.
    """
    cnf = to_cnf(formula, simplify=True)
    
    if cnf == True:
        return set()  # Tautology, no clauses needed
    if cnf == False:
        return {frozenset()}  # Empty clause (contradiction)
    
    clauses = set()
    
    # CNF is conjunction of disjunctions
    if isinstance(cnf, And):
        conjuncts = cnf.args
    else:
        conjuncts = [cnf]
    
    for conj in conjuncts:
        if isinstance(conj, Or):
            clause = frozenset(conj.args)
        else:
            clause = frozenset([conj])
        clauses.add(clause)
    
    return clauses

def resolve(clause1: FrozenSet, clause2: FrozenSet):
    """
    Apply resolution rule: find complementary literals and generate resolvent.
    Returns list of resolvents (may be multiple if multiple literals match).
    """
    resolvents = []
    
    for lit1 in clause1:
        # Check if negation of lit1 is in clause2
        if isinstance(lit1, Not):
            complement = lit1.args[0]
        else:
            complement = Not(lit1)
        
        if complement in clause2:
            # Found complementary pair, create resolvent
            resolvent = (clause1 - {lit1}) | (clause2 - {complement})
            resolvents.append(frozenset(resolvent))
    
    return resolvents

def resolution_refutation(clauses: Set[FrozenSet], max_iterations: int = 100) -> bool:
    """
    Resolution-based theorem proving: derive empty clause to prove unsatisfiability.
    Returns True if formula is unsatisfiable (empty clause derived).
    """
    clauses = set(clauses)  # Make mutable copy
    
    for iteration in range(max_iterations):
        new_clauses = set()
        
        # Try all pairs of clauses
        clause_list = list(clauses)
        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                resolvents = resolve(clause_list[i], clause_list[j])
                for resolvent in resolvents:
                    # Check if empty clause derived
                    if len(resolvent) == 0:
                        print(f"Empty clause derived at iteration {iteration}")
                        return True
                    new_clauses.add(resolvent)
        
        # Check if any new clauses were generated
        if new_clauses.issubset(clauses):
            # No new clauses, saturation reached
            print(f"Saturated at iteration {iteration}, formula satisfiable")
            return False
        
        clauses.update(new_clauses)
    
    print(f"Max iterations reached, inconclusive")
    return False

# Test resolution prover
p, q, r = symbols('p q r')

# Test 1: Prove unsatisfiability of p ∧ ¬p
formula1 = And(p, Not(p))
clauses1 = formula_to_clauses(formula1)
print("Test 1: p ∧ ¬p")
print(f"Clauses: {clauses1}")
result1 = resolution_refutation(clauses1)
print(f"Unsatisfiable: {result1}\n")

# Test 2: Prove (p ∨ q) ∧ (¬p ∨ r) ∧ ¬q ∧ ¬r is unsatisfiable
formula2 = And(Or(p, q), Or(Not(p), r), Not(q), Not(r))
clauses2 = formula_to_clauses(formula2)
print("Test 2: (p ∨ q) ∧ (¬p ∨ r) ∧ ¬q ∧ ¬r")
print(f"Clauses: {clauses2}")
result2 = resolution_refutation(clauses2)
print(f"Unsatisfiable: {result2}\n")

# Test 3: Prove satisfiable formula p ∨ q
formula3 = Or(p, q)
clauses3 = formula_to_clauses(formula3)
print("Test 3: p ∨ q")
print(f"Clauses: {clauses3}")
result3 = resolution_refutation(clauses3)
print(f"Unsatisfiable: {result3}\n")
```

Execute this to observe resolution deriving the empty clause for unsatisfiable formulas. The prover saturates the clause set by generating all possible resolvents until either the empty clause appears (unsatisfiability proven) or no new clauses can be generated (satisfiability indicated). For first-order logic, resolution operates on clauses with variables, requiring unification to match literals—a more complex operation implemented in provers like Prover9 and E.

### Tableau Method for Classical Logic

The tableau (analytic tableaux) method provides an alternative complete proof procedure based on systematic case analysis. A tableau is a tree where each branch represents a potential model, and the procedure attempts to close all branches by deriving contradictions. Implement a propositional tableau prover:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TableauNode:
    """Node in tableau tree containing set of formulas to satisfy."""
    formulas: List
    is_closed: bool = False
    children: List['TableauNode'] = field(default_factory=list)
    
    def __str__(self, indent=0):
        prefix = "  " * indent
        status = "✗ CLOSED" if self.is_closed else "◯ OPEN"
        result = f"{prefix}{status}: {{{', '.join(str(f) for f in self.formulas)}}}\n"
        for child in self.children:
            result += child.__str__(indent + 1)
        return result

def tableau_expand(node: TableauNode) -> bool:
    """
    Expand tableau node by applying decomposition rules.
    Returns True if node closes (contradiction found).
    """
    # Check for contradiction (formula and its negation present)
    for formula in node.formulas:
        if isinstance(formula, Not):
            if formula.args[0] in node.formulas:
                node.is_closed = True
                return True
        else:
            if Not(formula) in node.formulas:
                node.is_closed = True
                return True
    
    # Find expandable formula (non-atomic)
    for formula in node.formulas:
        if isinstance(formula, And):
            # α-formula (conjunctive): add both conjuncts to single branch
            remaining = [f for f in node.formulas if f != formula]
            child = TableauNode(remaining + list(formula.args))
            node.children.append(child)
            return tableau_expand(child)
        
        elif isinstance(formula, Or):
            # β-formula (disjunctive): create two branches
            remaining = [f for f in node.formulas if f != formula]
            child1 = TableauNode(remaining + [formula.args[0]])
            child2 = TableauNode(remaining + [formula.args[1]])
            node.children = [child1, child2]
            closed1 = tableau_expand(child1)
            closed2 = tableau_expand(child2)
            if closed1 and closed2:
                node.is_closed = True
                return True
            return False
        
        elif isinstance(formula, Implies):
            # Transform A → B to ¬A ∨ B and expand
            remaining = [f for f in node.formulas if f != formula]
            equivalent = Or(Not(formula.args[0]), formula.args[1])
            child = TableauNode(remaining + [equivalent])
            node.children.append(child)
            return tableau_expand(child)
        
        elif isinstance(formula, Not) and isinstance(formula.args[0], And):
            # ¬(A ∧ B) transforms to ¬A ∨ ¬B (De Morgan)
            remaining = [f for f in node.formulas if f != formula]
            equivalent = Or(Not(formula.args[0].args[0]), Not(formula.args[0].args[1]))
            child = TableauNode(remaining + [equivalent])
            node.children.append(child)
            return tableau_expand(child)
        
        elif isinstance(formula, Not) and isinstance(formula.args[0], Or):
            # ¬(A ∨ B) transforms to ¬A ∧ ¬B (De Morgan)
            remaining = [f for f in node.formulas if f != formula]
            equivalent = And(Not(formula.args[0].args[0]), Not(formula.args[0].args[1]))
            child = TableauNode(remaining + [equivalent])
            node.children.append(child)
            return tableau_expand(child)
    
    # No more expansion possible, check if still open
    return node.is_closed

def tableau_prove(formula) -> bool:
    """
    Prove formula by showing ¬formula leads to closed tableau (contradiction).
    Returns True if formula is valid.
    """
    # To prove formula, show ¬formula is unsatisfiable
    root = TableauNode([Not(formula)])
    is_closed = tableau_expand(root)
    
    print("Tableau:")
    print(root)
    
    return is_closed

# Test tableau prover
p, q, r = symbols('p q r')

# Test 1: Prove excluded middle p ∨ ¬p
formula1 = Or(p, Not(p))
print("Test 1: Proving p ∨ ¬p")
result1 = tableau_prove(formula1)
print(f"Valid: {result1}\n")

# Test 2: Prove modus ponens (p ∧ (p → q)) → q
formula2 = Implies(And(p, Implies(p, q)), q)
print("Test 2: Proving (p ∧ (p → q)) → q")
result2 = tableau_prove(formula2)
print(f"Valid: {result2}\n")

# Test 3: Try to prove invalid formula p → q
formula3 = Implies(p, q)
print("Test 3: Attempting to prove p → q (should fail)")
result3 = tableau_prove(formula3)
print(f"Valid: {result3}\n")
```

Execute this to observe the tableau branching structure. The method systematically explores all possible truth assignments, closing branches where contradictions arise. If all branches close, the negated formula is unsatisfiable, proving the original formula valid. Open branches represent countermodels, providing concrete falsifying interpretations.

### Proof Assistant Integration: Lean 4 Verification

Modern proof assistants like Lean provide mechanized environments for formal verification where metatheorems themselves can be proven correct. Install Lean 4 and implement a simple propositional proof to experience the type-theoretic foundation of proof verification. Create a file `ProofTheory.lean`:

```lean
-- ProofTheory.lean
-- Propositional logic proofs in Lean 4

-- Prove excluded middle using classical logic
theorem excluded_middle (p : Prop) : p ∨ ¬p := by
  by_cases h : p
  · left
    exact h
  · right
    exact h

-- Prove modus ponens
theorem modus_ponens (p q : Prop) (h1 : p) (h2 : p → q) : q := by
  exact h2 h1

-- Prove implication transitivity
theorem impl_trans (p q r : Prop) (h1 : p → q) (h2 : q → r) : p → r := by
  intro hp
  apply h2
  apply h1
  exact hp

-- Prove conjunction elimination
theorem and_elim_left (p q : Prop) (h : p ∧ q) : p := by
  exact h.left

theorem and_elim_right (p q : Prop) (h : p ∧ q) : q := by
  exact h.right

-- Prove disjunction introduction
theorem or_intro_left (p q : Prop) (h : p) : p ∨ q := by
  left
  exact h

-- Prove De Morgan's law
theorem de_morgan_and (p q : Prop) : ¬(p ∧ q) ↔ (¬p ∨ ¬q) := by
  constructor
  · intro h
    by_cases hp : p
    · right
      intro hq
      apply h
      exact ⟨hp, hq⟩
    · left
      exact hp
  · intro h hpq
    cases h with
    | inl hnp => exact hnp hpq.left
    | inr hnq => exact hnq hpq.right

#check excluded_middle
#check modus_ponens
#check impl_trans
```

Save this file and compile with `lean ProofTheory.lean` if Lean is installed, or use the Lean web playground at `live.lean-lang.org`. The type signatures encode proof obligations, and the tactic scripts construct proof terms through a combination of introduction, elimination, and case analysis tactics. The `#check` commands verify that the theorem statements have been proven with the correct types.

This Lean formalization demonstrates proof construction at the level of type theory, where propositions are types and proofs are terms inhabiting those types (Curry-Howard correspondence). The `by` keyword initiates tactic mode, allowing imperative proof construction through tactics like `intro` (introduce hypothesis), `exact` (provide proof term), `apply` (backward reasoning), and `cases` (case analysis). Each tactic transforms the proof goal, ultimately reducing it to trivial axioms or previously established theorems.

Extend the Lean file with a simple induction proof on natural numbers to demonstrate proof-theoretic induction:

```lean
-- Induction on natural numbers
theorem nat_add_zero (n : Nat) : n + 0 = n := by
  rfl  -- Reflexivity of equality

theorem nat_add_succ (n m : Nat) : n + (m + 1) = (n + m) + 1 := by
  rfl

-- Prove commutativity of addition by induction
theorem nat_add_comm (n m : Nat) : n + m = m + n := by
  induction m with
  | zero =>
    rw [Nat.add_zero, Nat.zero_add]
  | succ m' ih =>
    rw [Nat.add_succ, ih, Nat.succ_add]
```

This induction proof demonstrates structural recursion over the natural number type, with base case `zero` and inductive step `succ`. The `rw` tactic performs rewriting using equality lemmas, and `ih` refers to the inductive hypothesis. Such mechanized proofs provide absolute certainty that the theorem holds, as the proof assistant's kernel verifies every inference step against the foundational type theory.

## Formal Axioms Cheat Sheet & Verification Reference

### Sequent Calculus Rules (LK Classical)

**Structural Rules:**
- **Weakening Left:** $\Gamma \vdash \Delta \implies \Gamma, A \vdash \Delta$
- **Weakening Right:** $\Gamma \vdash \Delta \implies \Gamma \vdash A, \Delta$
- **Contraction Left:** $\Gamma, A, A \vdash \Delta \implies \Gamma, A \vdash \Delta$
- **Contraction Right:** $\Gamma \vdash A, A, \Delta \implies \Gamma \vdash A, \Delta$
- **Exchange:** Permute formulas in antecedent or succedent

**Logical Rules:**
- **Axiom:** $\Gamma, A \vdash A, \Delta$
- **Cut:** $\dfrac{\Gamma \vdash A, \Delta \quad \Gamma', A \vdash \Delta'}{\Gamma, \Gamma' \vdash \Delta, \Delta'}$
- **$\land$ Right:** $\dfrac{\Gamma \vdash A, \Delta \quad \Gamma \vdash B, \Delta}{\Gamma \vdash A \land B, \Delta}$
- **$\land$ Left:** $\dfrac{\Gamma, A, B \vdash \Delta}{\Gamma, A \land B \vdash \Delta}$
- **$\lor$ Right:** $\dfrac{\Gamma \vdash A, B, \Delta}{\Gamma \vdash A \lor B, \Delta}$
- **$\lor$ Left:** $\dfrac{\Gamma, A \vdash \Delta \quad \Gamma, B \vdash \Delta}{\Gamma, A \lor B \vdash \Delta}$
- **$\to$ Right:** $\dfrac{\Gamma, A \vdash B, \Delta}{\Gamma \vdash A \to B, \Delta}$
- **$\to$ Left:** $\dfrac{\Gamma \vdash A, \Delta \quad \Gamma, B \vdash \Delta}{\Gamma, A \to B \vdash \Delta}$
- **$\neg$ Right:** $\dfrac{\Gamma, A \vdash \Delta}{\Gamma \vdash \neg A, \Delta}$
- **$\neg$ Left:** $\dfrac{\Gamma \vdash A, \Delta}{\Gamma, \neg A \vdash \Delta}$

### Natural Deduction Rules

**Introduction Rules:**
- **$\land$I:** $\dfrac{A \quad B}{A \land B}$
- **$\lor$I₁:** $\dfrac{A}{A \lor B}$, **$\lor$I₂:** $\dfrac{B}{A \lor B}$
- **$\to$I:** $\dfrac{[A] \vdots B}{A \to B}$ (discharges assumption $A$)
- **$\neg$I:** $\dfrac{[A] \vdots \bot}{\neg A}$

**Elimination Rules:**
- **$\land$E₁:** $\dfrac{A \land B}{A}$, **$\land$E₂:** $\dfrac{A \land B}{B}$
- **$\lor$E:** $\dfrac{A \lor B \quad [A] \vdots C \quad [B] \vdots C}{C}$
- **$\to$E:** $\dfrac{A \to B \quad A}{B}$ (modus ponens)
- **$\neg$E:** $\dfrac{\neg A \quad A}{\bot}$
- **$\bot$E:** $\dfrac{\bot}{A}$ (ex falso quodlibet)

### Resolution and CNF Conversion

**CNF Conversion Steps:**
1. Eliminate implications: $A \to B \equiv \neg A \lor B$
2. Push negations inward (De Morgan): $\neg(A \land B) \equiv \neg A \lor \neg B$, $\neg(A \lor B) \equiv \neg A \land \neg B$
3. Distribute disjunctions over conjunctions: $(A \lor B) \land C \equiv (A \land C) \lor (B \land C)$

**Resolution Rule:**
- $\dfrac{C \lor A \quad D \lor \neg A}{C \lor D}$ (eliminate complementary literal $A$)

### Verification Commands

**SymPy Propositional Logic:**
```python
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent
from sympy.logic.inference import satisfiable
from sympy.logic.boolalg import to_cnf, simplify_logic
from sympy import symbols

# Check tautology
formula = Or(p, Not(p))
is_valid = satisfiable(Not(formula)) == False

# Convert to CNF
cnf_form = to_cnf(formula)

# Simplify
simplified = simplify_logic(formula)
```

**Z3 SMT Solver:**
```python
from z3 import Bool, Solver, sat, unsat, Or, And, Not, Implies

p, q = Bool('p'), Bool('q')
solver = Solver()
solver.add(Not(Or(p, Not(p))))  # Add negation of tautology
result = solver.check()  # Should return unsat
print(result)  # unsat means original is valid
```

**Lean 4 Proof Verification:**
```bash
# Check theorem
lean --version
lean ProofTheory.lean
# Should output "no errors" if all proofs verify
```

### Metatheorems

**Cut Elimination (Gentzen's Hauptsatz):**
Every provable sequent in LK has a cut-free proof. Proved by induction on cut rank and proof height with case analysis on cut formula structure.

**Normalization (Prawitz):**
Every natural deduction derivation reduces to normal form where no introduction immediately precedes elimination for the same connective. Corresponds to β-reduction in lambda calculus.

**Soundness and Completeness:**
- **Soundness:** If $\vdash A$ (provable), then $\vDash A$ (valid)
- **Completeness:** If $\vDash A$ (valid), then $\vdash A$ (provable)

For propositional logic, both hold. For first-order logic, completeness holds (Gödel 1930), but decidability fails. For second-order logic, completeness fails (incompleteness theorems).

### Complexity Classes

- **Propositional Satisfiability:** NP-complete
- **Propositional Validity:** coNP-complete
- **First-Order Validity:** Undecidable (reduction from Halting Problem)
- **Quantified Boolean Formulas (QBF):** PSPACE-complete

These complexity boundaries inform the design of practical theorem provers, which employ heuristics, incomplete procedures, and theory-specific decision procedures to handle tractable fragments efficiently while providing best-effort service on undecidable problems.
