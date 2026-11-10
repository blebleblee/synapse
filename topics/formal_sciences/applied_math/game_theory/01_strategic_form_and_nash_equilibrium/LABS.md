# Hands-On Operational Lab: Algorithmic Game Solvers, Repeated Tournaments & Shapley Power Indices

## Objective & Lab Prerequisites
In this lab, you will programmatically compute Pure and Mixed Strategy Nash Equilibria using linear support enumeration, simulate an evolutionary tournament of repeated games to test the Folk Theorem, and calculate exact Shapley power values for coalitional weighted voting games.

### Prerequisites
* Python 3.10+ with standard virtual environment.
* Install math and optimization packages:
  ```bash
  pip install numpy scipy
  ```

---

## Exercise 1: Computing Mixed Strategy Nash Equilibria via Indifference Linear Systems

Consider the canonical **Inspection Game** (e.g., Security Guard auditing an Employee):
* Employee strategies: Work ($W$) vs. Shirk ($S$).
* Guard strategies: Inspect ($I$) vs. Don't Inspect ($D$).

Payoff Matrix ($u_1 = \text{Employee}, u_2 = \text{Guard}$):
* $(W, I)$: $(1, -1)$
* $(W, D)$: $(2, 0)$
* $(S, I)$: $(-2, 1)$
* $(S, D)$: $(3, -2)$

Notice: No Pure Strategy Nash Equilibrium exists. We will compute the exact MSNE $(\sigma_1^*, \sigma_2^*)$ using Python.

### Python Solver Implementation (`solve_inspection.py`)

```python
cat << 'EOF' > solve_inspection.py
import numpy as np

# Payoff matrices
# Rows: Player 1 (0: Work, 1: Shirk)
# Cols: Player 2 (0: Inspect, 1: Don't Inspect)
A = np.array([
    [1, 2],    # Work
    [-2, 3]    # Shirk
])

B = np.array([
    [-1, 0],   # Inspect
    [1, -2]    # Don't Inspect
])

# Let p = Pr(P1 plays Work), 1-p = Pr(P1 plays Shirk)
# Let q = Pr(P2 plays Inspect), 1-q = Pr(P2 plays Don't Inspect)

# 1. Player 1 Indifference Condition:
# E[U_1(Work)] = E[U_1(Shirk)]
# 1*q + 2*(1-q) = -2*q + 3*(1-q)
# q + 2 - 2q = -2q + 3 - 3q
# 2 - q = 3 - 5q  =>  4q = 1  =>  q* = 0.25

# 2. Player 2 Indifference Condition:
# E[U_2(Inspect)] = E[U_2(Don't Inspect)]
# -1*p + 1*(1-p) = 0*p + -2*(1-p)
# -p + 1 - p = -2 + 2p
# 1 - 2p = -2 + 2p  =>  4p = 3  =>  p* = 0.75

print("Analytical Verification:")
print(f"  P1 (Employee) Mixed Strategy: Work={0.75:.2f}, Shirk={0.25:.2f}")
print(f"  P2 (Guard) Mixed Strategy:    Inspect={0.25:.2f}, Don't={0.75:.2f}")

# Numerical Verification of Expected Payoffs
p, q = 0.75, 0.25
u1_work = 1*q + 2*(1-q)
u1_shirk = -2*q + 3*(1-q)
print(f"\nP1 Expected Payoff (Work):  {u1_work:.2f}")
print(f"P1 Expected Payoff (Shirk): {u1_shirk:.2f} (Equilibrium Verified: Identical!)")

u2_inspect = -1*p + 1*(1-p)
u2_dont = 0*p + -2*(1-p)
print(f"\nP2 Expected Payoff (Inspect):    {u2_inspect:.2f}")
print(f"P2 Expected Payoff (Don't):      {u2_dont:.2f} (Equilibrium Verified: Identical!)")
EOF
python3 solve_inspection.py
```

---

## Exercise 2: Simulating the Folk Theorem & Axelrod Repeated Tournament

We will simulate an iterated Prisoner's Dilemma tournament over $T = 200$ rounds with discount factor $\delta = 0.95$ to observe how **Grim Trigger** and **Tit-for-Tat** enforce Pareto-optimal cooperation against uncooperative strategies.

