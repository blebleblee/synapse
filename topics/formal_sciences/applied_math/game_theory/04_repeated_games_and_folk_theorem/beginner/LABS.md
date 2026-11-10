# Beginner Hands-On Lab: Game Theory 04 Repeated Games And Folk Theorem

## Objective & Prerequisites
The objective of this lab is to set up the environment necessary for simulating repeated games and to execute a simple experiment to verify the setup. This lab assumes you have basic knowledge of Python and familiarity with command-line operations. We will use the `Axelrod` library, a popular Python library for simulating iterated prisoner's dilemma and other repeated games.

### Prerequisites:
- Python 3.6 or higher installed.
- `pip` installed and updated.
- Basic understanding of Python and command-line operations.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
1. **Install the Axelrod library**:
   Open your terminal or command prompt and run the following command:
   ```bash
   pip install axelrod
   ```

2. **Verify the installation**:
   Run the following command to check if the installation was successful:
   ```bash
   python -c "import axelrod as axl; print(axl.__version__)"
   ```
   You should see the version number of the installed Axelrod library printed in the terminal.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
1. **Create a Python script**:
   Create a new Python file named `repeated_game.py` and open it in your favorite text editor.

2. **Write the code to simulate a repeated game**:
   Add the following code to `repeated_game.py`:
   ```python
   import axelrod as axl

   # Create players
   player1 = axl.Cooperator()
   player2 = axl.Defector()

   # Create a match
   match = axl.Match((player1, player2), turns=5)

   # Play the match
   match.play()

   # Print the results
   print("Match results:")
   print(match.result)
   ```

3. **Run the script**:
   Execute the script by running the following command in your terminal:
   ```bash
   python repeated_game.py
   ```

   **Expected Output**:
   ```
   Match results:
   [('C', 'D'), ('C', 'D'), ('C', 'D'), ('C', 'D'), ('C', 'D')]
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
1. **Inspect the match results**:
   In the `repeated_game.py` script, add the following lines after the `match.play()` line to print more detailed information about the match:
   ```python
   # Print detailed match results
   print("Detailed match results:")
   for round_number, (p1_action, p2_action) in enumerate(match.result, start=1):
       print(f"Round {round_number}: Player 1 ({player1}) played {p1_action}, Player 2 ({player2}) played {p2_action}")
   ```

2. **Run the updated script**:
   Execute the script again by running the following command in your terminal:
   ```bash
   python repeated_game.py
   ```

   **Expected Output**:
   ```
   Match results:
   [('C', 'D'), ('C', 'D'), ('C', 'D'), ('C', 'D'), ('C', 'D')]
   Detailed match results:
   Round 1: Player 1 (Cooperator) played C, Player 2 (Defector) played D
   Round 2: Player 1 (Cooperator) played C, Player 2 (Defector) played D
   Round 3: Player 1 (Cooperator) played C, Player 2 (Defector) played D
   Round 4: Player 1 (Cooperator) played C, Player 2 (Defector) played D
   Round 5: Player 1 (Cooperator) played C, Player 2 (Defector) played D
   ```

## Challenge Exercise (Simple self-test for beginners)
1. **Modify the players**:
   Change the players in the `repeated_game.py` script to use `TitForTat` and `Random` strategies instead of `Cooperator` and `Defector`. Update the script accordingly:
   ```python
   import axelrod as axl

   # Create players
   player1 = axl.TitForTat()
   player2 = axl.Random()

   # Create a match
   match = axl.Match((player1, player2), turns=5)

   # Play the match
   match.play()

   # Print the results
   print("Match results:")
   print(match.result)

   # Print detailed match results
   print("Detailed match results:")
   for round_number, (p1_action, p2_action) in enumerate(match.result, start=1):
       print(f"Round {round_number}: Player 1 ({player1}) played {p1_action}, Player 2 ({player2}) played {p2_action}")
   ```

2. **Run the modified script**:
   Execute the script by running the following command in your terminal:
   ```bash
   python repeated_game.py
   ```

   **Expected Output**:
   The output will vary due to the random strategy of `Random`, but it should look something like this:
   ```
   Match results:
   [('C', 'D'), ('D', 'C'), ('C', 'D'), ('D', 'C'), ('C', 'D')]
   Detailed match results:
   Round 1: Player 1 (TitForTat) played C, Player 2 (Random) played D
   Round 2: Player 1 (TitForTat) played D, Player 2 (Random) played C
   Round 3: Player 1 (TitForTat) played C, Player 2 (Random) played D
   Round 4: Player 1 (TitForTat) played D, Player 2 (Random) played C
   Round 5: Player 1 (TitForTat) played C, Player 2 (Random) played D
   ```

This concludes the beginner hands-on lab for Game Theory 04 Repeated Games And Folk Theorem. You have successfully set up the environment, executed a simple experiment, and inspected the basic state of the game.
