# Lesson 2: Reflection Mechanisms in Autonomous AI Agents

## 1. First-Principles Intuition & Invariants

### Why Reflection Exists

An agent operating without reflection is an open-loop system: it executes a fixed policy regardless of outcomes. Open-loop control is acceptable only when the environment is perfectly modeled, fully deterministic, and stationary — conditions that essentially never hold in practice. The moment the environment deviates from the model (unexpected obstacles, distribution shift in inputs, latency spikes in tool calls), a non-reflective agent degrades silently and irrecoverably.

Reflection closes the loop. It introduces a *meta-cognitive layer* that observes the agent's own behavior as data, reasons about that data relative to goals, and updates the policy or plan accordingly. This is the same fundamental principle that underlies PID controllers, Bayesian inference, and evolutionary adaptation — feedback-driven correction toward a target.

Formally, we can define an agent's decision process as a Markov Decision Process (MDP) tuple:

$$\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{T}, \mathcal{R}, \gamma \rangle$$

where $\mathcal{S}$ is the state space, $\mathcal{A}$ the action space, $\mathcal{T}: \mathcal{S} \times \mathcal{A} \rightarrow \Delta(\mathcal{S})$ the stochastic transition function, $\mathcal{R}: \mathcal{S} \times \mathcal{A} \rightarrow \mathbb{R}$ the reward function, and $\gamma \in [0,1)$ the discount factor. A *reflecting* agent additionally maintains a *meta-state* $\hat{s} \in \hat{\mathcal{S}}$ that encodes beliefs about its own performance, and a *meta-policy* $\hat{\pi}: \hat{\mathcal{S}} \rightarrow \Delta(\Pi)$ that selects among a set of base policies $\Pi$. This two-level structure — object-level MDP plus meta-level MDP — is the theoretical skeleton of every practical reflection mechanism.

### The Three Invariants

Three invariants must hold for a reflection mechanism to be well-posed:

**Invariant 1 — Observability.** The agent must have access to sufficient signal to distinguish good outcomes from bad. If the performance metric $\rho: \text{Trajectory} \rightarrow \mathbb{R}$ is not computable from available observations, the reflection loop has no meaningful input. This is equivalent to the *detectability* condition in linear control theory: a system is detectable if all unstable modes are observable from the output.

**Invariant 2 — Credit Assignment.** The agent must be able to attribute an outcome to a specific action or sequence of actions. Without this, learning is impossible — gradient signal is zero everywhere. In temporal settings, this is the *temporal credit assignment problem*, first identified in Minsky (1961) and rigorously analyzed by Sutton (1984) in the context of temporal-difference learning. In LLM-based agents, credit assignment is nontrivial because the "action" is a multi-token generation and the outcome may not manifest until many tool calls later.

**Invariant 3 — Policy Improvement Monotonicity.** Each reflection step should not degrade expected return. Formally, if $\pi'$ is the policy after reflection, then $V^{\pi'}(s) \geq V^{\pi}(s)$ for all $s \in \mathcal{S}$. This is the *Policy Improvement Theorem* (Sutton & Barto, 2018, Chapter 4). Violation — a reflection that makes performance worse — indicates either a flawed performance metric, an over-aggressive learning rate, or catastrophic forgetting.

### Reflection Taxonomy

Contemporary literature distinguishes three distinct modes of reflection:

| Mode | Timing | Scope | Mechanism |
|------|--------|-------|-----------|
| **In-trajectory reflection** | Mid-task, after each action | Local: single step or subtask | Self-critique prompts, tool-call validation |
| **Post-hoc reflection** | After task completion | Global: entire trajectory | Trace summarization, error attribution |
| **Cross-episode reflection** | Across multiple tasks | Episodic memory, policy update | Memory writes, fine-tuning, RAG updates |

The seminal *Reflexion* paper (Shinn et al., 2023) operationalizes post-hoc reflection for LLM agents: after a failed episode, the agent generates a natural-language *reflection* summarizing what went wrong and stores it in an episodic memory buffer. On the next attempt, this reflection is prepended to the prompt, shifting the prior over actions without any gradient update. This is a form of *in-context reinforcement learning* — the context window plays the role of a parameter store that is updated between episodes.

