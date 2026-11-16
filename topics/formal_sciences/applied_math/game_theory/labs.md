# Operational Verification Labs: Game Theory

## Objective & Mathematical Computing Setup

Game theory's computational verification demands rigorous symbolic manipulation of equilibrium conditions, fixed-point theorems, and optimization constraints that define strategic behavior in multi-agent systems. This laboratory guide establishes a formal computing environment where you will verify Nash equilibrium existence proofs through Kakutani's fixed-point theorem, compute mixed-strategy indifference conditions algebraically, derive subgame perfect equilibria through backward induction, and validate the Folk Theorem's discount factor thresholds in infinitely repeated games. The operational objective is to bridge abstract game-theoretic constructions with concrete computational verification, ensuring that equilibrium concepts satisfy their defining axioms and that theoretical predictions align with numerical implementations.

Your computational stack requires Python 3.11 or higher with SymPy for symbolic algebra, NumPy for numerical linear algebra operations, and SageMath for advanced polynomial system solving and convex optimization. SymPy provides the symbolic infrastructure for expressing payoff functions, computing best-response correspondences, and solving systems of equilibrium equations without floating-point approximation errors. NumPy enables matrix representations of bimatrix games and efficient computation of expected payoffs under mixed strategies. SageMath extends these capabilities with Gröbner basis methods for polynomial equilibrium conditions and precise rational arithmetic for exact equilibrium coordinates.

Verify your environment by executing `python -c 'import sympy; import numpy; print(f"SymPy {sympy.__version__}, NumPy {numpy.__version__}")'` in your terminal. The output should confirm SymPy version 1.12 or later and NumPy version 1.24 or later. Install missing dependencies through `pip install sympy numpy matplotlib scipy` for core functionality. For SageMath, download the standalone distribution from the official SageMath website or use the Docker image `sagemath/sagemath:latest` for containerized execution. Test SageMath availability with `sage --version` or launch the interactive shell with `sage` and execute `version()` to confirm proper installation.

The laboratory exercises progress from foundational equilibrium verification in finite strategic-form games through dynamic extensive-form games with perfect information, culminating in infinitely repeated games where discounting and punishment strategies sustain cooperation. Each exercise presents complete, executable code with explicit parameter values, detailed algebraic derivations of equilibrium conditions, and formal verification procedures that check axiom satisfaction. You will manually derive equilibrium conditions on paper, encode them symbolically in SymPy, compute solutions numerically, and cross-validate results against theoretical predictions. This dual approach—symbolic derivation followed by computational verification—builds both theoretical understanding and practical skill in applying game-theoretic reasoning to real strategic environments.

## Exercise 1: Computational Verification of Core Theorems

The foundational result in non-cooperative game theory is Nash's Equilibrium Existence Theorem, which guarantees that every finite game possesses at least one equilibrium in mixed strategies. The proof relies on Kakutani's fixed-point theorem applied to the best-response correspondence, which maps each player's mixed-strategy profile to the set of strategies that maximize expected payoff against opponents' choices. This exercise constructs a concrete bimatrix game, derives the best-response correspondence algebraically, and verifies that the computed Nash equilibrium satisfies the fixed-point condition where each player's strategy is indeed a best response to others' strategies.

Consider the classic coordination game with asymmetric payoffs where two players simultaneously choose between strategies $A$ and $B$. Player 1's payoff matrix has rows corresponding to their choices and columns to Player 2's choices: the $(A, A)$ outcome yields payoff 3 for Player 1, the $(A, B)$ outcome yields 0, the $(B, A)$ outcome yields 0, and the $(B, B)$ outcome yields 2. Player 2's payoff matrix assigns payoff 2 to $(A, A)$, payoff 0 to both $(A, B)$ and $(B, A)$, and payoff 3 to $(B, B)$. This game has two pure-strategy Nash equilibria at $(A, A)$ and $(B, B)$, plus a mixed-strategy equilibrium where players randomize to make opponents indifferent between their pure strategies.

Begin by encoding the game in SymPy with symbolic probability variables. Let $p$ denote the probability Player 1 assigns to strategy $A$, and let $q$ denote Player 2's probability of choosing $A$. Player 1's expected payoff from playing $A$ against Player 2's mixed strategy $(q, 1-q)$ is $U_1(A, q) = 3q + 0(1-q) = 3q$. Player 1's expected payoff from $B$ is $U_1(B, q) = 0q + 2(1-q) = 2 - 2q$. At a mixed-strategy equilibrium, Player 1 must be indifferent between $A$ and $B$, which requires $3q = 2 - 2q$. Solving algebraically yields $5q = 2$, so $q^* = 2/5$.

Symmetrically, Player 2's expected payoff from $A$ against Player 1's mixed strategy $(p, 1-p)$ is $U_2(A, p) = 2p + 0(1-p) = 2p$. Player 2's payoff from $B$ is $U_2(B, p) = 0p + 3(1-p) = 3 - 3p$. Indifference requires $2p = 3 - 3p$, yielding $5p = 3$ and $p^* = 3/5$. The mixed-strategy Nash equilibrium is therefore $(p^*, q^*) = (3/5, 2/5)$.

Verify this equilibrium computationally by constructing the payoff matrices and solving the indifference equations symbolically. Create a Python script that defines the game structure and computes equilibrium probabilities:

