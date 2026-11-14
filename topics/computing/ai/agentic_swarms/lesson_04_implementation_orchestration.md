# Lesson 4: Implementation Orchestration

## 1. First-Principles Intuition & Invariants

The transition from conceptual multi-agent architectures to production-grade agentic swarms demands rigorous orchestration mechanisms that govern agent lifecycles, inter-agent communication protocols, resource allocation boundaries, and failure recovery semantics. At its foundation, an agentic swarm represents a distributed computational graph where nodes execute stateful inference operations and edges transmit structured messages carrying context, intermediate reasoning artifacts, and control signals. Unlike traditional microservice architectures where service boundaries are statically defined by API contracts, agentic swarms exhibit dynamic topology reconfiguration: agents spawn, terminate, and reorganize communication paths based on runtime problem decomposition and resource availability.

The fundamental invariant distinguishing robust swarm implementations from brittle prototypes lies in their adherence to the **agent autonomy-coordination duality principle**. Each agent must maintain local decision-making authority—selecting inference strategies, managing internal state, and determining message dispatch schedules—while simultaneously participating in global coordination protocols that prevent resource exhaustion, cyclic dependencies, and deadlock conditions. This duality mirrors the tension between process isolation and inter-process communication in operating systems: agents require strong isolation guarantees to prevent cascading failures, yet must maintain low-latency communication channels to enable coherent collective behavior.

Production orchestration systems must satisfy three critical invariants that emerge from the physics of distributed inference workloads. First, **bounded resource consumption** dictates that agent populations cannot grow unboundedly regardless of problem complexity; orchestrators must enforce memory limits, GPU allocation quotas, and token budget constraints at both per-agent and swarm-aggregate levels. Second, **message ordering guarantees** determine correctness properties for collaborative reasoning: certain workflows require strict causal ordering where agent B processes messages from agent A in transmission order, while others tolerate reordering for throughput optimization. Third, **observability completeness** requires that all agent state transitions, message exchanges, and resource utilization metrics flow into centralized telemetry systems, enabling operators to reconstruct execution traces and diagnose emergent pathologies.

The lifecycle of an agent within a managed swarm progresses through six canonical states that define its relationship to both the orchestration substrate and peer agents. An agent begins in the **provisioning** state where the orchestrator allocates computational resources—CPU cores, GPU memory slices, or API rate limit tokens—and initializes the agent's execution context with problem-specific configuration, system prompts, and tool access credentials. Upon successful resource acquisition, the agent transitions to **ready** status, signaling availability to receive task assignments and participate in message passing protocols. Active inference work occurs in the **executing** state where the agent invokes language model APIs, processes tool call responses, and generates intermediate reasoning artifacts. When computation completes or resource budgets exhaust, agents enter **idle** status where they remain allocated but inactive, allowing rapid reactivation without reinitialization overhead. Controlled shutdown sequences transition agents through **draining** phases that flush message queues and persist checkpoint state before reaching terminal **terminated** status where all resources return to the orchestrator's allocation pool.

Message passing architectures for agentic swarms diverge sharply from traditional distributed systems paradigms because they must accommodate the semantic richness of natural language exchanges combined with structured metadata for routing, priority, and causal relationships. A production message envelope encapsulates not merely payload content but provenance information tracking which agents participated in prior reasoning chains, semantic annotations indicating message intent categories like "delegation request," "evidence contribution," or "consensus vote," and resource attribution data quantifying token consumption and inference latency. The choice between synchronous request-response patterns and asynchronous publish-subscribe topologies fundamentally shapes swarm behavior: synchronous messaging creates explicit dependency graphs where agent A blocks awaiting agent B's response, enabling deterministic execution but limiting parallelism, while asynchronous patterns maximize throughput at the cost of introducing complex eventual consistency semantics.

Resource constraints in multi-agent systems manifest across four orthogonal dimensions that orchestrators must regulate independently. **Computational resources** include GPU memory for parallel inference, CPU cycles for tool execution and message serialization, and network bandwidth for distributing model weights in federated deployments. **Token budgets** represent the most financially critical constraint: each agent consumes input and output tokens at market rates, and orchestrators must prevent runaway costs through per-agent rate limiting, swarm-level spend caps, and priority-based allocation where high-value reasoning paths receive preferential token access. **Concurrency limits** bound the number of simultaneously executing agents to prevent context thrashing where excessive parallelism degrades individual agent performance through resource contention. Finally, **temporal constraints** enforce wall-clock deadlines for task completion, requiring orchestrators to preemptively terminate agents that exceed latency budgets and redistribute their workloads.

The observability challenge in swarm orchestration stems from the combinatorial explosion of state space: a swarm with ten agents exchanging messages produces execution traces spanning thousands of events per second, embedding causal relationships that span multiple reasoning hops and involving both structured metadata and unstructured natural language artifacts. Traditional distributed tracing systems designed for microservices prove inadequate because they model service interactions as discrete RPC calls with bounded payloads, whereas agent message exchanges carry rich semantic context that operators must analyze to diagnose reasoning failures. A complete observability stack for production swarms must capture three complementary data streams: **event logs** recording state transitions with microsecond timestamps and causal ordering metadata, **message archives** preserving full content of inter-agent exchanges with semantic annotations, and **resource telemetry** tracking GPU utilization curves, token consumption rates, and memory allocation watermarks at per-agent granularity.

## 2. Core Architecture & Mechanics

Production orchestration platforms for agentic swarms decompose into five architectural layers that separate concerns and enable independent scaling of different operational aspects. At the foundation, the **resource substrate layer** interfaces with underlying compute infrastructure—Kubernetes clusters, cloud VM fleets, or bare-metal GPU servers—translating abstract agent resource requests into concrete allocations of CPU cores, memory pages, and accelerator devices. Above this, the **agent runtime layer** manages individual agent process lifecycles, injecting environment configuration, exposing tool APIs, and enforcing isolation boundaries through containerization or process sandboxing. The **message transport layer** implements reliable delivery semantics for inter-agent communication, providing primitives for point-to-point messaging, broadcast distribution, and ordered multicast with exactly-once delivery guarantees. Coordination logic resides in the **orchestration control plane** which interprets high-level task graphs, performs resource scheduling, and enforces global invariants like total token budget constraints. Finally, the **observability plane** runs orthogonally across all layers, collecting telemetry streams and exposing query interfaces for operational analysis.

The agent runtime layer implements the core execution primitive: a managed process or container that encapsulates a single agent's inference loop, tool execution environment, and communication interfaces. A robust runtime design employs a supervisor process pattern where a lightweight control agent wraps the primary inference engine, intercepting all external interactions to enforce resource limits and collect telemetry. This supervisor architecture enables transparent injection of monitoring instrumentation without modifying agent code and provides a unified mechanism for lifecycle management regardless of whether agents run as Python processes, compiled binaries, or serverless functions.