---

## 2. Core Architecture & Mechanics

### The Reflection Loop

The reflection mechanism is not a single module — it is a control architecture comprising four cooperating subsystems:

```mermaid
graph TD
    ENV["Environment / Tools"]
    ACT["Action Executor\n(Object-Level Policy π)"]
    MON["Performance Monitor\nρ: Trajectory → ℝ"]
    REF["Reflector\n(Meta-Policy π̂)"]
    MEM["Memory Store\n(Episodic + Semantic)"]
    PLAN["Planner / Goal Manager"]

    ENV -->|"observations, tool results"| ACT
    ACT -->|"actions, tool calls"| ENV
    ACT -->|"execution trace"| MON
    MON -->|"scored trajectory"| REF
    REF -->|"reflection text / updated beliefs"| MEM
    MEM -->|"retrieved context"| ACT
    MEM -->|"retrieved context"| PLAN
    PLAN -->|"subgoal sequence"| ACT
    REF -->|"plan revision"| PLAN
```

Each subsystem has a precisely defined contract:

**Performance Monitor** ingests the full execution trace — the sequence of (thought, action, observation) triples — and emits a scalar score or structured critique. The monitor can be:
- *Rule-based*: deterministic functions over trace features (e.g., did the final answer match ground truth; did a tool call raise an exception).
- *Model-based*: a separate LLM call that acts as a critic, evaluating coherence, factual accuracy, and goal alignment.
- *Hybrid*: rule-based pass/fail gates combined with an LLM critic for qualitative diagnosis.

**Reflector** takes the scored trace and produces a *reflection artifact* — a structured or free-text description of what failed and why. The quality of this artifact is the single largest determinant of whether the next episode improves. A weak reflector produces vague output ("the agent made mistakes"); a strong reflector performs root-cause analysis ("in step 3, the agent assumed the API returned ISO 8601 timestamps, but the actual format was Unix epoch milliseconds, causing the date comparison to always evaluate false").

**Memory Store** persists reflection artifacts and successful trajectories. Architecture choices here have major downstream consequences:
- *Flat episodic buffer*: simple FIFO queue of past reflections. O(1) write, O(n) retrieval.
- *Retrieval-augmented store*: embeddings indexed in a vector database. Enables semantic retrieval of the most relevant past reflections for a given new task. This is the architecture used in *MemGPT* (Packer et al., 2023) and *Generative Agents* (Park et al., 2023).
- *Structured knowledge graph*: facts extracted from reflections stored as (subject, predicate, object) triples. Enables logical reasoning over accumulated experience.

**Planner** receives updated context from memory and from the reflector to revise the subgoal sequence. In hierarchical agent architectures (e.g., AutoGen, LangGraph), this corresponds to a supervisor agent that re-routes tasks after a failed subagent execution.

### The Reflexion Pattern: Concrete Implementation

The following is a production-quality implementation of the Reflexion loop for a tool-using LLM agent. It uses the OpenAI API directly (no framework magic obscuring the mechanics) to make the data flow explicit.

