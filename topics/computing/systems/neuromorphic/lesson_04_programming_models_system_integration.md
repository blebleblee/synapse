# Lesson 4: Programming Models for Neuromorphic Systems

## 1. First-Principles Intuition & Invariants

The history of computing has always been a negotiation between the architecture of the machine and the architecture of thought. Von Neumann's separation of memory and processor was not inevitable—it was a pragmatic engineering decision made in an era when magnetic cores were expensive and transistors were unreliable. That decision calcified into five decades of programming models: sequential instruction streams, explicit memory allocation, synchronous clocking, and the assumption that computation is fundamentally about transforming data at rest. Neuromorphic computing is a repudiation of that assumption at the physical level, and programming it demands an equally fundamental repudiation at the software level.

The brain does not compute by fetching an instruction, performing an operation, and writing a result. It computes by propagating *change*. A neuron's membrane potential is not a register holding a value; it is an analog state that integrates weighted inputs over time, decays toward a resting potential, and fires a spike only when a threshold is crossed. That spike travels down an axon, crosses a synapse, and either excites or inhibits the downstream neuron's future probability of firing. The critical invariant here is temporal: the *timing* of a spike carries information, not merely its occurrence. This is the foundation of Spike Timing Dependent Plasticity (STDP), the dominant plasticity rule in biological and many artificial neuromorphic systems, which strengthens a synapse when the presynaptic neuron fires just before the postsynaptic neuron and weakens it when the order is reversed. Time is not a clock cycle to be minimized; it is an encoding dimension.

For the systems programmer approaching neuromorphic hardware for the first time, the paradigm shift manifests in four core invariants that must remain anchored throughout every design decision.

The first is the **event-driven execution invariant**. Neuromorphic processors are fundamentally idle. Intel's Loihi 2 and IBM's NorthPole consume microjoules per inference precisely because neurons that are not spiking consume no dynamic power—there is no clock ticking through empty cycles. This means that the programming model is not sequential dispatch; it is reactive event propagation. A neuron computes only when it receives a spike event. The programmer's job is to define what happens when an event arrives, not to orchestrate a schedule of operations.

The second is the **spatial locality invariant**. Neuromorphic processors like Intel's Loihi 2 partition neurons and synapses across a mesh of neuromorphic cores. Loihi 2's 128 cores, each housing up to 8,192 neurons and their associated synaptic weights, are interconnected by an on-chip network that routes spikes as packets. The latency of a spike crossing the mesh is bounded by the network topology, not by shared memory bus contention. This means that synapse mapping—deciding which neurons live on which core—is an NP-hard graph partitioning problem with real, measurable performance consequences. A poorly partitioned network with high inter-core fanout will saturate the mesh, increasing latency and energy consumption in ways that have no analogue in CPU cache-miss penalties.

The third is the **temporal encoding invariant**. Unlike artificial neural networks where activation values are precise floating-point numbers, spiking neural networks encode information in the rate and timing of discrete binary events. Rate coding—where higher firing frequency represents higher activation magnitude—is the simplest model and the easiest to compile from a conventional ANN. Temporal coding is more information-dense but harder to train and harder to map to hardware that may quantize time into discrete timesteps. Many frameworks expose this as a tuneable parameter: the number of simulation timesteps per inference window determines the resolution of temporal encoding and the energy-latency tradeoff.

The fourth is the **hardware heterogeneity invariant**. No production system today runs purely on neuromorphic silicon. Loihi 2 is paired with an x86 Lakemont management core running a real-time operating system called NxOS. BrainScaleS-2 at Heidelberg couples its analog neuromorphic substrate with a RISC-V embedded processor for plasticity computation. Spinnaker 2 at Dresden uses 152 ARM Cortex-M4 cores as its computational fabric alongside dedicated neuromorphic accelerators. The programming model must therefore span a heterogeneous boundary: host CPUs handle data ingestion, preprocessing, network compilation, and plasticity updates; neuromorphic cores handle spike propagation and integration. Getting this boundary wrong—sending too much data across the PCIe link per timestep, or computing on-host what should run on-chip—destroys the energy efficiency that justifies the architecture in the first place.

Understanding these invariants is not academic preparation. They are the load-bearing walls of the system. Every optimization, every compilation decision, and every failure mode in this lesson traces back to one or more of them.