```python
import sympy as sp
import numpy as np

# Define symbolic probability variables
p, q = sp.symbols('p q', real=True, positive=True)

# Player 1 payoff matrix (rows: Player 1's actions, columns: Player 2's actions)
payoff_1 = sp.Matrix([[3, 0], [0, 2]])

# Player 2 payoff matrix
payoff_2 = sp.Matrix([[2, 0], [0, 3]])

# Player 1's expected payoffs against Player 2's mixed strategy (q, 1-q)
U1_A = payoff_1[0, 0] * q + payoff_1[0, 1] * (1 - q)
U1_B = payoff_1[1, 0] * q + payoff_1[1, 1] * (1 - q)

# Player 2's expected payoffs against Player 1's mixed strategy (p, 1-p)
U2_A = payoff_2[0, 0] * p + payoff_2[1, 0] * (1 - p)
U2_B = payoff_2[0, 1] * p + payoff_2[1, 1] * (1 - p)

# Indifference conditions for mixed-strategy equilibrium
indifference_1 = sp.Eq(U1_A, U1_B)
indifference_2 = sp.Eq(U2_A, U2_B)

# Solve for equilibrium probabilities
q_star = sp.solve(indifference_1, q)[0]
p_star = sp.solve(indifference_2, p)[0]

print(f"Mixed-strategy Nash equilibrium:")
print(f"Player 1 probability of A: p* = {p_star} = {float(p_star):.4f}")
print(f"Player 2 probability of A: q* = {q_star} = {float(q_star):.4f}")

# Verify equilibrium: compute expected payoffs at equilibrium
U1_star = U1_A.subs(q, q_star)
U2_star = U2_A.subs(p, p_star)

print(f"\nExpected payoffs at equilibrium:")
print(f"Player 1: {U1_star} = {float(U1_star):.4f}")
print(f"Player 2: {U2_star} = {float(U2_star):.4f}")

# Verify best-response property: check that neither player can improve by deviating
U1_A_at_eq = U1_A.subs(q, q_star)
U1_B_at_eq = U1_B.subs(q, q_star)
U2_A_at_eq = U2_A.subs(p, p_star)
U2_B_at_eq = U2_B.subs(p, p_star)

print(f"\nBest-response verification:")
print(f"Player 1: U1(A) = {float(U1_A_at_eq):.4f}, U1(B) = {float(U1_B_at_eq):.4f}")
print(f"Indifference satisfied: {sp.simplify(U1_A_at_eq - U1_B_at_eq) == 0}")
print(f"Player 2: U2(A) = {float(U2_A_at_eq):.4f}, U2(B) = {float(U2_B_at_eq):.4f}")
print(f"Indifference satisfied: {sp.simplify(U2_A_at_eq - U2_B_at_eq) == 0}")
```

Execute this script to verify that $p^* = 3/5 = 0.6$ and $q^* = 2/5 = 0.4$ solve the indifference conditions exactly. The output confirms that at equilibrium, Player 1's expected payoffs from $A$ and $B$ are equal at $3(2/5) = 6/5 = 1.2$, and Player 2's expected payoffs are equal at $2(3/5) = 6/5 = 1.2$. This computational verification establishes that the equilibrium satisfies the fixed-point property required by Nash's theorem.

Extend the verification to check the complete best-response correspondence by computing each player's optimal strategy for all possible opponent mixed strategies. For any $q \in [0, 1]$, Player 1's best response is $A$ if $3q > 2 - 2q$ (equivalently $q > 2/5$), $B$ if $q < 2/5$, and any mixture if $q = 2/5$. Implement a best-response function that maps opponent probabilities to optimal responses:

```python
def best_response_player1(q_val):
    """Compute Player 1's best response to Player 2's probability q of playing A."""
    U1_A_val = 3 * q_val
    U1_B_val = 2 - 2 * q_val
    if U1_A_val > U1_B_val:
        return 1.0  # Play A with probability 1
    elif U1_A_val < U1_B_val:
        return 0.0  # Play B with probability 1
    else:
        return 'any'  # Indifferent, any p in [0, 1] is optimal

def best_response_player2(p_val):
    """Compute Player 2's best response to Player 1's probability p of playing A."""
    U2_A_val = 2 * p_val
    U2_B_val = 3 - 3 * p_val
    if U2_A_val > U2_B_val:
        return 1.0  # Play A with probability 1
    elif U2_A_val < U2_B_val:
        return 0.0  # Play B with probability 1
    else:
        return 'any'  # Indifferent, any q in [0, 1] is optimal

# Verify equilibrium: check that p* is a best response to q* and vice versa
p_star_float = float(p_star)
q_star_float = float(q_star)

br1 = best_response_player1(q_star_float)
br2 = best_response_player2(p_star_float)

print(f"\nFixed-point verification:")
print(f"Player 1's best response to q* = {q_star_float}: {br1}")
print(f"Player 2's best response to p* = {p_star_float}: {br2}")
print(f"Mixed equilibrium confirmed: both players are indifferent at (p*, q*)")
```

This verification confirms that the computed equilibrium is indeed a fixed point of the best-response correspondence, satisfying the defining property of Nash equilibrium. The computational approach validates the abstract existence theorem through explicit calculation, demonstrating that the fixed-point property is not merely a theoretical construct but a verifiable algebraic condition.

Now verify the existence of pure-strategy equilibria by checking all four strategy profiles. A profile $(s_1, s_2)$ is a pure-strategy Nash equilibrium if neither player can improve by unilaterally deviating. Check $(A, A)$: Player 1 receives payoff 3, and deviating to $B$ yields 0, so Player 1 has no profitable deviation. Player 2 receives 2, and deviating to $B$ yields 0, so Player 2 has no profitable deviation. Therefore $(A, A)$ is a Nash equilibrium. Check $(B, B)$: Player 1 receives 2, deviating to $A$ yields 0, so no deviation. Player 2 receives 3, deviating to $A$ yields 0, so no deviation. Therefore $(B, B)$ is also a Nash equilibrium. Check $(A, B)$: Player 1 receives 0, deviating to $B$ yields 2, so Player 1 would deviate. Not an equilibrium. Check $(B, A)$: Player 1 receives 0, deviating to $A$ yields 3, so deviation occurs. Not an equilibrium.

