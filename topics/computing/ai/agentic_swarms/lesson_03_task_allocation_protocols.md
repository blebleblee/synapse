# Lesson 3: Task Allocation Protocols

## 1. First-Principles Intuition & Invariants

The central problem in any multi-agent system is deceptively simple to state and genuinely hard to solve: given a set of tasks and a set of agents, which agent should do which task, decided by whom, at what moment, and according to what criteria? This question, in its full generality, is a variant of the assignment problem first formalized by Harold Kuhn in 1955 as the Hungarian algorithm — a polynomial-time solution to bipartite matching that optimizes a cost matrix. But the Hungarian algorithm assumes a static world: all tasks are known in advance, all agents are identical in capability, costs are deterministic, and no agent will fail mid-execution. An agentic swarm violates every one of these assumptions simultaneously. Tasks arrive in streams. Agents are heterogeneous specialists. Costs are probabilistic estimates derived from prior execution traces. Agents crash, stall, or return incorrect results. The allocation protocol is therefore not a one-shot optimization but a continuous, adaptive control loop running over a distributed system whose topology, capability distribution, and workload are all in flux.

Understanding why allocation is hard requires grounding the problem in information theory before touching any implementation. At the moment of allocation, the orchestrating system holds an estimate of each agent's capability vector, its current utilization, and the task's resource and skill requirements. These estimates are inherently noisy. An agent that completed ten NLP summarization tasks successfully may still fail on the eleventh if the input text contains adversarial tokens that exceed its context window, or if the downstream API it depends on returns a 503. The allocator is therefore making decisions under uncertainty about a stochastic system, which places the problem firmly in the domain of Markov Decision Processes. The optimal policy is not the one that minimizes expected cost on a single allocation step but the one that maximizes expected cumulative reward over the lifetime of the swarm's execution horizon — accounting for the opportunity cost of assigning a high-capability agent to a trivial task when a harder task is thirty seconds from arriving.

Three invariants govern every task allocation protocol worth implementing in production, regardless of the specific strategy chosen.

The first is **semantic matching**: a task must be allocated to an agent that possesses the capability to execute it. This sounds obvious but is architecturally non-trivial. Agents in a heterogeneous swarm expose capability manifests — structured declarations of what tools they can invoke, what input schemas they accept, and what output contracts they guarantee. The allocator must maintain an indexed registry of these manifests and perform semantic matching between task requirements and agent capabilities at the moment of dispatch. Failure to enforce this invariant produces silent degradation: an agent receives a task it can partially execute, produces malformed output, and the downstream pipeline proceeds with corrupted state.

The second invariant is **load awareness**: allocation decisions must be conditioned on current agent utilization, not just static capability. An agent that is theoretically capable but processing nine concurrent tasks has degraded effective throughput and elevated latency for any new task assigned to it. The allocator must maintain a live utilization model — whether through heartbeat telemetry, queue depth signals, or probabilistic decay over last-known state — and prefer agents with headroom over agents operating near saturation.

The third invariant is **failure-budget accounting**: every allocation decision implicitly bets a portion of the system's fault tolerance reserve. If the same task is assigned to the only agent capable of executing it, the system has created a single point of failure. A robust allocator tracks redundancy coverage across the task graph and ensures that critical path tasks are either replicated across multiple capable agents or backed by a hot-standby escalation path.

These three invariants interact. Maximizing semantic match quality tends to concentrate assignments on highly capable agents, violating load awareness. Distributing load evenly tends to assign tasks to marginally capable agents, degrading output quality. Maintaining redundancy requires holding capable agents in reserve, reducing throughput. Task allocation is therefore a constrained multi-objective optimization problem, and the specific protocol chosen reflects a deliberate trade-off among these competing pressures.

---

## 2. Core Architecture & Mechanics

### The Allocation Protocol Taxonomy

Task allocation protocols for agentic swarms fall into three architectural families: **centralized hierarchical**, **decentralized flat**, and **market-based auction**. These are not merely organizational patterns — they encode fundamentally different assumptions about where information lives, who makes decisions, and how the system behaves under partial failure.

#### Centralized Hierarchical Allocation

