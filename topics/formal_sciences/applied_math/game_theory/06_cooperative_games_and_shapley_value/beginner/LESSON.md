# Beginner Technical Lesson: Game Theory 06 Cooperative Games And Shapley Value
## 1. Core Mechanics & Basic Principles (How it works under the hood at a fundamental level)

### Cooperative Games
In cooperative game theory, players can form coalitions to achieve a common goal. The focus is on how the players can collaborate to maximize their collective payoff and how the payoff should be distributed among them. A cooperative game is typically defined by a characteristic function \(v\), which specifies the total payoff that a coalition of players can achieve.

Formally, a cooperative game is a pair \((N, v)\), where:
- \(N\) is a finite set of players, \(N = \{1, 2, \ldots, n\}\).
- \(v: 2^N \rightarrow \mathbb{R}\) is a characteristic function that assigns a real number \(v(S)\) to each coalition \(S \subseteq N\), representing the total payoff that the coalition \(S\) can achieve.

### Shapley Value
The Shapley value is a method for distributing the total gains to the players, assuming that they work together as a team. It is based on the marginal contribution of each player to every possible coalition they could join. The Shapley value \(\phi_i(v)\) for player \(i\) in a game \((N, v)\) is given by:

\[
\phi_i(v) = \frac{1}{n!} \sum_{\pi \in \Pi(N)} \left( v(S_i^{\pi} \cup \{i\}) - v(S_i^{\pi}) \right)
\]

where \(\Pi(N)\) is the set of all permutations of the players in \(N\), and \(S_i^{\pi}\) is the set of players preceding player \(i\) in permutation \(\pi\).

Alternatively, the Shapley value can be expressed as:

\[
\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(n-|S|-1)!}{n!} \left( v(S \cup \{i\}) - v(S) \right)
\]

This formula calculates the average marginal contribution of player \(i\) across all possible coalitions.

## 2. Step-by-Step Component Breakdown

1. **Define the Set of Players**: Identify the players involved in the game.
2. **Define the Characteristic Function**: Determine the payoff for each possible coalition.
3. **Calculate Marginal Contributions**: For each player, calculate their marginal contribution to every possible coalition.
4. **Compute the Shapley Value**: Use the Shapley value formula to determine the fair distribution of the total payoff among the players.

## 3. First Working Implementation (Complete, clean, commented starter code or configuration)

Here is a simple Python implementation to calculate the Shapley value for a cooperative game with three players.

```python
from itertools import permutations, combinations

def shapley_value(v):
    n = len(v) - 1  # Number of players
    phi = [0] * (n + 1)  # Initialize Shapley values for each player

    # Iterate over all permutations of players
    for pi in permutations(range(1, n + 1)):
        for i in range(1, n + 1):
            # Find the set of players preceding player i in permutation pi
            S_i = [pi[j] for j in range(pi.index(i))]
            # Calculate the marginal contribution of player i
            phi[i] += v[tuple(sorted(S_i + [i]))] - v[tuple(sorted(S_i))]

    # Normalize by the number of permutations
    for i in range(1, n + 1):
        phi[i] /= factorial(n)

    return phi[1:]  # Return Shapley values for players 1 to n

# Example characteristic function for a game with 3 players
v = {
    (): 0,
    (1,): 2,
    (2,): 3,
    (3,): 1,
    (1, 2): 5,
    (1, 3): 4,
    (2, 3): 6,
    (1, 2, 3): 8
}

# Calculate Shapley values
shapley_values = shapley_value(v)
print("Shapley Values:", shapley_values)
```

**Note**: The `factorial` function from the `math` module should be imported to use in the code.

## 4. What Can Go Wrong (Simple common mistakes and how to spot them)

1. **Incorrect Characteristic Function**: Ensure that the characteristic function \(v\) is defined for all possible coalitions.
2. **Permutation Errors**: Verify that all permutations of players are considered in the calculation.
3. **Normalization**: Make sure to divide by the total number of permutations to get the average marginal contribution.
4. **Indexing Issues**: Pay attention to the indexing of players and coalitions to avoid off-by-one errors.

## 5. Key Takeaways & Review Checklist

- **Cooperative Games**: Understand the concept of cooperative games and the role of the characteristic function.
- **Shapley Value**: Grasp the formula and intuition behind the Shapley value.
- **Implementation**: Be able to implement the Shapley value calculation in a programming language.
- **Common Mistakes**: Be aware of potential pitfalls in defining the characteristic function and calculating permutations.

By following this lesson, you should have a solid foundation in cooperative games and the Shapley value, enabling you to apply these concepts to more complex scenarios.
