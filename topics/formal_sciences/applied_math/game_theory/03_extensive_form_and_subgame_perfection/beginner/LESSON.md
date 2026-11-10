# Beginner Technical Lesson: Game Theory 03 Extensive Form And Subgame Perfection

## 1. Core Mechanics & Basic Principles

### Extensive Form Games
In game theory, extensive form games are a way of representing games that have a sequential structure. Unlike normal form games, which present all possible strategies and payoffs in a single table, extensive form games use a tree structure to depict the sequence of moves and the information available to each player at each decision point.

### Subgame Perfection
Subgame perfection is a refinement of the Nash equilibrium concept for extensive form games. It requires that players' strategies form a Nash equilibrium in every subgame of the game. A subgame is a part of the game tree that starts at a single decision node and includes all the subsequent decision nodes and terminal nodes. Subgame perfection ensures that players' strategies are credible and consistent throughout the game.

## 2. Step-by-Step Component Breakdown

### Game Tree Representation
- **Nodes:** Represent decision points for players.
- **Edges:** Represent actions that players can take.
- **Terminal Nodes:** Represent the end of the game and the payoffs for each player.

### Information Sets
- **Information Set:** A set of nodes such that a player cannot distinguish between them when making a decision. This represents imperfect information in the game.

### Strategies
- **Strategy:** A complete plan of actions for a player, specifying what action to take at every decision node in the game tree.

### Payoffs
- **Payoff:** The numerical value that represents the utility or benefit to a player at the end of the game.

### Subgame Perfect Nash Equilibrium (SPNE)
- **Subgame:** A part of the game tree starting from a single decision node.
- **SPNE:** A strategy profile that is a Nash equilibrium in every subgame of the game.

## 3. First Working Implementation

Let's consider a simple example of an extensive form game: the Centipede Game. In this game, two players take turns choosing between "Pass" or "Take" a pot of money that increases with each turn. If a player chooses "Take," the game ends, and the player takes the pot, while the other player gets nothing. If both players choose "Pass," the pot increases, and the game continues to the next turn.

We will use Python to represent this game and find the subgame perfect Nash equilibrium.

```python
# Import necessary libraries
from itertools import product

# Define the Centipede Game parameters
players = ['Player 1', 'Player 2']
max_turns = 4
initial_pot = 10
increment = 5

# Function to generate all possible strategies
def generate_strategies(max_turns):
    actions = ['Pass', 'Take']
    return list(product(actions, repeat=max_turns))

# Function to evaluate a strategy profile
def evaluate_strategy_profile(strategy_profile):
    pot = initial_pot
    for turn in range(max_turns):
        player = players[turn % 2]
        action = strategy_profile[turn]
        if action == 'Take':
            return {players[0]: pot if player == players[0] else 0,
                    players[1]: pot if player == players[1] else 0}
        pot += increment
    return {players[0]: pot, players[1]: pot}

# Generate all possible strategy profiles
all_strategy_profiles = list(product(generate_strategies(max_turns), repeat=2))

# Find the subgame perfect Nash equilibrium
def is_spne(strategy_profile):
    for turn in range(max_turns):
        player = players[turn % 2]
        opponent = players[(turn + 1) % 2]
        current_action = strategy_profile[turn % 2][turn]
        opponent_strategy = strategy_profile[(turn + 1) % 2]
        if current_action == 'Pass':
            # Check if taking is better for the current player
            take_strategy = list(strategy_profile[turn % 2])
            take_strategy[turn] = 'Take'
            take_strategy = tuple(take_strategy)
            take_payoff = evaluate_strategy_profile((take_strategy, opponent_strategy))[player]
            pass_payoff = evaluate_strategy_profile(strategy_profile)[player]
            if take_payoff > pass_payoff:
                return False
    return True

spne = [sp for sp in all_strategy_profiles if is_spne(sp)]

# Print the subgame perfect Nash equilibrium
print("Subgame Perfect Nash Equilibrium:")
for sp in spne:
    print(f"Player 1: {sp[0]}, Player 2: {sp[1]}")
```

## 4. What Can Go Wrong

### Common Mistakes
- **Incorrect Strategy Representation:** Ensure that each strategy covers all decision nodes for a player.
- **Ignoring Subgames:** When checking for subgame perfection, ensure that every subgame is considered.
- **Misinterpreting Payoffs:** Verify that the payoffs are correctly calculated for each terminal node.

### How to Spot Mistakes
- **Check Strategy Completeness:** Ensure that each strategy includes an action for every decision node.
- **Verify Subgame Equilibria:** Manually check a few subgames to ensure that the strategies form a Nash equilibrium in each.
- **Cross-Check Payoffs:** Double-check the payoffs at each terminal node to ensure they are correctly calculated.

## 5. Key Takeaways & Review Checklist

### Key Takeaways
- **Extensive Form Games:** Represent games with a sequential structure using a tree.
- **Subgame Perfection:** Refine Nash equilibrium by ensuring strategies are credible in every subgame.
- **Implementation:** Use Python to represent and solve simple extensive form games.

### Review Checklist
- [ ] Understand the structure of extensive form games.
- [ ] Define and identify subgames.
- [ ] Calculate payoffs for terminal nodes.
- [ ] Determine the subgame perfect Nash equilibrium.
- [ ] Avoid common mistakes in strategy representation and payoff calculation.