In a hierarchical topology, an orchestrator agent holds the global task graph, maintains the agent registry, and issues allocation decisions as directives. Sub-orchestrators may manage sub-domains, creating a tree of decision authority. The orchestrator receives task completion signals and re-plans continuously.

```
┌───────────────────────────────────────────────────────┐
│                  Root Orchestrator                    │
│  [Task Graph] → [Planner] → [Allocator] → [Monitor]   │
└──────────┬────────────────────────┬───────────────────┘
           │                        │
   ┌───────▼───────┐        ┌───────▼───────┐
   │ Sub-Orch A    │        │ Sub-Orch B    │
   │ (NLP Domain)  │        │ (Code Domain) │
   └──┬────────┬───┘        └──┬────────┬───┘
      │        │               │        │
  ┌───▼──┐ ┌───▼──┐        ┌───▼──┐ ┌───▼──┐
  │Ag-1  │ │Ag-2  │        │Ag-3  │ │Ag-4  │
  └──────┘ └──────┘        └──────┘ └──────┘
```

The critical data structure underpinning this model is the **task graph** — a directed acyclic graph (DAG) where nodes are tasks and edges encode dependencies. Each node carries a task descriptor that specifies the required capability profile, estimated compute cost, priority weight, deadline (if bounded), and input/output schemas. The allocator traverses this DAG in topological order, resolving tasks whose dependencies are already satisfied and whose required capability is available in the agent registry.

A complete Python implementation of this orchestrator core illustrates the mechanics concretely:

```python
from __future__ import annotations

import asyncio
import heapq
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set


class TaskStatus(Enum):
    PENDING = auto()
    READY = auto()
    ASSIGNED = auto()
    COMPLETED = auto()
    FAILED = auto()


class AgentStatus(Enum):
    IDLE = auto()
    BUSY = auto()
    UNREACHABLE = auto()


@dataclass(order=True)
class Task:
    priority: float                           # Lower value = higher priority (min-heap)
    task_id: str = field(compare=False)
    capability_required: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)
    dependencies: Set[str] = field(compare=False, default_factory=set)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    result: Optional[Any] = field(compare=False, default=None)
    assigned_agent: Optional[str] = field(compare=False, default=None)
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)


@dataclass
class Agent:
    agent_id: str
    capabilities: Set[str]
    max_concurrency: int
    active_tasks: Set[str] = field(default_factory=set)
    status: AgentStatus = field(default=AgentStatus.IDLE)
    execute_fn: Optional[Callable[..., Coroutine]] = field(default=None, repr=False)

    @property
    def utilization(self) -> float:
        return len(self.active_tasks) / self.max_concurrency

    @property
    def has_capacity(self) -> bool:
        return len(self.active_tasks) < self.max_concurrency


class HierarchicalOrchestrator:
    """
    Centralized hierarchical task allocator with priority-based scheduling,
    dependency resolution, and retry-aware fault tolerance.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
        self._agents: Dict[str, Agent] = {}
        self._ready_queue: List[Task] = []   # Min-heap by priority
        self._completed: Set[str] = set()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Registry                                                             #
    # ------------------------------------------------------------------ #

    def register_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task
        if not task.dependencies:
            task.status = TaskStatus.READY
            heapq.heappush(self._ready_queue, task)

    def register_agent(self, agent: Agent) -> None:
        self._agents[agent.agent_id] = agent

    # ------------------------------------------------------------------ #
    # Dependency Resolution                                                #
    # ------------------------------------------------------------------ #

    def _resolve_downstream(self, completed_task_id: str) -> None:
        """Promote tasks whose dependencies are now fully satisfied."""
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if completed_task_id in task.dependencies:
                remaining = task.dependencies - self._completed
                if not remaining:
                    task.status = TaskStatus.READY
                    heapq.heappush(self._ready_queue, task)

    # ------------------------------------------------------------------ #
    # Agent Selection: Capability + Load-Aware                            #
    # ------------------------------------------------------------------ #

    def _select_agent(self, capability: str) -> Optional[Agent]:
        """
        Select the least-loaded agent that satisfies the capability
        requirement and has available concurrency capacity.
        """
        candidates = [
            a for a in self._agents.values()
            if capability in a.capabilities
            and a.has_capacity
            and a.status == AgentStatus.IDLE
        ]
        if not candidates:
            return None
        # Sort by utilization ascending; prefer least loaded agent
        candidates.sort(key=lambda a: a.utilization)
        return candidates[0]

    # ------------------------------------------------------------------ #
    # Allocation & Execution Loop                                          #
    # ------------------------------------------------------------------ #

    async def _dispatch(self, task: Task, agent: Agent) -> None:
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent = agent.agent_id
        agent.active_tasks.add(task.task_id)
        if len(agent.active_tasks) >= agent.max_concurrency:
            agent.status = AgentStatus.BUSY

        try:
            assert agent.execute_fn is not None, (
                f"Agent {agent.agent_id} has no execute_fn registered"
            )
            result = await asyncio.wait_for(
                agent.execute_fn(task.task_id, task.payload),
                timeout=60.0,
            )
            async with self._lock:
                task.result = result
                task.status = TaskStatus.COMPLETED
                self._completed.add(task.task_id)
                agent.active_tasks.discard(task.task_id)
                agent.status = AgentStatus.IDLE
                self._resolve_downstream(task.task_id)

        except (asyncio.TimeoutError, Exception) as exc:
            async with self._lock:
                agent.active_tasks.discard(task.task_id)
                agent.status = AgentStatus.IDLE
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.READY
                    task.assigned_agent = None
                    heapq.heappush(self._ready_queue, task)
                else:
                    task.status = TaskStatus.FAILED
                    print(f"[ORCHESTRATOR] Task {task.task_id} failed after "
                          f"{task.max_retries} retries: {exc}")

    async def run(self) -> None:
        """Main scheduling loop: drain the ready queue against available agents."""
        while True:
            async with self._lock:
                dispatch_batch: List[tuple[Task, Agent]] = []
                temp_heap: List[Task] = []

                while self._ready_queue:
                    task = heapq.heappop(self._ready_queue)
                    agent = self._select_agent(task.capability_required)
                    if agent is not None:
                        dispatch_batch.append((task, agent))
                    else:
                        temp_heap.append(task)

                for t in temp_heap:
                    heapq.heappush(self._ready_queue, t)

            if dispatch_batch:
                await asyncio.gather(
                    *(self._dispatch(t, a) for t, a in dispatch_batch)
                )
            else:
                await asyncio.sleep(0.05)

            async with self._lock:
                all_terminal = all(
                    t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                    for t in self._tasks.values()
                )
                if all_terminal:
                    break
```

