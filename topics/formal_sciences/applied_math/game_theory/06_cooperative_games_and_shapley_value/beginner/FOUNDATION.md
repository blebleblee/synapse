# Beginner Foundation: Game Theory 06 Cooperative Games And Shapley Value

## 1. Everyday Intuition & First Principles

Imagine you and your friends are playing a game where you can either play individually or form teams. If you form a team, you can achieve more points together than you could alone. However, the question arises: how should the points be distributed among the team members? This is where cooperative game theory comes into play. Specifically, the Shapley value provides a fair way to distribute the total gains to the players, based on their individual contributions to the team.

## 2. Foundational Vocabulary & Glossary

- **Cooperative Game:** A game where players can form coalitions to achieve a common goal. Unlike non-cooperative games, players can make binding agreements.
- **Coalition:** A group of players who decide to work together in a cooperative game.
- **Characteristic Function:** A function that assigns a value to every possible coalition, representing the total payoff that the coalition can achieve if it acts together.
- **Shapley Value:** A method for distributing the total gains of a cooperative game among the players, based on their marginal contributions to all possible coalitions.
- **Marginal Contribution:** The additional value a player brings to a coalition by joining it.
- **Null Player:** A player whose presence does not change the value of any coalition they join.

### Examples

- **Cooperative Game:** A group of workers deciding whether to strike for better wages. If they strike together, they can negotiate more effectively than if they strike individually.
- **Coalition:** In the workers' example, a coalition could be a subset of workers who decide to strike together.
- **Characteristic Function:** If the workers' coalition can negotiate a 10% wage increase, the characteristic function assigns a value of 10% to that coalition.
- **Shapley Value:** If the workers' coalition consists of Alice, Bob, and Charlie, the Shapley value determines how the 10% wage increase should be divided among them based on their individual contributions.
- **Marginal Contribution:** If Alice's presence in the coalition increases the wage increase from 8% to 10%, her marginal contribution is 2%.
- **Null Player:** If Dave's presence in any coalition does not change the wage increase, he is a null player.

## 3. Visual System Flow

### ASCII Diagram

```
+-------------------+
| Cooperative Game  |
+-------------------+
          |
          v
+-------------------+
| Characteristic    |
| Function (v)      |
+-------------------+
          |
          v
+-------------------+
| Coalitions        |
+-------------------+
          |
          v
+-------------------+
| Marginal          |
| Contributions     |
+-------------------+
          |
          v
+-------------------+
| Shapley Value     |
+-------------------+
```

### Mermaid Flowchart

```mermaid
graph TD;
    A[Cooperative Game] --> B[Characteristic Function (v)];
    B --> C[Coalitions];
    C --> D[Marginal Contributions];
    D --> E[Shapley Value];
```

## 4. Common Beginner Misconceptions & Mental Traps

- **Misconception:** The Shapley value always gives equal pay to all players. **Trap:** This is incorrect. The Shapley value considers each player's marginal contribution to all coalitions, which may vary.
- **Misconception:** The Shapley value is only applicable in games with monetary payoffs. **Trap:** The Shapley value can be applied to any type of payoff, including non-monetary benefits.
- **Misconception:** The Shapley value is always the fairest distribution method. **Trap:** While the Shapley value is a fair method, other distribution methods may be more appropriate in certain situations.

## 5. Socratic Discussion Starters

1. Can you think of a real-world scenario where cooperative game theory and the Shapley value could be applied?
2. How does the Shapley value ensure that players are incentivized to join coalitions?
3. What are the limitations of using the Shapley value in cooperative game theory?
4. How does the concept of a null player affect the distribution of payoffs in the Shapley value?
5. Can you explain the difference between the Shapley value and other distribution methods in cooperative game theory?
