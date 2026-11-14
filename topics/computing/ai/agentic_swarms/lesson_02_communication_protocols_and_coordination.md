# Lesson 2: Communication Protocols, Coordination Mechanisms

## 1. First-Principles Intuition & Invariants

The hardest problem in multi-agent systems is not intelligence — it is agreement. A single capable agent that acts in isolation produces tractable, auditable behavior. Twenty agents acting concurrently produce a distributed system, and distributed systems are where assumptions go to die. The moment you decompose a task across multiple reasoning engines, you inherit every unsolved problem in distributed computing: partial failures, network partitions, stale reads, race conditions, and the fundamental impossibility results that have governed the field since Leslie Lamport's work on logical clocks in 1978. The novelty of agentic swarms is not that they escape these constraints; it is that they expose them at the semantic layer, where the state being synchronized is not a database row but a belief, a plan, or an inferred world model.

To build intuition from first principles, consider what an agent actually needs to communicate. At minimum, it must share *observations* (what it sensed or retrieved), *intentions* (what it plans to do next), *results* (what an action produced), and *constraints* (what it must not conflict with). These four categories define the message space, and every communication architecture in multi-agent systems is essentially a different answer to the question of how these message types are routed, stored, and consumed. The wrong answer creates agents that duplicate work, contradict each other, or deadlock waiting for a signal that will never arrive.

The foundational invariant of any correct multi-agent communication substrate is **causal consistency**: if agent B's action is causally downstream of agent A's output, then B must have observed A's result before acting. Violating this invariant produces the class of bugs where an agent's plan is built on superseded state — a synthesizer agent that generates a report based on a retrieval result that another agent has already invalidated and replaced. In a single-threaded pipeline, causal ordering is free because execution order implies it. In a swarm where agents run concurrently on different threads, processes, or machines, causal ordering must be engineered deliberately.

The second invariant is **liveness under partial failure**. In a swarm of N agents, some subset will stall: an LLM call times out, a tool invocation returns an error, an agent's context window overflows and it enters an incoherent state. The communication substrate must ensure that the remaining agents can continue making progress. This requirement immediately rules out architectures where agents hold exclusive locks on shared resources, or where the failure of one agent blocks the message queue that all other agents consume from. Liveness-preserving designs tend toward asynchronous, non-blocking message passing with explicit timeout semantics and dead-letter queues for unprocessable messages.

The third invariant is **semantic coherence of the shared world model**. Unlike a traditional distributed database where the replicated state is a well-typed schema, the shared state in an agentic swarm is semi-structured: it includes natural language summaries, partially completed plans, retrieved document chunks, and tool call histories. Two agents reading the same blackboard at the same logical time must derive compatible beliefs about what has been established, what is in progress, and what remains open. This requires that every write to the shared state carry sufficient metadata — author agent ID, timestamp, confidence, scope, and task lineage — for a reader to correctly contextualize what it is reading. Without this metadata, the shared world model degrades into an unstructured heap of text that agents hallucinate relationships between.

These three invariants — causal consistency, liveness under partial failure, and semantic coherence — are the design axioms against which every architecture in this lesson should be evaluated.

---

## 2. Core Architecture & Mechanics

### 2.1 Message Passing: Topology and Semantics

Message passing is the most explicit and auditable coordination primitive available. Each agent has an inbox, produces messages addressed to other agents or broadcast channels, and processes messages from its inbox sequentially or with bounded concurrency. The topology of who sends to whom determines the information flow characteristics of the whole system.

The three canonical topologies are peer-to-peer, hub-and-spoke (orchestrator), and pub/sub broadcast. Each trades off latency, coordination overhead, and fault tolerance differently.

```
Peer-to-Peer (Full Mesh)         Hub-and-Spoke (Orchestrator)      Pub/Sub (Broadcast)

  A ──────── B                        A                           Topic: "research_results"
  │ ╲      ╱ │                        │                                    │
  │   ╲  ╱   │                   Orchestrator                   ┌──────────┼──────────┐
  │     ╳    │                  ╱    │     ╲                     ↓          ↓          ↓
  │   ╱  ╲   │                B      C      D                  Agent A   Agent B   Agent C
  │ ╱      ╲ │
  C ──────── D
```

In peer-to-peer topologies, every agent maintains direct communication channels to every other agent. This is optimal for small swarms (N ≤ 5) where tight coordination is needed and the communication graph is dense, but it scales as O(N²) in channel count and produces O(N²) message volume when agents broadcast updates. For a swarm of twenty specialized agents, full-mesh messaging is operationally untenable.