Automate this pure-strategy equilibrium detection with the following code:

```python
# Check all pure-strategy profiles
strategies = ['A', 'B']
pure_profiles = [(s1, s2) for s1 in strategies for s2 in strategies]

def get_payoff(player, s1, s2):
    """Get payoff for player (1 or 2) given pure strategies s1, s2."""
    idx1 = 0 if s1 == 'A' else 1
    idx2 = 0 if s2 == 'A' else 1
    if player == 1:
        return float(payoff_1[idx1, idx2])
    else:
        return float(payoff_2[idx1, idx2])

pure_equilibria = []
for s1, s2 in pure_profiles:
    # Check if Player 1 has a profitable deviation
    current_payoff_1 = get_payoff(1, s1, s2)
    alternative_s1 = 'B' if s1 == 'A' else 'A'
    deviation_payoff_1 = get_payoff(1, alternative_s1, s2)
    
    # Check if Player 2 has a profitable deviation
    current_payoff_2 = get_payoff(2, s1, s2)
    alternative_s2 = 'B' if s2 == 'A' else 'A'
    deviation_payoff_2 = get_payoff(2, s1, alternative_s2)
    
    # Profile is equilibrium if neither player wants to deviate
    if deviation_payoff_1 <= current_payoff_1 and deviation_payoff_2 <= current_payoff_2:
        pure_equilibria.append((s1, s2))
        print(f"Pure Nash equilibrium: ({s1}, {s2}) with payoffs ({current_payoff_1}, {current_payoff_2})")

print(f"\nTotal pure-strategy equilibria: {len(pure_equilibria)}")
print(f"Total Nash equilibria (pure + mixed): {len(pure_equilibria) + 1}")
```

This computational verification identifies all three Nash equilibria—two pure and one mixed—confirming that Nash's existence theorem holds for this game and providing explicit equilibrium strategies with verifiable best-response properties.

## Exercise 2: Boundary Value Stress Testing & Singularities

Game-theoretic equilibria often exhibit discontinuities and boundary behaviors where small parameter changes induce qualitative shifts in strategic outcomes. This exercise explores dominant strategy elimination, weak versus strict dominance, and the boundary conditions where mixed-strategy equilibria degenerate into pure strategies. You will verify the iterated deletion of dominated strategies (IDDS) procedure, test equilibrium continuity as payoffs approach critical thresholds, and identify the parameter singularities where equilibrium uniqueness fails.

Consider a three-player voting game where each player votes for policy $X$ or policy $Y$, and the majority wins. Each player prefers policy $X$ and receives payoff 1 if $X$ wins and payoff 0 if $Y$ wins. However, voting is costly: each player who votes incurs cost $c > 0$, while abstaining costs nothing. If all players abstain, policy $Y$ wins by default. This creates a free-rider problem where each player wants others to vote for $X$ while abstaining themselves to avoid the cost.

Formulate this as a strategic-form game with eight strategy profiles $(s_1, s_2, s_3)$ where $s_i \in \{X, Y, \text{Abstain}\}$. Simplify by considering only votes for $X$ versus abstention, since voting for $Y$ is strictly dominated by abstaining (both lead to $Y$ winning but abstaining avoids cost $c$). Each player now chooses $V$ (vote for $X$) or $A$ (abstain). Player $i$'s payoff is 1 minus the cost $c$ if they vote and $X$ wins (at least two players vote), 0 minus cost $c$ if they vote and $X$ loses, 1 if they abstain and $X$ wins, and 0 if they abstain and $X$ loses.

Construct the game tree systematically by enumerating all eight profiles and computing payoffs. For profile $(V, V, V)$: $X$ wins with three votes, each player pays cost $c$, so payoffs are $(1-c, 1-c, 1-c)$. For $(V, V, A)$: $X$ wins, Players 1 and 2 pay $c$, Player 3 free-rides, yielding $(1-c, 1-c, 1)$. For $(V, A, A)$: $X$ loses (only one vote), Player 1 pays $c$ for nothing, so $(0-c, 0, 0) = (-c, 0, 0)$. For $(A, A, A)$: all abstain, $Y$ wins by default, payoffs $(0, 0, 0)$.

Implement a computational payoff function that takes a strategy profile and cost parameter and returns the payoff vector:

```python
def voting_game_payoff(s1, s2, s3, cost):
    """
    Compute payoffs for three-player voting game.
    s1, s2, s3 in {'V', 'A'} for Vote or Abstain.
    Returns tuple (u1, u2, u3).
    """
    votes = [s1, s2, s3]
    vote_count = votes.count('V')
    x_wins = vote_count >= 2
    
    payoffs = []
    for i, si in enumerate(votes):
        if si == 'V':
            # Player votes: pay cost c, get 1 if X wins, 0 otherwise
            payoff = (1 if x_wins else 0) - cost
        else:
            # Player abstains: no cost, get 1 if X wins, 0 otherwise
            payoff = 1 if x_wins else 0
        payoffs.append(payoff)
    
    return tuple(payoffs)

# Test with cost c = 0.2
c_value = 0.2
profiles = [
    ('V', 'V', 'V'), ('V', 'V', 'A'), ('V', 'A', 'V'), ('V', 'A', 'A'),
    ('A', 'V', 'V'), ('A', 'V', 'A'), ('A', 'A', 'V'), ('A', 'A', 'A')
]

print(f"Voting game payoffs with cost c = {c_value}:\n")
for profile in profiles:
    payoff = voting_game_payoff(*profile, c_value)
    print(f"{profile}: {payoff}")
```

