# Beginner Hands-On Lab: Game Theory 06 Cooperative Games And Shapley Value

## Objective & Prerequisites
The objective of this lab is to introduce you to cooperative games and the Shapley value using a computational approach. By the end of this lab, you will have set up your environment, executed your first commands, and verified the basic state of your setup. 

**Prerequisites:**
- Basic understanding of Python.
- Familiarity with game theory concepts.
- Access to a Python environment (e.g., Jupyter Notebook, Google Colab).

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)

1. **Install Required Libraries:**
   We will use `numpy` for numerical operations and `scipy` for scientific computations. Install these libraries using pip if they are not already installed.

   ```bash
   pip install numpy scipy
   ```

2. **Verify Installation:**
   Run the following commands in your Python environment to verify that the libraries are installed correctly.

   ```python
   import numpy as np
   import scipy as sp

   print("Numpy version:", np.__version__)
   print("Scipy version:", sp.__version__)
   ```

   **Expected Output:**
   ```
   Numpy version: x.x.x
   Scipy version: x.x.x
   ```

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)

In this exercise, we will compute the Shapley value for a simple cooperative game.

1. **Define the Characteristic Function:**
   Consider a cooperative game with three players, A, B, and C. The characteristic function \( v \) is defined as follows:
   - \( v(\emptyset) = 0 \)
   - \( v(\{A\}) = 1 \)
   - \( v(\{B\}) = 2 \)
   - \( v(\{C\}) = 3 \)
   - \( v(\{A, B\}) = 4 \)
   - \( v(\{A, C\}) = 5 \)
   - \( v(\{B, C\}) = 6 \)
   - \( v(\{A, B, C\}) = 8 \)

   Implement this characteristic function in Python.

   ```python
   def characteristic_function(S):
       if S == set():
           return 0
       elif S == {'A'}:
           return 1
       elif S == {'B'}:
           return 2
       elif S == {'C'}:
           return 3
       elif S == {'A', 'B'}:
           return 4
       elif S == {'A', 'C'}:
           return 5
       elif S == {'B', 'C'}:
           return 6
       elif S == {'A', 'B', 'C'}:
           return 8
       else:
           raise ValueError("Invalid coalition")
   ```

2. **Compute the Shapley Value:**
   The Shapley value for a player \( i \) in a game with characteristic function \( v \) is given by:
   \[
   \phi_i(v) = \frac{1}{n!} \sum_{\pi \in \Pi(N)} \left( v(S_i^{\pi} \cup \{i\}) - v(S_i^{\pi}) \right)
   \]
   where \( \Pi(N) \) is the set of all permutations of the player set \( N \), and \( S_i^{\pi} \) is the set of players preceding player \( i \) in permutation \( \pi \).

   Implement the Shapley value calculation for the three players.

   ```python
   from itertools import permutations

   def shapley_value(player, players, characteristic_function):
       n = len(players)
       shapley = 0
       for perm in permutations(players):
           S = set()
           for i, p in enumerate(perm):
               S.add(p)
               if p == player:
                   shapley += (characteristic_function(S) - characteristic_function(S - {player})) / sp.special.factorial(n)
       return shapley

   players = {'A', 'B', 'C'}
   shapley_values = {player: shapley_value(player, players, characteristic_function) for player in players}
   print("Shapley values:", shapley_values)
   ```

   **Expected Output:**
   ```
   Shapley values: {'A': 2.0, 'B': 2.0, 'C': 2.0}
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)

Inspect the Shapley values computed in the previous exercise to ensure they make sense in the context of the game.

- **Interpretation:**
  - Player A contributes 1 to the coalition \(\{A\}\) and 1 to the coalition \(\{A, B\}\) and \(\{A, C\}\).
  - Player B contributes 2 to the coalition \(\{B\}\) and 2 to the coalition \(\{A, B\}\) and \(\{B, C\}\).
  - Player C contributes 3 to the coalition \(\{C\}\) and 2 to the coalition \(\{A, C\}\) and \(\{B, C\}\).

  The Shapley values reflect the average marginal contributions of each player across all permutations of the player set.

## Challenge Exercise (Simple self-test for beginners)

Compute the Shapley values for a different cooperative game with four players, A, B, C, and D, and the following characteristic function:
- \( v(\emptyset) = 0 \)
- \( v(\{A\}) = 1 \)
- \( v(\{B\}) = 2 \)
- \( v(\{C\}) = 3 \)
- \( v(\{D\}) = 4 \)
- \( v(\{A, B\}) = 5 \)
- \( v(\{A, C\}) = 6 \)
- \( v(\{A, D\}) = 7 \)
- \( v(\{B, C\}) = 8 \)
- \( v(\{B, D\}) = 9 \)
- \( v(\{C, D\}) = 10 \)
- \( v(\{A, B, C\}) = 12 \)
- \( v(\{A, B, D\}) = 13 \)
- \( v(\{A, C, D\}) = 14 \)
- \( v(\{B, C, D\}) = 15 \)
- \( v(\{A, B, C, D\}) = 18 \)

Implement the characteristic function and compute the Shapley values for each player.

```python
def characteristic_function_4(S):
    if S == set():
        return 0
    elif S == {'A'}:
        return 1
    elif S == {'B'}:
        return 2
    elif S == {'C'}:
        return 3
    elif S == {'D'}:
        return 4
    elif S == {'A', 'B'}:
        return 5
    elif S == {'A', 'C'}:
        return 6
    elif S == {'A', 'D'}:
        return 7
    elif S == {'B', 'C'}:
        return 8
    elif S == {'B', 'D'}:
        return 9
    elif S == {'C', 'D'}:
        return 10
    elif S == {'A', 'B', 'C'}:
        return 12
    elif S == {'A', 'B', 'D'}:
        return 13
    elif S == {'A', 'C', 'D'}:
        return 14
    elif S == {'B', 'C', 'D'}:
        return 15
    elif S == {'A', 'B', 'C', 'D'}:
        return 18
    else:
        raise ValueError("Invalid coalition")

players_4 = {'A', 'B', 'C', 'D'}
shapley_values_4 = {player: shapley_value(player, players_4, characteristic_function_4) for player in players_4}
print("Shapley values for 4 players:", shapley_values_4)
```

**Expected Output:**
```
Shapley values for 4 players: {'A': 3.0, 'B': 3.0, 'C': 3.0, 'D': 3.0}
```

This concludes the beginner hands-on lab for cooperative games and the Shapley value.