This orchestrator captures the essential mechanics of hierarchical allocation. The `_select_agent` method enforces both semantic matching (capability membership test) and load awareness (utilization-sorted candidate selection). The `_resolve_downstream` method implements topological dependency resolution without requiring a full graph traversal on each step — it only examines tasks that remain pending, and only promotes those whose dependency set becomes empty after recording the latest completion. The retry mechanism implements the failure-budget invariant: tasks are re-queued up to a configured maximum before being marked terminal failures, allowing the system to absorb transient agent failures without immediate escalation.

#### Decentralized Flat Topology: Contract Net Protocol

The hierarchical model's strength — global visibility — is also its weakness. The orchestrator is a bottleneck and a single point of failure. As swarm scale grows beyond dozens of agents, the orchestrator's scheduling loop becomes a latency sink, and its state becomes a consistency challenge in the face of network partitions. The decentralized alternative eliminates the central authority entirely by having agents negotiate task ownership among themselves through a **Contract Net Protocol (CNP)**, originally formalized by Reid Smith in 1980 and subsequently adopted into the FIPA agent communication standards.

In CNP, a manager agent (which may itself be an executor on other tasks) broadcasts a **call for proposals (CFP)** announcement when it has a task requiring allocation. Agents that receive the CFP and possess the required capability evaluate their own current load and willingness to accept, then respond with a **bid** encoding their estimated execution cost and latency. The manager collects bids within a time window, selects the winning bid using a scoring function, issues an **award** to the winning agent, and sends **reject** notifications to others. The winning agent confirms acceptance and executes.

