# Beginner Hands-On Lab: Game Theory 03 Extensive Form And Subgame Perfection

## Objective & Prerequisites
The objective of this lab is to introduce you to the concepts of extensive form games and subgame perfection in game theory. We will set up a basic environment using Python and the `nashpy` library, which is a popular tool for analyzing games. By the end of this lab, you will be able to define and analyze simple extensive form games and understand the concept of subgame perfection.

### Prerequisites
- Basic knowledge of Python programming.
- Familiarity with game theory concepts such as normal form games.
- Access to a Python environment (e.g., Jupyter Notebook, Google Colab).

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)

1. **Install Required Libraries:**
   Open your terminal or command prompt and run the following command to install `nashpy` and `matplotlib`:
   ```bash
   pip install nashpy matplotlib
   ```

2. **Verify Installation:**
   Create a new Python script or Jupyter Notebook and run the following commands to verify that the libraries are installed correctly:
   ```python
   import nashpy as nash
   import matplotlib.pyplot as plt

   print("nashpy version:", nash.__version__)
   print("matplotlib version:", plt.__version__)
   ```

   **Expected Output:**
   ```
   nashpy version: X.X.X
   matplotlib version: X.X.X
   ```
   (Note: The version numbers may vary.)

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)

1. **Define a Simple Extensive Form Game:**
   We will define a simple extensive form game using `nashpy`. Consider a game where Player 1 has two choices (A or B) and Player 2 has two choices (X or Y) depending on Player 1's choice.

   ```python
   import nashpy as nash

   # Define the payoffs for Player 1 and Player 2
   player1_payoffs = [[(3, 1), (0, 0)], [(1, 0), (2, 2)]]
   player2_payoffs = [[(1, 3), (0, 0)], [(0, 1), (2, 2)]]

   # Create the extensive form game
   game = nash.ExtensiveFormGame([player1_payoffs, player2_payoffs])
   ```

2. **Visualize the Game:**
   We can visualize the game tree using `matplotlib`.

   ```python
   import matplotlib.pyplot as plt

   # Plot the game tree
   game.plot()
   plt.show()
   ```

   **Expected Output:**
   A game tree diagram showing the choices of Player 1 and Player 2 with their respective payoffs.

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)

1. **Inspect the Game Structure:**
   We can inspect the structure of the game by printing the game object.

   ```python
   print(game)
   ```

   **Expected Output:**
   ```
   ExtensiveFormGame with players: (2,)
   Player 0: [(3, 1), (0, 0)], [(1, 0), (2, 2)]
   Player 1: [(1, 3), (0, 0)], [(0, 1), (2, 2)]
   ```

2. **Find Subgame Perfect Equilibria:**
   We can find the subgame perfect equilibria of the game using the `get_subgame_perfect_equilibria` method.

   ```python
   equilibria = game.get_subgame_perfect_equilibria()
   for eq in equilibria:
       print(eq)
   ```

   **Expected Output:**
   ```
   (0, 0)
   (1, 1)
   ```
   (Note: The output may vary depending on the specific game and the method used to find equilibria.)

## Challenge Exercise (Simple self-test for beginners)

1. **Modify the Game:**
   Modify the payoffs of the game to create a different extensive form game. For example, change the payoffs to:
   ```python
   player1_payoffs = [[(2, 1), (0, 0)], [(1, 0), (3, 2)]]
   player2_payoffs = [[(1, 2), (0, 0)], [(0, 1), (3, 2)]]
   ```

2. **Re-run the Analysis:**
   Re-run the steps from Exercise 2 and Exercise 3 to analyze the new game. Visualize the game tree and find the subgame perfect equilibria.

   **Expected Output:**
   A new game tree diagram and a list of subgame perfect equilibria for the modified game.

By completing this lab, you should have a basic understanding of how to define and analyze extensive form games using `nashpy` and how to find subgame perfect equilibria.