---

## 2. Core Architecture & Mechanics

### The Neuron-Synapse Mapping Abstraction

The atom of neuromorphic programming is the neuron-synapse graph. Unlike a matrix multiplication in a dense neural network, where the abstraction is a tensor operation and the hardware mapping is handled entirely by the BLAS library, in a neuromorphic system the programmer—or the compiler—must reason about the physical placement of neurons and the routing of synaptic connections with explicit awareness of hardware topology.

Consider the Leaky Integrate-and-Fire (LIF) neuron model, which is the dominant model on current digital neuromorphic hardware due to its computational simplicity and hardware mappability. Its dynamics are governed by:

$$\tau_m \frac{dV}{dt} = -(V - V_{rest}) + R \cdot I_{syn}(t)$$

where $V$ is the membrane potential, $\tau_m$ is the membrane time constant, $V_{rest}$ is the resting potential, $R$ is the membrane resistance, and $I_{syn}(t)$ is the synaptic input current. When $V$ crosses a threshold $V_{th}$, the neuron emits a spike and $V$ is reset to $V_{reset} \leq V_{rest}$. On digital hardware like Loihi 2, this differential equation is approximated as a discrete difference equation executed once per timestep—typically one millisecond of simulated biological time. The hardware stores per-neuron state as a compact integer representation: membrane potential, refractory counter, and threshold as 24-bit fixed-point values packed into SRAM local to each neuromorphic core.

The synapse is not merely a weight scalar. On Loihi 2, each synapse entry in the synaptic memory table encodes a weight, a delay (1–62 timesteps), and a compartment tag that allows one presynaptic spike to simultaneously update multiple dendritic compartments of a target neuron. The synaptic table for a core is a dense compressed sparse row (CSR) matrix stored in a banked on-chip SRAM. Reading the synaptic memory on a spike event is not a random-access memory operation in the conventional sense; the hardware fan-out engine reads contiguous rows from the CSR table, accumulates weighted inputs into destination compartment registers, and does so in a pipelined fashion across the 32-channel mesh router.

The practical consequence for the programmer is that synapse density and sparsity are first-class design concerns. A neuron with 1,000 incoming synaptic connections consumes dramatically more synaptic memory than one with 50. Loihi 2 provides approximately 128 KB of synaptic SRAM per core, which at 8 bits per weight can store roughly 128,000 synapses. If your network has neurons with high fan-in, you either distribute those neurons across multiple cores—splitting their dendritic trees—or you use weight compression schemes like the shared-weight dendrite models Loihi 2's hardware supports for convolutional mappings.

The following diagram illustrates the internal signal path from a spike event to a membrane potential update on a single Loihi 2 core:

```
Incoming Spike Packet (from mesh router)
           │
           ▼
  ┌─────────────────────┐
  │   Spike Scheduler   │  ◄── Delay buffer (ring buffer, 1–62 timestep slots)
  └─────────┬───────────┘
            │  (after delay elapses)
            ▼
  ┌─────────────────────┐
  │  Synaptic Fan-Out   │  ◄── Reads CSR synapse table from local SRAM
  │      Engine         │      (presynaptic neuron ID → weight × compartment pairs)
  └─────────┬───────────┘
            │  (weighted input current)
            ▼
  ┌─────────────────────────────────────┐
  │   Compartment Accumulator Array     │  ◄── 8,192 compartment registers
  │   (one entry per neuron per core)   │      updated via atomic add
  └─────────┬───────────────────────────┘
            │
            ▼  (at timestep boundary)
  ┌─────────────────────┐
  │   Neuron Dynamics   │  ◄── LIF update: decay V, add I_syn, check threshold
  │      Processor      │
  └─────────┬───────────┘
            │  (if V > V_threshold)
            ▼
  ┌─────────────────────┐
  │   Spike Generation  │  ◄── Emits spike packet: (dest_core, neuron_id, delay)
  │   & Mesh Routing    │      injected into on-chip network
  └─────────────────────┘
```

This pipeline runs in lockstep across all cores, synchronized by a global timestep barrier. Every core advances together, which eliminates the race conditions that would otherwise arise when spikes cross core boundaries mid-timestep. The barrier is implemented as a hardware synchronization tree rooted at the mesh controller; the latency of a full timestep on Loihi 2 is on the order of 10–100 microseconds of wall-clock time depending on network activity.