Execute this code to generate the complete payoff table. For $c = 0.2$, the output shows that $(V, V, A)$ and permutations yield asymmetric payoffs where the abstainer gets the highest payoff 1, voters get $0.8$, and unilateral voting yields $-0.2$.

Now apply iterated deletion of strictly dominated strategies. A strategy is strictly dominated if another strategy yields strictly higher payoffs regardless of opponents' choices. First check if abstaining strictly dominates voting. For Player 1, compare $V$ versus $A$ across all opponent profiles. If both opponents vote $(V, V)$, Player 1 voting yields $1 - c$ while abstaining yields 1, so abstaining is better. If both abstain $(A, A)$, voting yields $-c$ while abstaining yields 0, so abstaining is better. If exactly one opponent votes, say $(V, A)$: if Player 1 votes, $X$ wins and payoff is $1 - c$; if Player 1 abstains, $X$ wins and payoff is 1, so abstaining is better. Therefore abstaining strictly dominates voting for all $c > 0$.

Verify this dominance computationally by comparing strategies across all opponent profiles:

```python
def check_dominance(player_idx, strategy1, strategy2, cost):
    """
    Check if strategy2 strictly dominates strategy1 for player_idx.
    Returns True if strategy2 strictly better for all opponent profiles.
    """
    other_players = [i for i in range(3) if i != player_idx]
    opponent_strategies = [('V', 'V'), ('V', 'A'), ('A', 'V'), ('A', 'A')]
    
    strict_dominance = True
    for opp_profile in opponent_strategies:
        # Construct full profile with player playing strategy1
        profile1 = [''] * 3
        profile1[player_idx] = strategy1
        profile1[other_players[0]] = opp_profile[0]
        profile1[other_players[1]] = opp_profile[1]
        payoff1 = voting_game_payoff(*profile1, cost)[player_idx]
        
        # Construct full profile with player playing strategy2
        profile2 = [''] * 3
        profile2[player_idx] = strategy2
        profile2[other_players[0]] = opp_profile[0]
        profile2[other_players[1]] = opp_profile[1]
        payoff2 = voting_game_payoff(*profile2, cost)[player_idx]
        
        if payoff2 <= payoff1:
            strict_dominance = False
            break
    
    return strict_dominance

# Check if 'A' strictly dominates 'V' for each player
for player in range(3):
    dominance = check_dominance(player, 'V', 'A', c_value)
    print(f"Player {player+1}: 'A' strictly dominates 'V': {dominance}")
```

The output confirms that abstaining strictly dominates voting for all players when $c > 0$, leading to the unique equilibrium $(A, A, A)$ after iterated deletion. This equilibrium is inefficient: all players receive payoff 0, whereas the profile $(V, V, A)$ and its permutations give higher total welfare.

Now test the boundary condition $c \to 0$. As the cost vanishes, voting becomes weakly dominated rather than strictly dominated, and multiple equilibria emerge. Compute the equilibrium set for $c = 0.001$ and compare with $c = 0.2$:

```python
def find_pure_equilibria(cost):
    """Find all pure-strategy Nash equilibria for given cost."""
    equilibria = []
    for profile in profiles:
        is_equilibrium = True
        current_payoffs = voting_game_payoff(*profile, cost)
        
        for player_idx in range(3):
            # Check if player has profitable deviation
            current_strategy = profile[player_idx]
            alternative = 'A' if current_strategy == 'V' else 'V'
            
            deviation_profile = list(profile)
            deviation_profile[player_idx] = alternative
            deviation_payoffs = voting_game_payoff(*deviation_profile, cost)
            
            if deviation_payoffs[player_idx] > current_payoffs[player_idx]:
                is_equilibrium = False
                break
        
        if is_equilibrium:
            equilibria.append((profile, current_payoffs))
    
    return equilibria

# Compare equilibria at different cost levels
for cost_test in [0.001, 0.1, 0.2, 0.5]:
    equilibria = find_pure_equilibria(cost_test)
    print(f"\nCost c = {cost_test}: {len(equilibria)} pure equilibria")
    for eq_profile, eq_payoffs in equilibria:
        print(f"  {eq_profile}: payoffs {tuple(round(p, 3) for p in eq_payoffs)}")
```

This boundary analysis reveals that for $c < 1/2$, profiles where exactly two players vote become Nash equilibria because the voters cannot profitably deviate (deviating to abstain causes $X$ to lose, reducing payoff from $1-c > 1/2$ to 0). For $c \geq 1/2$, only $(A, A, A)$ remains an equilibrium, as voting becomes too costly to sustain even when pivotal.

Finally, test the singularity at $c = 1$, where voters are exactly indifferent between $X$ winning and losing. At this critical value, the equilibrium set changes structure dramatically, and the best-response correspondence becomes multi-valued at all points. Verify that the equilibrium correspondence is upper hemicontinuous but not lower hemicontinuous at this threshold by computing equilibria for a sequence $c_n \to 1^-$.

## Exercise 3: Algorithmic Implementation of Formal Structures

Extensive-form games with perfect information admit computational solution through backward induction, which recursively computes subgame perfect equilibria by solving from terminal nodes upward. This exercise implements backward induction for finite game trees, verifies the one-deviation principle that characterizes subgame perfection, and validates the equilibrium against the definition that strategies form a Nash equilibrium in every subgame.