```python
# Production agent runtime supervisor implementation
import asyncio
import time
import psutil
from dataclasses import dataclass
from typing import Optional, Callable, Any
from enum import Enum

class AgentState(Enum):
    PROVISIONING = "provisioning"
    READY = "ready"
    EXECUTING = "executing"
    IDLE = "idle"
    DRAINING = "draining"
    TERMINATED = "terminated"

@dataclass
class ResourceQuota:
    """Per-agent resource limits enforced by supervisor."""
    max_memory_mb: int
    max_cpu_percent: float
    token_budget: int
    max_execution_time_sec: int
    max_tool_calls: int

@dataclass
class AgentMetrics:
    """Real-time resource utilization metrics."""
    current_memory_mb: float
    cpu_percent: float
    tokens_consumed: int
    execution_time_sec: float
    tool_calls_made: int
    messages_sent: int
    messages_received: int

class AgentSupervisor:
    """Supervises agent lifecycle and resource enforcement."""
    
    def __init__(
        self,
        agent_id: str,
        agent_factory: Callable[[], Any],
        quota: ResourceQuota,
        message_bus: 'MessageBus',
        metrics_sink: 'MetricsSink'
    ):
        self.agent_id = agent_id
        self.agent_factory = agent_factory
        self.quota = quota
        self.message_bus = message_bus
        self.metrics_sink = metrics_sink
        
        self.state = AgentState.PROVISIONING
        self.agent_instance: Optional[Any] = None
        self.process: Optional[psutil.Process] = None
        
        self.metrics = AgentMetrics(
            current_memory_mb=0.0,
            cpu_percent=0.0,
            tokens_consumed=0,
            execution_time_sec=0.0,
            tool_calls_made=0,
            messages_sent=0,
            messages_received=0
        )
        
        self.start_time: Optional[float] = None
        self.checkpoint_state: Optional[dict] = None
        self._resource_monitor_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        
    async def provision(self) -> bool:
        """Allocate resources and initialize agent instance."""
        try:
            # Initialize agent with injected dependencies
            self.agent_instance = self.agent_factory()
            self.process = psutil.Process()
            
            # Verify initial resource allocation
            initial_memory = self.process.memory_info().rss / (1024 * 1024)
            if initial_memory > self.quota.max_memory_mb:
                raise ResourceError(f"Initial memory {initial_memory}MB exceeds quota")
            
            self.state = AgentState.READY
            self._emit_state_transition("provisioning", "ready")
            return True
            
        except Exception as e:
            self._emit_error("provision_failed", str(e))
            self.state = AgentState.TERMINATED
            return False
    
    async def execute(self, task: dict) -> None:
        """Execute agent inference with resource monitoring."""
        if self.state != AgentState.READY:
            raise StateError(f"Cannot execute from state {self.state}")
        
        self.state = AgentState.EXECUTING
        self.start_time = time.time()
        self._emit_state_transition("ready", "executing")
        
        # Start concurrent resource monitoring
        self._resource_monitor_task = asyncio.create_task(
            self._monitor_resources()
        )
        self._message_handler_task = asyncio.create_task(
            self._handle_messages()
        )
        
        try:
            # Wrap agent execution with token tracking
            result = await self._execute_with_limits(task)
            
            # Update metrics
            self.metrics.execution_time_sec = time.time() - self.start_time
            self._emit_metrics()
            
            # Transition to idle for reuse
            self.state = AgentState.IDLE
            self._emit_state_transition("executing", "idle")
            
            return result
            
        except ResourceExhausted as e:
            self._emit_error("resource_exhausted", str(e))
            await self.drain()
            raise
        except Exception as e:
            self._emit_error("execution_failed", str(e))
            await self.terminate()
            raise
        finally:
            # Cancel monitoring tasks
            if self._resource_monitor_task:
                self._resource_monitor_task.cancel()
            if self._message_handler_task:
                self._message_handler_task.cancel()
    
    async def _execute_with_limits(self, task: dict) -> Any:
        """Execute agent with enforced resource limits."""
        original_call = self.agent_instance.call_llm
        
        async def tracked_llm_call(*args, **kwargs):
            # Enforce token budget before each LLM call
            estimated_tokens = self._estimate_tokens(args, kwargs)
            if self.metrics.tokens_consumed + estimated_tokens > self.quota.token_budget:
                raise ResourceExhausted("Token budget exceeded")
            
            response = await original_call(*args, **kwargs)
            
            # Update token consumption from response
            actual_tokens = response.usage.total_tokens
            self.metrics.tokens_consumed += actual_tokens
            
            return response
        
        # Monkey-patch with tracking wrapper
        self.agent_instance.call_llm = tracked_llm_call
        
        try:
            return await asyncio.wait_for(
                self.agent_instance.run(task),
                timeout=self.quota.max_execution_time_sec
            )
        except asyncio.TimeoutError:
            raise ResourceExhausted("Execution time limit exceeded")
    
    async def _monitor_resources(self) -> None:
        """Continuously monitor and enforce resource limits."""
        while True:
            try:
                # Sample current resource usage
                mem_info = self.process.memory_info()
                self.metrics.current_memory_mb = mem_info.rss / (1024 * 1024)
                self.metrics.cpu_percent = self.process.cpu_percent(interval=0.1)
                
                # Enforce hard limits
                if self.metrics.current_memory_mb > self.quota.max_memory_mb:
                    raise ResourceExhausted(
                        f"Memory {self.metrics.current_memory_mb}MB exceeds quota"
                    )
                
                if self.metrics.cpu_percent > self.quota.max_cpu_percent:
                    # Soft limit: throttle but don't kill
                    self._emit_warning("cpu_throttle", self.metrics.cpu_percent)
                
                # Emit metrics every 5 seconds
                self._emit_metrics()
                
                await asyncio.sleep(5)
                
            except ResourceExhausted:
                raise
            except Exception as e:
                self._emit_error("monitoring_error", str(e))
    
    async def _handle_messages(self) -> None:
        """Process incoming messages from other agents."""
        async for message in self.message_bus.subscribe(self.agent_id):
            self.metrics.messages_received += 1
            
            try:
                # Deliver message to agent instance
                await self.agent_instance.receive_message(message)
            except Exception as e:
                self._emit_error("message_handling_failed", str(e))
    
    async def drain(self) -> None:
        """Gracefully shutdown agent, flushing state."""
        if self.state == AgentState.TERMINATED:
            return
        
        self.state = AgentState.DRAINING
        self._emit_state_transition(self.state.value, "draining")
        
        try:
            # Flush message queue
            await self.message_bus.flush(self.agent_id)
            
            # Persist checkpoint for potential recovery
            self.checkpoint_state = await self.agent_instance.save_checkpoint()
            
            # Final metrics emission
            self._emit_metrics()
            
        finally:
            await self.terminate()
    
    async def terminate(self) -> None:
        """Hard termination, release all resources."""
        self.state = AgentState.TERMINATED
        self._emit_state_transition(self.state.value, "terminated")
        
        # Cancel all background tasks
        if self._resource_monitor_task:
            self._resource_monitor_task.cancel()
        if self._message_handler_task:
            self._message_handler_task.cancel()
        
        # Release agent resources
        if self.agent_instance:
            await self.agent_instance.cleanup()
            self.agent_instance = None
        
        # Unsubscribe from message bus
        await self.message_bus.unsubscribe(self.agent_id)
    
    def _estimate_tokens(self, args, kwargs) -> int:
        """Heuristic token estimation for budget enforcement."""
        # Simplified: 1 token ≈ 4 characters
        text = str(args) + str(kwargs)
        return len(text) // 4
    
    def _emit_state_transition(self, from_state: str, to_state: str) -> None:
        """Emit structured state transition event."""
        event = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            "event_type": "state_transition",
            "from_state": from_state,
            "to_state": to_state
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_metrics(self) -> None:
        """Emit current resource utilization metrics."""
        metrics_dict = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            **self.metrics.__dict__
        }
        self.metrics_sink.emit_metrics(metrics_dict)
    
    def _emit_error(self, error_type: str, details: str) -> None:
        """Emit error event for operational alerting."""
        event = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            "event_type": "error",
            "error_type": error_type,
            "details": details,
            "state": self.state.value
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_warning(self, warning_type: str, value: Any) -> None:
        """Emit warning for soft limit violations."""
        event = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            "event_type": "warning",
            "warning_type": warning_type,
            "value": value
        }
        self.metrics_sink.emit_event(event)

class ResourceError(Exception):
    """Raised when resource allocation fails."""
    pass

class ResourceExhausted(Exception):
    """Raised when resource limits are exceeded during execution."""
    pass

class StateError(Exception):
    """Raised when operation is invalid for current state."""
    pass
```