### Event-Driven Programming with NxSDK

Intel's NxSDK is the production API for Loihi 2 and its successor hardware. It exposes a Python-based specification layer backed by a C runtime that compiles neuron-synapse graphs to hardware configuration bitstreams. The design philosophy is declarative: you describe the network topology and neuron parameters, and the SDK's compiler handles the placement and routing. Understanding what that compiler does—and when to override it—is the difference between a system that meets its latency budget and one that does not.

The core programming object in NxSDK is the `CompartmentGroup`, which represents a population of neurons sharing the same parameter template. Creating a population of 1,024 LIF neurons with a 20 ms time constant, a threshold of 400 (in fixed-point units), and a decay constant of 4096 (representing approximately 0.5 per timestep in Q12 fixed-point) looks like this:

```python
import nxsdk.api.n2a as nx

net = nx.NxNet()

# LIF neuron prototype: vThMant sets firing threshold mantissa
# vDecay = 4096 corresponds to ~0.5 decay per timestep in U(0,4096) range
proto = nx.CompartmentPrototype(
    vThMant=400,
    vDecay=4096,
    currentDecay=4096,
    functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
    compartmentVoltageDecay=4096
)

# Allocate 1024 neurons sharing this prototype
population = net.createCompartmentGroup(size=1024, prototype=proto)
```

The synaptic connection between two populations is specified as a `ConnectionGroup`, which wraps a weight matrix and a connection prototype that encodes delay, weight precision, and learning rule association:

```python
# Source population: 512 input neurons
source = net.createCompartmentGroup(size=512, prototype=proto)

# Synapse prototype: 8-bit weights, 1 timestep delay, no plasticity
syn_proto = nx.ConnectionPrototype(
    weightBits=8,
    delay=1,
    signMode=nx.SYNAPSE_SIGN_MODE.MIXED
)

# Dense random connectivity: 512 -> 1024, weight matrix W
import numpy as np
rng = np.random.default_rng(42)
W = rng.integers(-128, 127, size=(1024, 512), dtype=np.int8)

conn = source.connect(
    population,
    prototype=syn_proto,
    weight=W
)
```

This specification is entirely host-side Python; nothing has executed on neuromorphic hardware yet. The critical step is compilation, which NxSDK performs when you call `net.compiler.compile(net)`. The compiler's job is a graph partitioning problem: it must assign neurons to cores such that the synaptic memory constraints of each core are not exceeded, the inter-core spike traffic on the mesh is minimized, and the total core count is within the chip's capacity. For the dense 512→1024 connectivity above, the weight matrix W has 524,288 entries at 8 bits each, totaling 512 KB—far more than any single core can hold. The compiler automatically shards the connection across multiple cores, splitting the fan-in of destination neurons across multiple synaptic memory banks.

### Spike Injection and Readout: The Host Boundary

The host-neuromorphic boundary is managed through two hardware mechanisms: spike injectors and spike probes. A spike injector is a special hardware channel that allows the host CPU to synthesize spike events and inject them into the mesh at the start of a timestep. A spike probe accumulates the firing times of designated output neurons and DMA-transfers them to host memory at the end of a timestep window. Both are rate-limited by the PCIe bandwidth and the chip's I/O controller, making them the most common bottleneck in real deployments.

For a sensory processing pipeline—say, processing events from a Dynamic Vision Sensor (DVS) camera—the data flow looks like this:

```
DVS Camera (USB3)
      │  raw event stream: (x, y, polarity, timestamp) tuples at ~1M events/sec
      ▼
Host CPU (preprocessing)
      │  bin events into 1ms timestep windows
      │  map (x,y,polarity) → neuron ID
      │  pack spike list: array of uint16 neuron IDs
      ▼
PCIe DMA → Spike Injector Channel → Mesh Router → Input Population
                                                         │
                                              Neuromorphic cores process
                                              N timesteps of inference
                                                         │
                                              Output Population fires
                                                         │
                                        Spike Probe → DMA → Host memory
      ▼
Host CPU (decode)
      │  classify output spike population activity
      ▼
Application
```