```
Manager                 Agent-1              Agent-2              Agent-3
   │                      │                    │                    │
   │── CFP(task_id) ──────►│                    │                    │
   │── CFP(task_id) ───────────────────────────►│                    │
   │── CFP(task_id) ────────────────────────────────────────────────►│
   │                      │                    │                    │
   │◄── BID(cost=0.3) ────│                    │                    │
   │◄── BID(cost=0.6) ─────────────────────────│                    │
   │                      │               [no capability:           │
   │                      │                silent drop]             │
   │                      │                    │                    │
   │── AWARD(agent-1) ───►│                    │                    │
   │── REJECT(agent-2) ──────────────────────► │                    │
   │                      │                    │                    │
   │◄── CONFIRM ──────────│                    │                    │
   │                      │                    │                    │
   │                   [execute]               │                    │
   │                      │                    │                    │
   │◄── RESULT ───────────│                    │                    │
```

The CNP is elegant but introduces several failure modes that a naive implementation will discover under production load. The bidding window creates a hard latency floor: the manager must wait for the window to close before awarding, which adds hundreds of milliseconds to allocation latency even when the winning agent responds immediately. Adaptive window sizing — contracting the window when bids arrive from all reachable capable agents, extending it when only partial coverage is received — mitigates this at the cost of implementation complexity. Additionally, the manager itself is an availability dependency; if it crashes after issuing CFPs but before collecting bids, the task is orphaned. A robust CNP implementation therefore requires the manager to persist the task state to durable storage before broadcasting, enabling recovery by a replacement manager.

#### Auction-Based Allocation: Combinatorial and VCG Mechanisms

Market-based allocation extends the CNP concept by introducing formal auction mechanisms that optimize for global efficiency rather than bilateral negotiation. The simplest market mechanism is an **English auction**, where the winning agent is the one that bids the lowest execution cost (treating cost as negative value). This is straightforward but ignores the combinatorial structure of task bundles: an agent that can execute tasks A and B together may exploit shared context and complete both for less than the sum of their individual costs, but a single-task auction never surfaces this synergy.

**Combinatorial auctions** address this by allowing agents to submit bundle bids that express package pricing across multiple tasks. The allocator then solves the **winner determination problem** — finding the allocation of bundles to agents that maximizes total utility subject to each task being assigned exactly once. Unfortunately, the winner determination problem is NP-complete in the general case, which makes exact combinatorial auctions impractical at scale. In production swarms, this is typically addressed through two pragmatic approximations: restricting bundle size (agents may bid on packages of at most $k$ tasks, where $k$ is small, commonly 2 or 3), or using greedy iterative auctions that sequentially award the highest-scoring bid in each round and remove awarded tasks from subsequent rounds.

The theoretically principled solution is the **Vickrey-Clarke-Groves (VCG) mechanism**, which guarantees truthful bidding as a dominant strategy — agents maximize their expected payoff by reporting their true execution costs rather than strategically shading bids. VCG works by paying each winning agent not what it bid, but the opportunity cost its participation imposed on others: the difference between the total social welfare achievable without that agent and the welfare achieved with it. This eliminates the incentive to underbid (take on tasks cheaply and then fail or deliver low quality) because the payment is decoupled from the bid itself. For multi-agent systems where agents are autonomously optimizing their own execution portfolio, VCG's incentive compatibility property is architecturally important — it means the allocation mechanism is robust to self-interested agents operating under incomplete information.

The practical limitation of VCG at swarm scale is computational: computing the counterfactual social welfare without each winning agent requires solving the winner determination problem repeatedly, once per winner. For swarms of tens of agents executing hundreds of concurrent tasks, this remains tractable. At the scale of large multi-agent pipelines with thousands of micro-tasks, approximate VCG variants or simpler scoring functions become necessary.