```python
"""
reflexion_agent.py — Production implementation of the Reflexion loop.

Architecture:
  - Object-level policy: GPT-4o with tool calls
  - Reflector: separate GPT-4o critic call
  - Memory: in-process episodic buffer with cosine-similarity retrieval
  - Performance monitor: hybrid rule + critic

Requires: openai>=1.30.0, numpy, python-dotenv
"""
from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads OPENAI_API_KEY from a .env file if present
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """A single (thought, action, observation) triple in a trajectory."""
    thought: str
    action: dict[str, Any]   # {"type": "tool_call", "name": str, "args": dict} | {"type": "answer", "value": str}
    observation: str
    success: bool = True      # False if the action raised an exception


@dataclass
class Episode:
    """One complete attempt at a task."""
    task: str
    steps: list[Step] = field(default_factory=list)
    final_answer: str | None = None
    score: float = 0.0        # 0.0 (total failure) to 1.0 (perfect)
    reflection: str = ""      # Post-hoc reflection artifact


@dataclass
class ReflectionMemory:
    """
    Episodic memory for reflection artifacts.

    Uses embedding-based retrieval so that reflections from semantically
    similar past tasks are surfaced for new tasks — not just the most recent.
    """
    _entries: list[tuple[np.ndarray, str]] = field(default_factory=list)

    def _embed(self, text: str) -> np.ndarray:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def write(self, task: str, reflection: str) -> None:
        embedding = self._embed(task + "\n" + reflection)
        self._entries.append((embedding, reflection))

    def retrieve(self, task: str, top_k: int = 3) -> list[str]:
        """Return the top_k most relevant past reflections for the given task."""
        if not self._entries:
            return []
        query_emb = self._embed(task)
        # Cosine similarity: dot product of L2-normalised vectors
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        scores = []
        for emb, text in self._entries:
            emb_norm = emb / (np.linalg.norm(emb) + 1e-9)
            scores.append((float(query_norm @ emb_norm), text))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scores[:top_k]]


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

ToolFn = Callable[..., str]

TOOL_REGISTRY: dict[str, tuple[ToolFn, dict]] = {}


def register_tool(name: str, description: str, parameters: dict):
    """Decorator to register a Python function as an agent tool."""
    def decorator(fn: ToolFn) -> ToolFn:
        TOOL_REGISTRY[name] = (fn, {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })
        return fn
    return decorator


@register_tool(
    name="python_exec",
    description="Execute a Python code snippet and return stdout. Use for calculations, data manipulation.",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute."},
        },
        "required": ["code"],
        "additionalProperties": False,
    },
)
def python_exec(code: str) -> str:
    """
    Sandboxed Python execution.
    WARNING: In production, replace with a proper sandbox (e.g., RestrictedPython,
    a subprocess with seccomp, or a containerised executor).
    """
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<agent>", "exec"), {})  # noqa: S102
        return buf.getvalue() or "(no output)"
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Performance monitor
# ---------------------------------------------------------------------------

def rule_based_score(episode: Episode, ground_truth: str | None) -> float:
    """
    Fast, deterministic scoring layer.
    Returns 1.0 for perfect, 0.0 for complete failure, 0.7 for partial.
    """
    # Hard failure: any tool call raised an exception
    if any(not step.success for step in episode.steps):
        return 0.0
    # Hard success: exact match with ground truth (when available)
    if ground_truth and episode.final_answer:
        if ground_truth.strip().lower() == episode.final_answer.strip().lower():
            return 1.0
        # Partial credit: ground truth is a substring of the answer
        if ground_truth.strip().lower() in (episode.final_answer or "").lower():
            return 0.7
    # No ground truth — defer to LLM critic
    return -1.0  # sentinel: "needs LLM evaluation"


def llm_critic_score(episode: Episode, task: str) -> tuple[float, str]:
    """
    LLM-based critic. Returns (score, critique_text).
    The critic is instructed to be harsh and specific.
    """
    trace_text = "\n".join(
        f"Step {i+1}:\n  Thought: {s.thought}\n  Action: {json.dumps(s.action)}\n  Observation: {s.observation}"
        for i, s in enumerate(episode.steps)
    )
    prompt = textwrap.dedent(f"""
        You are a strict evaluator for an AI agent.

        TASK: {task}

        EXECUTION TRACE:
        {trace_text}

        FINAL ANSWER: {episode.final_answer or "(none)"}

        Evaluate the agent's performance. Respond in JSON with exactly these fields:
        {{
          "score": <float between 0.0 and 1.0>,
          "critique": "<specific, actionable description of what went wrong or right>"
        }}

        Be specific about which step failed and why. Do not be lenient.
    """)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    result = json.loads(response.choices[0].message.content)
    return float(result["score"]), result["critique"]


# ---------------------------------------------------------------------------
# Reflector
# ---------------------------------------------------------------------------

def generate_reflection(episode: Episode, task: str, critique: str) -> str:
    """
    Produce a natural-language reflection artifact.

    The reflection must be specific enough to change behaviour on the next attempt.
    Generic reflections ("I should be more careful") are useless — the prompt
    explicitly penalises vagueness.
    """
    prompt = textwrap.dedent(f"""
        You are a reflective AI agent reviewing your own failed or suboptimal attempt.

        TASK: {task}
        SCORE: {episode.score:.2f} / 1.00
        CRITIQUE: {critique}

        Write a concise but technically precise reflection (3–6 sentences) that:
        1. Identifies the specific root cause of the failure.
        2. Explains what assumption or action was incorrect.
        3. States a concrete, actionable change for the next attempt.

        Do NOT write generic advice. If you cannot identify the root cause, say so explicitly.
        Begin with "In this attempt, ..."
    """)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Object-level policy (action executor)
# ---------------------------------------------------------------------------

def run_episode(task: str, prior_reflections: list[str], max_steps: int = 10) -> Episode:
    """
    Execute one episode of the agent attempting the task.

    Prior reflections are injected into the system prompt, shifting the
    prior over actions without any weight update — this is in-context RL.
    """
    episode = Episode(task=task)
    tools = [spec for _, spec in TOOL_REGISTRY.values()]

    system_parts = [
        "You are a precise, tool-using AI agent. Think step-by-step before acting.",
        "When you have the final answer, respond with FINAL_ANSWER: <answer>.",
    ]
    if prior_reflections:
        reflection_block = "\n\n".join(
            f"Past reflection {i+1}:\n{r}" for i, r in enumerate(prior_reflections)
        )
        system_parts.append(
            f"\n\nLearn from your past mistakes:\n{reflection_block}"
        )

    messages: list[dict] = [
        {"role": "system", "content": "\n".join(system_parts)},
        {"role": "user", "content": task},
    ]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.0,
        )
        msg = response.choices[0].message
        messages.append(msg)

        # --- Check for final answer ---
        if msg.content and "FINAL_ANSWER:" in msg.content:
            episode.final_answer = msg.content.split("FINAL_ANSWER:", 1)[1].strip()
            break

        # --- Process tool calls ---
        if not msg.tool_calls:
            # Model stopped without a final answer or tool call — treat as failure
            episode.steps.append(Step(
                thought=msg.content or "",
                action={"type": "no_op"},
                observation="Agent produced no action and no final answer.",
                success=False,
            ))
            break

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            tool_fn, _ = TOOL_REGISTRY.get(fn_name, (None, None))
            if tool_fn is None:
                observation = f"ERROR: Unknown tool '{fn_name}'"
                success = False
            else:
                observation = tool_fn(**fn_args)
                success = not observation.startswith("ERROR:")

            episode.steps.append(Step(
                thought=msg.content or "",
                action={"type": "tool_call", "name": fn_name, "args": fn_args},
                observation=observation,
                success=success,
            ))
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": observation,
            })

    return episode


# ---------------------------------------------------------------------------
# Reflexion outer loop
# ---------------------------------------------------------------------------

def reflexion(
    task: str,
    max_episodes: int = 4,
    success_threshold: float = 0.9,
    ground_truth: str | None = None,
    memory: ReflectionMemory | None = None,
) -> Episode:
    """
    Outer Reflexion loop.

    Runs up to max_episodes attempts, reflecting after each failure.
    Returns the best episode (by score).
    """
    if memory is None:
        memory = ReflectionMemory()

    best_episode: Episode | None = None

    for episode_idx in range(max_episodes):
        # Retrieve relevant past reflections from memory
        prior_reflections = memory.retrieve(task, top_k=3)

        print(f"\n=== Episode {episode_idx + 1} / {max_episodes} ===")
        episode = run_episode(task, prior_reflections)

        # Score the episode
        rule_score = rule_based_score(episode, ground_truth)
        if rule_score >= 0:
            episode.score = rule_score
            critique = "Rule-based evaluation: exact or near-exact match." if rule_score > 0 else \
                       "Rule-based evaluation: tool execution errors detected."
        else:
            episode.score, critique = llm_critic_score(episode, task)

        print(f"Score: {episode.score:.2f} | Critique: {critique[:120]}...")

        if best_episode is None or episode.score > best_episode.score:
            best_episode = episode

        # Success — stop early
        if episode.score >= success_threshold:
            print("Success threshold reached. Stopping.")
            break

        # Generate and persist reflection for next episode
        reflection = generate_reflection(episode, task, critique)
        episode.reflection = reflection
        memory.write(task, reflection)
        print(f"Reflection: {reflection[:200]}...")

    return best_episode  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mem = ReflectionMemory()

    result = reflexion(
        task=(
            "What is the compound annual growth rate (CAGR) of an investment "
            "that grows from $12,500 to $31,200 over 7 years? "
            "Express the answer as a percentage rounded to two decimal places."
        ),
        max_episodes=4,
        success_threshold=0.9,
        ground_truth="13.96%",
        memory=mem,
    )

    print(f"\n=== Final Answer ===\n{result.final_answer}")
    print(f"Best score: {result.score:.2f}")
```