The key performance constraint is that the entire round-trip—inject spikes, run N timesteps, read output spikes—must complete before the next batch of DVS events overflows the input buffer. At 1M events per second with 1ms timestep windows, the host has 1ms of wall-clock time per timestep iteration. On Loihi 2, a single-chip inference timestep for a moderately sized SNN (around 65,000 neurons) runs in approximately 50–80 microseconds, leaving substantial headroom. The host preprocessing and DMA transfer typically account for 200–400 microseconds, making them the dominant latency contributor—a fact that motivates keeping preprocessing on-chip or using FPGA-based spike encoding that bypasses the host CPU entirely.

### Compilation from High-Level Specifications to Neuromorphic Substrates

The compilation stack for neuromorphic systems has no mature analog in conventional compiler infrastructure. There is no LLVM IR for spiking neural networks. Instead, compilation pipelines are hardware-specific and vertically integrated, though the community is converging around intermediate representations that separate the concerns of network description, neuron model specification, and hardware placement.

The most practically useful high-level framework for Loihi today is **Lava**, Intel's open-source asynchronous message-passing framework that presents a process-graph abstraction inspired by communicating sequential processes (CSP). In Lava, computation is expressed as a directed graph of `Process` objects that communicate through typed `Port` connections. Each process has a `run_condition` that determines when it executes, and processes can be mapped to either host CPU threads or neuromorphic cores through a backend-specific `ProcessModel`.

The elegant engineering insight in Lava is that the same process graph, written once, can target multiple backends. A `LIF` process written in pure Python using `PyLoihiProcessModel` runs in simulation on the host CPU for debugging. The same `LIF` process compiled with `NcProcessModel` runs on Loihi 2 neuromorphic cores. The backend selection happens at runtime through the compiler's process model registry, which performs a priority-ordered search for the most efficient available implementation:

```python
from lava.proc.lif.process import LIF
from lava.proc.dense.process import Dense
from lava.magma.core.run_configs import Loihi2HwCfg
from lava.magma.core.run_conditions import RunSteps

# Network definition: identical for simulation and hardware targets
lif_pop = LIF(
    shape=(1024,),
    du=4096,        # current decay: U(0,4095), 4096 ≈ 0 decay (full accumulation)
    dv=4096,        # voltage decay
    vth=400         # firing threshold
)

dense_conn = Dense(
    weights=W.astype(np.int8),
    num_message_bits=8
)

# Wire: input spikes flow through dense weights into LIF population
sparse_input = SpikeIn(shape=(512,))   # host-injected spikes
sparse_input.s_out.connect(dense_conn.s_in)
dense_conn.a_out.connect(lif_pop.a_in)

# Compile and run on Loihi 2 hardware
run_cfg = Loihi2HwCfg()
lif_pop.run(condition=RunSteps(num_steps=100), run_cfg=run_cfg)
lif_pop.stop()
```

The Lava compiler, when targeting `Loihi2HwCfg`, performs several transformations in sequence. First, it resolves process model bindings, selecting `NcProcessModel` for each process that has one registered. Second, it performs sub-process partition: large populations are split into groups that fit within single-core neuron budgets. Third, it runs a graph partitioning heuristic—currently a greedy balanced bin-packing algorithm weighted by synaptic memory footprint—to assign core indices to compartment groups. Fourth, it generates the hardware configuration bitstream: a binary blob that programs each core's synaptic memory, compartment parameter registers, and axon routing tables. Finally, it generates the spike channel configuration that maps host-side port connections to hardware DMA channels.

For networks derived from pre-trained conventional ANNs, the compilation pipeline has an additional front-end stage: **ANN-to-SNN conversion**. Tools like `lava-dl` and Intel's `neural-compressor`-compatible Loihi export path perform this conversion by replacing ReLU activations with rate-coded LIF neurons. The fundamental insight is that for a ReLU unit with output value $a$, a LIF neuron with constant input current $I = a \cdot w_{scale}$ will fire at a rate proportional to $a$ over a sufficient time window. The accuracy of this approximation improves with longer simulation windows and degrades with sparser spike trains. In practice, ResNet-20 converted to SNN achieves approximately 91% accuracy on CIFAR-10 with 50–100 timesteps, compared to 92.5% in the original ANN—a 1.5-point accuracy penalty in exchange for a 10–100× energy reduction on neuromorphic hardware.

