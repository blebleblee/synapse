# Hands-On Operational Lab: Game Theory

## Objective & Prerequisites

**Objective**: To develop hands-on proficiency in modeling strategic interactions using formal game theory frameworks through operational command-line workflows. Participants will construct, validate, and debug game-theoretic models while developing intuition for equilibrium concepts.

**Prerequisites**:
- Basic understanding of 2-player strategic games
- Familiarity with Python command-line interfaces
- Knowledge of Nash equilibrium concepts
- Basic algebraic manipulation skills
- Python 3.7+ installed (tested environment)

> 💡 *Professor's Note*: This lab emphasizes *operational* rigor over theoretical abstraction. We'll use concrete command-line interactions to build intuition before formal proofs.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify the system's baseline functionality and expected outputs for a standard game.

### Step-by-Step Workflow
1. Create the game theory command-line tool:
```bash
mkdir -p ~/game_theory_lab && cd ~/game_theory_lab
cat > game_theory.py << 'EOF'
import sys

def prisoner_dilemma():
    print("Payoff matrix for Prisoner's Dilemma:")
    print("Player 1: [ [3, 0], [5, 1] ]")
    print("Player 2: [ [3, 5], [0, 1] ]")
    print("Nash Equilibrium: (Defect, Defect)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python game_theory.py --game <game_name>")
        print("Example: python game_theory.py --game prisoner_dilemma")
        sys.exit(1)
    game_name = sys.argv[1]
    if game_name == "prisoner_dilemma":
        prisoner_dilemma()
    else:
        print(f"Game {game_name} not implemented")
EOF
```

2. Verify system state with explicit command:
```bash
python game_theory.py --game prisoner_dilemma
```

### Expected Output
```
Payoff matrix for Prisoner's Dilemma:
Player 1: [ [3, 0], [5, 1] ]
Player 2: [ [3, 5], [0, 1] ]
Nash Equilibrium: (Defect, Defect)
```

### Verification Protocol
| Component          | Expected Output                          | Validation Method                     |
|---------------------|-------------------------------------------|---------------------------------------|
| Payoff Matrix       | Player 1: [[3,0],[5,1]]                  | Direct string comparison             |
| Player 2 Matrix     | [[3,5],[0,1]]                           | Direct string comparison             |
| Nash Equilibrium    | (Defect, Defect)                        | Consistency check with game theory   |

> ✅ *Why this works*: The Prisoner's Dilemma payoff structure is mathematically defined by the condition:  
> $T > R > P > S$ where $T$=temptation, $R$=reward, $P$=punishment, $S$=sucker payoff.  
> Here: $T=5$, $R=3$, $P=1$, $S=0$ → satisfies $T>R>P>S$ → unique Nash equilibrium at (Defect, Defect).

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Model a coordination game and analyze its equilibrium properties through interactive command execution.

### Step-by-Step Workflow
1. **Extend the game model** with a coordination game:
```bash
cat > game_theory.py << 'EOF'
import sys

def prisoner_dilemma():
    print("Payoff matrix for Prisoner's Dilemma:")
    print("Player 1: [ [3, 0], [5, 1] ]")
    print("Player 2: [ [3, 5], [0, 1] ]")
    print("Nash Equilibrium: (Defect, Defect)")

def coordination_game():
    print("Payoff matrix for Coordination Game:")
    print("Player 1: [ [1, 0], [0, 1] ]")
    print("Player 2: [ [1, 0], [0, 1] ]")
    print("Nash Equilibria: (Cooperate, Cooperate), (Defect, Defect)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python game_theory.py --game <game_name>")
        print("Example: python game_theory.py --game coordination")
        sys.exit(1)
    game_name = sys.argv[1]
    if game_name == "prisoner_dilemma":
        prisoner_dilemma()
    elif game_name == "coordination":
        coordination_game()
    else:
        print(f"Game {game_name} not implemented")
EOF
```

2. **Deploy the new game model**:
```bash
python game_theory.py --game coordination
```

3. **Analyze equilibrium properties** (interactive step):
```bash
# Check if (Cooperate, Cooperate) is a Nash equilibrium
python game_theory.py --game coordination | grep "Cooperate"
```

### Expected Output
```
Payoff matrix for Coordination Game:
Player 1: [ [1, 0], [0, 1] ]
Player 2: [ [1, 0], [0, 1] ]
Nash Equilibria: (Cooperate, Cooperate), (Defect, Defect)
```

### Key Insight
The coordination game has **two pure-strategy Nash equilibria**:
- $(Cooperate, Cooperate)$: Payoff $(1,1)$
- $(Defect, Defect)$: Payoff $(0,0)$