The message transport layer provides reliable inter-agent communication abstractions that isolate agents from underlying network protocols and failure modes. Production implementations typically employ a message broker architecture where a centralized or distributed queue system mediates all agent-to-agent exchanges, enabling features like message persistence, delivery acknowledgments, and ordered delivery guarantees. The choice of message broker technology profoundly impacts swarm behavior: in-memory queues like Python's asyncio queues offer minimal latency but no durability across process failures, Redis Streams provide microsecond-latency pub/sub with limited persistence, while distributed brokers like Apache Kafka guarantee exactly-once semantics and infinite retention at the cost of millisecond-scale latency.

```python
# Message bus implementation with multiple delivery semantics
import asyncio
import json
import uuid
from typing import Dict, Set, Optional, AsyncIterator
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

class DeliveryMode(Enum):
    """Message delivery semantic guarantees."""
    AT_MOST_ONCE = "at_most_once"      # Fire and forget, no acks
    AT_LEAST_ONCE = "at_least_once"    # Retry until ack
    EXACTLY_ONCE = "exactly_once"       # Deduplication + acks

@dataclass
class Message:
    """Structured message envelope for inter-agent communication."""
    message_id: str
    sender_id: str
    recipient_id: str
    content: dict
    metadata: dict
    timestamp: float
    sequence_number: int
    parent_message_id: Optional[str] = None
    priority: int = 0
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'Message':
        return cls(**json.loads(data))

class MessageBus:
    """In-memory message broker with configurable delivery semantics."""
    
    def __init__(self, delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE):
        self.delivery_mode = delivery_mode
        
        # Per-agent message queues (recipient_id -> deque[Message])
        self._queues: Dict[str, deque[Message]] = defaultdict(deque)
        
        # Subscriber notification events (recipient_id -> Event)
        self._notify_events: Dict[str, asyncio.Event] = defaultdict(asyncio.Event)
        
        # Active subscriptions tracking
        self._active_subscribers: Set[str] = set()
        
        # Delivery acknowledgment tracking (message_id -> bool)
        self._pending_acks: Dict[str, Message] = {}
        
        # Deduplication for exactly-once (message_id -> bool)
        self._delivered_messages: Set[str] = set()
        
        # Sequence number tracking per sender (sender_id -> int)
        self._sequence_numbers: Dict[str, int] = defaultdict(int)
        
        # Message archive for debugging (limited retention)
        self._message_archive: deque[Message] = deque(maxlen=10000)
        
        self._lock = asyncio.Lock()
    
    async def publish(
        self,
        sender_id: str,
        recipient_id: str,
        content: dict,
        metadata: Optional[dict] = None,
        parent_message_id: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """Publish message to specific recipient."""
        
        # Generate unique message ID
        message_id = f"{sender_id}:{uuid.uuid4().hex}"
        
        # Assign monotonic sequence number per sender
        sequence_number = self._sequence_numbers[sender_id]
        self._sequence_numbers[sender_id] += 1
        
        message = Message(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            metadata=metadata or {},
            timestamp=asyncio.get_event_loop().time(),
            sequence_number=sequence_number,
            parent_message_id=parent_message_id,
            priority=priority
        )
        
        async with self._lock:
            # Exactly-once: check if already delivered
            if self.delivery_mode == DeliveryMode.EXACTLY_ONCE:
                if message_id in self._delivered_messages:
                    return message_id  # Deduplicate
            
            # Enqueue message (priority queue behavior)
            self._insert_by_priority(recipient_id, message)
            
            # Archive for debugging
            self._message_archive.append(message)
            
            # Track for acknowledgment if needed
            if self.delivery_mode in [DeliveryMode.AT_LEAST_ONCE, DeliveryMode.EXACTLY_ONCE]:
                self._pending_acks[message_id] = message
            
            # Notify subscriber if active
            if recipient_id in self._active_subscribers:
                self._notify_events[recipient_id].set()
        
        return message_id
    
    async def subscribe(self, agent_id: str) -> AsyncIterator[Message]:
        """Subscribe to incoming messages for agent."""
        async with self._lock:
            self._active_subscribers.add(agent_id)
        
        try:
            while True:
                # Wait for messages or notification
                message = await self._get_next_message(agent_id)
                
                if message is None:
                    # No messages available, wait for notification
                    await self._notify_events[agent_id].wait()
                    self._notify_events[agent_id].clear()
                    continue
                
                # Mark as delivered for exactly-once
                if self.delivery_mode == DeliveryMode.EXACTLY_ONCE:
                    async with self._lock:
                        self._delivered_messages.add(message.message_id)
                
                yield message
                
                # Auto-ack for at-most-once
                if self.delivery_mode == DeliveryMode.AT_MOST_ONCE:
                    await self.acknowledge(message.message_id)
                
        finally:
            async with self._lock:
                self._active_subscribers.discard(agent_id)
    
    async def _get_next_message(self, agent_id: str) -> Optional[Message]:
        """Retrieve next message from agent's queue."""
        async with self._lock:
            queue = self._queues.get(agent_id)
            if queue and len(queue) > 0:
                return queue.popleft()
            return None
    
    def _insert_by_priority(self, recipient_id: str, message: Message) -> None:
        """Insert message maintaining priority order (higher priority first)."""
        queue = self._queues[recipient_id]
        
        # Simple insertion sort by priority (descending)
        inserted = False
        for i, existing in enumerate(queue):
            if message.priority > existing.priority:
                queue.insert(i, message)
                inserted = True
                break
        
        if not inserted:
            queue.append(message)
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message delivery (removes from pending)."""
        async with self._lock:
            if message_id in self._pending_acks:
                del self._pending_acks[message_id]
                return True
            return False
    
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe agent from message bus."""
        async with self._lock:
            self._active_subscribers.discard(agent_id)
    
    async def flush(self, agent_id: str) -> int:
        """Flush remaining messages in agent's queue."""
        async with self._lock:
            queue = self._queues.get(agent_id)
            if queue:
                count = len(queue)
                queue.clear()
                return count
            return 0
    
    async def broadcast(
        self,
        sender_id: str,
        content: dict,
        recipient_ids: Set[str],
        metadata: Optional[dict] = None
    ) -> list[str]:
        """Broadcast message to multiple recipients."""
        message_ids = []
        
        for recipient_id in recipient_ids:
            msg_id = await self.publish(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                metadata=metadata
            )
            message_ids.append(msg_id)
        
        return message_ids
    
    def get_queue_depth(self, agent_id: str) -> int:
        """Query current queue depth for agent."""
        return len(self._queues.get(agent_id, []))
    
    def get_pending_acks(self) -> int:
        """Query total number of unacknowledged messages."""
        return len(self._pending_acks)
    
    def get_message_history(
        self,
        sender_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        limit: int = 100
    ) -> list[Message]:
        """Retrieve message history for debugging."""
        messages = list(self._message_archive)
        
        # Filter by sender/recipient if specified
        if sender_id:
            messages = [m for m in messages if m.sender_id == sender_id]
        if recipient_id:
            messages = [m for m in messages if m.recipient_id == recipient_id]
        
        return messages[-limit:]
```