### Detailed Data-Flow Walkthrough

```mermaid
sequenceDiagram
    participant U as User / Orchestrator
    participant RL as Reflexion Loop
    participant AP as Action Policy (GPT-4o)
    participant T as Tool Executor
    participant PM as Performance Monitor
    participant RF as Reflector (GPT-4o)
    participant MS as Memory Store

    U->>RL: task + max_episodes
    loop For each episode
        RL->>MS: retrieve(task, top_k=3)
        MS-->>RL: prior_reflections[]
        RL->>AP: system_prompt + prior_reflections + task
        loop Until FINAL_ANSWER or max_steps
            AP-->>RL: tool_call(name, args)
            RL->>T: execute(name, args)
            T-->>RL: observation
            RL->>AP: tool_result(observation)
        end
        AP-->>RL: FINAL_ANSWER: <value>
        RL->>PM: score(episode, ground_truth)
        PM-->>RL: score + critique
        alt score >= threshold
            RL->>U: return best_episode
        else score < threshold
            RL->>RF: generate_reflection(episode, critique)
            RF-->>RL: reflection_text
            RL->>MS: write(task, reflection_text)
        end
    end
    RL->>U: return best_episode
```

---

## 3. Reflection Architectures Beyond Reflexion

### 3.1 Self-Consistency as Implicit Reflection