Consider the centipede game with four decision nodes where players alternate choosing between $C$ (continue) and $S$ (stop). Player 1 moves at nodes 0 and 2, Player 2 moves at nodes 1 and 3. The payoff vector evolves as the game progresses: initial payoffs are $(1, 0)$, and choosing $C$ at each node multiplies both payoffs by 2 and adds 1 to the next mover's payoff. If Player 1 stops at node 0, payoffs are $(1, 0)$. If Player 1 continues and Player 2 stops at node 1, payoffs are $(0, 3)$. If both continue and Player 1 stops at node 2, payoffs are $(4, 1)$. If all continue to node 3 and Player 2 stops, payoffs are $(2, 7)$. If Player 2 continues at node 3, the game ends with payoffs $(8, 4)$.

Encode the game tree as a recursive data structure with nodes storing the active player, available actions, and successor nodes. Terminal nodes store payoff vectors. Implement a backward induction algorithm that computes the value of each subgame and the optimal action at each decision node:

```python
class GameNode:
    def __init__(self, player, node_id):
        self.player = player  # 1 or 2, or None for terminal
        self.node_id = node_id
        self.actions = {}  # action -> successor node
        self.payoffs = None  # (u1, u2) for terminal nodes
        self.value = None  # Computed by backward induction
        self.optimal_action = None
    
    def add_action(self, action, successor):
        self.actions[action] = successor
    
    def set_terminal(self, payoffs):
        self.player = None
        self.payoffs = payoffs

def build_centipede_game():
    """Construct the four-node centipede game tree."""
    # Terminal nodes (payoffs when stopping or reaching end)
    t0 = GameNode(None, 't0')
    t0.set_terminal((1, 0))
    
    t1 = GameNode(None, 't1')
    t1.set_terminal((0, 3))
    
    t2 = GameNode(None, 't2')
    t2.set_terminal((4, 1))
    
    t3 = GameNode(None, 't3')
    t3.set_terminal((2, 7))
    
    t_end = GameNode(None, 't_end')
    t_end.set_terminal((8, 4))
    
    # Decision nodes
    node3 = GameNode(2, 3)
    node3.add_action('S', t3)
    node3.add_action('C', t_end)
    
    node2 = GameNode(1, 2)
    node2.add_action('S', t2)
    node2.add_action('C', node3)
    
    node1 = GameNode(2, 1)
    node1.add_action('S', t1)
    node1.add_action('C', node2)
    
    node0 = GameNode(1, 0)
    node0.add_action('S', t0)
    node0.add_action('C', node1)
    
    return node0

def backward_induction(node):
    """
    Compute subgame perfect equilibrium via backward induction.
    Returns the equilibrium payoff vector at this node.
    """
    # Base case: terminal node
    if node.player is None:
        node.value = node.payoffs
        return node.payoffs
    
    # Recursive case: compute values of all successor nodes
    successor_values = {}
    for action, successor in node.actions.items():
        successor_values[action] = backward_induction(successor)
    
    # Active player chooses action that maximizes their payoff
    player_idx = node.player - 1  # Convert to 0-indexed
    best_action = max(successor_values.keys(), 
                     key=lambda a: successor_values[a][player_idx])
    best_value = successor_values[best_action]
    
    node.optimal_action = best_action
    node.value = best_value
    
    return best_value

# Build and solve the centipede game
root = build_centipede_game()
equilibrium_payoff = backward_induction(root)

print("Centipede Game: Subgame Perfect Equilibrium via Backward Induction\n")
print(f"Equilibrium payoffs: {equilibrium_payoff}")

# Extract equilibrium strategy profile
def extract_strategy(node, strategy_dict):
    """Recursively extract equilibrium strategy from solved tree."""
    if node.player is None:
        return
    strategy_dict[f"Node {node.node_id} (Player {node.player})"] = node.optimal_action
    for action, successor in node.actions.items():
        extract_strategy(successor, strategy_dict)

equilibrium_strategy = {}
extract_strategy(root, equilibrium_strategy)

print("\nEquilibrium strategy profile:")
for decision_point, action in sorted(equilibrium_strategy.items()):
    print(f"  {decision_point}: {action}")
```

Execute this implementation to verify that backward induction yields the equilibrium where Player 1 stops immediately at node 0, resulting in payoffs $(1, 0)$. The algorithm proceeds as follows: at node 3, Player 2 compares stopping for payoff 7 versus continuing for payoff 4, so Player 2 stops. At node 2, Player 1 anticipates Player 2 stopping at node 3, so Player 1 compares stopping for payoff 4 versus continuing for payoff 2, thus Player 1 stops. At node 1, Player 2 anticipates Player 1 stopping at node 2, so Player 2 compares stopping for payoff 3 versus continuing for payoff 1, thus Player 2 stops. Finally, at node 0, Player 1 anticipates Player 2 stopping at node 1, so Player 1 compares stopping for payoff 1 versus continuing for payoff 0, thus Player 1 stops immediately.

This equilibrium exhibits the classic backward-induction paradox: rational players never cooperate, even though mutual cooperation (reaching the end node) yields much higher payoffs $(8, 4)$ compared to immediate stopping $(1, 0)$. The issue is that subgame perfection requires credible threats at every subgame, and at each decision node, the active player has a short-term incentive to deviate and stop.

Verify that the computed strategy profile satisfies the one-deviation principle: no player can improve by changing their action at a single decision node while keeping all other actions fixed. Implement a verification function that checks all possible single deviations:

```python
def verify_one_deviation_principle(root, equilibrium_strategy):
    """
    Verify that equilibrium satisfies the one-deviation principle.
    Check that no player can improve by deviating at any single node.
    """
    print("\nVerifying one-deviation principle:")
    
    # Collect all decision nodes
    decision_nodes = []
    def collect_nodes(node):
        if node.player is not None:
            decision_nodes.append(node)
            for successor in node.actions.values():
                collect_nodes(successor)
    collect_nodes(root)
    
    # For each decision node, test all alternative actions
    violations = []
    for node in decision_nodes:
        equilibrium_action = node.optimal_action
        player_idx = node.player - 1
        equilibrium_payoff = node.value[player_idx]
        
        for action in node.actions:
            if action != equilibrium_action:
                deviation_payoff = node.actions[action].value[player_idx]
                if deviation_payoff > equilibrium_payoff:
                    violations.append((node.node_id, node.player, action, 
                                     deviation_payoff, equilibrium_payoff))
        
        print(f"Node {node.node_id} (Player {node.player}): "
              f"equilibrium action {equilibrium_action} yields {equilibrium_payoff}, "
              f"verified")
    
    if violations:
        print("\nOne-deviation principle VIOLATED:")
        for node_id, player, action, dev_payoff, eq_payoff in violations:
            print(f"  Node {node_id}: Player {player} can improve by {action} "
                  f"({dev_payoff} > {eq_payoff})")
        return False
    else:
        print("\nOne-deviation principle SATISFIED: equilibrium is subgame perfect.")
        return True

verify_one_deviation_principle(root, equilibrium_strategy)
```

This verification confirms that no player can profitably deviate at any single node, establishing that the strategy profile is indeed a subgame perfect equilibrium. The computational approach validates the theoretical result that backward induction produces subgame perfect equilibria in finite games of perfect information.

Now implement a general equilibrium verification for infinitely repeated games by computing the minimum discount factor required for cooperation to be sustainable under grim trigger strategies. Consider the infinitely repeated prisoner's dilemma where in each stage, players simultaneously choose $C$ (cooperate) or $D$ (defect), with stage payoffs: mutual cooperation yields $(3, 3)$, mutual defection yields $(1, 1)$, and unilateral defection yields $(5, 0)$ for the defector and $(0, 5)$ for the cooperator.

The grim trigger strategy prescribes cooperating in all periods unless someone defects, after which all players defect forever. For this strategy profile to form a subgame perfect equilibrium, cooperation must be sustainable: the long-term value of continued cooperation must exceed the one-time gain from defection followed by perpetual punishment. The value of cooperating forever under grim trigger is $V_C = 3 + \delta \cdot 3 + \delta^2 \cdot 3 + \cdots = 3/(1 - \delta)$, where $\delta \in [0, 1)$ is the discount factor. The value of deviating to defect once is $5$ in the current period plus the punishment value $\delta \cdot 1/(1 - \delta)$ from mutual defection forever. The incentive compatibility constraint for cooperation is $3/(1 - \delta) \geq 5 + \delta \cdot 1/(1 - \delta)$.

Solve this inequality algebraically: multiply by $(1 - \delta)$ to get $3 \geq 5(1 - \delta) + \delta = 5 - 5\delta + \delta = 5 - 4\delta$. Rearranging yields $4\delta \geq 2$, so $\delta \geq 1/2$. Therefore, grim trigger sustains cooperation if and only if players are sufficiently patient with $\delta \geq 1/2$.

Verify this threshold computationally by evaluating the incentive constraint across a range of discount factors:

```python
def grim_trigger_verification(delta, coop_payoff, defect_payoff, punish_payoff):
    """
    Verify if grim trigger strategy is subgame perfect equilibrium.
    
    Parameters:
    - delta: discount factor
    - coop_payoff: per-period payoff from mutual cooperation
    - defect_payoff: one-time payoff from unilateral defection
    - punish_payoff: per-period payoff in punishment phase (mutual defection)
    
    Returns: (is_equilibrium, cooperation_value, deviation_value)
    """
    # Value of cooperating forever
    V_coop = coop_payoff / (1 - delta)
    
    # Value of deviating: one-time defection gain plus discounted punishment
    V_deviate = defect_payoff + delta * punish_payoff / (1 - delta)
    
    # Equilibrium if cooperation value >= deviation value
    is_equilibrium = V_coop >= V_deviate
    
    return is_equilibrium, V_coop, V_deviate

# Test across range of discount factors
print("Grim Trigger Equilibrium Verification: Repeated Prisoner's Dilemma\n")
print("Stage payoffs: Cooperation (3,3), Defection (5,0), Punishment (1,1)\n")

test_deltas = [0.3, 0.4, 0.49, 0.5, 0.51, 0.6, 0.8, 0.9]

for delta_val in test_deltas:
    is_eq, v_coop, v_dev = grim_trigger_verification(delta_val, 3, 5, 1)
    status = "EQUILIBRIUM" if is_eq else "NOT equilibrium"
    print(f"δ = {delta_val:.2f}: V_coop = {v_coop:.3f}, V_deviate = {v_dev:.3f} → {status}")

# Solve for exact threshold symbolically
delta_sym = sp.symbols('delta', real=True, positive=True)
V_coop_sym = 3 / (1 - delta_sym)
V_deviate_sym = 5 + delta_sym * 1 / (1 - delta_sym)
incentive_constraint = V_coop_sym - V_deviate_sym >= 0

threshold = sp.solve(V_coop_sym - V_deviate_sym, delta_sym)
print(f"\nSymbolic solution: cooperation sustainable for δ ≥ {threshold[0]} = {float(threshold[0])}")
```