The orchestration control plane coordinates swarm-level decisions by interpreting task specifications into agent spawning schedules and message routing policies. A production control plane implements a declarative reconciliation loop mirroring Kubernetes controllers: operators submit desired state specifications describing target agent populations, resource allocations, and coordination topologies, while the control plane continuously observes actual state and executes corrective actions to minimize divergence. This declarative paradigm enables self-healing behavior where the orchestrator automatically respawns failed agents, rebalances resource assignments when new compute nodes join the cluster, and scales agent populations in response to workload changes.

```python
# Swarm orchestration control plane
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import random

class SwarmTopology(Enum):
    """Predefined agent communication topologies."""
    FULLY_CONNECTED = "fully_connected"  # All agents communicate
    HIERARCHICAL = "hierarchical"         # Tree structure
    PIPELINE = "pipeline"                 # Linear chain
    STAR = "star"                         # Central coordinator

@dataclass
class SwarmSpec:
    """Declarative specification for desired swarm state."""
    swarm_id: str
    agent_count: int
    agent_type: str
    topology: SwarmTopology
    resource_quota: ResourceQuota
    token_budget_total: int
    max_execution_time_sec: int
    
    # Optional advanced configuration
    autoscaling_enabled: bool = False
    min_agents: int = 1
    max_agents: int = 10
    scale_up_threshold: float = 0.8  # CPU/memory utilization
    scale_down_threshold: float = 0.3

@dataclass
class SwarmState:
    """Actual observed state of running swarm."""
    swarm_id: str
    active_agents: Dict[str, AgentSupervisor] = field(default_factory=dict)
    message_bus: Optional[MessageBus] = None
    total_tokens_consumed: int = 0
    total_messages_exchanged: int = 0
    start_time: float = 0.0

class SwarmOrchestrator:
    """Orchestrates multi-agent swarm lifecycle and coordination."""
    
    def __init__(
        self,
        metrics_sink: 'MetricsSink',
        max_concurrent_swarms: int = 10
    ):
        self.metrics_sink = metrics_sink
        self.max_concurrent_swarms = max_concurrent_swarms
        
        # Swarm registry (swarm_id -> SwarmState)
        self._swarms: Dict[str, SwarmState] = {}
        
        # Desired state specifications (swarm_id -> SwarmSpec)
        self._desired_specs: Dict[str, SwarmSpec] = {}
        
        # Reconciliation loop task
        self._reconcile_task: Optional[asyncio.Task] = None
        
        # Global resource pool
        self._available_tokens = 1000000  # Example: 1M token pool
        
    async def create_swarm(self, spec: SwarmSpec) -> str:
        """Create new swarm from declarative specification."""
        if len(self._swarms) >= self.max_concurrent_swarms:
            raise ResourceError("Maximum concurrent swarms limit reached")
        
        # Validate resource availability
        if spec.token_budget_total > self._available_tokens:
            raise ResourceError(f"Insufficient token budget: need {spec.token_budget_total}, have {self._available_tokens}")
        
        # Register desired state
        self._desired_specs[spec.swarm_id] = spec
        
        # Initialize actual state
        state = SwarmState(
            swarm_id=spec.swarm_id,
            start_time=asyncio.get_event_loop().time()
        )
        
        # Create dedicated message bus for swarm
        state.message_bus = MessageBus(delivery_mode=DeliveryMode.AT_LEAST_ONCE)
        
        self._swarms[spec.swarm_id] = state
        
        # Reserve tokens from global pool
        self._available_tokens -= spec.token_budget_total
        
        # Trigger immediate reconciliation
        await self._reconcile_swarm(spec.swarm_id)
        
        return spec.swarm_id
    
    async def _reconcile_swarm(self, swarm_id: str) -> None:
        """Reconcile actual state with desired specification."""
        spec = self._desired_specs.get(swarm_id)
        state = self._swarms.get(swarm_id)
        
        if not spec or not state:
            return
        
        current_agent_count = len(state.active_agents)
        desired_agent_count = spec.agent_count
        
        # Scale up: spawn missing agents
        if current_agent_count < desired_agent_count:
            agents_to_spawn = desired_agent_count - current_agent_count
            await self._spawn_agents(swarm_id, agents_to_spawn)
        
        # Scale down: terminate excess agents
        elif current_agent_count > desired_agent_count:
            agents_to_terminate = current_agent_count - desired_agent_count
            await self._terminate_agents(swarm_id, agents_to_terminate)
        
        # Configure communication topology
        await self._configure_topology(swarm_id)
        
        # Emit reconciliation event
        self._emit_reconciliation_event(swarm_id, current_agent_count, desired_agent_count)
    
    async def _spawn_agents(self, swarm_id: str, count: int) -> None:
        """Spawn new agents in swarm."""
        spec = self._desired_specs[swarm_id]
        state = self._swarms[swarm_id]
        
        # Calculate per-agent token quota
        per_agent_token_quota = spec.token_budget_total // spec.agent_count
        
        per_agent_quota = ResourceQuota(
            max_memory_mb=spec.resource_quota.max_memory_mb,
            max_cpu_percent=spec.resource_quota.max_cpu_percent,
            token_budget=per_agent_token_quota,
            max_execution_time_sec=spec.max_execution_time_sec,
            max_tool_calls=spec.resource_quota.max_tool_calls
        )
        
        for _ in range(count):
            agent_id = f"{swarm_id}:agent:{len(state.active_agents)}"
            
            # Create agent supervisor
            supervisor = AgentSupervisor(
                agent_id=agent_id,
                agent_factory=lambda: self._create_agent_instance(spec.agent_type),
                quota=per_agent_quota,
                message_bus=state.message_bus,
                metrics_sink=self.metrics_sink
            )
            
            # Provision agent
            success = await supervisor.provision()
            
            if success:
                state.active_agents[agent_id] = supervisor
                self._emit_agent_spawned(swarm_id, agent_id)
            else:
                self._emit_error(swarm_id, "agent_spawn_failed", agent_id)
    
    async def _terminate_agents(self, swarm_id: str, count: int) -> None:
        """Terminate agents from swarm (least loaded first)."""
        state = self._swarms[swarm_id]
        
        # Select agents to terminate (e.g., by lowest token consumption)
        agents_by_usage = sorted(
            state.active_agents.items(),
            key=lambda x: x[1].metrics.tokens_consumed
        )
        
        for agent_id, supervisor in agents_by_usage[:count]:
            await supervisor.drain()
            del state.active_agents[agent_id]
            self._emit_agent_terminated(swarm_id, agent_id)
    
    async def _configure_topology(self, swarm_id: str) -> None:
        """Configure message routing based on topology."""
        spec = self._desired_specs[swarm_id]
        state = self._swarms[swarm_id]
        
        agent_ids = list(state.active_agents.keys())
        
        if spec.topology == SwarmTopology.FULLY_CONNECTED:
            # Each agent can message any other agent (no restrictions)
            pass  # Default message bus behavior
        
        elif spec.topology == SwarmTopology.HIERARCHICAL:
            # Organize into tree: first agent is root
            if len(agent_ids) > 0:
                root_id = agent_ids[0]
                for i, agent_id in enumerate(agent_ids[1:], start=1):
                    parent_idx = (i - 1) // 2
                    parent_id = agent_ids[parent_idx]
                    # Configure routing: agent can only message parent and children
                    # (Simplified: would need routing table in production)
        
        elif spec.topology == SwarmTopology.PIPELINE:
            # Linear chain: agent[i] -> agent[i+1]
            for i in range(len(agent_ids) - 1):
                # Configure routing: agent[i] can only message agent[i+1]
                pass
        
        elif spec.topology == SwarmTopology.STAR:
            # Central coordinator: all agents message agent[0]
            if len(agent_ids) > 0:
                coordinator_id = agent_ids[0]
                # Configure routing: only coordinator can broadcast
    
    async def submit_task(self, swarm_id: str, task: dict) -> None:
        """Submit task to swarm for distributed execution."""
        state = self._swarms.get(swarm_id)
        if not state:
            raise ValueError(f"Swarm {swarm_id} not found")
        
        # Distribute task to all agents (simplified)
        # Production: would use task decomposition strategies
        for agent_id, supervisor in state.active_agents.items():
            asyncio.create_task(supervisor.execute(task))
    
    async def autoscale_swarm(self, swarm_id: str) -> None:
        """Autoscale swarm based on resource utilization."""
        spec = self._desired_specs.get(swarm_id)
        state = self._swarms.get(swarm_id)
        
        if not spec or not state or not spec.autoscaling_enabled:
            return
        
        # Calculate average resource utilization
        total_cpu = sum(s.metrics.cpu_percent for s in state.active_agents.values())
        total_memory = sum(s.metrics.current_memory_mb for s in state.active_agents.values())
        
        avg_cpu = total_cpu / len(state.active_agents) if state.active_agents else 0
        avg_memory = total_memory / len(state.active_agents) if state.active_agents else 0
        
        current_count = len(state.active_agents)
        
        # Scale up if high utilization
        if avg_cpu > spec.scale_up_threshold * 100 and current_count < spec.max_agents:
            spec.agent_count = min(current_count + 1, spec.max_agents)
            await self._reconcile_swarm(swarm_id)
            self._emit_autoscale_event(swarm_id, "scale_up", current_count, spec.agent_count)
        
        # Scale down if low utilization
        elif avg_cpu < spec.scale_down_threshold * 100 and current_count > spec.min_agents:
            spec.agent_count = max(current_count - 1, spec.min_agents)
            await self._reconcile_swarm(swarm_id)
            self._emit_autoscale_event(swarm_id, "scale_down", current_count, spec.agent_count)
    
    async def destroy_swarm(self, swarm_id: str) -> None:
        """Destroy swarm and release all resources."""
        state = self._swarms.get(swarm_id)
        spec = self._desired_specs.get(swarm_id)
        
        if not state:
            return
        
        # Terminate all agents
        for supervisor in state.active_agents.values():
            await supervisor.terminate()
        
        # Release token budget
        if spec:
            self._available_tokens += spec.token_budget_total
        
        # Cleanup
        del self._swarms[swarm_id]
        if spec:
            del self._desired_specs[swarm_id]
        
        self._emit_swarm_destroyed(swarm_id)
    
    async def run_reconciliation_loop(self, interval_sec: int = 10) -> None:
        """Continuously reconcile all swarms."""
        while True:
            for swarm_id in list(self._swarms.keys()):
                try:
                    await self._reconcile_swarm(swarm_id)
                    await self.autoscale_swarm(swarm_id)
                except Exception as e:
                    self._emit_error(swarm_id, "reconciliation_error", str(e))
            
            await asyncio.sleep(interval_sec)
    
    def _create_agent_instance(self, agent_type: str):
        """Factory method for creating agent instances."""
        # Placeholder: would instantiate actual agent classes
        from types import SimpleNamespace
        
        # Mock agent with required interface
        agent = SimpleNamespace()
        agent.call_llm = lambda *args, **kwargs: asyncio.sleep(0)
        agent.run = lambda task: asyncio.sleep(1)
        agent.receive_message = lambda msg: None
        agent.save_checkpoint = lambda: {}
        agent.cleanup = lambda: None
        
        return agent
    
    def _emit_reconciliation_event(self, swarm_id: str, current: int, desired: int):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "event_type": "reconciliation",
            "current_agents": current,
            "desired_agents": desired
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_agent_spawned(self, swarm_id: str, agent_id: str):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "agent_id": agent_id,
            "event_type": "agent_spawned"
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_agent_terminated(self, swarm_id: str, agent_id: str):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "agent_id": agent_id,
            "event_type": "agent_terminated"
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_autoscale_event(self, swarm_id: str, action: str, from_count: int, to_count: int):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "event_type": "autoscale",
            "action": action,
            "from_agent_count": from_count,
            "to_agent_count": to_count
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_swarm_destroyed(self, swarm_id: str):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "event_type": "swarm_destroyed"
        }
        self.metrics_sink.emit_event(event)
    
    def _emit_error(self, swarm_id: str, error_type: str, details: str):
        event = {
            "timestamp": asyncio.get_event_loop().time(),
            "swarm_id": swarm_id,
            "event_type": "error",
            "error_type": error_type,
            "details": details
        }
        self.metrics_sink.emit_event(event)
```

