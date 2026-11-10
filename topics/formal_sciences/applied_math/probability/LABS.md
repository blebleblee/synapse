# Hands-On Operational Lab: Probability  
*Formal Sciences | Applied Mathematics*  

---

## Objective & Prerequisites  
**Objective**: Develop rigorous operational skills in probability modeling, validation, and fault analysis through structured simulations. Students will translate theoretical concepts into executable workflows while maintaining mathematical precision.  

**Prerequisites**:  
1. Basic understanding of set theory and probability axioms (e.g., $P(A \cup B) = P(A) + P(B) - P(A \cap B)$)  
2. Proficiency in Python (version ≥ 3.8) and the `random` module  
3. Familiarity with discrete probability spaces (e.g., sample spaces, events)  
4. *Mathematical intuition*: Ability to visualize probability distributions and validate results against theoretical expectations  

> 💡 **Key Insight**: Probability is not about "guessing" outcomes—it’s about *systematically quantifying uncertainty* through well-defined sample spaces and axiomatic constraints.

---

## Exercise 1: Exploration & System State Inspection  
*Verify foundational concepts through explicit simulation outputs.*  

**Goal**: Confirm that coin flip simulations align with theoretical probability ($P(\text{Heads}) = 0.5$) using empirical data.  

### Step-by-Step Workflow  
1. **Initialize environment** (run in terminal):  
   ```bash
   python3 -c "import random; print(f'Random seed: {random.getstate()}')"
   ```  
   *Expected Output*: `Random seed: (123456, 78901234567890)` (a unique seed for reproducibility)  

2. **Simulate 10,000 coin flips** (save results to `coin_flips.txt`):  
   ```bash
   python3 -c "import random; flips = [random.choice(['H', 'T']) for _ in range(10000)]; with open('coin_flips.txt', 'w') as f: f.write(''.join(flips))"
   ```  

3. **Analyze empirical distribution** (run in terminal):  
   ```bash
   cat coin_flips.txt | wc -l  # Total flips (should be 10,000)
   python3 -c "with open('coin_flips.txt') as f: heads = f.read().count('H'); print(f'Heads: {heads}, Tails: {10000-heads}, P(Heads) ≈ {heads/10000:.4f}')"
   ```  
   *Expected Output*:  
   ```
   Heads: 4987, Tails: 5013, P(Heads) ≈ 0.4987
   ```  

4. **Theoretical validation** (critical step):  
   ```python
   # In your Python environment
   from sympy import Rational
   P_theoretical = Rational(1, 2)  # Exact probability
   P_empirical = 4987 / 10000     # From Exercise 1 output
   print(f"Empirical vs. Theoretical: {P_empirical} vs. {P_theoretical} (Difference: {abs(P_empirical - P_theoretical):.6f})")
   ```  
   *Expected Output*:  
   ```
   Empirical vs. Theoretical: 0.4987 vs. 1/2 (Difference: 0.0012)
   ```  

> ✅ **Verification**: The empirical probability converges to $0.5$ within the expected margin of error for $n=10,000$ (per the *Central Limit Theorem*). This confirms the simulation adheres to the axioms of probability.

---

## Exercise 2: Building & Deploying / Modeling Scenario  
*Model a dice-rolling experiment with rigorous probability calculation.*  

**Goal**: Compute the exact probability of rolling a sum of 7 with two fair dice using combinatorial analysis, then validate via simulation.  

### Step-by-Step Workflow  
1. **Define sample space** (theoretical):  
   - Total outcomes: $6 \times 6 = 36$  
   - Favorable outcomes for sum=7: $(1,6), (2,5), (3,4), (4,3), (5,2), (6,1)$ → $6$ outcomes  
   - Theoretical probability: $P(7) = \frac{6}{36} = \frac{1}{6}$  

2. **Build Python model** (save as `dice_probability.py`):  
   ```python
   import random
   from collections import Counter

   def simulate_dice_trials(trials=10000):
       counts = Counter()
       for _ in range(trials):
           roll1 = random.randint(1, 6)
           roll2 = random.randint(1, 6)
           total = roll1 + roll2
           counts[total] += 1
       return counts

   if __name__ == "__main__":
       counts = simulate_dice_trials()
       p_7_empirical = counts[7] / 10000
       print(f"Empirical P(sum=7) = {p_7_empirical:.4f}")
       print(f"Theoretical P(sum=7) = 1/6 ≈ {1/6:.4f}")
   ```  

3. **Execute and validate** (run in terminal):  
   ```bash
   python3 dice_probability.py
   ```  
   *Expected Output*:  
   ```
   Empirical P(sum=7) = 0.1668
   Theoretical P(sum=7) = 1/6 ≈ 0.1667
   ```  

