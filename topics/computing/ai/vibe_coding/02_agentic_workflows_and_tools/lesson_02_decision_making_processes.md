# Lesson 2: Decision Making Processes

## 1. First-Principles Intuition & Invariants

In the realm of agentic workflows and tools, decision-making processes are foundational to the autonomy and adaptability of intelligent systems. These processes enable machines to navigate complex environments, learn from interactions, and make optimal choices. At the heart of these processes lie algorithms and models that encapsulate the essence of decision-making, such as reinforcement learning and decision trees. To understand these mechanisms, we must delve into the theoretical underpinnings and the mathematical invariants that govern their behavior.

Reinforcement learning (RL) is a paradigm within machine learning where an agent learns to make decisions by interacting with an environment. The agent receives feedback in the form of rewards or penalties, which guide its actions towards maximizing cumulative reward over time. This process is inherently iterative, with the agent continuously refining its policy—a strategy that maps states to actions—based on the outcomes of its actions. The mathematical invariant in RL is the Bellman equation, which expresses the relationship between the value of a state and the expected future rewards. The Bellman equation is a recursive formula that captures the essence of optimal decision-making in a Markov decision process (MDP):

V(s) = max_a sum_{s'} P(s'|s,a) [R(s,a,s') + gamma V(s')]

Here, V(s) is the value of state s, a is an action, P(s'|s,a) is the transition probability from state s to state s' under action a, R(s,a,s') is the reward received for transitioning from state s to state s' under action a, and gamma is the discount factor that determines the importance of future rewards.

Decision trees, on the other hand, are a class of algorithms used for classification and regression tasks. They operate by partitioning the input space into regions based on feature values, and assigning a decision or prediction to each region. The core invariant in decision trees is the greedy algorithm that selects the feature and threshold that best separates the data at each node. This separation is typically measured using criteria such as information gain, Gini impurity, or variance reduction. The decision tree is constructed recursively, with each node representing a decision based on a feature, and each branch representing the outcome of that decision. The leaves of the tree represent the final decisions or predictions.

Both reinforcement learning and decision trees are grounded in the principles of optimization and decision theory. They provide a framework for making decisions in uncertain and dynamic environments, and they rely on mathematical invariants to ensure that the decisions are optimal or near-optimal. Understanding these invariants is crucial for designing and implementing agentic workflows and tools that can make intelligent and adaptive decisions.

## 2. Core Architecture & Mechanics

To dissect the internal data structures, algorithms, and execution models of decision-making processes, we will explore the architecture and mechanics of reinforcement learning and decision trees in detail.

### Reinforcement Learning

Reinforcement learning involves an agent that interacts with an environment to learn a policy that maximizes cumulative reward. The agent's decision-making process is governed by a policy, which is a mapping from states to actions. The policy is updated iteratively based on the agent's experiences, which are represented as state-action-reward-state (SARS) tuples. The core data structures in RL include the state space, action space, reward function, and value function.

The state space represents the set of all possible states that the agent can encounter. Each state is typically represented as a vector of features that describe the environment. The action space represents the set of all possible actions that the agent can take. Each action is typically represented as a discrete or continuous value that specifies the agent's behavior. The reward function maps state-action pairs to scalar rewards, which indicate the desirability of the outcomes. The value function maps states to scalar values, which represent the expected cumulative reward starting from that state.

The execution model of RL involves the agent interacting with the environment in a sequence of episodes. Each episode consists of a sequence of time steps, where the agent observes the current state, selects an action based on the policy, receives a reward from the environment, and transitions to the next state. The agent's goal is to learn a policy that maximizes the expected cumulative reward over all episodes. This is achieved through iterative updates to the policy based on the agent's experiences.

One popular algorithm for RL is Q-learning, which is a model-free algorithm that learns the action-value function, also known as the Q-function. The Q-function maps state-action pairs to scalar values, which represent the expected cumulative reward starting from that state and taking that action. The Q-learning algorithm updates the Q-function iteratively using the Bellman equation:

Q(s, a) = Q(s, a) + alpha [r + gamma max_{a'} Q(s', a') - Q(s, a)]

Here, Q(s, a) is the Q-value of state-action pair (s, a), alpha is the learning rate, r is the reward received for transitioning from state s to state s' under action a, and gamma is the discount factor. The Q-learning algorithm selects actions based on the Q-values using an exploration-exploitation strategy, such as epsilon-greedy or softmax.

### Decision Trees

Decision trees are a class of algorithms used for classification and regression tasks. They operate by partitioning the input space into regions based on feature values, and assigning a decision or prediction to each region. The core data structures in decision trees include the feature space, decision nodes, and leaf nodes.

The feature space represents the set of all possible feature values that the input data can take. Each feature is typically represented as a continuous or discrete value that describes a characteristic of the input data. The decision nodes represent the decisions based on feature values. Each decision node is associated with a feature and a threshold, and it has branches that represent the possible outcomes of the decision. The leaf nodes represent the final decisions or predictions. Each leaf node is associated with a class label or a regression value.

The execution model of decision trees involves constructing the tree recursively based on the input data. The tree is constructed by selecting the feature and threshold that best separates the data at each node. This separation is typically measured using criteria such as information gain, Gini impurity, or variance reduction. The feature and threshold selection process is repeated recursively until a stopping criterion is met, such as reaching a maximum tree depth or achieving a minimum number of samples per leaf node.