Hub-and-spoke concentrates routing logic in an orchestrator agent that sequences work, dispatches subtasks to specialist agents, and aggregates results. The orchestrator is the natural fit for hierarchical task decomposition — a user request arrives, the orchestrator decomposes it into retrieval, reasoning, and synthesis subtasks, routes each to the appropriate specialist, then assembles the final response. The critical failure mode is orchestrator bottleneck: if the orchestrator's context window fills, its reasoning degrades, and it begins routing inconsistently. Well-engineered orchestrators externalize their task state to a durable store (a task queue with explicit status fields) rather than relying on the LLM's context window as the authoritative record of what has been dispatched.

Pub/sub topologies decouple producers from consumers through named channels (topics). An agent publishes a message to `research_results` without knowing which agents are subscribed. This is the right model for swarms where the consumption of a result is not predetermined — a research agent publishes its findings, and the downstream agents that need those findings independently subscribe and react. The architectural cost is that causal ordering must be enforced by the message broker (via topic partitions and sequence numbers, as in Kafka's partition offset model) rather than being implicit in the call graph.

For production agentic systems, the right substrate for pub/sub message passing is a durable, ordered message queue — Redis Streams, Kafka, or a purpose-built agent message bus. The critical properties are message durability (a consuming agent crashing does not lose the message), consumer group semantics (a message is delivered to exactly one agent in a group, preventing duplicate processing), and dead-letter handling (messages that fail processing N times are moved to a quarantine queue for inspection rather than silently dropped).

The following implementation uses Redis Streams, which provides ordered, persistent message delivery with consumer group semantics natively:

```python
import redis
import json
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Any
from enum import Enum

class MessageType(str, Enum):
    TASK_DISPATCH   = "task_dispatch"
    TASK_RESULT     = "task_result"
    BELIEF_UPDATE   = "belief_update"
    CONSTRAINT      = "constraint"
    HEARTBEAT       = "heartbeat"

@dataclass
class AgentMessage:
    msg_id:      str        = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id:   str        = ""
    msg_type:    MessageType = MessageType.TASK_DISPATCH
    task_lineage: list[str] = field(default_factory=list)  # causal chain of task IDs
    timestamp:   float      = field(default_factory=time.time)
    confidence:  float      = 1.0
    payload:     dict       = field(default_factory=dict)

class AgentMessageBus:
    """
    Redis Streams-backed message bus with consumer group semantics.
    Guarantees: at-least-once delivery, ordered within a topic,
    persistent across consumer crashes, dead-letter on N failures.
    """
    DEAD_LETTER_STREAM = "swarm:dead_letter"
    MAX_DELIVERY_ATTEMPTS = 3

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.r = redis.from_url(redis_url, decode_responses=True)

    def ensure_consumer_group(self, topic: str, group: str) -> None:
        try:
            self.r.xgroup_create(name=topic, groupname=group, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def publish(self, topic: str, msg: AgentMessage) -> str:
        """Publish a message to a topic stream. Returns the Redis stream entry ID."""
        raw = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
               for k, v in asdict(msg).items()}
        return self.r.xadd(topic, raw)

    def consume(
        self,
        topic: str,
        group: str,
        consumer_id: str,
        count: int = 10,
        block_ms: int = 2000,
    ) -> list[tuple[str, AgentMessage]]:
        """
        Consume pending messages for this consumer, then fetch new ones.
        Returns list of (stream_entry_id, AgentMessage) tuples.
        """
        self.ensure_consumer_group(topic, group)
        # First drain any messages pending from a previous crashed session.
        raw_pending = self.r.xreadgroup(
            groupname=group, consumername=consumer_id,
            streams={topic: "0"}, count=count
        )
        entries = raw_pending or []
        if not entries or not entries[0][1]:
            # No pending backlog; fetch new messages.
            raw_new = self.r.xreadgroup(
                groupname=group, consumername=consumer_id,
                streams={topic: ">"}, count=count, block=block_ms
            )
            entries = raw_new or []

        result: list[tuple[str, AgentMessage]] = []
        for _stream, messages in entries:
            for entry_id, fields in messages:
                try:
                    msg = AgentMessage(
                        msg_id=fields["msg_id"],
                        sender_id=fields["sender_id"],
                        msg_type=MessageType(fields["msg_type"]),
                        task_lineage=json.loads(fields["task_lineage"]),
                        timestamp=float(fields["timestamp"]),
                        confidence=float(fields["confidence"]),
                        payload=json.loads(fields["payload"]),
                    )
                    result.append((entry_id, msg))
                except (KeyError, ValueError, json.JSONDecodeError) as exc:
                    self._send_to_dead_letter(entry_id, fields, str(exc))
                    self.r.xack(topic, group, entry_id)
        return result

    def ack(self, topic: str, group: str, entry_id: str) -> None:
        self.r.xack(topic, group, entry_id)

    def nack_with_retry(
        self,
        topic: str,
        group: str,
        entry_id: str,
        original_msg: AgentMessage,
        error: str,
    ) -> None:
        """
        On processing failure: check delivery count. If under threshold,
        re-add to stream so another consumer can retry. Otherwise, dead-letter.
        """
        info = self.r.xpending_range(topic, group, min=entry_id, max=entry_id, count=1)
        delivery_count = info[0]["times_delivered"] if info else 1
        self.r.xack(topic, group, entry_id)
        if delivery_count < self.MAX_DELIVERY_ATTEMPTS:
            self.publish(topic, original_msg)
        else:
            self._send_to_dead_letter(entry_id, asdict(original_msg), error)

    def _send_to_dead_letter(self, entry_id: str, fields: dict, reason: str) -> None:
        self.r.xadd(self.DEAD_LETTER_STREAM, {
            "original_entry_id": entry_id,
            "reason": reason,
            "fields": json.dumps(fields),
            "ts": time.time(),
        })
```

Notice that `AgentMessage` carries `task_lineage` — a list of ancestor task IDs. This is a vector of causal provenance. When agent B processes a message, it appends its own task ID to the lineage before publishing downstream. Any consumer can reconstruct the causal graph of the entire computation from the lineage fields alone, which makes debugging a failed swarm run tractable: you can trace exactly which agent produced which result, and in what order.

### 2.2 The Blackboard Architecture

The blackboard is the oldest and most direct architectural pattern for multi-agent coordination. The name comes from the metaphor of a physical blackboard in a room full of specialists: anyone can write a partial result, and anyone can read and build on what others have written. In software, the blackboard is a shared, structured, persistent data store that all agents read from and write to, with the coordination logic emergent from agents responding to the state they observe rather than receiving explicit instructions.

The original blackboard systems (HEARSAY-II in the 1970s, HASP/SIAP in the 1980s) used a monitor process that matched the current blackboard state against each knowledge source's trigger conditions and scheduled activations. Modern LLM-based swarms implement a structurally identical pattern, but the knowledge sources are tool-augmented language models and the trigger conditions are expressed as semantic relevance rather than syntactic pattern matching.

A blackboard for an agentic swarm has four distinct layers of state:

The **task registry** holds the decomposition of the user's goal into subtasks, each with a status (`pending`, `in_progress`, `complete`, `failed`), an assigned agent ID, and an expiry timestamp. The **evidence store** holds retrieved documents, computed values, and tool outputs — the raw material that agents synthesize from. The **belief store** holds agent-level conclusions: structured assertions like "the Q3 revenue figure is $4.2B, sourced from document chunk ID 7f3a, confidence 0.91." The **plan layer** holds the current action sequence that the swarm has committed to, along with any temporal or logical constraints between steps.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BLACKBOARD STATE                            │
│                                                                     │
│  ┌──────────────────┐   ┌──────────────────┐                       │
│  │   Task Registry  │   │  Evidence Store  │                       │
│  │                  │   │                  │                       │
│  │ task_001: DONE   │   │ doc_chunk_7f3a   │                       │
│  │ task_002: ACTIVE │   │ tool_result_b2c  │                       │
│  │ task_003: PENDING│   │ web_fetch_11d9   │                       │
│  └──────────────────┘   └──────────────────┘                       │
│                                                                     │
│  ┌──────────────────┐   ┌──────────────────┐                       │
│  │  Belief Store    │   │   Plan Layer     │                       │
│  │                  │   │                  │                       │
│  │ belief_a: 0.91   │   │ step_1 → step_2  │                       │
│  │ belief_b: 0.74   │   │ constraint: b→c  │                       │
│  │ belief_c: 0.88   │   │ step_3 BLOCKED   │                       │
│  └──────────────────┘   └──────────────────┘                       │
│                                ↑                                    │
│           Agents read/write through versioned key-value API         │
└─────────────────────────────────────────────────────────────────────┘
         ↑                   ↑                   ↑
    Researcher Agent    Analyst Agent      Synthesizer Agent
```

The critical implementation question is the write semantics. Naive blackboard implementations allow concurrent writes that silently overwrite each other, producing the classic lost-update anomaly: two agents both read belief `b` as unset, both compute it, and one's result overwrites the other's. The correct primitive is a **compare-and-swap (CAS)** write: an agent reads the current version number of a belief, performs its computation, then writes back only if the version number has not changed since the read. If the version has advanced — meaning another agent wrote first — the write is rejected and the agent re-reads and recomputes.

```python
import redis
import json
import time
from typing import Any

class BlackboardStore:
    """
    Versioned blackboard built on Redis.
    All writes are optimistic CAS using WATCH/MULTI/EXEC transactions.
    Each key stores a JSON envelope: {version, author, timestamp, confidence, value}.
    """

    TASK_NS    = "bb:task:"
    EVIDENCE_NS = "bb:evidence:"
    BELIEF_NS  = "bb:belief:"
    PLAN_NS    = "bb:plan:"

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.r = redis.from_url(redis_url, decode_responses=True)

    def _make_envelope(
        self, value: Any, author: str, confidence: float, version: int
    ) -> str:
        return json.dumps({
            "version":    version,
            "author":     author,
            "timestamp":  time.time(),
            "confidence": confidence,
            "value":      value,
        })

    def read(self, key: str) -> dict | None:
        raw = self.r.get(key)
        return json.loads(raw) if raw else None

    def cas_write(
        self,
        key: str,
        value: Any,
        author: str,
        confidence: float,
        expected_version: int | None,
    ) -> bool:
        """
        Optimistic CAS write. Returns True on success, False on version conflict.
        expected_version=None means the key must not exist (first write).
        """
        with self.r.pipeline() as pipe:
            try:
                pipe.watch(key)
                current_raw = pipe.get(key)
                current = json.loads(current_raw) if current_raw else None

                current_version = current["version"] if current else None
                if current_version != expected_version:
                    pipe.reset()
                    return False  # Version conflict — caller must re-read and retry.

                new_version = (expected_version or 0) + 1
                pipe.multi()
                pipe.set(key, self._make_envelope(value, author, confidence, new_version))
                pipe.execute()
                return True

            except redis.WatchError:
                return False  # Another client wrote between WATCH and EXEC.

    def write_belief(
        self,
        belief_id: str,
        value: Any,
        author: str,
        confidence: float,
        max_retries: int = 5,
    ) -> bool:
        """Write a belief with automatic CAS retry up to max_retries times."""
        key = self.BELIEF_NS + belief_id
        for attempt in range(max_retries):
            current = self.read(key)
            expected = current["version"] if current else None
            # Refuse to overwrite a higher-confidence belief from another agent.
            if current and current["confidence"] >= confidence:
                return False  # Existing belief is more authoritative; skip write.
            success = self.cas_write(key, value, author, confidence, expected)
            if success:
                return True
            time.sleep(0.01 * (2 ** attempt))  # Exponential backoff on conflict.
        return False

    def update_task_status(
        self,
        task_id: str,
        status: str,
        agent_id: str,
        result_key: str | None = None,
    ) -> bool:
        key = self.TASK_NS + task_id
        for _ in range(5):
            current = self.read(key)
            if current is None:
                return False  # Task does not exist.
            task_data = current["value"]
            task_data["status"]   = status
            task_data["agent_id"] = agent_id
            if result_key:
                task_data["result_key"] = result_key
            success = self.cas_write(
                key, task_data, agent_id, 1.0, current["version"]
            )
            if success:
                return True
            time.sleep(0.01)
        return False
```

The confidence-based write guard in `write_belief` is not a correctness mechanism but a semantic one: it encodes the multi-agent epistemology that a higher-confidence belief should not be overwritten by a weaker inference. This is exactly the kind of domain-specific coordination logic that distinguishes an agentic blackboard from a generic cache.

### 2.3 Consensus Mechanisms for Distributed Belief

When a swarm must converge on a single authoritative answer — not merely share results, but formally agree on them — message passing and CAS writes are insufficient. What you need is a consensus protocol: a procedure by which N agents, some of which may be faulty or slow, reach agreement on a value that no single agent can unilaterally revoke.

For small swarms (3–9 agents), you can implement a lightweight voting protocol. Each agent that completes a subtask publishes a **proposal** to a shared consensus channel. A coordinator (which may rotate using a leader election protocol) collects proposals and applies a quorum rule: a belief is accepted if ⌊N/2⌋ + 1 agents have proposed it, where agreement is measured semantically (via embedding similarity above a threshold) rather than by exact string match. This is the multi-agent analog of Raft's majority quorum, adapted for the fact that two LLM agents reasoning independently about the same evidence may produce equivalent but non-identical text.

The semantic quorum is implemented by embedding each proposal, clustering them, and accepting the cluster whose centroid is supported by a majority:

```python
import numpy as np
from openai import OpenAI
from dataclasses import dataclass
from typing import Sequence

@dataclass
class Proposal:
    agent_id:   str
    task_id:    str
    text:       str
    confidence: float
    embedding:  np.ndarray = None

class SemanticQuorumConsensus:
    """
    Accepts a set of agent proposals and returns the consensus value
    if a simple majority of proposals are semantically equivalent
    (cosine similarity >= threshold). Otherwise returns None, signaling
    that the swarm has not yet converged and more evidence is needed.
    """

    def __init__(self, similarity_threshold: float = 0.88):
        self.client = OpenAI()
        self.threshold = similarity_threshold

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        vectors = np.array([e.embedding for e in response.data], dtype=np.float32)
        # L2-normalize for cosine similarity via dot product.
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-10)

    def run(self, proposals: list[Proposal]) -> dict | None:
        if not proposals:
            return None

        texts = [p.text for p in proposals]
        embeddings = self.embed(texts)
        for i, p in enumerate(proposals):
            p.embedding = embeddings[i]

        n = len(proposals)
        quorum = n // 2 + 1
        # Build a similarity matrix.
        sim_matrix = embeddings @ embeddings.T  # shape (n, n), cosine similarities

        # For each proposal, count how many others agree with it.
        for i, anchor in enumerate(proposals):
            agreeing_indices = [
                j for j in range(n)
                if sim_matrix[i, j] >= self.threshold
            ]
            if len(agreeing_indices) >= quorum:
                # Consensus reached. Return the proposal with highest confidence
                # among the agreeing set as the canonical answer.
                agreeing = [proposals[j] for j in agreeing_indices]
                best = max(agreeing, key=lambda p: p.confidence)
                return {
                    "consensus_text":   best.text,
                    "quorum_size":      len(agreeing_indices),
                    "total_proposals":  n,
                    "canonical_agent":  best.agent_id,
                    "mean_similarity":  float(np.mean([
                        sim_matrix[i, j] for j in agreeing_indices
                    ])),
                }
        return None  # No quorum reached.