The observability plane collects telemetry from all orchestration layers and exposes query interfaces for operational analysis and debugging. Production observability stacks implement three complementary data pipelines: high-cardinality event streams capturing state transitions and errors with full contextual metadata, time-series metrics aggregating resource utilization at configurable granularities, and full-content message archives enabling trace reconstruction across multi-hop reasoning chains. These pipelines terminate in storage systems optimized for their access patterns: event logs flow into append-only datastores supporting temporal range queries, metrics aggregate into time-series databases enabling percentile calculations and anomaly detection, and message archives persist into searchable document stores indexed by conversation threads and semantic content.

```python
# Observability stack implementation
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import statistics

@dataclass
class TimeSeriesPoint:
    """Single time-series data point."""
    timestamp: float
    metric_name: str
    value: float
    tags: Dict[str, str]

class MetricsSink:
    """Centralized metrics collection and aggregation."""
    
    def __init__(self, retention_seconds: int = 3600):
        self.retention_seconds = retention_seconds
        
        # Event log (append-only)
        self._events: deque[dict] = deque(maxlen=100000)
        
        # Time-series metrics (metric_name -> [TimeSeriesPoint])
        self._metrics: Dict[str, deque[TimeSeriesPoint]] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        
        # Aggregated statistics cache
        self._stats_cache: Dict[str, dict] = {}
        self._cache_ttl_sec = 60
        self._last_cache_update = 0
        
        # Start background cleanup task
        asyncio.create_task(self._cleanup_old_data())
    
    def emit_event(self, event: dict) -> None:
        """Emit structured event to log."""
        self._events.append(event)
    
    def emit_metrics(self, metrics: dict) -> None:
        """Emit metrics dictionary (flat key-value pairs)."""
        timestamp = metrics.get("timestamp", time.time())
        
        # Extract tags (swarm_id, agent_id, etc.)
        tags = {
            k: v for k, v in metrics.items()
            if isinstance(v, str) and k.endswith("_id")
        }
        
        # Convert each numeric metric to time-series point
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key != "timestamp":
                point = TimeSeriesPoint(
                    timestamp=timestamp,
                    metric_name=key,
                    value=float(value),
                    tags=tags
                )
                self._metrics[key].append(point)
        
        # Invalidate cache
        self._last_cache_update = 0
    
    def query_events(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_type: Optional[str] = None,
        swarm_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[dict]:
        """Query event log with filters."""
        results = []
        
        for event in reversed(self._events):
            # Time range filter
            if start_time and event.get("timestamp", 0) < start_time:
                continue
            if end_time and event.get("timestamp", float("inf")) > end_time:
                continue
            
            # Type filter
            if event_type and event.get("event_type") != event_type:
                continue
            
            # Entity filters
            if swarm_id and event.get("swarm_id") != swarm_id:
                continue
            if agent_id and event.get("agent_id") != agent_id:
                continue
            
            results.append(event)
            
            if len(results) >= limit:
                break
        
        return results
    
    def query_metrics(
        self,
        metric_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
        aggregation: str = "raw"  # raw, avg, sum, p50, p95, p99
    ) -> List[TimeSeriesPoint]:
        """Query time-series metrics with optional aggregation."""
        if metric_name not in self._metrics:
            return []
        
        points = self._metrics[metric_name]
        
        # Filter by time range
        filtered = [
            p for p in points
            if (start_time is None or p.timestamp >= start_time) and
               (end_time is None or p.timestamp <= end_time)
        ]
        
        # Filter by tags
        if tags:
            filtered = [
                p for p in filtered
                if all(p.tags.get(k) == v for k, v in tags.items())
            ]
        
        # Apply aggregation
        if aggregation == "raw":
            return filtered
        
        if not filtered:
            return []
        
        values = [p.value for p in filtered]
        
        if aggregation == "avg":
            agg_value = statistics.mean(values)
        elif aggregation == "sum":
            agg_value = sum(values)
        elif aggregation == "p50":
            agg_value = statistics.median(values)
        elif aggregation == "p95":
            agg_value = statistics.quantiles(values, n=20)[18]  # 95th percentile
        elif aggregation == "p99":
            agg_value = statistics.quantiles(values, n=100)[98]  # 99th percentile
        else:
            agg_value = statistics.mean(values)
        
        # Return single aggregated point
        return [TimeSeriesPoint(
            timestamp=filtered[-1].timestamp,
            metric_name=metric_name,
            value=agg_value,
            tags=filtered[0].tags
        )]
    
    def get_statistics(self, force_refresh: bool = False) -> dict:
        """Get cached aggregate statistics across all metrics."""
        current_time = time.time()
        
        # Return cached if recent
        if not force_refresh and (current_time - self._last_cache_update) < self._cache_ttl_sec:
            return self._stats_cache
        
        stats = {}
        
        for metric_name, points in self._metrics.items():
            if not points:
                continue
            
            values = [p.value for p in points]
            
            stats[metric_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "p50": statistics.median(values),
                "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
            }
        
        self._stats_cache = stats
        self._last_cache_update = current_time
        
        return stats
    
    async def _cleanup_old_data(self) -> None:
        """Background task to remove expired data."""
        while True:
            current_time = time.time()
            cutoff_time = current_time - self.retention_seconds
            
            # Clean events
            while self._events and self._events[0].get("timestamp", 0) < cutoff_time:
                self._events.popleft()
            
            # Clean metrics
            for metric_name in list(self._metrics.keys()):
                points = self._metrics[metric_name]
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()
                
                # Remove empty metric series
                if not points:
                    del self._metrics[metric_name]
            
            await asyncio.sleep(300)  # Run every 5 minutes
    
    def export_trace(
        self,
        swarm_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> dict:
        """Export complete execution trace for debugging."""
        events = self.query_events(
            start_time=start_time,
            end_time=end_time,
            swarm_id=swarm_id
        )
        
        # Collect all relevant metrics
        metrics = {}
        for metric_name in self._metrics.keys():
            points = self.query_metrics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                tags={"swarm_id": swarm_id}
            )
            if points:
                metrics[metric_name] = [asdict(p) for p in points]
        
        return {
            "swarm_id": swarm_id,
            "start_time": start_time,
            "end_time": end_time,
            "events": events,
            "metrics": metrics,
            "trace_generated_at": time.time()
        }
```