Wang et al. (2022) introduce *Self-Consistency*: sample $k$ reasoning chains independently, then take a majority vote over final answers. This is reflection without a critic — the ensemble of chains implicitly evaluates each other. The key insight is that consistency across independently sampled paths is a proxy for correctness: an answer that emerges from many different reasoning routes is less likely to be an artifact of a single flawed chain.

Self-consistency is cheap to implement and requires no ground truth, but it scales as $O(k)$ in token cost and provides no diagnostic signal about *why* an answer is wrong.

### 3.2 Constitutional AI and Critique-Revision

Anthropic's Constitutional AI (Bai et al., 2022) operationalizes reflection through explicit *critique-revision* cycles: the model first generates a response, then critiques it against a fixed set of principles (the "constitution"), then revises the response in light of the critique. This is applied recursively until the critique finds no violations.

The architectural implication is important: the same model serves as both actor and critic. This creates a potential for *sycophantic* reflection — the critic approves whatever the actor produces. Research (Huang et al., 2023, "Large Language Models Cannot Self-Correct Reasoning Yet") shows this is a real failure mode: intrinsic self-correction without external feedback tends to degrade rather than improve reasoning accuracy. The lesson is that an effective critic requires either a *separate* model, *ground-truth signal injection*, or *external tool execution* to anchor its evaluation.

### 3.3 Tree-of-Thought Reflection