> 🔍 *Why this matters*: This demonstrates how game structure determines equilibrium multiplicity. In coordination games, players share common interests but face strategic ambiguity – a critical concept in economics and social choice theory.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce and resolve a critical bug in the game model to develop systematic debugging skills.

### Step-by-Step Workflow
1. **Inject a critical bug** (missing closing bracket):
```bash
cat > game_theory.py << 'EOF'
import sys

def prisoner_dilemma():
    print("Payoff matrix for Prisoner's Dilemma:")
    print("Player 1: [ [3, 0], [5, 1] ]")
    print("Player 2: [ [3, 5], [0, 1] ]")
    print("Nash Equilibrium: (Defect, Defect)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python game_theory.py --game <game_name>")
        print("Example: python game_theory.py --game prisoner_dilemma")
        sys.exit(1)
    game_name = sys.argv[1]
    if game_name == "prisoner_dilemma":
        prisoner_dilemma()
    else:
        print(f"Game {game_name} not implemented")
EOF
```

2. **Trigger failure**:
```bash
python game_theory.py --game prisoner_dilemma
```

3. **Observe error**:
```
Traceback (most recent call last):
  File "game_theory.py", line 10, in <module>
    if game_name == "prisoner_dilemma":
UnboundLocalError: local variable 'game_name' referenced before assignment
```

4. **Analyze failure**:
```bash
# Check variable scope
python -c "print('game_name' in globals())"
```

5. **Fix the bug** (add missing closing bracket):
```bash
cat > game_theory.py << 'EOF'
import sys

def prisoner_dilemma():
    print("Payoff matrix for Prisoner's Dilemma:")
    print("Player 1: [ [3, 0], [5, 1] ]")
    print("Player 2: [ [3, 5], [0, 1] ]")
    print("Nash Equilibrium: (Defect, Defect)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python game_theory.py --game <game_name>")
        print("Example: python game_theory.py --game prisoner_dilemma")
        sys.exit(1)
    game_name = sys.argv[1]
    if game_name == "prisoner_dilemma":
        prisoner_dilemma()
    else:
        print(f"Game {game_name} not implemented")
EOF
```

6. **Verify fix**:
```bash
python game_theory.py --game prisoner_dilemma
```

### Failure Analysis Protocol
| Failure Type        | Root Cause                     | Resolution Strategy               |
|---------------------|---------------------------------|-----------------------------------|
| UnboundLocalError   | `game_name` not defined        | Add `sys.argv[1]` assignment     |
| Syntax Error        | Missing closing bracket        | Validate all brackets in code    |
| Type Mismatch       | Incorrect game name            | Add input validation             |

> 💡 *Professor's Insight*: This bug demonstrates how **variable scoping** and **command-line argument parsing** are critical in operational game theory implementations. In real-world systems, such errors cause cascading failures in strategic modeling.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem Statement**:  
*Construct a game theory model for the "Stag Hunt" scenario where two hunters must choose between:*
- *Hunting a stag (requires cooperation)* → payoff $(2,2)$
- *Hunting a rabbit (individual)* → payoff $(1,1)$

*Derive the Nash equilibria using the following steps:*
1. Write the payoff matrix
2. Verify the equilibrium using the command-line tool
3. Explain why this game has *multiple* equilibria
4. Compare with the Prisoner's Dilemma

**Socratic Discussion Prompts**:
1. Why does the Stag Hunt have two equilibria while Prisoner's Dilemma has one?
2. How would you modify the payoff matrix to eliminate the "defect" equilibrium?
3. What real-world systems exhibit this equilibrium structure? (Hint: Consider environmental policy or technology adoption)

**Expected Output Format**:
```markdown
## My Analysis
- Payoff matrix: [ ... ]
- Nash equilibria: [ ... ]
- Key insight: [ ... ]

## Why This Matters
[Your explanation connecting to formal sciences]
```

> 🎯 *Professor's Challenge*: **Prove** that the Stag Hunt has exactly two pure-strategy Nash equilibria using the definition:  
> *A strategy profile $s^*$ is a Nash equilibrium if for all players $i$, $u_i(s^*) \geq u_i(s_i, s_{-i}^*)$ for all $s_i$.*

**Submit your analysis** to the AI Tutor for feedback. The system will validate your proof against formal game theory axioms.

---

> ✨ *Final Note from Professor*:  
> "Game theory is not about predicting outcomes – it's about understanding the *structure of strategic reasoning*. In this lab, you've built the tools to move from abstract concepts to operational verification. Remember: **The most powerful game theory models are those that fail predictably**."