## 3. High-Performance Optimization & Failure Modes

Performance optimization in swarm orchestration operates across three distinct dimensions that require independent tuning strategies. Throughput optimization focuses on maximizing the rate at which the swarm processes tasks by parallelizing agent execution, batching message deliveries, and prefetching tool call results to hide latency. Latency optimization minimizes end-to-end task completion time through careful scheduling that places dependent agents on low-latency network paths, employing priority queues to expedite critical reasoning chains, and maintaining warm agent pools to eliminate cold-start overhead. Cost optimization balances token expenditure against task value by implementing tiered agent architectures where expensive frontier models handle only the most complex subtasks while cheaper models process routine operations, caching inference results to avoid redundant API calls, and terminating speculative reasoning branches that fail early quality checks.

The critical optimization lever for inference-dominated workloads lies in batching strategies that amortize fixed costs across multiple inference requests. When multiple agents simultaneously require language model completions, a batching scheduler can consolidate their requests into a single API call that processes prompts in parallel on the provider's infrastructure, reducing both latency through request pipelining and cost through volume discounts. Production batching implementations must balance two competing forces: larger batches improve throughput and reduce per-token costs, but increase latency for individual requests that must wait for the batch window to close. Adaptive batching algorithms dynamically adjust window sizes based on current queue depth and historical latency distributions, shrinking windows during periods of sparse activity to minimize wait time and expanding windows during bursts to maximize throughput.

