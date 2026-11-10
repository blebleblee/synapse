# Intermediate Operational Lab: Game Theory 03 Extensive Form And Subgame Perfection
## Objective & Prerequisites
### Objective
The objective of this lab is to deepen your understanding of extensive form games and subgame perfection through hands-on experience with a production deployment scenario. You will configure, deploy, and troubleshoot a game-theoretic model that simulates a real-world decision-making process.

### Prerequisites
- Basic understanding of game theory, including extensive form games and subgame perfection.
- Familiarity with Python and its libraries, particularly `numpy` and `networkx`.
- Basic knowledge of software deployment and troubleshooting.

## Exercise 1: Advanced Environment Configuration & Diagnostics
### Task
Set up a Python environment with the necessary libraries and configure a game-theoretic model using `networkx` to represent an extensive form game.

### Steps
1. **Install Required Libraries:**
   ```bash
   pip install numpy networkx matplotlib
   ```

2. **Create a Python Script:**
   Create a file named `game_theory_lab.py` and import the necessary libraries.
   ```python
   import numpy as np
   import networkx as nx
   import matplotlib.pyplot as plt
   ```

3. **Define the Game Structure:**
   Use `networkx` to define the nodes and edges of the game tree.
   ```python
   G = nx.DiGraph()
   G.add_nodes_from(['Root', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2'])
   G.add_edges_from([('Root', 'A1'), ('Root', 'A2'), ('A1', 'B1'), ('A1', 'B2'), ('A2', 'C1'), ('A2', 'C2'), ('B1', 'D1'), ('B1', 'D2'), ('B2', 'D1'), ('B2', 'D2'), ('C1', 'D1'), ('C1', 'D2'), ('C2', 'D1'), ('C2', 'D2')])
   ```

4. **Visualize the Game Tree:**
   Use `matplotlib` to visualize the game tree.
   ```python
   pos = nx.spring_layout(G)
   nx.draw(G, pos, with_labels=True, node_size=3000, node_color='lightblue', font_size=10, font_weight='bold')
   plt.show()
   ```

5. **Diagnostics:**
   Ensure that the game tree is correctly structured and that all nodes and edges are properly defined.

## Exercise 2: Building & Deploying a Production Scenario (Multi-step operational workflow)
### Task
Build and deploy a production scenario that simulates a real-world decision-making process using the game-theoretic model.

### Steps
1. **Define Payoffs:**
   Assign payoffs to each terminal node in the game tree.
   ```python
   payoffs = {
       'D1': (3, 2),
       'D2': (1, 4)
   }
   ```

2. **Implement Subgame Perfect Equilibrium:**
   Write a function to find the subgame perfect equilibrium of the game.
   ```python
   def find_subgame_perfect_equilibrium(G, payoffs):
       # Implement the algorithm to find the subgame perfect equilibrium
       # This is a simplified example and may require more sophisticated algorithms
       # for complex games.
       equilibrium = {}
       for node in G.nodes():
           if G.out_degree(node) == 0:
               equilibrium[node] = payoffs[node]
       return equilibrium

   equilibrium = find_subgame_perfect_equilibrium(G, payoffs)
   print("Subgame Perfect Equilibrium:", equilibrium)
   ```

3. **Deploy the Model:**
   Deploy the model to a production environment. This can be simulated by running the script in a production-like setting.
   ```bash
   python game_theory_lab.py
   ```

4. **Monitor the Deployment:**
   Monitor the deployment for any issues or errors. Ensure that the model is running correctly and producing the expected results.

## Exercise 3: Troubleshooting Standard Failure Modes
### Task
Troubleshoot common failure modes that may occur during the deployment and operation of the game-theoretic model.

### Steps
1. **Identify Common Failure Modes:**
   - Incorrect node or edge definitions.
   - Incorrect payoffs assigned to terminal nodes.
   - Errors in the algorithm for finding the subgame perfect equilibrium.
   - Issues with the visualization of the game tree.

2. **Troubleshooting Steps:**
   - Verify that all nodes and edges are correctly defined in the game tree.
   - Check that the payoffs assigned to terminal nodes are correct.
   - Debug the algorithm for finding the subgame perfect equilibrium.
   - Ensure that the visualization of the game tree is correct and that all nodes and edges are properly displayed.

3. **Resolve Issues:**
   Resolve any issues that are identified during the troubleshooting process. Ensure that the model is running correctly and producing the expected results.

## Challenge Exercise (Real-world operational scenario)
### Task
Simulate a real-world decision-making process using the game-theoretic model. The scenario should involve multiple players and multiple decision points, and should be representative of a real-world situation.

### Steps
1. **Define the Scenario:**
   Define a real-world decision-making process that can be modeled using an extensive form game. For example, a business negotiation between two companies.

2. **Define the Players and Actions:**
   Define the players and their possible actions in the game. For example, the two companies can choose to either cooperate or compete.

3. **Define the Payoffs:**
   Define the payoffs for each possible outcome of the game. For example, the payoffs can represent the profit or loss for each company.

4. **Implement the Game Model:**
   Implement the game model using `networkx` and `numpy`.

5. **Find the Subgame Perfect Equilibrium:**
   Use the algorithm for finding the subgame perfect equilibrium to determine the optimal strategy for each player.

6. **Deploy and Monitor the Model:**
   Deploy the model to a production environment and monitor it for any issues or errors. Ensure that the model is running correctly and producing the expected results.

7. **Analyze the Results:**
   Analyze the results of the model and compare them to the real-world scenario. Determine whether the model accurately represents the real-world decision-making process and whether the optimal strategy is realistic.

8. **Iterate and Improve:**
   Iterate and improve the model based on the analysis of the results. Refine the model to better represent the real-world decision-making process and to produce more accurate results.
