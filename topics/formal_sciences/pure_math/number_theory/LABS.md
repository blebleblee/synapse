# Hands-On Operational Lab: Number Theory

## Objective & Prerequisites

**Objective**: To develop hands-on proficiency in number theory concepts through computational verification, modeling, and fault analysis. This lab emphasizes the *operational* relationship between formal mathematical structures and their computational implementations—critical for understanding the foundations of cryptography, algorithm design, and pure mathematical reasoning.

**Prerequisites**:
- Basic familiarity with Python programming (or willingness to learn minimal syntax)
- Understanding of core number theory concepts: integers, primes, divisibility, greatest common divisors (GCD)
- A shell environment (Linux/macOS terminal or Windows PowerShell) with Python 3.7+ installed
- Basic knowledge of the Euclidean algorithm and prime factorization

> 💡 *Why this matters*: Number theory is the bedrock of modern cryptography (e.g., RSA). This lab bridges abstract mathematical concepts with executable verification—essential for formal scientists who must both *prove* theorems and *implement* them.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify the fundamental theorem of arithmetic through computational factorization.

**Step 1: Create a prime factorization script**  
Save this script as `factor.py`:

```python
def prime_factors(n):
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

if __name__ == "__main__":
    num = 360
    print(f"Prime factors of {num}: {prime_factors(num)}")
```

**Step 2: Run the script and inspect output**  
In your terminal:
```bash
python3 factor.py
```

**Expected Output**:
```
Prime factors of 360: [2, 2, 2, 3, 3, 5]
```

**Why this works**:  
The algorithm iteratively divides by primes (starting from 2). The inner loop ensures all factors of `d` are extracted before moving to the next candidate. This matches the fundamental theorem of arithmetic: **every integer > 1 has a unique prime factorization**. The output confirms `360 = 2³ × 3² × 5¹`.

> 🔍 *System State Check*: Verify your environment by running:
> ```bash
> python3 --version
> ```
> *Expected output*: `Python 3.x.x`

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Implement the Euclidean algorithm for GCD and validate its correctness.

**Step 1: Create a GCD script**  
Save this script as `gcd.py`:

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

if __name__ == "__main__":
    a = 48
    b = 18
    print(f"GCD of {a} and {b} is {gcd(a, b)}")
```

**Step 2: Deploy and run the script**  
In your terminal:
```bash
python3 gcd.py
```

**Expected Output**:
```
GCD of 48 and 18 is 6
```

**Why this works**:  
The Euclidean algorithm repeatedly replaces `(a, b)` with `(b, a % b)` until `b = 0`. The last non-zero remainder is the GCD. For `48` and `18`:
1. `48 % 18 = 12` → `(18, 12)`
2. `18 % 12 = 6` → `(12, 6)`
3. `12 % 6 = 0` → GCD = `6`

This is a *formal* proof of correctness: The algorithm terminates in `O(log min(a,b))` steps and satisfies the invariant `gcd(a, b) = gcd(b, a % b)`.

> 🛠️ *Operational Workflow*:  
> `Create script → Validate syntax → Run → Verify output → Analyze steps`  
> *This is the standard workflow for formal science labs*.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce a bug in the GCD implementation and debug it using formal reasoning.

**Step 1: Create a faulty GCD script**  
Save this script as `faulty_gcd.py`:

```python
def gcd(a, b):
    while b != 0:
        a, b = b, a // b  # BUG: Uses integer division instead of modulus
    return a

if __name__ == "__main__":
    a = 48
    b = 18
    print(f"GCD of {a} and {b} is {gcd(a, b)}")
```

**Step 2: Inject the fault and run**  
In your terminal:
```bash
python3 faulty_gcd.py
```

**Expected Output (with bug)**:
```
GCD of 48 and 18 is 9
```

**Why the bug fails**:  
The algorithm uses `a // b` (integer division) instead of `a % b` (remainder). For `48` and `18`:
1. `48 // 18 = 2` → `(18, 2)`
2. `18 // 2 = 9` → `(2, 9)`
3. `2 // 9 = 0` → GCD = `9` (incorrect)

**Step 3: Debug the fault**  
1. **Identify the invariant**: The correct algorithm must satisfy `gcd(a, b) = gcd(b, a % b)`.  
2. **Trace the error**: The bug breaks the invariant because `a % b` is not preserved.  
3. **Fix the script**: Replace `a // b` with `a % b` (as in `gcd.py`).  
4. **Re-run**: `python3 gcd.py` → Output: `6` (correct).

**Key Insight**:  
> *Formal debugging requires understanding the mathematical invariant, not just syntax*. The bug was a **semantic error** (wrong operation) that violated the algorithm's foundational property.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Prove that for any positive integers \(a\) and \(b\), the GCD \(\gcd(a, b)\) can be expressed as a linear combination of \(a\) and \(b\). That is, show there exist integers \(x\) and \(y\) such that:  
\[
\gcd(a, b) = x \cdot a + y \cdot b
\]

**Socratic Discussion Prompts** (for your AI Tutor):  
1. How would you use the Euclidean algorithm to derive \(x\) and \(y\)?  
2. What is the role of *backward substitution* in this proof?  
3. Why is this result critical for cryptographic systems (e.g., RSA)?  
4. Can you find a counterexample where this fails? (Hint: Consider \(a = 0\) or \(b = 0\))

**Why this is challenging**:  
This problem requires connecting the *computational process* (Euclidean algorithm) with *formal proof* (linear combinations). The solution involves working backward through the algorithm steps to express the GCD as a combination of the original inputs.

> 💡 *Your next step*: Run `python3 gcd.py` and trace the steps for `a=48, b=18` to see how the GCD emerges as a linear combination. Then ask your AI Tutor: *"How would you extend this to prove the extended Euclidean algorithm?"*

---

> ✅ **Lab Completion Checklist**  
> - [ ] Ran `factor.py` to verify prime factorization  
> - [ ] Executed `gcd.py` to confirm GCD correctness  
> - [ ] Debugged `faulty_gcd.py` using formal reasoning  
> - [ ] Prepared for Socratic discussion on linear combinations  

This lab demonstrates how formal mathematics becomes *operational* through precise computational implementation—exactly the skillset required for formal scientists in the 21st century.
