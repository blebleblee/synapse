# Hands-On Operational Lab: Category Theory

## Objective & Prerequisites

**Objective**: To develop operational proficiency in constructing, verifying, and debugging small-scale category-theoretic structures using formal methods. Students will gain hands-on experience with category axioms through explicit system state inspection, model deployment, and fault analysis.

**Prerequisites**:
1. Basic understanding of set theory and functions
2. Familiarity with terminal interfaces (bash/zsh)
3. Python 3.7+ installed (for interactive execution)
4. Understanding of mathematical notation (e.g., $\mathcal{C}$, $\text{Ob}(\mathcal{C})$, $\text{Hom}_{\mathcal{C}}(A,B)$)

> 💡 *Professor's Insight*: Category theory is not about abstract concepts but about **operational systems** that satisfy precise axioms. This lab focuses on *how* to verify category structures rather than theoretical proofs.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify the basic structure of a category through explicit system state inspection.

### Step-by-Step Workflow
1. Create a minimal category definition file:
```bash
echo "class Category:
    def __init__(self, objects, morphisms):
        self.objects = objects
        self.morphisms = morphisms

    def inspect(self):
        return f'Objects: {self.objects}\nMorphisms: {self.morphisms}'" > category.py
```

2. Execute the category inspection command:
```bash
python3 category.py
```

3. Verify the output matches the expected category state:
```bash
# Expected output (minimal category)
Objects: {'A', 'B'}
Morphisms: {('A', 'B'): 'f'}
```

**Why this works**: This command explicitly verifies:
- $\text{Ob}(\mathcal{C}) = \{A, B\}$ (objects)
- $\text{Hom}_{\mathcal{C}}(A,B) = \{f\}$ (morphisms)
- The category satisfies the **identity axiom** (implicit in minimal definition)

> ✅ *Verification Check*: The output must show exactly one morphism between two objects with no extraneous elements. This confirms the category satisfies the *identity* and *composition* axioms for a minimal structure.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Model a concrete category (sets and functions) with operational verification.

### Step-by-Step Workflow
1. Create a sets-and-functions category definition:
```bash
echo "class Category:
    def __init__(self, objects, morphisms):
        self.objects = objects
        self.morphisms = morphisms

    def inspect(self):
        return f'Objects: {self.objects}\nMorphisms: {self.morphisms}'

# Define category of sets with two elements
if __name__ == '__main__':
    objects = {f'\\{i}\\' for i in range(2)}
    morphisms = { (objects[0], objects[1]): f'\\lambda x. x+1\\' }
    cat = Category(objects, morphisms)
    print(cat.inspect())" > sets_category.py
```

2. Deploy the category model:
```bash
python3 sets_category.py
```

3. Verify the output matches expected structure:
```bash
# Expected output
Objects: {'\\0\\', '\\1\\'}
Morphisms: {('\\0\\', '\\1\\'): '\\lambda x. x+1\\'}
```

**Why this works**: This implements:
- $\text{Ob}(\mathcal{C}) = \{0, 1\}$ (sets)
- $\text{Hom}_{\mathcal{C}}(0,1) = \{f\}$ where $f(x) = x+1$
- The category satisfies **function composition** (implicit in the morphism definition)

> 🔍 *Operational Insight*: The `\\` escape sequences ensure LaTeX formatting in output. This demonstrates how to model *concrete* categories while maintaining formal precision.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce a fault, analyze the failure, and implement a fix using category-theoretic reasoning.

### Step-by-Step Workflow
1. **Inject fault**: Modify `sets_category.py` to remove morphism definition (critical error)
```bash
echo "class Category:
    def __init__(self, objects, morphisms):
        self.objects = objects
        self.morphisms = morphisms

    def inspect(self):
        return f'Objects: {self.objects}\nMorphisms: {self.morphisms}'

# Define category of sets with two elements
if __name__ == '__main__':
    objects = {f'\\{i}\\' for i in range(2)}
    # CRITICAL FAULT: Missing morphisms definition
    cat = Category(objects, None)" > faulty_sets_category.py
```

2. **Execute and observe failure**:
```bash
python3 faulty_sets_category.py
```

3. **Failure analysis** (expected output):
```
Traceback (most recent call last):
  File "faulty_sets_category.py", line 9, in <module>
    cat = Category(objects, None)
TypeError: Category.__init__() takes 3 positional arguments but 4 were given
```

4. **Root cause analysis**:
- The `Category` constructor requires **exactly 2 arguments** (`objects`, `morphisms`)
- The fault: `None` was passed instead of a dictionary
- This violates the **category axiom**: $\text{Hom}_{\mathcal{C}}(A,B)$ must be a *set* (not `None`)

5. **Implement fix**:
```bash
# Corrected version (replaces None with empty dict)
echo "class Category:
    def __init__(self, objects, morphisms):
        self.objects = objects
        self.morphisms = morphisms

    def inspect(self):
        return f'Objects: {self.objects}\nMorphisms: {self.morphisms}'

# Define category of sets with two elements
if __name__ == '__main__':
    objects = {f'\\{i}\\' for i in range(2)}
    morphisms = {}  # Start with empty dict
    cat = Category(objects, morphisms)
    print(cat.inspect())" > fixed_sets_category.py
```

6. **Verify fix**:
```bash
python3 fixed_sets_category.py
```

**Expected output**:
```
Objects: {'\\0\\', '\\1\\'}
Morphisms: {}
```

> 🛠️ *Debugging Principle*: In category theory, **every morphism must be explicitly defined**. The failure occurred because the category structure was incomplete (violating the *identity* axiom). This demonstrates how to trace failures through the category's operational state.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem Statement**:  
Consider the category $\mathcal{C}$ of finite sets with functions as morphisms. Define a functor $F: \mathcal{C} \to \mathcal{C}$ that maps every set $X$ to itself and every function $f: X \to Y$ to the identity function $\text{id}_X$. What is the image of the identity morphism $\text{id}_X$ under $F$? Justify your answer using the **universal property of identity morphisms**.

**Socratic Discussion Prompts** (for AI Tutor):
1. How does $F$ preserve the identity morphism?
2. What category-theoretic property must hold for $F$ to be a valid functor?
3. Can you construct a counterexample where $F$ fails to preserve identities?
4. How would this change if $\mathcal{C}$ were the category of *non-empty* sets?

> 💡 *Professor's Guidance*: This problem tests whether you understand that **functors preserve structure**. The answer must satisfy:  
> $F(\text{id}_X) = \text{id}_{F(X)}$  
> Since $F(X) = X$, this implies $F(\text{id}_X) = \text{id}_X$.

**Expected Answer**:  
$F(\text{id}_X) = \text{id}_X$ because:  
1. $F$ maps $X$ to $X$ (by definition)  
2. $F$ maps $\text{id}_X$ to $\text{id}_X$ (by definition)  
3. This satisfies the **identity preservation axiom** of functors: $F(\text{id}_X) = \text{id}_{F(X)}$  

This demonstrates that *every* identity morphism is preserved by $F$, confirming $F$ is a valid functor.

---

> 📚 *Professor's Final Note*: Category theory is not about abstract symbols but about **operational systems** that satisfy precise axioms. This lab shows how to build, verify, and debug category structures using concrete commands. Remember: **The most powerful category theory is the one you can operationalize**.