```python
# Adaptive batching scheduler for LLM inference
import asyncio
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass
from collections import deque
import time

@dataclass
class InferenceRequest:
    """Single LLM inference request from agent."""
    request_id: str
    agent_id: str
    prompt: str
    parameters: Dict[str, Any]
    priority: int
    submitted_at: float
    result_future: asyncio.Future

class AdaptiveBatchScheduler:
    """Batches LLM inference requests for throughput optimization."""
    
    def __init__(
        self,
        llm_client: Callable,
        min_batch_size: int = 1,
        max_batch_size: int = 20,
        max_wait_ms: int = 50,
        target_latency_p95_ms: int = 500
    ):
        self.llm_client = llm_client
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.target_latency_p95_ms = target_latency_p95_ms
        
        # Request queue (priority-ordered)
        self._queue: deque[InferenceRequest] = deque()
        self._queue_lock = asyncio.Lock()
        
        # Batch processing task
        self._batch_processor_task: Optional[asyncio.Task] = None
        
        # Latency tracking for adaptation
        self._latency_samples: deque[float] = deque(maxlen=1000)
        
        # Adaptive parameters
        self._current_batch_size = min_batch_size
        self._current_wait_ms = max_wait_ms
        
    async def start(self) -> None:
        """Start batch processing loop."""
        self._batch_processor_task = asyncio.create_task(
            self._batch_processing_loop()
        )
    
    async def stop(self) -> None:
        """Stop batch processing and drain queue."""
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
    
    async def submit_request(
        self,
        agent_id: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Any:
        """Submit inference request and await result."""
        request = InferenceRequest(
            request_id=f"{agent_id}:{time.time()}",
            agent_id=agent_id,
            prompt=prompt,
            parameters=parameters or {},
            priority=priority,
            submitted_at=time.time(),
            result_future=asyncio.Future()
        )
        
        async with self._queue_lock:
            # Insert by priority (higher priority first)
            inserted = False
            for i, existing in enumerate(self._queue):
                if request.priority > existing.priority:
                    self._queue.insert(i, request)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(request)
        
        # Await result
        return await request.result_future
    
    async def _batch_processing_loop(self) -> None:
        """Main loop that forms and processes batches."""
        while True:
            try:
                # Wait for minimum batch or timeout
                await asyncio.sleep(self._current_wait_ms / 1000.0)
                
                # Extract batch
                batch = await self._extract_batch()
                
                if not batch:
                    continue
                
                # Process batch
                batch_start = time.time()
                await self._process_batch(batch)
                batch_duration_ms = (time.time() - batch_start) * 1000
                
                # Record latency for adaptation
                for request in batch:
                    request_latency = (time.time() - request.submitted_at) * 1000
                    self._latency_samples.append(request_latency)
                
                # Adapt batch parameters
                self._adapt_batch_parameters()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Batch processing error: {e}")
    
    async def _extract_batch(self) -> List[InferenceRequest]:
        """Extract next batch from queue."""
        async with self._queue_lock:
            if not self._queue:
                return []
            
            # Extract up to current_batch_size requests
            batch_size = min(len(self._queue), self._current_batch_size)
            batch = [self._queue.popleft() for _ in range(batch_size)]
            
            return batch
    
    async def _process_batch(self, batch: List[InferenceRequest]) -> None:
        """Process batch through LLM API."""
        if len(batch) == 1:
            # Single request: no batching overhead
            request = batch[0]
            try:
                result = await self.llm_client(
                    prompt=request.prompt,
                    **request.parameters
                )
                request.result_future.set_result(result)
            except Exception as e:
                request.result_future.set_exception(e)
        
        else:
            # Batch request: combine prompts
            prompts = [req.prompt for req in batch]
            
            try:
                # Assume llm_client supports batch inference
                results = await self.llm_client(
                    prompts=prompts,
                    **batch[0].parameters  # Use first request's parameters
                )
                
                # Distribute results
                for request, result in zip(batch, results):
                    request.result_future.set_result(result)
            
            except Exception as e:
                # Batch failed: fail all requests
                for request in batch:
                    request.result_future.set_exception(e)
    
    def _adapt_batch_parameters(self) -> None:
        """Adapt batch size and wait time based on latency."""
        if len(self._latency_samples) < 100:
            return  # Not enough data
        
        # Calculate p95 latency
        sorted_latencies = sorted(self._latency_samples)
        p95_idx = int(0.95 * len(sorted_latencies))
        current_p95_ms = sorted_latencies[p95_idx]
        
        # Adapt batch size to meet latency target
        if current_p95_ms > self.target_latency_p95_ms:
            # Latency too high: reduce batch size for faster processing
            self._current_batch_size = max(
                self.min_batch_size,
                self._current_batch_size - 2
            )
            
            # Reduce wait time to process sooner
            self._current_wait_ms = max(
                10,
                int(self._current_wait_ms * 0.8)
            )
        
        elif current_p95_ms < self.target_latency_p95_ms * 0.7:
            # Latency comfortable: increase batch size for better throughput
            self._current_batch_size = min(
                self.max_batch_size,
                self._current_batch_size + 1
            )
            
            # Can afford longer wait for larger batches
            self._current_wait_ms = min(
                self.max_wait_ms,
                int(self._current_wait_ms * 1.1)
            )
    
    def get_queue_depth(self) -> int:
        """Query current queue depth."""
        return len(self._queue)
    
    def get_latency_stats(self) -> dict:
        """Get current latency statistics."""
        if not self._latency_samples:
            return {}
        
        sorted_samples = sorted(self._latency_samples)
        
        return {
            "p50_ms": sorted_samples[len(sorted_samples) // 2],
            "p95_ms": sorted_samples[int(0.95 * len(sorted_samples))],
            "p99_ms": sorted_samples[int(0.99 * len(sorted_samples))],
            "mean_ms": sum(sorted_samples) / len(sorted_samples),
            "current_batch_size": self._current_batch_size,
            "current_wait_ms": self._current_wait_ms
        }
```

Resource constraint violations represent the most common failure mode in production swarm deployments, manifesting as token budget exhaustion that halts reasoning mid-task, memory pressure that triggers out-of-memory kills, and API rate limit errors that cascade across dependent agents. Robust orchestrators implement multi-layered defense mechanisms that prevent, detect, and recover from resource exhaustion. Prevention mechanisms include conservative resource reservation where agents receive allocations smaller than their quota to provide safety margins, admission control that rejects new tasks when system-wide utilization exceeds thresholds, and speculative execution cutoffs that terminate agents showing patterns indicating runaway consumption. Detection mechanisms continuously monitor resource utilization curves to identify anomalies like exponential token burn rates or linear memory growth that predict imminent exhaustion. Recovery mechanisms range from graceful degradation strategies that reduce swarm size to fit available resources, to checkpoint-and-restart schemes that persist agent state before termination and resume execution when resources become available.

Message delivery failures introduce subtle correctness bugs that manifest as incomplete reasoning chains where agents miss critical evidence contributions, duplicate work when retransmitted messages trigger redundant computations, and deadlock scenarios where circular dependencies between agents prevent any progress. Production message buses implement failure detection through heartbeat protocols where agents periodically signal liveness to the orchestrator, enabling rapid detection of crashed agents whose pending messages can be redistributed. Delivery guarantees must match semantic requirements: at-least-once delivery suffices for idempotent operations like evidence gathering where duplicate messages merely waste computation, while exactly-once delivery proves essential for non-idempotent operations like vote aggregation where duplicates corrupt results. Implementing exactly-once semantics requires both sender-side deduplication tracking message IDs already transmitted and receiver-side deduplication tracking message IDs already processed, combined with durable storage to survive process restarts.