```

This protocol has an important failure mode: it can silently produce a spurious quorum when multiple agents hallucinate the same wrong answer because they were all given the same misleading context. Semantic agreement does not imply factual correctness. The mitigation is to require that each proposal cite specific evidence keys from the blackboard's evidence store, and to verify that the cited evidence actually entails the proposed belief — a secondary verification step performed by a dedicated critic agent before the consensus result is committed.

### 2.4 Synchronization Primitives: Barriers, Semaphores, and Leases

Multi-agent coordination patterns often require synchronization beyond message acknowledgment. Three primitives cover the majority of real-world cases: barriers, semaphores, and leases.

A **barrier** is a synchronization point at which all participating agents must arrive before any can proceed. In agentic workflows, barriers appear naturally at phase transitions: all retrieval agents must complete before the synthesis agent begins, all sub-hypotheses must be evaluated before the final conclusion is drawn. A barrier is implemented as a counter in the shared store, initialized to N (the number of participating agents). Each agent that completes its phase decrements the counter atomically; the agent that decrements it to zero signals all waiting agents to proceed. Redis provides `INCR`/`DECR` with atomic semantics and `BLPOP` for efficient waiting:

```python
import redis
import time

class DistributedBarrier:
    """
    A distributed barrier for N agents. All agents call arrive_and_wait();
    the last arrival signals all waiters via a Redis list notification.
    Times out after deadline_seconds if not all agents arrive.
    """

    def __init__(self, r: redis.Redis, barrier_id: str, n_agents: int):
        self.r = r
        self.counter_key = f"barrier:{barrier_id}:counter"
        self.signal_key  = f"barrier:{barrier_id}:signal"
        self.n_agents    = n_agents
        # Initialize counter only if it doesn't exist (first caller sets it).
        self.r.setnx(self.counter_key, n_agents)

    def arrive_and_wait(self, agent_id: str, deadline_seconds: float = 60.0) -> bool:
        remaining = self.r.decr(self.counter_key)
        if remaining == 0:
            # This agent was the last to arrive; unblock all waiters.
            for _ in range(self.n_agents - 1):
                self.r.lpush(self.signal_key, "go")
            self.r.expire(self.signal_key, 10)
            return True
        elif remaining < 0:
            # Already past this barrier; this is a stale call.
            return True
        else:
            # Wait for the signal with a deadline.
            result = self.r.blpop(self.signal_key, timeout=int(deadline_seconds))
            return result is not None  # None means timeout — not all agents arrived.


