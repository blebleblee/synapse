# Foundation: Number Theory

## 1. Conceptual Mental Model (Core intuition, analogies, and first principles)

Number theory operates at the intersection of discrete mathematics and algebraic structures, focusing on the **integers** as the fundamental building blocks of mathematical reality. At its core, number theory reveals how seemingly simple properties of whole numbers generate profound structural patterns and constraints.

**Core intuition**: Integers form a *ring* (a structure with addition, subtraction, and multiplication) where the concept of *primality* acts as the irreducible "atoms" of the system. Just as atoms combine to form molecules, primes combine via multiplication to generate all composite numbers. This discrete, countable nature creates a system where patterns emerge from strict rules rather than continuous variables.

**First principles**:
- **Discreteness**: Integers are discrete and countable (unlike real numbers)
- **Closure**: The set of integers is closed under addition and multiplication
- **Divisibility**: A relation `a | b` (read "a divides b") exists when `b = k·a` for some integer `k`
- **Fundamental constraint**: Every integer > 1 has a unique prime factorization (up to order)

**Key analogy**: Think of prime numbers as the "atomic particles" of the integer system. While atoms combine to form matter, primes combine via multiplication to generate all integers. This analogy highlights why number theory is the *foundation* of mathematics—its rules govern how complex structures emerge from simple building blocks.

**Why this matters**: Number theory provides the rigorous framework for cryptography (e.g., RSA), algorithm design, and understanding the distribution of primes. Its power lies in revealing how deep mathematical structures arise from simple, discrete rules.

---

## 2. Essential Terminology & Taxonomy

Here are 6 foundational terms critical to understanding number theory:

1. **Prime Number**: A natural number `p > 1` such that `p | a` implies `a = 1` or `a = p` (has no divisors other than 1 and itself).  
   *Example*: `2`, `3`, `5`, `7` (note: `1` is *not* prime)

2. **Composite Number**: A natural number `n > 1` that is *not* prime (i.e., has at least one divisor other than 1 and itself).  
   *Example*: `4 = 2·2`, `6 = 2·3`

3. **Divisibility Relation**: For integers `a`, `b` (`b ≠ 0`), `a | b` iff there exists integer `k` such that `b = k·a`.  
   *Notation*: `a | b` (read: "a divides b")

4. **Greatest Common Divisor (GCD)**: The largest positive integer `d` such that `d | a` and `d | b`. Denoted `gcd(a, b)`.  
   *Example*: `gcd(12, 18) = 6`

5. **Fundamental Theorem of Arithmetic (FTA)**: Every integer `n > 1` has a *unique* factorization into primes: `n = p₁^e₁ · p₂^e₂ · ... · pₖ^eₖ` (up to order of primes).

6. **Euclidean Algorithm**: A method for computing `gcd(a, b)` via repeated division:  
   `a = q₁·b + r₁` → `b = q₂·r₁ + r₂` → ... → `rₙ₋₁ = qₙ·rₙ + 0`  
   `gcd(a, b) = rₙ`

---

## 3. Architecture & Core Workflow

```mermaid
graph LR
    A[Integer System ℤ] --> B[Prime Numbers ℙ]
    A --> C[Divisibility Relation]
    C --> D[GCD]
    C --> E[LCM]
    D --> F[Euclidean Algorithm]
    E --> G[LCM Formula: lcm(a,b) = |a·b|/gcd(a,b)]
    B --> H[Fundamental Theorem of Arithmetic]
    H --> I[Unique Prime Factorization]
    F --> D
    G --> E
```

**Workflow Explanation**:
1. **Start** with the integer system `ℤ`
2. **Identify primes** (`ℙ`) as irreducible elements
3. **Apply divisibility** to define relationships between integers
4. **Compute GCD** using the Euclidean Algorithm (reducing problem size iteratively)
5. **Derive LCM** from GCD via the formula `lcm(a,b) = |a·b|/gcd(a,b)`
6. **Verify uniqueness** via FTA (every `n > 1` has *one* prime factorization)

This architecture shows how number theory transforms simple integer relationships into a self-consistent system with deep structural properties.

---

## 4. Common Misconceptions & Mental Traps

| Misconception | Why It's Traps | Correct Insight |
|---------------|----------------|-----------------|
| "All even numbers are composite" | Ignores `2` (the only even prime) | Primes are *not* restricted to odd numbers |
| "Euclidean algorithm always terminates in one step" | Overlooks iterative reduction | Requires `O(log min(a,b))` steps (e.g., `gcd(100, 27)` takes 4 steps) |
| "The fundamental theorem applies to all integers including 0" | 0 has no prime factorization | FTA applies *only* to `n > 1`; `0` is undefined in factorization |
| "Primes are randomly distributed" | Misinterprets density | Primes follow predictable patterns (e.g., twin primes, prime gaps) |
| "GCD is always smaller than the inputs" | Confuses magnitude | `gcd(a,b) ≤ min(|a|, |b|)` but can equal either input |

**Critical mental trap**: Assuming number theory operates in a *continuous* space. Integers are discrete—this discreteness creates unique constraints (e.g., no two distinct primes differ by 1 except `2` and `3`).

---

## 5. Socratic Discussion Starters

1. **Why does the Euclidean algorithm *guarantee* termination?**  
   *Hint*: Consider the invariant property of the remainder sequence and how it bounds the problem size. How does this differ from infinite descent in other contexts?*

2. **If the fundamental theorem of arithmetic held for *all* integers (including negatives), how would factorization change?**  
   *Hint*: Recall that `-1` is a unit in `ℤ`. How does this affect the uniqueness of factorization?*

3. **Can we define a "prime" in a system with *more* than one dimension (e.g., Gaussian integers)?**  
   *Hint*: Compare the ring `ℤ[i]` (Gaussian integers) to `ℤ`. What makes primes in `ℤ[i]` different from `ℤ`?*

These questions target the *structural* foundations of number theory—moving beyond computation to explore why the integer system is uniquely suited for generating mathematical depth through discrete constraints.
