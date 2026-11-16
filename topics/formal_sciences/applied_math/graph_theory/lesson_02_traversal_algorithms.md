# Lesson 2: Traversal Algorithms, Paths, Cycles

## 1. First-Principles Intuition & Invariants

The fundamental problem in graph theory reduces to a single question: given two vertices in a graph, can we reach one from the other, and if so, through which sequence of edges? This question of **reachability** underpins every algorithmic structure we build atop graph representations. Whether we model social networks, transportation systems, circuit topologies, or dependency resolution in software build systems, the capacity to systematically explore vertex neighborhoods and construct paths forms the bedrock of computational reasoning about relational structures.

Graph traversal algorithms provide mechanical procedures for visiting vertices in a systematic order, ensuring that every reachable vertex is discovered exactly once while maintaining structural invariants about the exploration frontier. The two canonical traversal strategies—**depth-first search (DFS)** and **breadth-first search (BFS)**—differ fundamentally in their choice of data structure for managing the exploration frontier, and this seemingly minor implementation detail cascades into profound differences in their computational properties, path optimality guarantees, and applications to cycle detection, topological ordering, and connectivity analysis.

Consider an undirected graph $G = (V, E)$ with vertex set $V$ and edge set $E \subseteq V \times V$. A **walk** in $G$ is a sequence of vertices $v_0, v_1, \ldots, v_k$ where consecutive vertices are adjacent: $(v_i, v_{i+1}) \in E$ for all $0 \le i < k$. A **path** is a walk with no repeated vertices. A **cycle** is a closed walk $v_0, v_1, \ldots, v_k, v_0$ where $v_0 = v_k$ and all intermediate vertices are distinct. These definitions extend naturally to directed graphs by respecting edge orientation.

The existence of paths and cycles imposes structural constraints on graphs that traversal algorithms exploit. A graph is **connected** if every pair of vertices admits a path between them. For directed graphs, we distinguish between **weakly connected** (the underlying undirected graph is connected) and **strongly connected** (every ordered pair of vertices admits a directed path). The fundamental invariant we maintain during traversal is the **discovery time**: each vertex transitions from undiscovered to discovered exactly once, and the order of discoveries encodes structural information about distances, articulation points, bridges, and cycle membership.

Depth-first search prioritizes exploration depth over breadth, following edges as deeply as possible before backtracking. This strategy naturally aligns with recursive decomposition and stack-based computation, making DFS the canonical choice for problems involving topological structure, cycle detection, and component analysis. In contrast, breadth-first search explores vertices in order of increasing distance from a source vertex, maintaining a wavefront that advances uniformly outward. This level-by-level expansion guarantees shortest-path optimality in unweighted graphs and provides the foundation for more sophisticated shortest-path algorithms in weighted graphs.

The time complexity of both DFS and BFS admits a tight bound of $O(|V| + |E|)$ when graphs are represented using adjacency lists. This linearity arises because each vertex is discovered exactly once, and during its processing, we examine each incident edge exactly once (twice for undirected graphs, counted from both endpoints). The space complexity differs: DFS requires $O(|V|)$ space for the recursion stack (or explicit stack in iterative implementations), bounded by the graph's diameter in the worst case, while BFS requires $O(|V|)$ space for the queue, bounded by the maximum breadth of any level.

