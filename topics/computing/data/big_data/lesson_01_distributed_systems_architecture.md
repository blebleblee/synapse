# Lesson 01 Distributed Systems Architecture

## Preface

This lesson is the foundation on which every subsequent big data topic rests. Before you can reason about Spark shuffles, Kafka replication, or Flink checkpoints, you need a precise mental model of what a distributed system actually is, what guarantees it can and cannot provide, and how those constraints shape every architectural decision you will ever make at scale.

We build that model from first principles, moving from the mathematics of distributed consensus through the physics of network communication to the engineering of fault-tolerant pipelines. Every claim is grounded in either a formal theorem or a runnable implementation.

---

## Table of Contents

1. [What Is a Distributed System?](#1-what-is-a-distributed-system)
2. [The Fundamental Impossibility Results](#2-the-fundamental-impossibility-results)
3. [Time, Clocks, and Ordering](#3-time-clocks-and-ordering)
4. [Failure Models and Fault Tolerance](#4-failure-models-and-fault-tolerance)
5. [Consistency Models](#5-consistency-models)
6. [The CAP Theorem in Depth](#6-the-cap-theorem-in-depth)
7. [PACELC: Beyond CAP](#7-pacelc-beyond-cap)
8. [Replication Strategies](#8-replication-strategies)
9. [Partitioning and Sharding](#9-partitioning-and-sharding)
10. [Consensus Algorithms: Raft](#10-consensus-algorithms-raft)
11. [Distributed Coordination Patterns](#11-distributed-coordination-patterns)
12. [Big Data Architecture Patterns](#12-big-data-architecture-patterns)
13. [The Lambda Architecture](#13-the-lambda-architecture)
14. [The Kappa Architecture](#14-the-kappa-architecture)
15. [Complete Working Implementation: A Distributed Log](#15-complete-working-implementation-a-distributed-log)
16. [Observability and Debugging](#16-observability-and-debugging)
17. [Production Checklist](#17-production-checklist)
18. [Exercises](#18-exercises)

---

## 1. What Is a Distributed System?

### 1.1 Formal Definition

A **distributed system** is a collection of autonomous computational entities — nodes — that communicate exclusively by passing messages over a network, with no shared memory, and that present a coherent service to external observers.

More formally, let:

- **N** = {n₁, n₂, …, nₖ} be the finite set of nodes
- **C** ⊆ N × N be the set of directed communication channels
- **M** be the (possibly infinite) message alphabet
- **S_i** be the local state space of node nᵢ
- **A_i** be the set of local actions node nᵢ can take (compute, send, receive)

A distributed system is a tuple **(N, C, M, {S_i}, {A_i})** together with an execution model that defines how nodes interleave their actions.

The critical invariant is **no shared state**: the only way node nᵢ can influence node nⱼ is by sending a message along some channel (nᵢ, nⱼ) ∈ C, possibly transitively through intermediate nodes.

### 1.2 Why Distribute?

Three orthogonal motivations drive distribution, and they impose different architectural pressures:

| Motivation | Driver | Key Metric | Example |
|---|---|---|---|
| Scalability | Dataset exceeds single-machine capacity | Throughput, storage | HDFS, BigQuery |
| Availability | Service must survive hardware failure | Uptime, MTTR | ZooKeeper, etcd |
| Latency | Geographic proximity to users | p99 latency | CDNs, regional databases |
| Collaboration | Multiple independent owners | Interoperability | Federated learning |

A system designed primarily for scalability (e.g., a batch processing pipeline) makes very different trade-offs from one designed for availability (e.g., a coordination service). Conflating these motivations is the source of most architectural mistakes.

### 1.3 The Execution Model

Two classical execution models bound the design space:

**Synchronous model**: There exists a known upper bound Δ on message delay and a known bound δ on relative clock drift. Every step completes within a known number of rounds. This model is easy to reason about but physically unrealisable across a wide-area network.

**Asynchronous model**: No bounds on message delay or clock drift are assumed. Messages may be arbitrarily delayed but not lost (reliable channels). This is the foundation of the FLP impossibility result below.

Real systems operate in the **partially synchronous model** (Dwork, Lynch, Stockmeyer 1988): the system behaves asynchronously during fault periods but eventually enters a synchronous phase of duration at least GST (Global Stabilisation Time). This model is what Raft, Paxos, and Zab are actually designed for.

```text
Timeline of partial synchrony:

t=0          t=GST          t=∞
|------------|--------------|----→
  Asynchronous  Synchronous
  (no bounds)   (bounds hold)
```

---

## 2. The Fundamental Impossibility Results

These are not engineering limitations you can overcome with better hardware. They are mathematical facts.

### 2.1 The FLP Impossibility Theorem

**Theorem (Fischer, Lynch, Paterson 1985)**: In a fully asynchronous message-passing system where processes can fail by crashing, there is no deterministic algorithm that solves distributed consensus, even if at most one process fails.

**Proof sketch**: Assume algorithm A solves consensus. Consider a bivalent initial configuration C₀ (one reachable from which both 0 and 1 can be decided, whose existence is proven by a reachability argument). There must exist some event e from C₀ that leads to another bivalent configuration, because if every event led to a univalent configuration, A would be trivially correct on all asynchronous schedules. By repeating this construction, we build an infinite admissible execution with no decision — a contradiction.

**Practical implication**: The FLP result does *not* say consensus is impossible. It says you must relax at least one of:
1. **Determinism** — use randomised algorithms (Ben-Or 1983)
2. **Full asynchrony** — assume partial synchrony (Paxos, Raft)
3. **Failure model** — only handle benign failures with extra assumptions

### 2.2 The CAP Theorem

**Theorem (Brewer 2000, formalised Gilbert & Lynch 2002)**: A distributed data store cannot simultaneously provide all three of:

- **C**onsistency: Every read receives the most recent write or an error
- **A**vailability: Every request receives a (non-error) response
- **P**artition tolerance: The system continues operating despite arbitrary message loss between nodes

**Proof sketch (Gilbert & Lynch)**: Consider two nodes n₁, n₂ with a network partition between them. Node n₁ receives write W. If the system is available, n₁ must respond to writes and n₂ must respond to reads without communicating. If n₂ returns stale data, C is violated. If n₂ returns an error, A is violated.

**The correct reading**: Since network partitions are a physical reality you cannot prevent, the real trade-off is between C and A *during* a partition. This is a narrow special case. The more practically useful framing is PACELC (Section 7).

### 2.3 The Two Generals Problem

Two generals on opposite sides of a valley must coordinate an attack. They can only communicate by messenger crossing the valley (which may be captured). They need consensus on a time to attack simultaneously.

**Theorem**: No protocol guarantees agreement in the presence of message loss.

**Proof by induction**: Any protocol has a finite last message. If that last message is lost, the generals are in the same epistemic state as if it was never sent — no agreement is possible. Removing the last message reduces the protocol to a shorter one, which by induction also cannot guarantee agreement.

This result underlies why TCP's connection teardown uses TIME_WAIT rather than a clean 4-way handshake guarantee — perfect agreement is physically impossible.

---

## 3. Time, Clocks, and Ordering

### 3.1 Why Physical Clocks Fail

Physical clocks drift. Network Time Protocol (NTP) synchronises clocks to within ~100ms on a local network, ~1-10ms with dedicated servers, and ~1ms with PTP (Precision Time Protocol). But:

- Clock drift between synchronisations can be milliseconds to seconds
- Leap seconds cause clocks to jump or repeat
- VM clock skew during live migration can be tens of seconds
- A system relying on wall-clock ordering for event causality will silently produce wrong answers

Google's Spanner uses TrueTime — atomic clocks plus GPS receivers — with bounded uncertainty ε ≈ 7ms. For every other system, we use logical clocks.

### 3.2 Lamport Clocks

**Definition (Lamport 1978)**: The *happens-before* relation → is the smallest relation satisfying:

1. If a and b are events in the same process and a occurs before b, then a → b
2. If a is the sending of a message and b is the receipt of that message, then a → b
3. Transitivity: if a → b and b → c, then a → c

**Lamport Clock Algorithm**:

Each process maintains a counter `C`. For each event:
- Local event: `C := C + 1`
- Send message: `C := C + 1`, attach `C` to message
- Receive message with timestamp `T`: `C := max(C, T) + 1`

**Guarantee**: if a → b, then C(a) < C(b). The converse does not hold — concurrent events may have any clock ordering.

```python
# lamport_clock.py — complete implementation
import threading
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LamportClock:
    """
    Thread-safe Lamport logical clock.
    
    Invariant: if event a happens-before event b,
    then clock(a) < clock(b).
    """
    _time: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def tick(self) -> int:
        """Increment clock for a local event. Returns new timestamp."""
        with self._lock:
            self._time += 1
            return self._time

    def send(self) -> int:
        """Prepare timestamp for outgoing message."""
        return self.tick()

    def receive(self, msg_timestamp: int) -> int:
        """
        Update clock on message receipt.
        C := max(C, T_msg) + 1
        """
        with self._lock:
            self._time = max(self._time, msg_timestamp) + 1
            return self._time

    @property
    def time(self) -> int:
        with self._lock:
            return self._time


@dataclass
class Message:
    sender: str
    payload: Any
    timestamp: int


class Process:
    """
    Simulated distributed process with a Lamport clock.
    """

    def __init__(self, name: str):
        self.name = name
        self.clock = LamportClock()
        self.log: list[tuple[int, str]] = []
        self._inbox: list[Message] = []
        self._lock = threading.Lock()

    def local_event(self, description: str) -> int:
        t = self.clock.tick()
        self.log.append((t, f"[LOCAL] {description}"))
        return t

    def send_message(self, payload: Any) -> Message:
        t = self.clock.send()
        msg = Message(sender=self.name, payload=payload, timestamp=t)
        self.log.append((t, f"[SEND ] payload={payload}"))
        return msg

    def receive_message(self, msg: Message) -> None:
        t = self.clock.receive(msg.timestamp)
        self.log.append((t, f"[RECV ] from={msg.sender} payload={msg.payload} msg_ts={msg.timestamp}"))

    def print_log(self) -> None:
        print(f"\nProcess {self.name}:")
        for ts, event in sorted(self.log):
            print(f"  t={ts:3d}  {event}")


def simulate_lamport_clocks():
    """
    Simulate the classic 3-process example from Lamport 1978.
    
    Timeline:
        P1: e1 ──send(m1)──────────────────── e4
        P2:          ────recv(m1)── e2 ──send(m2)──
        P3:                              ────recv(m2)── e3
    """
    p1 = Process("P1")
    p2 = Process("P2")
    p3 = Process("P3")

    # P1: local event, then send
    p1.local_event("start computation")
    m1 = p1.send_message("data chunk A")

    # P2: receives, does work, sends
    p2.receive_message(m1)
    p2.local_event("process chunk A")
    m2 = p2.send_message("result B")

    # P3: receives
    p3.receive_message(m2)
    p3.local_event("store result B")

    # P1 continues independently
    p1.local_event("start computation 2")

    p1.print_log()
    p2.print_log()
    p3.print_log()

    # Verify happens-before: clock(send m1) < clock(recv m1)
    send_ts = m1.timestamp
    recv_ts = dict(p2.log)[next(ts for ts, e in p2.log if "recv" in e.lower())]
    print(f"\nVerification: send(m1) ts={send_ts} < recv(m1) ts={recv_ts}: {send_ts < recv_ts}")


if __name__ == "__main__":
    simulate_lamport_clocks()
```

### 3.3 Vector Clocks

Lamport clocks detect causality in one direction. **Vector clocks** (Fidge 1988, Mattern 1988) capture it completely.

Each process i maintains a vector V of length n (one entry per process). Rules:

- **Local event**: `V[i] += 1`
- **Send**: `V[i] += 1`, attach entire `V` to message
- **Receive** message with vector `W`: `V[j] = max(V[j], W[j])` for all j, then `V[i] += 1`

**Causality detection**:
- `V_a < V_b` (a → b) iff `V_a[i] ≤ V_b[i]` for all i, with at least one strict inequality
- `V_a || V_b` (concurrent) iff neither `V_a < V_b` nor `V_b < V_a`

```python
# vector_clock.py — complete implementation
from __future__ import annotations
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from typing import NamedTuple


class VectorTimestamp(NamedTuple):
    """Immutable snapshot of a vector clock."""
    vector: tuple[int, ...]
    process_id: int

    def happens_before(self, other: VectorTimestamp) -> bool:
        """Returns True if self → other (self happens before other)."""
        v1, v2 = self.vector, other.vector
        if len(v1) != len(v2):
            raise ValueError("Vector clocks of different sizes are incomparable")
        # all components ≤ and at least one strictly <
        return (all(v1[i] <= v2[i] for i in range(len(v1))) and
                any(v1[i] < v2[i] for i in range(len(v1))))

    def concurrent_with(self, other: VectorTimestamp) -> bool:
        """Returns True if self || other (events are concurrent)."""
        return (not self.happens_before(other) and
                not other.happens_before(self))

    def __str__(self) -> str:
        return f"[{', '.join(str(v) for v in self.vector)}]"


class VectorClock:
    """
    Thread-safe vector clock for a single process.
    
    Args:
        process_id: This process's index in the vector (0-based)
        num_processes: Total number of processes in the system
    """

    def __init__(self, process_id: int, num_processes: int):
        if process_id < 0 or process_id >= num_processes:
            raise ValueError(f"process_id {process_id} out of range [0, {num_processes})")
        self.process_id = process_id
        self.num_processes = num_processes
        self._vector: list[int] = [0] * num_processes
        self._lock = threading.Lock()

    def tick(self) -> VectorTimestamp:
        """Increment own component for a local event."""
        with self._lock:
            self._vector[self.process_id] += 1
            return VectorTimestamp(tuple(self._vector), self.process_id)

    def send(self) -> VectorTimestamp:
        """Prepare timestamp for outgoing message."""
        return self.tick()

    def receive(self, remote_vector: tuple[int, ...]) -> VectorTimestamp:
        """
        Merge remote vector and increment own component.
        V[j] = max(V[j], W[j]) for all j, then V[i] += 1
        """
        with self._lock:
            if len(remote_vector) != self.num_processes:
                raise ValueError("Remote vector has wrong length")
            for j in range(self.num_processes):
                self._vector[j] = max(self._vector[j], remote_vector[j])
            self._vector[self.process_id] += 1
            return VectorTimestamp(tuple(self._vector), self.process_id)

    def snapshot(self) -> VectorTimestamp:
        with self._lock:
            return VectorTimestamp(tuple(self._vector), self.process_id)


@dataclass
class VectorMessage:
    sender_id: int
    payload: object
    vector: tuple[int, ...]


def demonstrate_vector_clocks():
    """
    Demonstrate causality detection with vector clocks.
    
    Three processes, four messages, showing concurrent events.
    """
    n = 3
    clocks = [VectorClock(i, n) for i in range(n)]
    events: dict[str, VectorTimestamp] = {}

    # P0: event a
    events["a"] = clocks[0].tick()
    print(f"a (P0 local):      {events['a']}")

    # P0 sends to P1
    send_ts = clocks[0].send()
    msg_0_to_1 = VectorMessage(0, "hello", send_ts.vector)
    events["send_0_1"] = send_ts
    print(f"send(P0→P1):       {events['send_0_1']}")

    # P1 receives
    events["recv_0_1"] = clocks[1].receive(msg_0_to_1.vector)
    print(f"recv(P0→P1 at P1): {events['recv_0_1']}")

    # P2: independent event
```