### BrainScaleS-2 and Analog Compilation: A Contrast

The digital compilation model of Loihi is not universal. BrainScaleS-2, the analog-mixed-signal neuromorphic system developed at Heidelberg University, operates at 1,000× biological real-time—its neurons integrate in microseconds rather than milliseconds—and uses analog circuits to implement neuron dynamics with zero dynamic power for the integration itself. Programming BrainScaleS-2 means solving a **calibration and mapping problem** rather than a purely digital compilation problem.

Each of BrainScaleS-2's 512 analog neuron circuits has manufacturing-induced parameter variations: the threshold voltage, leak conductance, and reset potential are slightly different for every circuit due to transistor mismatch. The hardware abstraction library (PyNN-based `pynn_brainscales`) must therefore calibrate each neuron individually, measuring its actual electrical behavior and computing per-neuron correction coefficients that are stored in digital-to-analog converter (DAC) registers alongside the circuit. This calibration loop, which runs before every experiment, is a closed-loop measurement system: the embedded RISC-V processor triggers neural activation, the analog-to-digital converters on-chip record membrane trajectories, and the host computer runs a least-squares parameter fit to find the DAC settings that bring each neuron closest to the target parameters.

The resulting programming model is fundamentally probabilistic in a way that Loihi is not. When you specify a threshold of 400 arbitrary units on Loihi, that is exactly what executes. When you specify a threshold on BrainScaleS-2, you are specifying a target that the calibration system will approximate within a hardware-dependent error bound, typically ±5% of the target value. This imprecision is not a bug; it is a feature that some learning algorithms—particularly those inspired by biological robustness to noise—can exploit. But it demands that the programmer design networks with explicit tolerance for parameter variation, using techniques like homeostatic plasticity rules that push neurons toward target firing rates regardless of their exact threshold values.

---

## 3. High-Performance Optimization & Failure Modes

### Core Partitioning and the Graph Placement Problem

The single most impactful optimization available to a neuromorphic systems programmer is informed graph partitioning. The default compilers in both NxSDK and Lava use greedy heuristics that are correct but rarely optimal for networks with structured connectivity. Understanding the hardware cost model enables manual partitioning that can reduce inter-core traffic by 30–70% on locally connected networks like convolutional SNNs.

The cost metric to minimize is **inter-core axon count**, where an axon represents a spike routing entry that crosses a core boundary. Each inter-core spike requires a mesh packet containing the destination core address, the destination compartment address, and the spike payload. On Loihi 2's 8×16 mesh, the worst-case packet latency scales with the Manhattan distance between source and destination cores: a spike crossing the full diagonal of the mesh (7 + 15 = 22 hops) has approximately 22× the routing latency of a hop-0 spike. More critically, each core has a finite axon input bandwidth: on Loihi 2, approximately 4,096 axon entries per core. A network that places a highly connected hub neuron in the center of a core's input fan-in budget will trigger axon overflow, causing the compiler to silently split the neuron across multiple cores—which may violate the latency assumptions of the original network designer.

For a convolutional SNN processing 32×32 input images with a 5×5 kernel in the first layer, the optimal partitioning strategy maps spatially adjacent input patches to the same core, exploiting the kernel's locality to keep the majority of synaptic fan-in on-core. This is the neuromorphic analogue of cache-aware matrix multiplication: aligning data access patterns with the memory hierarchy. In NxSDK, you can override the automatic partitioner by providing explicit `coreAllocation` constraints:

```python
from nxsdk.graph.nxBoard import N2Board
from nxsdk.arch.n2a.compiler.mapping.compiler_config import CompilerConfig

# Configure compiler: disable auto-partitioning, use manual core hints
cfg = CompilerConfig(
    # Snap populations to 8x8 spatial tiles, mapping to core grid
    snappingGranularity=64,
    # Maximize weight precision at cost of capacity
    synapseCompressionMode=CompilerConfig.SynapseCompressionMode.LOSSLESS
)

compiler = net.compiler
compiler.config = cfg
board = compiler.compile(net)
```