```python
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Bid:
    agent_id: str
    task_id: str
    estimated_cost: float        # Lower is better (execution cost estimate)
    estimated_latency_ms: float
    capability_confidence: float  # 0.0–1.0: self-reported execution confidence
    timestamp: float = field(default_factory=time.monotonic)


@dataclass
class AuctionTask:
    task_id: str
    capability_required: str
    payload: Dict[str, Any]
    priority: float
    cfp_deadline: float          # Absolute monotonic time when bidding closes


class AuctionAllocator:
    """
    Single-task sealed-bid auction with weighted scoring.
    Score = (1/cost) * confidence * priority_weight - latency_penalty
    """

    def __init__(
        self,
        bid_window_seconds: float = 0.5,
        latency_weight: float = 0.001,
    ) -> None:
        self._bid_window = bid_window_seconds
        self._latency_weight = latency_weight
        self._open_auctions: Dict[str, AuctionTask] = {}
        self._bid_registry: Dict[str, List[Bid]] = {}
        self._award_callbacks: Dict[str, asyncio.Future] = {}

    def _score_bid(self, bid: Bid, task: AuctionTask) -> float:
        if bid.estimated_cost <= 0:
            return float("-inf")
        throughput_score = (1.0 / bid.estimated_cost) * bid.capability_confidence
        latency_penalty = bid.estimated_latency_ms * self._latency_weight
        return task.priority * throughput_score - latency_penalty

    async def run_auction(
        self,
        task: AuctionTask,
        broadcast_cfp: Any,          # Callable: async (task_id, capability) -> None
        notify_award: Any,           # Callable: async (agent_id, task_id) -> None
        notify_reject: Any,          # Callable: async (agent_id, task_id) -> None
    ) -> Optional[str]:
        """
        Broadcast CFP, collect bids within the window, award the winner.
        Returns the winning agent_id, or None if no bids were received.
        """
        self._open_auctions[task.task_id] = task
        self._bid_registry[task.task_id] = []

        await broadcast_cfp(task.task_id, task.capability_required, task.payload)
        await asyncio.sleep(self._bid_window)

        bids = self._bid_registry.pop(task.task_id, [])
        self._open_auctions.pop(task.task_id, None)

        if not bids:
            return None

        scored = sorted(bids, key=lambda b: self._score_bid(b, task), reverse=True)
        winner = scored[0]

        await notify_award(winner.agent_id, task.task_id)
        reject_coros = [
            notify_reject(b.agent_id, task.task_id)
            for b in scored[1:]
        ]
        if reject_coros:
            await asyncio.gather(*reject_coros)

        return winner.agent_id

    def receive_bid(self, bid: Bid) -> bool:
        """Called when an agent submits a bid for an open auction."""
        if bid.task_id not in self._open_auctions:
            return False
        task = self._open_auctions[bid.task_id]
        if time.monotonic() > task.cfp_deadline:
            return False
        self._bid_registry[bid.task_id].append(bid)
        return True
```

The scoring function in this implementation expresses a deliberate trade-off. High-confidence, low-cost agents on high-priority tasks earn the best scores, while latency is penalized proportionally through the `latency_weight` coefficient. In practice, the values of these weights should be tuned against empirical execution traces rather than set by intuition — a swarm processing latency-sensitive real-time tasks needs a higher `latency_weight` than one processing batch analytics workloads where throughput dominates.

---

## 3. High-Performance Optimization & Failure Modes

### Locality-Aware Allocation and Context Reuse

A dimension of allocation efficiency that swarm implementations routinely underweight is **context locality**. Many LLM-backed agents maintain soft state: a loaded vector index, a warmed KV cache, an open database connection, or an active session with a downstream tool. Allocating a semantically similar task to the same agent that just completed a related task can dramatically reduce execution latency by exploiting this warm state. This is conceptually identical to cache-aware scheduling in CPU schedulers, where the kernel prefers to reschedule a thread on the same core that last ran it to exploit L1/L2 cache residency.

Implementing context locality in a task allocator requires a **recency-weighted affinity score** that augments the base utilization score. When an agent completes a task tagged with topic vector $\mathbf{v}_t$, the allocator records this vector against the agent. When a new task with vector $\mathbf{v}_{new}$ arrives, the affinity score for that agent is computed as:

$$\text{affinity}(a, t) = \cos(\mathbf{v}_t, \mathbf{v}_{new}) \cdot e^{-\lambda \cdot \Delta\tau}$$

where $\Delta\tau$ is the elapsed time since the last related task and $\lambda$ is a decay constant reflecting how quickly the warm state degrades (tool connections time out, KV caches are evicted, vector indices are paged out). This affinity score is added to the agent's selection weight, creating a soft preference without overriding capability or capacity constraints.