Yao et al. (2023) extend chain-of-thought into a tree search over partial solutions. Reflection here operates at the node-evaluation level: after generating a partial reasoning step, the model *evaluates* each node (via self-scoring: "Is this step promising? Rate 1–10") and uses breadth-first or depth-first search, with the LLM's own evaluation of each state, to prune the search tree.

```mermaid
graph TD
    ROOT["Root: Task"]
    T1["Thought 1a\nscore: 7/10"]
    T2["Thought 1b\nscore: 4/10"]
    T3["Thought 1c\nscore: 9/10"]
    T3A["Thought 2a\nscore: 8/10"]
    T3B["Thought 2b\nscore: 3/10"]
    T3A1["Thought 3a\nscore: 10/10 ✓"]

    ROOT --> T1
    ROOT --> T2
    ROOT --> T3
    T3 --> T3A
    T3 --> T3B
    T3A --> T3A1

    style T2 fill:#ffcccc,stroke:#cc0000,color:#0f172a
    style T3B fill:#ffcccc,stroke:#cc0000,color:#0f172a
    style T3A1 fill:#ccffcc,stroke:#00cc00,color:#0f172a
```

The reflection operation is the node scoring function. Pruned branches (shown in red) represent discarded hypotheses — the agent has implicitly reflected that those reasoning paths are unlikely to yield correct answers.

---

## 4. High-Performance Optimization & Failure Modes

### 4.1 Latency Budget Allocation

Reflection is not free. Each critic call and each reflection generation adds latency proportional to the token count of the execution trace. In a production system with p99 latency SLAs, the reflection budget must be explicitly managed:

```text
Total latency budget = T_plan + T_execute + T_reflect
T_reflect = T_critic + T_reflector + T_retrieval
```

Optimization strategies in order of impact:

**Lazy reflection**: Only invoke the full critic+reflector pipeline when the rule-based monitor detects a failure signal (exception, empty result, contradiction with known facts). Pass through immediately on rule-based success. This eliminates the LLM critic call for the majority of successful runs.

**Asynchronous reflection**: Write reflections to memory asynchronously, outside the critical path. The current episode cannot benefit from its own reflection, so there is no logical requirement to block on it. Use a background thread or async task.

**Trace compression**: The LLM critic does not need the full raw trace — only the semantically significant steps. A lightweight heuristic filter (e.g., keep steps where `success=False`, keep the final 3 steps, keep steps where the observation exceeds a novelty threshold) can reduce trace length by 60–80% with minimal impact on critique quality.

**Speculative reflection**: For high-stakes tasks where multiple episodes are expected, begin generating the reflection for episode $n$ speculatively while episode $n+1$ is still executing. The reflection will be ready to write to memory the moment episode $n+1$ completes.

### 4.2 Failure Mode Taxonomy

```mermaid
graph TD
    FM["Reflection Failure Modes"]
    FM --> HA["Hallucinated Attribution\n(Reflector invents a cause\nthat did not occur in the trace)"]
    FM --> SC["Sycophantic Critique\n(Critic approves bad output;\nactor & critic share weights)"]
    FM --> RM["Reward Misspecification\n(Metric optimised ≠ true goal;\nGoodhart's Law)"]
    FM --> FG["Forgetting\n(New reflections overwrite\ncritical old knowledge)"]
    FM --> OC["Oscillation\n(Agent alternates between\ntwo suboptimal strategies)"]
    FM --> OO["Over-reflection\n(Excessive self-doubt;\ncompetent plans abandoned)"]

    HA --> HA_M["Mitigation: Ground critic in\nexact trace line references"]
    SC --> SC_M["Mitigation: Separate critic model;\nexternal ground-truth signal"]
    RM --> RM_M["Mitigation: Multi-objective metrics;\nhuman eval spot-checks"]
    FG --> FG_M["Mitigation: Importance-weighted\nmemory; never-evict critical entries"]
    OC --> OC_M["Mitigation: Detect oscillation;\nforce exploration via temperature"]
    OO --> OO_M["Mitigation: Confidence threshold;\nlimit reflection episodes"]
```