class DistributedSemaphore:
    """
    Counting semaphore limiting concurrent access to a resource (e.g.,
    an external API with rate limits) across all agents in the swarm.
    """

    def __init__(self, r: redis.Redis, semaphore_id: str, max_concurrent: int):
        self.r = r
        self.key = f"semaphore:{semaphore_id}"
        self.max = max_concurrent
        self.r.setnx(self.key, max_concurrent)

    def acquire(self, timeout_seconds: float = 30.0) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            remaining = self.r.decr(self.key)
            if remaining >= 0:
                return True
            # We went negative; undo and wait.
            self.r.incr(self.key)
            time.sleep(0.1)
        return False

    def release(self) -> None:
        count = self.r.incr(self.key)
        if count > self.max:
            # Guard against over-release bugs.
            self.r.decr(self.key)


class DistributedLease:
    """
    Exclusive lease (distributed mutex) with automatic expiry.
    Prevents two agents from claiming the same task concurrently.
    Uses SET NX PX atomics — no WATCH/MULTI/EXEC overhead.
    """

    def __init__(self, r: redis.Redis, resource_id: str, ttl_ms: int = 30_000):
        self.r = r
        self.key = f"lease:{resource_id}"
        self.ttl_ms = ttl_ms

    def acquire(self, holder_id: str) -> bool:
        result = self.r.set(self.key, holder_id, nx=True, px=self.ttl_ms)
        return result is True

    def release(self, holder_id: str) -> bool:
        """Conditionally release: only the holder may release its own lease."""
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = self.r.eval(script, 1, self.key, holder_id)
        return bool(result)

    def extend(self, holder_id: str) -> bool:
        """Extend TTL if still the holder (heartbeat pattern)."""
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("pexpire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        result = self.r.eval(script, 1, self.key, holder_id, self.ttl_ms)
        return bool(result)
```

The lease TTL is the decisive parameter for swarm reliability. Set it too short, and an agent that is simply slow (waiting on a 20-second LLM call) loses its lease mid-task, allowing another agent to claim the same work and produce a duplicate. Set it too long, and a crashed agent holds its lease for minutes, stalling downstream dependents. The correct pattern is for the working agent to run a background heartbeat thread that calls `extend` every TTL/3 milliseconds as long as the task is in progress, and to release the lease (or let it expire) only on completion or confirmed failure.

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 Context Propagation and the Stale-Read Problem

The most common silent failure in production agentic swarms is not a crash — it is an agent making a decision based on stale state. An analyst agent reads the blackboard, finds no belief for `q3_revenue`, queries an LLM to infer it, and writes back a value. Meanwhile, a research agent has just retrieved the actual Q3 earnings release and written the correct figure. The analyst's inferred value overwrites the retrieved fact because the confidence guard in `write_belief` did not distinguish between high-confidence inference and directly retrieved evidence.

The fix is to enforce a strict evidence hierarchy in the blackboard metadata. Every written value should carry a `source_type` field from an ordered enum: `DIRECT_RETRIEVAL > TOOL_COMPUTED > AGENT_INFERRED > SYNTHESIZED`. The CAS write logic compares source types before confidence scores: a retrieved value cannot be overwritten by an inferred one, regardless of the inferred confidence level. This is a semantic invariant of the data model, not just a performance optimization.

Stale reads are exacerbated by LLM context caching. When an agent's context window is populated at the start of a task, it reflects the blackboard state at that moment. If the agent runs for 30 seconds before writing a result, the context it reasoned from is 30 seconds stale. For fast-moving swarms where the blackboard is updated frequently, agents should not load blackboard state into their prompts at task initialization; they should query the blackboard as a tool call at the moment they need a specific value. This converts the blackboard read from a snapshot operation (stale by design) to a point-in-time query against the current state.

### 3.2 Communication Topology Scaling and Hotspot Mitigation

As swarm size grows, the orchestrator in a hub-and-spoke topology becomes a throughput bottleneck. An orchestrator LLM can process one request at a time, so its effective task dispatch throughput is bounded by the LLM's tokens-per-second rate and the size of the routing decision prompt. For a swarm where each subtask dispatch requires a 500-token routing decision and the orchestrator model runs at 50 tokens/second, the maximum dispatch rate is 0.1 tasks/second — which serializes a swarm of 10 parallel agents into effectively sequential execution.

The architectural solution is hierarchical orchestration: replace the single orchestrator with a two-level tree. A top-level strategic orchestrator decomposes the user's goal into major workstreams and assigns each to a mid-level tactical orchestrator. Tactical orchestrators manage the fine-grained task dispatch within their workstream. This reduces the strategic orchestrator's prompt size by an order of magnitude (it describes workstreams, not individual tool calls) and parallelizes dispatch across the tactical layer.

```
                     Strategic Orchestrator
                    (goal decomposition only)
                   /           |           \
          Tactical-A      Tactical-B      Tactical-C
         (retrieval       (analysis       (synthesis
          workstream)      workstream)     workstream)
        /    |    \       /    |    \       /    |    \
      R1    R2    R3    A1    A2    A3    S1    S2    S3
```

The tactical orchestrators share the blackboard and message bus with each other. When a retrieval agent in Tactical-A's workstream produces a result needed by an analysis agent in Tactical-B's workstream, the message is published to the shared bus and consumed directly — the strategic orchestrator is not involved and need not be queried.

### 3.3 Failure Taxonomy and Recovery Patterns

Production swarms fail in five structurally distinct ways, each requiring a different recovery mechanism.

**Agent timeout failure** occurs when an agent's LLM call does not return within the expected window. The correct response is for the lease TTL to expire (automatically releasing the task back to the work queue), and for a watchdog process to publish a `TASK_FAILED` event to the message bus. Any waiting downstream agents receive this event and can either wait for a retry or proceed with the task marked as unavailable. The worst response is an indefinitely blocking `await` on the LLM call with no timeout, which stalls the entire consumer goroutine or thread.

**Belief contradiction failure** occurs when two agents write incompatible beliefs about the same fact (agent A asserts revenue is $4.2B, agent B asserts $3.9B, both with high confidence from different retrieved sources). This is not a bug but an epistemic conflict that the swarm must surface rather than silently resolve. The blackboard should maintain both beliefs with their source evidence, and a designated arbitration agent should be tasked with reading both sources, identifying the discrepancy, and writing an arbitrated belief with a `CONFLICTED` flag and a pointer to the evidence. The final synthesizer must handle `CONFLICTED` beliefs explicitly — reporting uncertainty rather than picking one value arbitrarily.

**Circular dependency deadlock** occurs when task A is waiting for task B, which is waiting for task A — the multi-agent analog of a mutex deadlock. This is surprisingly easy to create in hierarchical task decomposition, particularly when agents are allowed to spawn new tasks dynamically. Detection requires maintaining the task dependency graph as an explicit data structure on the blackboard and running a cycle detection pass (DFS with coloring) whenever a new dependency is registered. Any detected cycle should trigger an immediate `DEADLOCK_DETECTED` event that cancels all tasks in the cycle and re-plans from the last consistent state.

**Context overflow failure** occurs when an agent's accumulated task history, instructions, and blackboard excerpts exceed the model's context window. The agent begins truncating or silently ignoring early context, producing inconsistent behavior. The mitigation is to instrument every agent with a token counter on its context, and to trigger a **context compression** step — a secondary LLM call that summarizes the agent's history into a compact state representation — before the context reaches 80% of the window limit. The compressed state replaces the full history, and the agent continues from the summary.

**Cascading hallucination** is the most dangerous failure mode and the hardest to detect at runtime. It occurs when one agent publishes an incorrect belief with high confidence, and downstream agents treat it as ground truth, build on it, and publish further incorrect conclusions. The incorrect belief propagates through the swarm's reasoning chain, and by the time it reaches the final synthesizer, it is embedded in multiple layers of inference. The architectural defense is mandatory **citation chains**: every belief must reference the evidence keys it was derived from, and the evidence keys must reference the original retrieved sources. A critic agent that samples the final answer and traces its citation chain back to source documents can catch hallucinated beliefs before they are delivered to the user.

### 3.4 End-to-End Swarm Runtime: Integration Pattern

The following brings together the message bus, blackboard, consensus, and synchronization primitives into a minimal but complete agent runtime loop. This is the scaffolding that every agent in the swarm runs, with the agent-specific logic confined to `process_task`:

```python
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

@dataclass
class SwarmAgentConfig:
    agent_id:          str
    agent_role:        str           # e.g., "researcher", "analyst", "synthesizer"
    input_topic:       str           # Redis stream to consume from
    output_topic:      str           # Redis stream to publish results to
    consumer_group:    str
    task_lease_ttl_ms: int = 30_000
    heartbeat_interval: float = 8.0  # seconds; must be < task_lease_ttl_ms / 1000 / 3

class SwarmAgentRuntime:
    """
    Generic agent runtime loop. Agents consume from an input topic,
    acquire a lease on each task, process it, write results to the
    blackboard and output topic, and ack the message.
    """

    def __init__(
        self,
        config: SwarmAgentConfig,
        bus: AgentMessageBus,
        blackboard: BlackboardStore,
        process_task: Callable[[AgentMessage, BlackboardStore], Awaitable[AgentMessage]],
    ):
        self.cfg         = config
        self.bus         = bus
        self.blackboard  = blackboard
        self.process     = process_task
        self._running    = False

    async def run(self) -> None:
        self._running = True
        logger.info(f"Agent {self.cfg.agent_id} ({self.cfg.agent_role}) starting.")
        while self._running:
            entries = self.bus.consume(
                topic=self.cfg.input_topic,
                group=self.cfg.consumer_group,
                consumer_id=self.cfg.agent_id,
                count=1,
                block_ms=2000,
            )
            for entry_id, msg in entries:
                await self._handle_message(entry_id, msg)

    async def _handle_message(self, entry_id: str, msg: AgentMessage) -> None:
        lease = DistributedLease(
            self.blackboard.r,
            resource_id=msg.payload.get("task_id", msg.msg_id),
            ttl_ms=self.cfg.task_lease_ttl_ms,
        )
        if not lease.acquire(self.cfg.agent_id):
            # Another agent already has this task. Ack without processing.
            self.bus.ack(self.cfg.input_topic, self.cfg.consumer_group, entry_id)
            return

        heartbeat_task = asyncio.create_task(
            self._heartbeat(lease, self.cfg.heartbeat_interval)
        )
        try:
            self.blackboard.update_task_status(
                msg.payload.get("task_id", msg.msg_id),
                status="in_progress",
                agent_id=self.cfg.agent_id,
            )
            result_msg = await self.process(msg, self.blackboard)
            result_msg.task_lineage = msg.task_lineage + [msg.msg_id]
            result_msg.sender_id    = self.cfg.agent_id
            self.bus.publish(self.cfg.output_topic, result_msg)
            self.blackboard.update_task_status(
                msg.payload.get("task_id", msg.msg_id),
                status="complete",
                agent_id=self.cfg.agent_id,
                result_key=self.cfg.output_topic + ":" + result_msg.msg_id,
            )
            self.bus.ack(self.cfg.input_topic, self.cfg.consumer_group, entry_id)
        except Exception as exc:
            logger.error(f"Agent {self.cfg.agent_id} failed on {entry_id}: {exc}")
            self.bus.nack_with_retry(
                self.cfg.input_topic,
                self.cfg.consumer_group,
                entry_id,
                msg,
                str(exc),
            )
        finally:
            heartbeat_task.cancel()
            lease.release(self.cfg.agent_id)

    async def _heartbeat(self, lease: DistributedLease, interval: float) -> None:
        while True:
            await asyncio.sleep(interval)
            if not lease.extend(self.cfg.agent_id):
                logger.warning(f"Agent {self.cfg.agent_id} lost lease during heartbeat.")
                break

    def stop(self) -> None:
        self._running = False
```

This runtime cleanly separates the coordination mechanics (lease acquisition, heartbeat, ack/nack, blackboard status updates, lineage propagation) from the agent's reasoning logic (the `process_task` callback). A research agent, an analyst agent, and a synthesizer agent all run this same runtime loop; they differ only in their `process_task` implementation. The lineage threading (`result_msg.task_lineage = msg.task_lineage + [msg.msg_id]`) ensures that every message in the system carries its full causal ancestry, making the complete information flow of any swarm run reconstructable from the message bus log alone.

The architectural principles in this lesson — explicit message envelopes with causal lineage, versioned blackboard writes with semantic evidence hierarchies, semantic quorum consensus for belief convergence, distributed synchronization primitives with heartbeat-based lease management, and hierarchical orchestration to avoid dispatch bottlenecks — form the mechanical substrate on which every higher-order coordination pattern in the subsequent lessons will depend. Building on a substrate that gets these primitives wrong produces swarms that appear to work in testing (where failures are rare and timing is predictable) and degrade unpredictably in production (where LLM calls vary in latency by an order of magnitude and agent failures are routine). Getting the communication substrate right is not an optimization; it is the precondition for correctness.
