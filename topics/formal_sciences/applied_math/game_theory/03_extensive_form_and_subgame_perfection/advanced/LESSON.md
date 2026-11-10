# Advanced Technical Lesson: Game Theory 03 Extensive Form And Subgame Perfection

## 1. Low-Level Internals & Deep Theory (Hardware registers, kernel memory, formal proofs)

### Extensive Form Games
An extensive form game is a representation of a game where the sequence of actions is explicitly modeled. It is often depicted using a game tree, where each node represents a decision point for a player, and each branch represents an action that the player can take. The game tree structure is crucial for understanding the temporal sequence of actions and the information available to players at each decision point.

#### Game Tree Representation
A game tree can be formally defined as a tuple \((N, H, A, Z, u)\), where:
- \(N\) is the set of players.
- \(H\) is the set of histories, where a history is a finite sequence of actions.
- \(A: H \rightarrow 2^A\) is the action function, which specifies the set of actions available at each history.
- \(Z \subseteq H\) is the set of terminal histories, where the game ends.
- \(u: Z \times N \rightarrow \mathbb{R}\) is the payoff function, which assigns a payoff to each player at each terminal history.

### Subgame Perfection
Subgame perfection is a refinement of the Nash equilibrium concept for extensive form games. It requires that players' strategies form a Nash equilibrium in every subgame of the game. A subgame is a part of the game tree that starts at a single node and includes all of its descendants.

#### Definition of Subgame Perfection
A strategy profile \(\sigma\) is a subgame perfect equilibrium if, for every subgame \(G'\) of the game \(G\), the restriction of \(\sigma\) to \(G'\) is a Nash equilibrium of \(G'\).

#### Formal Proof of Subgame Perfection
To formally prove that a strategy profile \(\sigma\) is a subgame perfect equilibrium, we need to verify that for every subgame \(G'\) with set of histories \(H'\), the strategy profile \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\).