For networks that exceed a single Loihi 2 chip's 128 cores, multi-chip partitioning introduces off-chip spike routing through the board's FPGA-based spike router (the N2A/N3A boards use a Cyclone V FPGA as the inter-chip network fabric). Off-chip spikes consume approximately 10× the energy of on-chip spikes, making multi-chip boundary crossing the dominant energy cost for large-scale networks. The compiler's cost model assigns a penalty weight to inter-chip edges in its partitioning objective, but for networks with global connectivity patterns—such as fully-connected readout layers following convolutional feature extraction—manual placement of the readout layer on a dedicated "output chip" that receives fan-in from all feature chips minimizes the number of inter-chip crossings.

### Timestep Latency and Synchronization Overhead

The global timestep barrier is both a correctness guarantee and a performance bottleneck. Because all cores must complete their neuron dynamics computation before any core can begin the next timestep, the wall-clock time per timestep is determined by the most heavily loaded core in the network—the neuromorphic analogue of Amdahl's Law applied to spatial parallelism.

A core becomes a bottleneck when it has an unusually high synaptic fan-in throughput requirement. If a core hosts 8,192 neurons each with 500 incoming synapses, and 10% of presynaptic neurons fire in a given timestep, the fan-out engine must process 8,192 × 500 × 0.10 = 409,600 synaptic operations within that timestep's time budget. At Loihi 2's internal processing rate of approximately 2 billion synaptic operations per second per core, this takes approximately 200 microseconds—double the typical timestep duration of 100 microseconds for a lightly loaded network. The hardware handles this by stalling the global barrier until all cores complete, transparently increasing the timestep duration. The programmer observes this as unexplained latency variance, often without any error or warning from the SDK.

Diagnosing this requires using the hardware performance counters exposed through NxSDK's probe infrastructure:

```python
import nxsdk.api.n2a as nx

# Attach performance counter probes to measure per-core synapse operation counts
# and timestep execution cycles
board = compiler.compile(net)

# Access the chip execution statistics after a run
run_cfg = nx.N2Compiler.RunConfig(numSteps=1000)
board.run(run_cfg)

# Read per-core execution time from hardware registers
exec_stats = board.executionStatistics
for core_id, stats in enumerate(exec_stats.coreStats):
    print(f"Core {core_id:3d}: "
          f"syn_ops={stats.synapticOperations:>10d}, "
          f"spike_rx={stats.spikesReceived:>8d}, "
          f"stall_cycles={stats.stallCycles:>8d}")
```

A core with disproportionately high `stallCycles` relative to its neighbors is the bottleneck. The mitigation is to split that core's neuron population across two cores, reducing per-core fan-in by half and balancing the pipeline. If the high synaptic load is unavoidable—for instance, in a fully-connected output layer receiving from all earlier layers—the alternative is to increase the target timestep duration in the compiler configuration, explicitly accepting higher latency in exchange for correctness.

### Spike Rate Explosion and the Silent Network Failure Mode

The most dangerous failure mode in neuromorphic system design has no equivalent in conventional deep learning: spike rate explosion. In a conventional neural network, if a ReLU layer outputs very large activation values, the downstream layer's weights can compensate or the training process will push the network toward a stable fixed point. In a spiking network running in real-time on hardware, a neuron that fires every timestep at the maximum rate saturates the synaptic fan-out engine of its destination core, creates a cascade of over-threshold activations in downstream neurons, and can cause the network to enter a fully synchronized state where every neuron fires every timestep. This is the neuromorphic equivalent of a software runaway process, and it consumes maximum power, saturates the mesh, and produces meaningless output—all without any exception or error from the hardware.

The proximate cause is almost always a miscalibrated weight scale. When converting a pre-trained ANN to SNN, the weight scaling factor that converts floating-point activations to integer spike rates must be chosen carefully. If the scale is too large, the constant input current to each LIF neuron exceeds its threshold on the first timestep, and without a sufficient refractory period to prevent re-firing, the neuron enters continuous firing. The fundamental invariant is that for a LIF neuron to encode meaningful information, its input current integrated over one timestep must be strictly less than its threshold voltage minus its current membrane potential in the typical non-firing case. Formally: $\sum_i w_i \cdot r_i < V_{th} - V_{reset}$ where $r_i$ is the expected firing rate of presynaptic neuron $i$ and $w_i$ is the corresponding weight. This bound must be verified analytically before deployment, not discovered empirically on hardware.