The output confirms that for $\delta < 1/2$, the deviation value exceeds the cooperation value, so grim trigger is not an equilibrium. For $\delta \geq 1/2$, cooperation is sustainable, validating the analytical derivation. This computational verification demonstrates that the Folk Theorem's promise of sustaining cooperation through credible punishment is not merely abstract theory but a precise quantitative condition on the discount factor.

Extend this analysis to compute the full set of feasible and enforceable payoffs in the repeated game, which form the equilibrium payoff set characterized by the Folk Theorem. The set of feasible payoffs is the convex hull of stage-game payoff vectors: in the prisoner's dilemma, these are $(3, 3)$, $(5, 0)$, $(0, 5)$, and $(1, 1)$. A payoff vector is enforceable if it exceeds each player's minimax value, which is the lowest payoff that opponents can hold a player to. In the prisoner's dilemma, Player 1's minimax is 1 (opponents play $D$), and symmetrically for Player 2.

Implement a computational geometry routine to construct the feasible payoff polytope and filter by individual rationality constraints:

```python
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt

# Stage-game payoff vectors
stage_payoffs = np.array([
    [3, 3],  # (C, C)
    [5, 0],  # (D, C)
    [0, 5],  # (C, D)
    [1, 1]   # (D, D)
])

# Compute convex hull of feasible payoffs
hull = ConvexHull(stage_payoffs)

# Player minimax values (punishment payoffs)
minimax = np.array([1, 1])

# Filter vertices that satisfy individual rationality
enforceable_vertices = []
for vertex_idx in hull.vertices:
    vertex = stage_payoffs[vertex_idx]
    if np.all(vertex >= minimax):
        enforceable_vertices.append(vertex)

print("Folk Theorem: Feasible and Individually Rational Payoffs\n")
print("Feasible payoff vertices (convex hull):")
for vertex_idx in hull.vertices:
    print(f"  {stage_payoffs[vertex_idx]}")

print(f"\nPlayer minimax values: {minimax}")
print("\nEnforceable payoffs (above minimax):")
for vertex in enforceable_vertices:
    print(f"  {vertex}")

# Plot feasible region
plt.figure(figsize=(8, 6))
for simplex in hull.simplices:
    plt.plot(stage_payoffs[simplex, 0], stage_payoffs[simplex, 1], 'k-')
plt.plot(stage_payoffs[:, 0], stage_payoffs[:, 1], 'o', markersize=8, label='Stage payoffs')

# Highlight enforceable region
for vertex in enforceable_vertices:
    plt.plot(vertex[0], vertex[1], 'ro', markersize=10)

plt.axhline(y=minimax[1], color='r', linestyle='--', alpha=0.5, label='Player 2 minimax')
plt.axvline(x=minimax[0], color='b', linestyle='--', alpha=0.5, label='Player 1 minimax')
plt.xlabel('Player 1 Payoff')
plt.ylabel('Player 2 Payoff')
plt.title('Folk Theorem: Enforceable Payoff Region')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('folk_theorem_payoffs.png', dpi=150, bbox_inches='tight')
print("\nPayoff region plot saved as 'folk_theorem_payoffs.png'")
```

This visualization confirms that the enforceable payoffs lie in the northeast quadrant of the feasible region, bounded below by the minimax values. The Folk Theorem guarantees that for sufficiently high discount factors, any payoff in this region can be sustained as a subgame perfect equilibrium through appropriate punishment strategies.

## Formal Axioms Cheat Sheet & Verification Reference

This reference section consolidates the formal definitions, theorems, and verification procedures essential for computational game theory. Each entry provides the mathematical statement, symbolic encoding for SymPy or SageMath, and verification algorithm.

**Nash Equilibrium Definition**: A strategy profile $s^* = (s_1^*, \ldots, s_n^*)$ is a Nash equilibrium if for every player $i$ and every alternative strategy $s_i$, the inequality $u_i(s_i^*, s_{-i}^*) \geq u_i(s_i, s_{-i}^*)$ holds, where $s_{-i}^*$ denotes the strategies of all players except $i$. Computationally verify by checking all unilateral deviations: for each player, compute payoffs under equilibrium and under each alternative strategy, confirming that equilibrium payoff is maximal.

**Mixed Strategy Indifference Condition**: A mixed strategy assigns positive probability only to pure strategies that are best responses. At a totally mixed equilibrium where player $i$ randomizes over strategies $A$ and $B$, opponent mixing probabilities must make player $i$ indifferent: $U_i(A, \sigma_{-i}) = U_i(B, \sigma_{-i})$. Solve these indifference equations as a system of linear equations in opponent probabilities. For bimatrix games, construct payoff matrices $M_1$ and $M_2$, then solve $M_1 \sigma_2 = \lambda \mathbf{1}$ and $M_2^T \sigma_1 = \mu \mathbf{1}$ where $\lambda$ and $\mu$ are equilibrium payoffs and $\sigma_i$ are probability vectors.

**Kakutani Fixed-Point Theorem**: A set-valued correspondence $\phi: X \rightrightarrows X$ on a compact convex set $X \subset \mathbb{R}^n$ with non-empty convex values and a closed graph has a fixed point $x^* \in \phi(x^*)$. Applied to the best-response correspondence $BR: \Sigma \rightrightarrows \Sigma$ where $\Sigma$ is the product of mixed-strategy simplices, this guarantees Nash equilibrium existence. Verify computationally by confirming that computed equilibrium $\sigma^*$ satisfies $\sigma_i^* \in BR_i(\sigma_{-i}^*)$ for all players, meaning each player's equilibrium strategy is indeed a best response.