4. **Mathematical justification** (critical step):  
   - **Why is $P(7) = \frac{1}{6}$?**  
     The sample space $\Omega = \{(i,j) \mid i,j \in \{1,2,3,4,5,6\}\}$ has $|\Omega| = 36$.  
     Event $A = \{(i,j) \mid i+j=7\}$ has $|A| = 6$.  
     By the *axiom of probability* (uniform distribution):  
     $$
     P(A) = \frac{|A|}{|\Omega|} = \frac{6}{36} = \frac{1}{6}
     $$  
     *This is exact*—no approximation is needed for fair dice.

> 🔍 **Key Insight**: The simulation converges to the theoretical value because the dice rolls are *independent and identically distributed* (i.i.d.) with a uniform distribution. This satisfies the *law of large numbers*.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging  
*Identify and resolve a critical error in the dice simulation.*  

**Scenario**: A student accidentally modifies the code to count *only* ordered pairs where $i < j$ (e.g., $(1,6)$ but not $(6,1)$).  

### Step-by-Step Workflow  
1. **Inject fault** (modify `dice_probability.py`):  
   ```python
   # Faulty version (only counts unordered pairs)
   def simulate_dice_trials(trials=10000):
       counts = Counter()
       for _ in range(trials):
           roll1 = random.randint(1, 6)
           roll2 = random.randint(1, 6)
           total = roll1 + roll2
           if roll1 < roll2:  # Fault: ignores (6,1) etc.
               counts[total] += 1
       return counts
   ```  

2. **Run faulty simulation** (terminal):  
   ```bash
   python3 faulty_dice.py  # (save modified code as faulty_dice.py)
   ```  
   *Expected Output*:  
   ```
   Empirical P(sum=7) = 0.0834  # (incorrectly low)
   ```  

3. **Failure analysis** (diagnose the error):  
   - **Why is the result wrong?**  
     The sample space has 36 outcomes, but the faulted code only counts 15 outcomes (for $i < j$).  
     For sum=7: Only 3 ordered pairs satisfy $i < j$: $(1,6), (2,5), (3,4)$.  
     Thus: $P_{\text{faulty}}(7) = \frac{3}{36} = \frac{1}{12} \approx 0.0833$ (matches output).  

4. **Debug and fix** (correct the code):  
   ```python
   # Fixed version (counts all ordered pairs)
   def simulate_dice_trials(trials=10000):
       counts = Counter()
       for _ in range(trials):
           roll1 = random.randint(1, 6)
           roll2 = random.randint(1, 6)
           total = roll1 + roll2
           counts[total] += 1  # No condition—counts all outcomes
       return counts
   ```  

5. **Revalidate** (terminal):  
   ```bash
   python3 fixed_dice.py
   ```  
   *Expected Output*:  
   ```
   Empirical P(sum=7) = 0.1668  # Matches theoretical 1/6
   ```  

> 💡 **Critical Takeaway**: Probability models *must* preserve the full sample space. A single condition (e.g., $i < j$) invalidates the model unless explicitly justified by the problem context.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor  
*Apply your skills to a novel problem—then discuss with the AI tutor.*  

**Problem**:  
> *A bag contains 5 red balls and 3 blue balls. Two balls are drawn without replacement. What is the probability that both balls are red?*  

**Your Task**:  
1. Derive the exact probability using combinatorial reasoning.  
2. Simulate the experiment 10,000 times to estimate the probability.  
3. **Discuss with the AI Tutor**:  
   - *Why does the simulation converge to the theoretical value?*  
   - *What happens if we draw with replacement?*  

**Socratic Prompt for AI Tutor**:  
> "Explain how the *law of large numbers* ensures that the simulation result converges to the theoretical probability. If we changed the problem to *with replacement*, how would the sample space change? Show the new probability calculation."  

**Expected AI Response Structure**:  
1. **Theoretical derivation** (using hypergeometric distribution)  
2. **Simulation convergence explanation** (via LLN)  
3. **With-replacement analysis** (binomial distribution)  

> 🌟 **Why this matters**: This problem bridges discrete probability theory with real-world applications (e.g., quality control, genetic sampling). The AI tutor will help you connect theory to practice through iterative reasoning.

---

**Final Note**: In formal sciences, *every step must be verifiable*. Always ask:  
> *"Does this output satisfy the axioms of probability?"*  
> *"Can I prove this result without simulation?"*  

This lab reinforces that probability is a *mathematical discipline*—not a heuristic tool. By mastering these operational steps, you build the foundation for advanced topics like Bayesian inference and stochastic processes.  

*Professor of Mathematics and Formal Logic*  
*Department of Applied Mathematics*