### Work Stealing for Flat Topologies

In decentralized swarms where agents maintain local task queues, uneven queue depths are inevitable: some agents exhaust their queue while others remain backlogged. **Work stealing** addresses this by allowing idle agents to pull tasks from overloaded peers' queues rather than waiting for new assignments from an allocator. This is the same mechanism underlying Java's `ForkJoinPool` and Go's goroutine scheduler.

The architectural requirement for work stealing in an agentic swarm is a **distributed queue with steal semantics**: each agent maintains a double-ended queue (deque) where new tasks are pushed to the back and self-consumed from the back (LIFO for the owner, to exploit recency locality), while stealing agents pull from the front (FIFO for the thief, to minimize contention on the owner's hot end). Redis `RPOPLPUSH` semantics or a purpose-built LMAX Disruptor-style ring buffer can implement this in distributed deployments. The critical operational concern is preventing cascading steal storms — if many agents become idle simultaneously and all attempt to steal from the same backlogged agent, contention on that agent's queue head can serialize operations and negate the benefit. A randomized victim selection policy (each stealing agent selects a victim uniformly at random from non-empty queues rather than targeting the longest queue) distributes contention effectively.

### Failure Mode: Allocation Thrashing Under Capability Scarcity

One of the most pathological failure modes in production swarms is **allocation thrashing**, which occurs when the demand for a rare capability exceeds supply and the allocation loop degenerates into a storm of rejected assignments and re-queued tasks. The mechanism is insidious: a task requiring capability `X` reaches the front of the ready queue, the allocator finds no available agent with capability `X` (all are busy), re-queues the task, and immediately re-examines it on the next scheduling tick. If the loop interval is short (sub-millisecond in an async event loop), this produces tight busy-wait behavior that consumes orchestrator CPU, pollutes scheduling telemetry with spurious allocation attempts, and starves other tasks of scheduling attention.

The mitigation has two parts. First, implement **capability-indexed backpressure**: when no agent with capability `X` is available, tasks requiring `X` are moved to a separate parked queue keyed by capability. The scheduling loop does not re-examine parked tasks until an agent with the required capability transitions from busy to idle, triggering a wake event that promotes the parked task back to the ready queue. This eliminates the thrash loop entirely. Second, instrument the allocator to emit a capability saturation signal when the parked queue depth for any capability exceeds a threshold. This signal feeds the swarm's auto-scaling layer, which provisions additional agents with the scarce capability. The combined effect is a self-regulating system that absorbs demand spikes without thrashing.

```python
import asyncio
from collections import defaultdict
from typing import DefaultDict, List


class BackpressureOrchestrator(HierarchicalOrchestrator):
    """
    Extends HierarchicalOrchestrator with capability-indexed parking
    to eliminate allocation thrashing under capability scarcity.
    """

    def __init__(self, saturation_threshold: int = 10) -> None:
        super().__init__()
        self._parked: DefaultDict[str, List[Task]] = defaultdict(list)
        self._saturation_threshold = saturation_threshold
        self._wake_events: DefaultDict[str, asyncio.Event] = defaultdict(asyncio.Event)

    def _select_agent(self, capability: str) -> Optional[Agent]:
        result = super()._select_agent(capability)
        if result is None:
            depth = len(self._parked[capability])
            if depth >= self._saturation_threshold:
                self._emit_saturation_signal(capability, depth)
        return result

    def _emit_saturation_signal(self, capability: str, depth: int) -> None:
        print(
            f"[BACKPRESSURE] Capability '{capability}' saturated: "
            f"{depth} tasks parked. Scaling signal emitted."
        )
        # In production: publish to metrics bus (e.g., Prometheus gauge,
        # CloudWatch metric) which triggers an autoscaler policy.

    def _park_task(self, task: Task) -> None:
        task.status = TaskStatus.PENDING
        self._parked[task.capability_required].append(task)
        self._wake_events[task.capability_required].clear()

    def _on_agent_available(self, capability: str) -> None:
        """Call this when an agent with `capability` transitions to idle."""
        parked = self._parked.get(capability, [])
        if parked:
            task = parked.pop(0)
            task.status = TaskStatus.READY
            import heapq
            heapq.heappush(self._ready_queue, task)
            self._wake_events[capability].set()

    async def run(self) -> None:
        while True:
            async with self._lock:
                dispatch_batch: List[tuple[Task, Agent]] = []
                temp_heap: List[Task] = []

                while self._ready_queue:
                    import heapq
                    task = heapq.heappop(self._ready_queue)
                    agent = self._select_agent(task.capability_required)
                    if agent is not None:
                        dispatch_batch.append((task, agent))
                    else:
                        # Park rather than re-queue — eliminates thrash
                        self._park_task(task)

                for t in temp_heap:
                    import heapq
                    heapq.heappush(self._ready_queue, t)

            if dispatch_batch:
                await asyncio.gather(
                    *(self._dispatch(t, a) for t, a in dispatch_batch)
                )
            else:
                await asyncio.sleep(0.05)

            async with self._lock:
                all_terminal = all(
                    t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                    for t in self._tasks.values()
                ) and all(
                    len(q) == 0 for q in self._parked.values()
                )
                if all_terminal:
                    break
```

### Failure Mode: Cascading Deadline Misses on the Critical Path

In task DAGs with hard deadlines, a subtle failure mode arises from priority inversion: a low-priority task at the head of a critical path occupies an agent that a high-priority task needs, causing the high-priority task to miss its deadline even though sufficient agent capacity nominally exists. This is the agentic analog of the Mars Pathfinder priority inversion bug of 1997, where a low-priority meteorological data collection task held a shared resource that a high-priority communication task was waiting on, causing the system watchdog to trigger resets.

The solution is **priority inheritance**: when a high-priority task is blocked waiting for a capability that is currently occupied by a lower-priority task, the executing low-priority task temporarily inherits the higher priority. In the agentic context, this manifests as a preemption signal to the executing agent: finish the current task as fast as possible (or checkpoint and yield if the task supports interruption), and the allocator elevates the blocked task's queue priority dynamically. For agents built on top of LLM inference, true preemption is impractical — a generation in progress cannot easily be interrupted mid-token. The practical mitigation is therefore **deadline-aware admission control**: before admitting a high-priority task into the DAG, the allocator performs a critical-path analysis to verify that sufficient capable agent capacity is available to meet the deadline, and rejects or re-routes the task if the analysis shows infeasibility.

### Observability: The Allocation Telemetry Contract

No allocation protocol is production-ready without an observability layer that exposes the metrics needed to diagnose the failure modes described above. At minimum, a swarm allocator must emit four metric families.

**Queue depth per capability** tracks how many tasks are waiting for each capability class, enabling proactive scaling before thrashing begins. **Assignment latency** measures the time between a task becoming ready and an agent beginning execution, surfacing bottlenecks in the selection loop or CFP round-trip time. **Agent utilization distribution** tracks the spread of load across agents — a high standard deviation indicates uneven allocation that is likely exploiting neither locality nor load balance. **Retry rate per task type** exposes systematic capability mismatches or agent instability that the allocation protocol's retry logic is absorbing silently.

These four metric families, instrumented as Prometheus counters and histograms and visualized as Grafana panels, give the operations team the diagnostic vocabulary to distinguish allocation algorithm problems (high assignment latency despite idle agents) from infrastructure problems (high retry rate on a specific capability class indicating a flaky agent implementation), without having to instrument individual agent execution.

The allocation protocol is not merely a scheduling detail — it is the nervous system of the swarm. The difference between a swarm that reliably completes complex multi-agent workflows under production load and one that thrashes, stalls, or silently degrades often lies entirely in whether the allocation layer correctly handles capability scarcity, respects the dependency graph under partial failure, and maintains enough observability to be diagnosed when behavior diverges from intent. The protocols in this lesson — hierarchical orchestration, Contract Net negotiation, auction scoring, work stealing, and backpressure parking — are not competing choices but a layered toolkit. Senior practitioners combine them, selecting the right mechanism for each layer of the swarm's topology based on scale, latency requirements, and fault tolerance budget.