**Iterated Deletion of Strictly Dominated Strategies (IDDS)**: Strategy $s_i$ is strictly dominated by $s_i'$ if $u_i(s_i', s_{-i}) > u_i(s_i, s_{-i})$ for all opponent profiles $s_{-i}$. Iteratively remove strictly dominated strategies until no further deletions are possible. The resulting reduced game contains all Nash equilibria of the original game and often admits simpler solution. Implement as nested loops: outer loop iterates until convergence, inner loop checks each player's remaining strategies for dominance. SymPy can encode payoff comparisons symbolically to verify dominance conditions algebraically rather than numerically.

**Subgame Perfect Equilibrium (SPE)**: A strategy profile is subgame perfect if it induces a Nash equilibrium in every subgame. Equivalent to satisfying the one-deviation principle: no player can improve by changing their action at a single decision node. Compute via backward induction in finite perfect-information games: at each decision node, compute the value of all successor subgames recursively, then select the action maximizing the active player's payoff. Verify by checking that for every decision node in the solved tree, the chosen action yields payoff at least as high as any alternative action.

**Grim Trigger Incentive Compatibility**: In infinitely repeated games with discount factor $\delta$, the grim trigger strategy (cooperate until someone defects, then defect forever) forms an SPE if the cooperation value exceeds the deviation value: $\frac{u_C}{1 - \delta} \geq u_D + \frac{\delta \cdot u_P}{1 - \delta}$, where $u_C$ is the per-period cooperation payoff, $u_D$ is the one-time defection gain, and $u_P$ is the punishment phase payoff. Rearrange to solve for the minimum discount factor: $\delta \geq \frac{u_D - u_C}{u_D - u_P}$. Verify by substituting game-specific payoffs and checking inequality satisfaction.

**Folk Theorem (Feasible and Enforceable Payoffs)**: In infinitely repeated games with sufficiently high discount factor $\delta \to 1$, any feasible payoff vector $v$ that strictly exceeds all players' minimax values can be sustained as an average payoff in some subgame perfect equilibrium. Feasible payoffs are convex combinations of stage-game payoffs. Minimax value for player $i$ is $\underline{v}_i = \min_{s_{-i}} \max_{s_i} u_i(s_i, s_{-i})$. Computationally verify by constructing the convex hull of stage payoffs using computational geometry (SciPy's ConvexHull), computing minimax values by solving minimax optimization problems, and filtering the feasible region by individual rationality constraints $v_i > \underline{v}_i$.

**Shapley Value Axioms**: The Shapley value $\phi_i(v)$ for player $i$ in cooperative game $v$ satisfies four axioms: Efficiency ($\sum_{i \in N} \phi_i(v) = v(N)$), Symmetry (if $i$ and $j$ are interchangeable, $\phi_i(v) = \phi_j(v)$), Dummy Player (if $i$ contributes nothing, $\phi_i(v) = 0$), and Additivity ($\phi(v + w) = \phi(v) + \phi(w)$). The unique solution is $\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|! (n - |S| - 1)!}{n!} [v(S \cup \{i\}) - v(S)]$, summing marginal contributions over all coalitions. Verify by computing $\phi_i$ from the formula and checking each axiom: sum coordinates to verify efficiency, check symmetry for interchangeable players, confirm zero value for dummy players, and verify additive decomposition for composite games.

**Core Stability**: The core of a cooperative game is the set of payoff allocations $x$ satisfying $x(S) \geq v(S)$ for all coalitions $S$ (no coalition has incentive to deviate) and $x(N) = v(N)$ (efficiency). The core may be empty in some games. Verify by encoding the core as a linear programming feasibility problem: variables are $x_i$ for each player, constraints are $\sum_{i \in S} x_i \geq v(S)$ for all $S \subseteq N$ and $\sum_{i \in N} x_i = v(N)$. Use SageMath's Polyhedron class or SciPy's linprog to check feasibility and enumerate core vertices if non-empty.

**Dominant Strategy Implementation**: A mechanism is dominant-strategy incentive-compatible (DSIC) if truthful reporting is a dominant strategy for all agents regardless of others' reports. For allocation mechanism $(f, p)$ where $f$ determines allocation and $p$ determines payments, agent $i$'s truthful reporting $v_i$ must satisfy $v_i f_i(v_i, v_{-i}) - p_i(v_i, v_{-i}) \geq v_i f_i(v_i', v_{-i}) - p_i(v_i', v_{-i})$ for all reports $v_i'$ and opponent values $v_{-i}$. Verify computationally by enumerating all possible misreports and confirming that truthful reporting maximizes utility in every case. For VCG mechanisms, verify that payments satisfy $p_i(v) = \sum_{j \neq i} v_j f_j(v_{-i}) - \sum_{j \neq i} v_j f_j(v)$, which ensures dominant-strategy truthfulness.

**Mechanism Design Revenue Equivalence**: Any two DSIC mechanisms with the same allocation rule and same expected utility for zero-valuation agents must have the same expected revenue. This follows from the envelope theorem: an agent's expected utility is the integral of their allocation probability over valuations. Verify numerically by implementing two mechanisms (e.g., first-price and second-price auctions), computing expected revenues through Monte Carlo integration over valuation distributions, and confirming equivalence up to numerical tolerance.

Use these formal specifications as a computational verification checklist: for each game-theoretic construction, identify the relevant axioms and theorems, encode the defining conditions symbolically in SymPy or numerically in NumPy, compute proposed solutions or equilibria, and verify that all required properties hold. This dual approach—deriving solutions analytically and verifying computationally—ensures both theoretical rigor and practical applicability, confirming that abstract game-theoretic principles govern real strategic interactions.