**Hallucinated Attribution** is particularly insidious in LLM-based critics. The model may generate a plausible-sounding but incorrect causal explanation ("The API call failed because the authentication token expired") when the trace shows the token was valid and the actual error was a malformed JSON body. The mitigation requires the critic prompt to reference specific step indices and quote exact observation text — grounding that makes fabrication detectable.

**Reward Misspecification** (Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure") is endemic. An agent optimised purely on task-completion rate may learn to produce confident-sounding wrong answers that satisfy a lenient critic. Defence requires diverse, complementary metrics: execution correctness *and* answer quality *and* reasoning coherence.

**Oscillation** occurs when reflection produces contradictory guidance across episodes. Episode 1 reflection: "You searched too broadly; narrow the query." Episode 2 reflection: "You missed results; broaden the query." The agent has no mechanism to reconcile these. The fix is to maintain a *reflection summary* that integrates across episodes rather than naively prepending the most recent reflection.

### 4.3 Memory Architecture for Persistent Reflection

The in-process `ReflectionMemory` above is sufficient for single-session use. For production multi-user, multi-session deployments, a persistent vector store is required:

```python
"""
persistent_memory.py — Production reflection memory using pgvector.

Schema (run once):
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE reflection_memory (
        id          BIGSERIAL PRIMARY KEY,
        agent_id    TEXT        NOT NULL,
        task_hash   TEXT        NOT NULL,
        task_text   TEXT        NOT NULL,
        reflection  TEXT        NOT NULL,
        score       REAL        NOT NULL,
        embedding   vector(1536) NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX ON reflection_memory
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

Requires: psycopg[binary]>=3.1, openai>=1.30.0
"""
from __future__ import annotations

import hashlib
import os
from typing import Sequence

import psycopg
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
DSN = os.environ["PGVECTOR_DSN"]  # e.g. "postgresql://user:pass@host/db"


def _embed(text: str) -> list[float]:
    return client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    ).data[0].embedding


def write_reflection(
    agent_id: str,
    task: str,
    reflection: str,
    score: float,
) -> None:
    task_hash = hashlib.sha256(task.encode()).hexdigest()[:16]
    embedding = _embed(task + "\n" + reflection)
    with psycopg.connect(DSN) as conn:
        conn.execute(
            """
            INSERT INTO reflection_memory
                (agent_id, task_hash, task_text, reflection, score, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
            """,
            (agent_id, task_hash, task, reflection, score, embedding),
        )
        conn.commit()


def retrieve_reflections(
    agent_id: str,
    task: str,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[tuple[float, str, str]]:
    """
    Returns list of (similarity, task_text, reflection) for the top_k
    most relevant past reflections for this agent.

    Filters by min_score to avoid retrieving low-quality reflections
    (e.g., reflections from near-random early episodes).
    """
    embedding = _embed(task)
    with psycopg.connect(DSN) as conn:
        rows = conn.execute(
            """
            SELECT
                1 - (embedding <=> %s::vector) AS cosine_similarity,
                task_text,
                reflection
            FROM reflection_memory
            WHERE agent_id = %s
              AND score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (embedding, agent_id, min_score, embedding, top_k),
        ).fetchall()
    return [(float(r[0]), r[1], r[2]) for r in rows]
```

The `ivfflat` index with cosine distance enables approximate nearest-neighbour search over millions of reflection embeddings in sub-millisecond time. The `min_score` filter is critical: without it, low-quality reflections from early, poorly-performing episodes pollute retrieval results for later, more capable episodes.

### 4.4 Measuring Reflection Effectiveness

Reflection mechanisms must be empirically evaluated, not just theoretically justified. The following metrics form a minimum viable evaluation suite:

| Metric | Definition | Good Signal |
|--------|-----------|-------------|
| **Pass@k** | Fraction of tasks solved within $k$ episodes | Increases with $k$ faster than random retry |
| **Reflection Utility Rate (RUR)** | Fraction of episodes where the agent's behaviour demonstrably changed in response to a reflection | >50% |
| **Critique Accuracy** | Fraction of critiques that correctly identify the actual root cause | >70% via human eval |
| **Score Trajectory Slope** | Linear regression slope of score vs. episode index | Positive (improving) |
| **Oscillation Rate** | Fraction of episode pairs where score decreases after a non-zero score | < 10% |

A reflection mechanism where Pass@k does not improve significantly over Pass@1 (baseline: retry without reflection) is not functioning. This is the null hypothesis that every reflection implementation must disprove.

---

## 5. Advanced Topics: Meta-Reflection and Learned Critics

### 5.1 Meta-Reflection

Standard reflection operates on a single task. *Meta-reflection* operates on the reflection process itself: after accumulating $N$ episodes across diverse tasks, the agent (or an operator) analyses the corpus of reflection artifacts to identify systematic biases.

For example, a meta-reflection might reveal: "This agent consistently over-relies on its first tool call result without verification. 73% of failures involve accepting an unverified intermediate result." This insight is structural — it cannot be captured by per-episode reflection because it requires cross-episode pattern recognition.

Meta-reflection artifacts are injected into the *system prompt* (not just the episodic context), making them part of the agent's persistent behavioural prior rather than task-specific context.

### 5.2 Learned Reward Models as Critics

The LLM-critic approach is powerful but expensive and potentially inconsistent. A trained *reward model* (RM) — a small classifier fine-tuned on (trajectory, human_label) pairs — can serve as a critic at a fraction of the latency cost. This is the approach used in RLHF (Reinforcement Learning from Human Feedback) pipelines: the RM internalises human preferences and can score trajectories in a single forward pass rather than a full LLM generation.

The tradeoff is brittleness: a reward model trained on a fixed distribution of tasks will produce unreliable scores on out-of-distribution inputs. The LLM critic, being a general reasoner, generalises better but costs more. In practice, the optimal architecture is a cascade: RM scores first (cheap), LLM critic invoked only when the RM score is in an uncertain region (e.g., 0.3–0.7).

### 5.3 Integration with External Verifiers

For tasks with formal correctness criteria — mathematical proofs, code, formal specifications — external *verifiers* provide ground truth that no LLM critic can match. A reflection loop grounded in a Python interpreter, a proof assistant (Lean, Coq), or a test suite receives binary, unambiguous feedback. This eliminates the hallucinated-attribution failure mode entirely for the scoring step.

The architecture is:

```mermaid
graph LR
    AG["Agent\n(LLM)"] -->|"code / proof"| VER["External Verifier\n(interpreter / test suite)"]
    VER -->|"pass/fail + error trace"| RF["Reflector\n(LLM)"]
    RF -->|"reflection"| MEM["Memory"]
    MEM -->|"prior reflections"| AG
```

The verifier provides the *what* (which assertion failed, which test case), and the reflector provides the *why* (root cause analysis in natural language). This division of labour — formal tools for correctness, LLMs for diagnosis — is the most robust reflection architecture currently known.

---

## 6. Summary

Reflection mechanisms transform agents from open-loop executors into closed-loop learners. The theoretical foundation rests on three invariants — observability, credit assignment, and policy improvement monotonicity — that must be satisfied for reflection to produce meaningful improvement.

The practical architecture combines a performance monitor (rule-based gates + LLM critic), a reflector (root-cause diagnosis), and a memory store (embedding-indexed episodic buffer) in a loop that runs for at most $k$ episodes before returning the best result. The Reflexion pattern (Shinn et al., 2023) demonstrates that this loop is achievable without any gradient updates — natural language reflections stored in context can substitute for parameter updates in many task settings.

Production deployment requires explicit management of the latency budget (lazy evaluation, trace compression, async writes), careful metric design to avoid Goodhart's Law, and empirical validation that reflection actually improves Pass@k over naive retry. Where formal verifiers exist, they should be integrated as the primary scoring signal, with LLM critics reserved for tasks without formal correctness criteria.