Cascading failures represent the most destructive failure pattern where a single agent's malfunction propagates through the swarm, ultimately incapacitating the entire collective. Common cascade triggers include unhandled exceptions that crash agent processes, malformed messages that cause parsing errors in recipients, and resource contention where one agent's excessive consumption starves peers. Production orchestrators implement circuit breaker patterns that isolate failing agents by monitoring error rates and temporarily blocking message delivery to agents that exceed thresholds, preventing their failures from affecting healthy agents. Bulkhead patterns partition swarm resources into isolated pools where agents handling different task categories draw from separate token budgets and compute allocations, ensuring that resource exhaustion in one partition cannot starve others. Fallback mechanisms provide degraded functionality when primary reasoning strategies fail, such as switching from multi-agent collaborative search to single-agent retrieval when coordination overhead exceeds available resources.

Debugging distributed agent systems demands specialized tooling that reconstructs causal relationships across asynchronous message exchanges and correlates failures with resource state. Production debugging workflows begin with trace reconstruction where engineers query the observability stack for all events and messages involving a particular task, using message parent IDs to build directed acyclic graphs showing information flow. Trace visualization tools render these graphs highlighting critical paths showing which agent sequences dominated latency, bottleneck analysis identifying agents whose slow responses blocked downstream work, and failure attribution showing which agent initiated error chains. Interactive replay systems allow engineers to reconstruct exact agent state at any point in execution by applying event logs to checkpoint snapshots, enabling hypothesis testing about failure causes through what-if analysis that modifies historical decisions and projects alternative outcomes.

The final operational challenge lies in cost management where uncontrolled token consumption can generate five-figure bills during development and six-figure bills in production. Cost attribution mechanisms track token expenditure at per-agent, per-task, and per-customer granularities, exposing optimization opportunities through marginal cost analysis that identifies which agent roles or reasoning strategies consume disproportionate resources relative to their value contributions. Cost optimization strategies include implementing token budget markets where agents bid for inference capacity based on their estimated value contribution, caching inference results in content-addressed stores where agents check for semantically equivalent prior queries before invoking expensive APIs, and pruning speculative reasoning branches using lightweight discriminator models that predict which exploration paths warrant expensive verification.

```python
# Cost tracking and optimization system
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time

@dataclass
class TokenUsage:
    """Token consumption details for single operation."""
    operation_id: str
    agent_id: str
    swarm_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: float
    cached: bool = False

class CostTracker:
    """Tracks and optimizes token expenditure across swarm."""
    
    def __init__(
        self,
        total_budget_usd: float,
        alert_threshold_pct: float = 0.8
    ):
        self.total_budget_usd = total_budget_usd
        self.alert_threshold_usd = total_budget_usd * alert_threshold_pct
        
        # Cost accounting
        self._total_spent_usd = 0.0
        self._usage_history: List[TokenUsage] = []
        
        # Per-entity spending (agent_id -> cost)
        self._agent_spending: Dict[str, float] = defaultdict(float)
        self._swarm_spending: Dict[str, float] = defaultdict(float)
        
        # Inference result cache (prompt_hash -> result)
        self._inference_cache: Dict[str, dict] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def record_usage(
        self,
        operation_id: str,
        agent_id: str,
        swarm_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cached: bool = False
    ) -> None:
        """Record token usage for cost tracking."""
        usage = TokenUsage(
            operation_id=operation_id,
            agent_id=agent_id,
            swarm_id=swarm_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            timestamp=time.time(),
            cached=cached
        )
        
        self._usage_history.append(usage)
        self._total_spent_usd += cost_usd
        self._agent_spending[agent_id] += cost_usd
        self._swarm_spending[swarm_id] += cost_usd
        
        # Alert if approaching budget
        if self._total_spent_usd >= self.alert_threshold_usd:
            self._emit_budget_alert()
    
    def check_budget_available(
        self,
        agent_id: str,
        estimated_cost_usd: float
    ) -> bool:
        """Check if operation fits within budget."""
        projected_total = self._total_spent_usd + estimated_cost_usd
        return projected_total <= self.total_budget_usd
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget in USD."""
        return max(0, self.total_budget_usd - self._total_spent_usd)
    
    def get_agent_spending(self, agent_id: str) -> float:
        """Get total spending for specific agent."""
        return self._agent_spending.get(agent_id, 0.0)
    
    def get_swarm_spending(self, swarm_id: str) -> float:
        """Get total spending for specific swarm."""
        return self._swarm_spending.get(swarm_id, 0.0)
    
    def get_cost_breakdown(self) -> dict:
        """Get detailed cost breakdown by entity."""
        return {
            "total_spent_usd": self._total_spent_usd,
            "remaining_budget_usd": self.get_remaining_budget(),
            "budget_utilization_pct": (self._total_spent_usd / self.total_budget_usd) * 100,
            "by_agent": dict(self._agent_spending),
            "by_swarm": dict(self._swarm_spending),
            "cache_hit_rate": self._get_cache_hit_rate(),
            "total_tokens": sum(u.input_tokens + u.output_tokens for u in self._usage_history),
        }
    
    def cache_inference_result(
        self,
        prompt: str,
        parameters: dict,
        result: dict
    ) -> None:
        """Cache inference result for reuse."""
        cache_key = self._compute_cache_key(prompt, parameters)
        self._inference_cache[cache_key] = result
    
    def lookup_cached_result(
        self,
        prompt: str,
        parameters: dict
    ) -> Optional[dict]:
        """Lookup cached inference result."""
        cache_key = self._compute_cache_key(prompt, parameters)
        
        if cache_key in self._inference_cache:
            self._cache_hits += 1
            return self._inference_cache[cache_key]
        else:
            self._cache_misses += 1
            return None
    
    def _compute_cache_key(self, prompt: str, parameters: dict) -> str:
        """Compute deterministic cache key from prompt and parameters."""
        import hashlib
        
        # Sort parameters for determinism
        param_str = str(sorted(parameters.items()))
        content = f"{prompt}::{param_str}"
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return 0.0
        return (self._cache_hits / total_requests) * 100
    
    def _emit_budget_alert(self) -> None:
        """Emit alert when approaching budget limit."""
        print(f"WARNING: Budget utilization at {(self._total_spent_usd / self.total_budget_usd) * 100:.1f}%")
        print(f"Spent: ${self._total_spent_usd:.2f} / ${self.total_budget_usd:.2f}")
```

Production deployment of swarm orchestration platforms requires careful attention to operational boundaries that separate development from production environments. Staging environments must mirror production topology including agent counts, resource quotas, and network latencies to expose performance bottlenecks and failure modes before production rollout. Progressive rollout strategies mitigate deployment risks through canary deployments where new orchestrator versions initially handle small traffic fractions, blue-green deployments that maintain parallel old and new environments enabling instant rollback, and feature flags that dynamically enable new coordination strategies without redeployment. Continuous verification systems monitor production swarms for regression in key quality metrics including task success rates, mean time to completion, and cost per task, triggering automatic rollback when metrics degrade beyond acceptable thresholds.