The mitigation strategy is threefold. First, implement a threshold normalization pass in the ANN-to-SNN compiler that scales weights layer-by-layer such that the maximum possible input current in each layer is bounded to 80% of the threshold voltage. This provides a 20% headroom against statistical fluctuations in the input spike train. Second, configure a refractory period of at least 2–3 timesteps for all neurons, which hard-caps the maximum firing rate at 33–50% of the timestep frequency and prevents the runaway cascade. Third, deploy a spike rate monitor on the output population as an operational safety check:

```python
# Attach a spike probe to the output population
# Monitor for anomalous firing rates indicative of rate explosion
output_probe = output_pop.probe(
    [nx.ProbeParameter.SPIKE],
    probeConditions=nx.PerformanceProbeCondition(tStart=1, dt=1)
)

# After run: compute per-neuron average firing rate
spike_data = output_probe[0].data   # shape: (num_neurons, num_timesteps)
firing_rates = spike_data.mean(axis=1)   # fraction of timesteps with spike

RATE_EXPLOSION_THRESHOLD = 0.8  # >80% firing rate indicates pathological state
pathological_neurons = np.where(firing_rates > RATE_EXPLOSION_THRESHOLD)[0]
if len(pathological_neurons) > 0:
    raise RuntimeError(
        f"Spike rate explosion detected in {len(pathological_neurons)} neurons: "
        f"indices {pathological_neurons[:10]}... "
        f"max_rate={firing_rates.max():.3f}. "
        f"Check weight scaling and refractory period configuration."
    )
```

### Plasticity Rules and On-Chip Learning

One of the genuine differentiators of neuromorphic hardware over conventional inference accelerators is the ability to perform local synaptic weight updates—plasticity—directly on-chip without round-tripping weight gradients through the host CPU. Loihi 2 implements this through its **learning engine**, a programmable rule processor co-located with each core's synaptic memory. The learning rule is specified as a set of trace update equations and a weight update equation, both expressed in a domain-specific microcode language that the NxSDK compiler translates to learning engine configuration registers.

The standard STDP rule is expressed in this framework as two exponentially decaying traces: a presynaptic trace $x_1$ that increments on every presynaptic spike and decays with time constant $\tau_{x_1}$, and a postsynaptic trace $y_1$ that increments on every postsynaptic spike and decays with time constant $\tau_{y_1}$. The weight update is then $\Delta w = A_+ \cdot x_1 \cdot \delta(t_{post}) - A_- \cdot y_1 \cdot \delta(t_{pre})$, where $A_+$ and $A_-$ are the learning rate constants for potentiation and depression respectively.

```python
# STDP learning rule specification in Lava's learning API
from lava.proc.learning_rules.stdp_learning_rule import STDPLoihi

stdp = STDPLoihi(
    learning_rate=1,       # integer learning rate mantissa
    A_plus=4,              # potentiation amplitude (Q-format integer)
    A_minus=-2,            # depression amplitude
    tau_plus=20,           # presynaptic trace decay time constant (timesteps)
    tau_minus=20,          # postsynaptic trace decay time constant
    t_epoch=4              # weight update epoch: apply every 4 timesteps
)

# Attach learning rule to connection
plastic_conn = Dense(
    weights=W_init.astype(np.int8),
    learning_rule=stdp,
    num_message_bits=8
)
```

The `t_epoch` parameter is critical for performance. Applying weight updates every timestep maximizes plasticity resolution but doubles the synaptic memory bandwidth requirement for each core hosting plastic synapses, since the learning engine must both read and write the weight table on every update cycle. Setting `t_epoch=4` amortizes this cost across four timesteps, reducing learning engine memory traffic by 4× at the cost of a 4-timestep granularity in the weight update dynamics. For most online learning applications—sensory adaptation, anomaly detection, continual learning—a 4–8 timestep epoch is indistinguishable from continuous update and is the production-recommended setting.

### Heterogeneous Workflow Orchestration

A complete production neuromorphic system is not a monolithic SNN running in isolation; it is a carefully orchestrated pipeline where host CPU, FPGA preprocessing stages, and neuromorphic cores each handle the portions of the computation they are best suited for. The architecture pattern that has emerged from production deployments at Intel Labs and partner research sites is the **three-layer model**:

The first layer is the **sensor interface layer**, which runs on an FPGA or DSP co-processor. This layer ingests raw sensor data (DVS events, audio frames, IMU readings), performs spike encoding (rate coding, latency coding, or population coding), and streams packed spike vectors to the neuromorphic chip at the chip's native DMA rate. Keeping this layer off the host CPU is essential for real-time operation at sub-millisecond latency budgets.

The second layer is the **neuromorphic inference layer**, which runs entirely on-chip. This layer executes the SNN forward pass, optionally applies on-chip plasticity rules, and maintains persistent network state between inference windows. The key design principle is that this layer should never stall waiting for host data. The spike injection channels must be pre-loaded with the full timestep's input spikes before the timestep executes, and the output probes must be read after the timestep completes, all within the inter-timestep window.

The third layer is the **host coordination layer**, which runs on the x86 management processor. This layer handles network compilation and configuration, reads output spike probes, runs application-level decoding (population vector decoding, winner-take-all classification), manages plasticity learning rate schedules, and handles multi-chip coordination for networks spanning multiple Loihi devices. This layer operates at the timescale of inference windows (10–100ms), not individual timesteps (1ms), and is therefore tolerant of OS scheduling jitter in a way that the spike injection pipeline is not.

The boundary discipline between these layers is as important as the implementation within them. Code that belongs in the host coordination layer but runs in the spike injection path—even a single Python function call that triggers garbage collection at the wrong moment—will cause a DMA underrun that injects zeros into the neuromorphic core's input, corrupting the network state silently and producing incorrect inference results with no error flag. The production mitigation is to run the spike injection path as a real-time C thread pinned to an isolated CPU core with `SCHED_FIFO` scheduling, communicating with the Python host layer through a lock-free ring buffer:

```c
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>

/* Lock-free ring buffer for host->injector spike transfer */
#define RING_SIZE 256
typedef struct {
    uint16_t  neuron_ids[512];   /* packed spike list per timestep */
    uint32_t  count;
    uint64_t  timestep;
} SpikeFrame;

typedef struct {
    SpikeFrame  frames[RING_SIZE];
    atomic_uint head;
    atomic_uint tail;
} SpikeRingBuffer;

static SpikeRingBuffer g_spike_ring;

/* Real-time injector thread: consumes frames from ring, writes to DMA channel */
static void* spike_injector_thread(void* arg) {
    NxDmaChannel* dma = (NxDmaChannel*)arg;

    struct sched_param sp = { .sched_priority = 90 };
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);

    while (1) {
        uint32_t tail = atomic_load_explicit(&g_spike_ring.tail,
                                              memory_order_acquire);
        uint32_t head = atomic_load_explicit(&g_spike_ring.head,
                                              memory_order_relaxed);
        if (tail == head) {
            /* spin-wait: no sleep to avoid scheduler latency */
            __builtin_ia32_pause();
            continue;
        }

        SpikeFrame* frame = &g_spike_ring.frames[tail % RING_SIZE];
        nx_dma_write(dma, frame->neuron_ids, frame->count * sizeof(uint16_t));

        atomic_store_explicit(&g_spike_ring.tail, tail + 1,
                               memory_order_release);
    }
    return NULL;
}
```

This architecture keeps Python's garbage collector, dynamic linker, and OS scheduler entirely out of the critical injection path while allowing the host coordination layer to remain in idiomatic Python. The ring buffer depth of 256 frames provides 256ms of injection headroom at 1ms timesteps—sufficient to absorb any host-side scheduling jitter while maintaining deterministic delivery to the hardware.

Mastering neuromorphic programming models means internalizing a fundamentally different relationship between time, space, and computation. The techniques in this lesson—neuron-synapse graph compilation, event-driven process modeling, graph partitioning, plasticity rule specification, and heterogeneous layer orchestration—are not independent tools. They are facets of a single coherent discipline: designing systems that compute by propagating *change* efficiently through sparse, time-aware, spatially distributed hardware. The engineer who grasps that invariant deeply will find that the specific API calls are secondary. The API changes with every hardware generation; the invariant does not.