```python
cat << 'EOF' > repeated_game_sim.py
import numpy as np

# Payoff mapping: (P1_action, P2_action) -> (P1_payoff, P2_payoff)
# Actions: 0 = Cooperate (C), 1 = Defect (D)
PAYOFFS = {
    (0, 0): (3, 3),   # Reward for mutual cooperation
    (0, 1): (0, 5),   # Sucker's payoff
    (1, 0): (5, 0),   # Temptation to defect
    (1, 1): (1, 1)    # Punishment for mutual defection
}

class AlwaysDefect:
    name = "Always Defect (ALLD)"
    def act(self, history_self, history_opp):
        return 1 # Always Defect

class TitForTat:
    name = "Tit-for-Tat (TFT)"
    def act(self, history_self, history_opp):
        if not history_opp:
            return 0 # Cooperate on round 1
        return history_opp[-1] # Copy opponent's previous move

class GrimTrigger:
    name = "Grim Trigger (GRIM)"
    def act(self, history_self, history_opp):
        if not history_opp:
            return 0
        if 1 in history_opp: # If opponent ever defected
            return 1 # Defect forever
        return 0

def play_match(p1, p2, rounds=200, delta=0.95):
    h1, h2 = [], []
    total_u1, total_u2 = 0.0, 0.0

    for t in range(rounds):
        a1 = p1.act(h1, h2)
        a2 = p2.act(h2, h1)
        h1.append(a1)
        h2.append(a2)

        u1, u2 = PAYOFFS[(a1, a2)]
        discount = delta ** t
        total_u1 += discount * u1
        total_u2 += discount * u2

    # Normalized average discounted payoff: (1 - delta) * sum
    norm1 = (1 - delta) * total_u1
    norm2 = (1 - delta) * total_u2
    return norm1, norm2

p_alld = AlwaysDefect()
p_tft = TitForTat()
p_grim = GrimTrigger()

print("==================================================")
print("     ITERATED PRISONER'S DILEMMA SIMULATION       ")
print("==================================================")

res_gg = play_match(GrimTrigger(), GrimTrigger())
print(f"GRIM vs. GRIM:       Normalized Payoff = {res_gg[0]:.3f} vs {res_gg[1]:.3f} (Sustains Cooperation!)")

res_gd = play_match(GrimTrigger(), AlwaysDefect())
print(f"GRIM vs. ALLD:       Normalized Payoff = {res_gd[0]:.3f} vs {res_gd[1]:.3f} (Punishment Enforced)")

res_dd = play_match(AlwaysDefect(), AlwaysDefect())
print(f"ALLD vs. ALLD:       Normalized Payoff = {res_dd[0]:.3f} vs {res_dd[1]:.3f} (Mutual Defection Trap)")

res_tt = play_match(TitForTat(), TitForTat())
print(f"TFT  vs. TFT:        Normalized Payoff = {res_tt[0]:.3f} vs {res_tt[1]:.3f} (Mutual Cooperation)")

res_td = play_match(TitForTat(), AlwaysDefect())
print(f"TFT  vs. ALLD:       Normalized Payoff = {res_td[0]:.3f} vs {res_td[1]:.3f}")
EOF
python3 repeated_game_sim.py
```

---

## Exercise 3: Calculating Exact Shapley Power Indices

In a coalitional weighted voting game $[q; w_1, w_2, \dots, w_n]$, players possess voting weights $w_i$. A coalition $S \subseteq N$ wins ($v(S) = 1$) if $\sum_{i \in S} w_i \ge q$, otherwise $v(S) = 0$.

We will compute the **Shapley-Shubik Power Index** using the exact combinatorial permutation formula:

$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

```python
cat << 'EOF' > shapley_index.py
import itertools
from math import factorial

def compute_shapley_values(weights, quota):
    n = len(weights)
    players = list(range(n))
    phi = [0.0] * n

    # Iterate over all possible permutations of player arrival
    permutations = list(itertools.permutations(players))
    total_perms = len(permutations)

    for perm in permutations:
        current_weight = 0
        winning = False

        for player in perm:
            prev_weight = current_weight
            current_weight += weights[player]

            # Did this player turn a losing coalition into a winning coalition?
            if prev_weight < quota and current_weight >= quota:
                phi[player] += 1.0 # This player is pivotal in this permutation
                break

    return [p / total_perms for p in phi]

# Example: Shareholder Voting
# 3 Shareholders with weights [49, 49, 2], Quota = 51
# Notice: Shareholder 3 has only 2% shares, but who holds the balance of power?
weights = [49, 49, 2]
quota = 51

shapley = compute_shapley_values(weights, quota)

print("==================================================")
print(f"  WEIGHTED VOTING GAME: Weights={weights}, Quota={quota}")
print("==================================================")
for idx, (w, p) in enumerate(zip(weights, shapley), 1):
    print(f"Player {idx} (Weight {w:2d}%): Shapley Power Index = {p:.4f} ({p*100:.1f}%)")

print("\nSurprising Mathematical Result:")
print("Although Player 3 holds only 2% of equity, they possess 33.3% of the true voting power!")
EOF
python3 shapley_index.py
```

---

## Exercise 4: Clean Up

```bash
rm -f solve_inspection.py repeated_game_sim.py shapley_index.py
```

---

## Challenge Lab: Socratic Exploration
1. In `Exercise 1`, change the payoff matrix so that Player 1 has a strictly dominant strategy. What happens to the mixed strategy support?
2. In `Exercise 2`, reduce the discount factor to $\delta = 0.2$. Run the simulation. Why does cooperation collapse, and how does this validate the Folk Theorem inequality $\delta \ge \frac{u(\text{defect}) - u(\text{coop})}{u(\text{defect}) - u(\text{punish})}$?