**Theorem:** Let \(G = (N, H, A, Z, u)\) be an extensive form game, and let \(\sigma\) be a strategy profile. Then \(\sigma\) is a subgame perfect equilibrium if and only if for every subgame \(G' = (N, H', A', Z', u')\) of \(G\), the restriction \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\).

**Proof:**
1. **Forward Direction:** Assume \(\sigma\) is a subgame perfect equilibrium. By definition, for every subgame \(G'\), \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\).
2. **Backward Direction:** Assume that for every subgame \(G'\), \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\). We need to show that \(\sigma\) is a subgame perfect equilibrium. By definition, this means that \(\sigma\) must be a Nash equilibrium in the original game \(G\). Since every subgame includes the entire game, \(\sigma\) being a Nash equilibrium in every subgame implies it is a Nash equilibrium in \(G\).

## 2. Critical Data Structures, Byte-Level Encodings & Invariants

### Data Structures for Game Trees
To implement extensive form games in a low-level system, such as a kernel or a hardware-based simulation, we need efficient data structures to represent game trees. Common data structures include:

- **Adjacency List:** Represents the game tree as a list of nodes, where each node contains a list of its children.
- **Binary Tree:** If the game tree is binary, a binary tree structure can be used.
- **Trie:** Useful for games with a large number of actions, where each node represents a prefix of a history.

### Byte-Level Encodings
Byte-level encodings are crucial for memory efficiency and performance in low-level systems. For example, actions can be encoded as integers, and histories can be represented as sequences of integers.

### Invariants
Invariants are critical for ensuring the correctness of the implementation. Key invariants for game trees include:
- **Node Invariant:** Each node must have a valid set of actions.
- **History Invariant:** Each history must be a valid sequence of actions.
- **Terminal Invariant:** Each terminal history must have a valid payoff for each player.

## 3. High-Value Advanced Code / Proof Implementation (Exhaustive, production-hardened)

### Example Implementation in C
Below is an example implementation of a simple game tree in C, focusing on memory efficiency and correctness.

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int player;
    int num_actions;
    struct Node** children;
    int* payoffs;
} Node;

Node* create_node(int player, int num_actions) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->player = player;
    node->num_actions = num_actions;
    node->children = (Node**)malloc(num_actions * sizeof(Node*));
    node->payoffs = (int*)malloc(num_actions * sizeof(int));
    return node;
}

void free_node(Node* node) {
    for (int i = 0; i < node->num_actions; i++) {
        free_node(node->children[i]);
    }
    free(node->children);
    free(node->payoffs);
    free(node);
}

int main() {
    // Create a simple game tree
    Node* root = create_node(0, 2);
    root->children[0] = create_node(1, 2);
    root->children[1] = create_node(1, 2);

    root->children[0]->children[0] = create_node(0, 0);
    root->children[0]->children[1] = create_node(0, 0);
    root->children[1]->children[0] = create_node(0, 0);
    root->children[1]->children[1] = create_node(0, 0);

    // Assign payoffs
    root->children[0]->children[0]->payoffs = (int[]){3, 1};
    root->children[0]->children[1]->payoffs = (int[]){0, 0};
    root->children[1]->children[0]->payoffs = (int[]){0, 0};
    root->children[1]->children[1]->payoffs = (int[]){1, 3};

    // Free the game tree
    free_node(root);

    return 0;
}
```

### Formal Proof in LaTeX
Below is a formal proof of subgame perfection in LaTeX.

```latex
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\section{Formal Proof of Subgame Perfection}

\textbf{Theorem:} Let \(G = (N, H, A, Z, u)\) be an extensive form game, and let \(\sigma\) be a strategy profile. Then \(\sigma\) is a subgame perfect equilibrium if and only if for every subgame \(G' = (N, H', A', Z', u')\) of \(G\), the restriction \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\).

\textbf{Proof:}
\begin{enumerate}
    \item \textbf{Forward Direction:} Assume \(\sigma\) is a subgame perfect equilibrium. By definition, for every subgame \(G'\), \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\).
    \item \textbf{Backward Direction:} Assume that for every subgame \(G'\), \(\sigma|_{H'}\) is a Nash equilibrium in \(G'\). We need to show that \(\sigma\) is a subgame perfect equilibrium. By definition, this means that \(\sigma\) must be a Nash equilibrium in the original game \(G\). Since every subgame includes the entire game, \(\sigma\) being a Nash equilibrium in every subgame implies it is a Nash equilibrium in \(G\).
\end{enumerate}

\end{document}
```

## 4. Extreme Failure Domains, Race Conditions, Memory Corruption & Mitigation

### Extreme Failure Domains
In low-level systems, extreme failure domains can arise from incorrect memory management, race conditions, and other concurrency issues. For game tree implementations, these issues can lead to incorrect game states and invalid strategy profiles.

### Race Conditions
Race conditions can occur when multiple threads access and modify shared data concurrently. To mitigate race conditions, synchronization mechanisms such as mutexes and locks can be used.

### Memory Corruption
Memory corruption can occur due to improper memory allocation and deallocation. To prevent memory corruption, it is essential to use memory-safe programming practices, such as bounds checking and avoiding dangling pointers.

### Mitigation Strategies
- **Use of Smart Pointers:** In languages that support smart pointers (e.g., C++), smart pointers can help manage memory automatically and prevent memory leaks.
- **Thread Safety:** Implement thread-safe data structures and use synchronization mechanisms to prevent race conditions.
- **Static Analysis:** Use static analysis tools to detect potential memory leaks and race conditions during the development process.

## 5. Mastery Invariants & Executive Summary

### Mastery Invariants
To master the concepts of extensive form games and subgame perfection, the following invariants must be understood:
- **Game Tree Representation:** Understand how to represent game trees using data structures and ensure that the representation is correct and efficient.
- **Subgame Perfection:** Understand the definition and formal proof of subgame perfection, and be able to apply it to specific games.
- **Low-Level Implementation:** Be proficient in implementing game trees in low-level systems, ensuring memory safety and thread safety.

### Executive Summary
This lesson provided an in-depth exploration of extensive form games and subgame perfection, focusing on low-level internals, critical data structures, and formal proofs. The implementation of game trees in C and the formal proof in LaTeX demonstrated the practical and theoretical aspects of the topic. By understanding and applying the concepts and techniques presented, principal architects, kernel developers, and security researchers can effectively model and analyze strategic interactions in complex systems.