The distinction between DFS and BFS extends beyond complexity analysis to the structural properties of the spanning trees they produce. A **spanning tree** of a connected graph $G$ is a subgraph $T = (V, E')$ where $E' \subseteq E$ and $T$ is a tree containing all vertices of $G$. The DFS spanning tree exhibits **back edges**—edges connecting a vertex to its ancestor in the tree—whose presence characterizes cycles in the graph. The BFS spanning tree exhibits **cross edges** and **forward edges** but maintains the critical property that edges connect vertices in the same or adjacent levels, enabling shortest-path reconstruction.

## 2. Core Architecture & Mechanics

The depth-first search algorithm maintains three vertex states: **white** (undiscovered), **gray** (discovered but not finished), and **black** (finished, all descendants explored). This tripartite coloring scheme enables precise tracking of the exploration frontier and immediate detection of back edges, which indicate cycles in directed graphs. We associate with each vertex $v$ a discovery time $d[v]$ and a finishing time $f[v]$, both monotonically increasing as the algorithm progresses. The interval $[d[v], f[v]]$ represents the lifespan of $v$ on the recursion stack, and the nested structure of these intervals encodes the tree topology.

The DFS procedure begins with all vertices colored white. For each white vertex $u$ encountered during the outer loop, we invoke a recursive exploration subroutine that colors $u$ gray, records its discovery time, recursively visits all white neighbors, and finally colors $u$ black upon completion. The recursive structure naturally implements backtracking: when we exhaust all neighbors of a vertex, we return to its parent and continue exploring siblings.

```
DFS(G):
    for each vertex u in V:
        color[u] = WHITE
        parent[u] = NIL
    time = 0
    
    for each vertex u in V:
        if color[u] == WHITE:
            DFS-Visit(G, u)

DFS-Visit(G, u):
    time = time + 1
    d[u] = time
    color[u] = GRAY
    
    for each vertex v in Adj[u]:
        if color[v] == WHITE:
            parent[v] = u
            DFS-Visit(G, v)
        else if color[v] == GRAY:
            // Back edge detected: (u, v) forms a cycle
            report cycle
    
    color[u] = BLACK
    time = time + 1
    f[u] = time
```

The classification of edges during DFS reveals deep structural properties. A **tree edge** $(u, v)$ is traversed during the first discovery of $v$ from $u$. A **back edge** $(u, v)$ connects a vertex to an ancestor in the DFS tree, characterized by $d[v] < d[u] < f[u] < f[v]$. A **forward edge** $(u, v)$ connects a vertex to a descendant, with $d[u] < d[v] < f[v] < f[u]$. A **cross edge** $(u, v)$ connects vertices in different subtrees, satisfying $d[v] < f[v] < d[u] < f[u]$. In undirected graphs, only tree edges and back edges exist, because edge $(u, v)$ is explored from both endpoints.

The fundamental theorem of DFS states: **A directed graph $G$ is acyclic if and only if a DFS of $G$ yields no back edges.** The proof follows directly from the observation that a back edge $(u, v)$ implies a path from $v$ to $u$ in the DFS tree combined with the edge $(u, v)$ forms a directed cycle. Conversely, any cycle must contain at least one back edge, because the first vertex on the cycle discovered by DFS has all other cycle vertices as descendants, forcing at least one edge to point back to an ancestor.

Breadth-first search replaces the recursion stack with an explicit queue, fundamentally altering the exploration order. BFS discovers vertices in order of increasing distance from a source vertex $s$, where distance $\delta(s, v)$ denotes the minimum number of edges in any path from $s$ to $v$. The algorithm maintains a queue $Q$ of discovered but unprocessed vertices, initializing $Q$ with the source $s$. In each iteration, we dequeue a vertex $u$, examine all its neighbors, and enqueue any undiscovered neighbors, coloring them gray to prevent duplicate enqueueing.

```
BFS(G, s):
    for each vertex u in V \ {s}:
        color[u] = WHITE
        d[u] = ∞
        parent[u] = NIL
    
    color[s] = GRAY
    d[s] = 0
    parent[s] = NIL
    Q = empty queue
    Enqueue(Q, s)
    
    while Q is not empty:
        u = Dequeue(Q)
        for each vertex v in Adj[u]:
            if color[v] == WHITE:
                color[v] = GRAY
                d[v] = d[u] + 1
                parent[v] = u
                Enqueue(Q, v)
        color[u] = BLACK
```

The correctness of BFS rests on the **shortest-path optimality invariant**: when we dequeue a vertex $u$ with distance $d[u]$, no undiscovered vertex $w$ satisfies $\delta(s, w) < d[u]$. This follows inductively from the queue property. Suppose we have just dequeued $u$ with $d[u] = k$. All vertices at distance less than $k$ have been dequeued and colored black. All vertices at distance exactly $k$ are either black or gray (in the queue). When we examine neighbors of $u$, any white neighbor $v$ has distance $\delta(s, v) = k + 1$, and we set $d[v] = d[u] + 1 = k + 1$ correctly. The queue ensures we process all distance-$k$ vertices before any distance-$(k+1)$ vertex.

The parent pointers maintained during traversal enable **path reconstruction**. Starting from a target vertex $v$ and following parent links backward to the source $s$ yields the vertices of a shortest path in reverse order. For DFS, the parent pointers define the DFS spanning tree, but the paths in this tree are not necessarily shortest paths. For BFS, the parent tree is a **shortest-path tree** rooted at $s$: the unique path from $s$ to any vertex $v$ in the tree is a shortest path in $G$.

**Cycle detection** exploits the temporal structure of DFS. In an undirected graph, we detect a cycle when we encounter an edge $(u, v)$ where $v$ is gray but not the parent of $u$. This indicates that $v$ is an ancestor of $u$ in the DFS tree, and the tree path from $v$ to $u$ combined with edge $(u, v)$ forms a cycle. In directed graphs, any back edge immediately certifies a cycle. To extract the actual cycle, we trace parent pointers from $u$ back to $v$, collecting the cycle vertices.

**Topological ordering** of a directed acyclic graph (DAG) $G = (V, E)$ is a linear ordering of vertices such that for every edge $(u, v) \in E$, vertex $u$ precedes $v$ in the ordering. Topological orderings exist if and only if $G$ is acyclic. The DFS-based topological sort algorithm runs DFS on $G$ and outputs vertices in reverse order of their finishing times. The correctness follows from the key observation: for any edge $(u, v)$ in a DAG, the finishing time $f[u]$ exceeds $f[v]$. If $v$ is discovered before $u$, it must finish before $u$ is discovered (otherwise we would have a back edge). If $u$ is discovered before $v$, then $v$ is a descendant of $u$ and finishes before $u$ finishes. Thus, ordering vertices by decreasing finishing time respects all edge directions.

```
Topological-Sort(G):
    run DFS(G) to compute finishing times f[v] for all v
    as each vertex is finished, insert it at the head of a linked list
    return the linked list of vertices
```

The **Eulerian path** problem asks whether a graph contains a path visiting every edge exactly once. Leonard Euler's solution to the Königsberg bridge problem established the foundational result: a connected undirected graph has an Eulerian path if and only if it has exactly zero or two vertices of odd degree. If all vertices have even degree, an Eulerian **circuit** (a closed Eulerian path) exists. The proof constructs the path algorithmically: starting at an odd-degree vertex (or any vertex if all degrees are even), we follow edges, removing them as we traverse, until we return to the start. If any edges remain, we find a vertex on the current path with unused edges, recursively construct a subcircuit from that vertex, and splice it into the main path. The degree parity constraint ensures this process terminates with all edges traversed.

For directed graphs, an Eulerian path exists if and only if the graph is connected (in the underlying undirected sense) and every vertex has equal in-degree and out-degree, except for at most two vertices: one with out-degree exceeding in-degree by one (the start) and one with in-degree exceeding out-degree by one (the end). The algorithmic construction mirrors the undirected case, respecting edge orientations.

The **Hamiltonian path** problem asks whether a graph contains a path visiting every vertex exactly once. Unlike the Eulerian case, no efficient characterization exists: determining Hamiltonian path existence is NP-complete. However, several sufficient conditions provide partial results. **Dirac's theorem** states that if $G$ is a simple graph with $n \ge 3$ vertices and every vertex has degree at least $n/2$, then $G$ contains a Hamiltonian cycle. **Ore's theorem** relaxes this to: if for every pair of non-adjacent vertices $u$ and $v$, the sum of their degrees satisfies $\deg(u) + \deg(v) \ge n$, then $G$ contains a Hamiltonian cycle.

The proof of Dirac's theorem proceeds by contradiction and path extension. Assume $G$ satisfies the degree condition but contains no Hamiltonian cycle. Let $P = v_1, v_2, \ldots, v_k$ be a longest path in $G$. If $k = n$, adding edge $(v_n, v_1)$ (which must exist by the degree condition) yields a Hamiltonian cycle, contradicting our assumption. Thus $k < n$. Vertex $v_1$ has at least $n/2$ neighbors, all of which lie on $P$ (else we could extend $P$). Similarly, $v_k$ has at least $n/2$ neighbors on $P$. Consider the set $S$ of indices $i$ such that $(v_1, v_{i+1}) \in E$ and $(v_k, v_i) \in E$. The size of $S$ satisfies $|S| \ge \deg(v_1) + \deg(v_k) - k \ge n/2 + n/2 - k = n - k > 0$. Thus there exists an index $i \in S$, and we construct the cycle $v_1, v_2, \ldots, v_i, v_k, v_{k-1}, \ldots, v_{i+1}, v_1$, contradicting the absence of a Hamiltonian cycle.

## 3. High-Performance Optimization & Failure Modes

The practical implementation of traversal algorithms demands careful attention to data structure selection and memory access patterns. Adjacency list representations using dynamic arrays or linked lists provide $O(1)$ amortized access to neighbors, but pointer chasing incurs cache misses for sparse graphs with dispersed vertex indices. For dense graphs where $|E| \approx |V|^2$, adjacency matrix representations enable $O(1)$ edge existence queries at the cost of $O(|V|^2)$ space. Hybrid representations using compressed sparse row (CSR) format store edge lists contiguously in memory, improving cache locality while maintaining linear space usage.

In BFS, the queue implementation critically impacts performance. Naive linked-list queues incur allocation overhead for each enqueue operation. Circular array-based queues with power-of-two sizes enable efficient modular indexing using bitwise AND operations. For very large graphs, out-of-core BFS algorithms partition the graph across disk or distributed memory, processing vertices in batches and maintaining frontier sets compactly using bitmap representations or Bloom filters for duplicate detection.

DFS recursion depth poses stack overflow risks for graphs with large diameter. Iterative DFS using an explicit stack avoids system stack limits and enables finer control over memory allocation. The stack stores vertex-iterator pairs $(u, \text{iter})$ representing the current position in the adjacency list of $u$, allowing resumption after recursive returns. This transformation preserves the DFS traversal order while replacing $O(d)$ system stack frames (where $d$ is depth) with a single growable data structure.

```
Iterative-DFS(G, s):
    S = empty stack
    Push(S, (s, iterator to Adj[s]))
    color[s] = GRAY
    
    while S is not empty:
        (u, iter) = Top(S)
        if iter has next vertex v:
            advance iter
            if color[v] == WHITE:
                color[v] = GRAY
                parent[v] = u
                Push(S, (v, iterator to Adj[v]))
        else:
            Pop(S)
            color[u] = BLACK
```

Parallel traversal algorithms partition the exploration frontier across multiple threads or processors, requiring synchronization to prevent race conditions during vertex coloring. Level-synchronous BFS processes each distance level in parallel: all distance-$k$ vertices are explored concurrently, and barriers synchronize before advancing to level $k+1$. Work-stealing parallelism allows threads to dynamically balance load by stealing unexplored vertices from others' local queues. Direction-optimizing BFS switches between top-down (push) and bottom-up (pull) traversal based on frontier size: when the frontier becomes large, checking which unvisited vertices have visited neighbors (pull) can be faster than enumerating neighbors of frontier vertices (push).

Cycle detection in massive graphs benefits from randomized algorithms. A **random walk** starting from vertex $s$ moves to a uniformly random neighbor at each step. If the graph contains a cycle reachable from $s$, a random walk detects it with high probability in time polynomial in $|V|$. For undirected graphs, a random walk of length $O(|V|^3)$ visits every edge with high probability, enabling approximate cycle detection with bounded error. Union-find data structures provide an alternative cycle detection mechanism: for each edge $(u, v)$, check whether $u$ and $v$ belong to the same connected component using Find operations; if so, adding $(u, v)$ creates a cycle. This approach achieves nearly linear time $O(|E| \alpha(|V|))$ where $\alpha$ is the inverse Ackermann function.

Topological sorting failure modes arise when the input graph contains cycles. The DFS-based algorithm detects this condition when encountering a back edge. An alternative algorithm due to Kahn performs topological sorting incrementally by maintaining in-degrees: repeatedly remove vertices with in-degree zero and decrement the in-degrees of their neighbors. If fewer than $|V|$ vertices are removed, the graph contains a cycle. This approach enables online topological sorting where edges are added dynamically, and we maintain a valid ordering by recomputing only the affected subgraph.

```
Kahn-Topological-Sort(G):
    compute in-degree[v] for all vertices v
    Q = queue containing all vertices with in-degree 0
    result = empty list
    
    while Q is not empty:
        u = Dequeue(Q)
        append u to result
        for each vertex v in Adj[u]:
            in-degree[v] = in-degree[v] - 1
            if in-degree[v] == 0:
                Enqueue(Q, v)
    
    if |result| < |V|:
        report "graph contains a cycle"
    return result
```

The detection of strongly connected components in directed graphs employs Tarjan's algorithm or Kosaraju's algorithm, both leveraging DFS finishing times. Kosaraju's algorithm performs two DFS passes: the first computes finishing times in $G$, and the second explores the transpose graph $G^T$ (with all edges reversed) in decreasing order of finishing times. Each tree in the second DFS forest corresponds to a strongly connected component. The correctness relies on the component graph being acyclic and the property that edges between components in $G^T$ respect the decreasing finishing time order.

Tarjan's algorithm performs a single DFS while maintaining a stack of vertices in the current component and a "low-link" value for each vertex indicating the smallest discovery time reachable from the vertex's subtree. When a vertex's low-link equals its discovery time, all vertices above it on the stack form a strongly connected component. The low-link values propagate back-edge information efficiently, achieving $O(|V| + |E|)$ time with a single pass.

Eulerian path construction using Hierholzer's algorithm builds the path incrementally by traversing edges and maintaining a stack of the current path. When we reach a dead end, we backtrack and explore unused edges from earlier vertices. The algorithm guarantees termination because the degree parity condition ensures we can always return to the starting vertex unless all edges have been used. Practical implementations mark edges as used with bit flags or remove them from adjacency lists, requiring $O(|E|)$ time and space.

Hamiltonian path search reduces to constraint satisfaction or backtracking search, exploring the exponential space of vertex permutations. Pruning techniques include degree constraints (vertices must have at least one unused neighbor), parity arguments (the path must alternate between independent sets in bipartite graphs), and symmetry breaking (fixing the starting vertex). Despite these optimizations, worst-case complexity remains exponential. For special graph classes—trees, complete graphs, bipartite graphs with perfect matchings—polynomial algorithms exist. Dynamic programming on subsets yields $O(2^n n^2)$ time for general graphs using the Held-Karp approach, storing whether a path exists through a subset $S$ ending at vertex $v$.

The interplay between traversal algorithms and graph topology reveals profound structural insights. Trees admit unique paths between vertices and support linear-time diameter computation via two BFS passes. Planar graphs enable face-based traversal using dual graphs. Series-parallel graphs decompose recursively, allowing traversal algorithms to exploit the decomposition tree. Each graph class imposes structural constraints that traversal algorithms exploit for efficiency, transforming intractable general problems into tractable special cases. Mastery of traversal mechanics provides the foundation for advanced algorithms in matching, flow, and optimization, where path existence and cycle structure determine feasibility and optimality conditions.
