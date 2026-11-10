# Beginner Technical Lesson: Game Theory 04 Repeated Games And Folk Theorem

## 1. Core Mechanics & Basic Principles

### Repeated Games
In game theory, a **repeated game** is an extension of a game that is played repeatedly over time. The key idea is that players' actions in one period can influence the outcomes in future periods. This introduces the possibility of cooperation and punishment strategies that are not present in one-shot games.

### Folk Theorem
The **Folk Theorem** in game theory states that in infinitely repeated games, any feasible and individually rational payoff can be sustained as a Nash equilibrium. This means that players can achieve outcomes that are better than the Nash equilibrium of the one-shot game, provided they can commit to a strategy that enforces cooperation.

## 2. Step-by-Step Component Breakdown

### Step 1: Define the One-Shot Game
First, define the one-shot game. For simplicity, consider a two-player game with the following payoff matrix:

\[
\begin{array}{c|cc}
& \text{Player 2: C} & \text{Player 2: D} \\
\hline
\text{Player 1: C} & (3, 3) & (0, 5) \\
\text{Player 1: D} & (5, 0) & (1, 1) \\
\end{array}
\]

Here, \(C\) stands for "Cooperate" and \(D\) stands for "Defect". The payoffs are given in the form \((\text{Payoff for Player 1}, \text{Payoff for Player 2})\).

### Step 2: Identify the Nash Equilibrium
The Nash equilibrium of this one-shot game is \((D, D)\) with a payoff of \((1, 1)\).

### Step 3: Consider Repeated Play
In a repeated game, players can use strategies that depend on the history of play. A common strategy is **Tit-for-Tat**, where a player cooperates on the first move and then mimics the opponent's previous move.

### Step 4: Apply the Folk Theorem
The Folk Theorem suggests that if the game is repeated infinitely, players can achieve payoffs better than \((1, 1)\). For example, they can achieve \((3, 3)\) if they cooperate repeatedly.

## 3. First Working Implementation

Below is a simple Python implementation of a repeated game using the Tit-for-Tat strategy. This example assumes an infinitely repeated game with a discount factor \(\delta\) that represents the weight of future payoffs.

```python
# Import necessary libraries
import numpy as np

# Define the payoff matrix
payoff_matrix = np.array([
    [(3, 3), (0, 5)],
    [(5, 0), (1, 1)]
])

# Define the Tit-for-Tat strategy
def tit_for_tat(history):
    if not history:
        return 'C'  # Cooperate on the first move
    else:
        return history[-1][1]  # Mimic the opponent's last move

# Simulate the repeated game
def simulate_game(num_rounds, strategy1, strategy2):
    history = []
    payoffs = [0, 0]
    
    for _ in range(num_rounds):
        move1 = strategy1(history)
        move2 = strategy2(history)
        
        # Determine the payoff based on the moves
        payoff1, payoff2 = payoff_matrix[move1 == 'D'][move2 == 'D']
        
        # Update the payoffs
        payoffs[0] += payoff1
        payoffs[1] += payoff2
        
        # Record the moves in history
        history.append((move1, move2))
    
    return payoffs, history

# Run the simulation
num_rounds = 100
payoffs, history = simulate_game(num_rounds, tit_for_tat, tit_for_tat)

# Print the results
print(f"Payoffs after {num_rounds} rounds: Player 1 = {payoffs[0]}, Player 2 = {payoffs[1]}")
```

## 4. What Can Go Wrong

### Common Mistakes
1. **Incorrect Payoff Calculation:** Ensure that the payoff matrix is correctly defined and that the payoffs are calculated based on the players' moves.
2. **Strategy Implementation:** Verify that the strategy function correctly implements the intended logic.
3. **Infinite Assumption:** Remember that the Folk Theorem relies on the assumption of an infinitely repeated game. In practice, games may have a finite number of rounds, which can affect the strategies and outcomes.

### How to Spot Mistakes
- **Check Payoffs:** Verify that the payoffs calculated match the payoff matrix.
- **Debug Strategy:** Use print statements or a debugger to trace the strategy function and ensure it behaves as expected.
- **Consider Finite Rounds:** If the game has a finite number of rounds, consider how this affects the strategies and outcomes.

## 5. Key Takeaways & Review Checklist

### Key Takeaways
- **Repeated Games:** Players can achieve better outcomes in repeated games through cooperation and punishment strategies.
- **Folk Theorem:** In infinitely repeated games, any feasible and individually rational payoff can be sustained as a Nash equilibrium.
- **Tit-for-Tat:** A simple yet effective strategy in repeated games.

### Review Checklist
- [ ] Define the one-shot game and its payoff matrix.
- [ ] Identify the Nash equilibrium of the one-shot game.
- [ ] Consider the implications of repeated play and the Folk Theorem.
- [ ] Implement a simple strategy (e.g., Tit-for-Tat) in a repeated game.
- [ ] Simulate the repeated game and verify the results.
- [ ] Be aware of common mistakes and how to spot them.
