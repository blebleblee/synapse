# Lesson 1: Quantum Mechanics Foundations for Computing

## 1. First-Principles Intuition & Invariants

Classical computers are, at their core, deterministic state machines operating over bits that are either zero or one. Every abstraction layered on top of that foundation, from transistor logic gates to operating system schedulers to distributed consensus protocols, inherits this binary certainty. A classical bit has a definite value at every moment in time. The entire discipline of systems programming is built on that invariant. Quantum computing demolishes it.

To understand why quantum mechanics enables a qualitatively different model of computation, you need to confront what physicists discovered about physical reality in the early twentieth century: at the scale of individual particles, nature is not deterministic. It is probabilistic in a deep, irreducible way that is not merely a reflection of human ignorance. A quantum system does not secretly have a definite state that we simply fail to measure accurately. Prior to measurement, the system genuinely exists in a superposition of multiple states simultaneously, and the act of measurement forces a probabilistic collapse to one of them. This is not a metaphor or an engineering approximation. It is the most precisely verified empirical fact in the history of physics.

The mathematical structure encoding this reality is the **Hilbert space**: a complete inner product space over the complex numbers. A quantum state is a unit vector in this space. For a single qubit, the Hilbert space is $\mathbb{C}^2$, two-dimensional complex vector space, and the computational basis vectors are conventionally written $|0\rangle$ and $|1\rangle$ using Dirac's bra-ket notation. These two vectors are orthonormal: $\langle 0 | 1 \rangle = 0$ and $\langle 0 | 0 \rangle = \langle 1 | 1 \rangle = 1$. Any qubit state is a normalized linear combination of them:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle, \quad \alpha, \beta \in \mathbb{C}, \quad |\alpha|^2 + |\beta|^2 = 1$$

The coefficients $\alpha$ and $\beta$ are called **probability amplitudes**. They are complex numbers, not probabilities themselves. The probability of measuring $|0\rangle$ is $|\alpha|^2$ and the probability of measuring $|1\rangle$ is $|\beta|^2$. The normalization constraint ensures these probabilities sum to one. This is the first postulate of quantum mechanics expressed in computational terms: the state of a quantum system is a unit vector in a Hilbert space.

What makes this qualitatively different from a probabilistic classical bit is interference. Because amplitudes are complex, they can be negative or imaginary. Paths leading to an outcome can cancel each other (destructive interference) or reinforce each other (constructive interference). A classical probability distribution cannot do this. This interference structure is precisely the resource that quantum algorithms exploit. Shor's algorithm for integer factoring and Grover's algorithm for unstructured search both work by constructing a sequence of unitary transformations that amplify the probability amplitude of the correct answer while suppressing amplitudes of incorrect answers. The computational speedup is not brute force parallelism; it is controlled interference.

The **Bloch sphere** provides the canonical geometric intuition for a single qubit. Because the global phase of a quantum state is physically unobservable, the state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ can always be written, up to global phase, as:

$$|\psi\rangle = \cos\frac{\theta}{2}|0\rangle + e^{i\phi}\sin\frac{\theta}{2}|1\rangle$$

where $\theta \in [0, \pi]$ is the polar angle and $\phi \in [0, 2\pi)$ is the azimuthal angle. Every pure qubit state corresponds to exactly one point on the surface of a unit sphere in three-dimensional real space. The north pole is $|0\rangle$, the south pole is $|1\rangle$, and the equatorial plane contains the uniform superpositions. Quantum gates are rotations of this sphere. This is not incidental: the mathematical group of single-qubit unitaries is $SU(2)$, which double-covers $SO(3)$, the rotation group of three-dimensional space.

**Entanglement** is the invariant that separates multi-qubit quantum systems from any classical probability distribution. Consider two qubits. Their joint Hilbert space is the tensor product $\mathbb{C}^2 \otimes \mathbb{C}^2 = \mathbb{C}^4$, spanned by $|00\rangle$, $|01\rangle$, $|10\rangle$, $|11\rangle$. A state is called a product state if it can be written as $|\psi_A\rangle \otimes |\psi_B\rangle$, meaning the two qubits are independent. A state is **entangled** if it cannot be written as such a product. The canonical example is the Bell state:

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

There is no pair of single-qubit states $|\psi_A\rangle$ and $|\psi_B\rangle$ whose tensor product equals $|\Phi^+\rangle$. The two qubits are correlated in a way that has no classical analog. Measuring qubit A and finding $|0\rangle$ instantly forces qubit B into state $|0\rangle$, regardless of the physical separation between them. This is not faster-than-light signaling; no information is transmitted because the measurement outcome is random. But the correlations between measurement outcomes, taken together across many runs, violate Bell's inequalities, which any classical hidden-variable theory must satisfy. The experimental violation of Bell's inequalities, confirmed definitively in loophole-free experiments by Hensen et al. (2015) and Giustina et al. (2015), is what elevates entanglement from mathematical formalism to confirmed physical phenomenon.

For systems programmers, the operational invariant to internalize is this: an $n$-qubit quantum state requires $2^n$ complex amplitudes to fully describe. A 50-qubit state requires $2^{50} \approx 10^{15}$ complex numbers, roughly 16 petabytes at double precision. Classical simulation of quantum systems is exponentially hard in the general case. This exponential state space is the resource quantum computers exploit. A quantum computer with $n$ qubits physically instantiates a $2^n$-dimensional complex vector, operates on it with unitary transformations, and extracts information by measurement. The engineering challenge is maintaining the coherence of that vector long enough to perform useful computation before decoherence, the coupling of the quantum system to its environment, destroys the quantum information.

The five postulates of quantum mechanics form the axiomatic foundation of the entire discipline. The first postulate assigns Hilbert spaces to systems. The second postulate states that the time evolution of a closed quantum system is governed by the Schrödinger equation: $i\hbar \frac{d}{dt}|\psi(t)\rangle = H|\psi(t)\rangle$, where $H$ is the Hamiltonian operator representing the total energy of the system. For quantum computation, the Hamiltonian determines what unitary operations a physical device can natively implement. The third postulate governs measurement: physical observables correspond to Hermitian operators, and measurement produces one of their real eigenvalues with probability given by the Born rule. The fourth postulate specifies that composite systems combine by tensor product. The fifth postulate covers identical particles, which is physically important but computationally secondary for circuit-model quantum computing.

The transition from pure states to **mixed states** is essential for practitioners building real quantum systems. A pure state is one that can be described by a single Hilbert space vector. A mixed state arises when you have a statistical ensemble of pure states, or when your system is entangled with an environment you cannot observe. The proper mathematical object is the **density matrix** $\rho$, a positive semidefinite Hermitian operator with unit trace. For a pure state, $\rho = |\psi\rangle\langle\psi|$ and $\text{Tr}(\rho^2) = 1$. For a mixed state, $\text{Tr}(\rho^2) < 1$. Decoherence is precisely the process by which the off-diagonal elements of $\rho$ (the coherences) decay to zero, leaving a diagonal density matrix that is indistinguishable from a classical probability distribution. When all coherences vanish, all quantum advantage is lost.

---

## 2. Core Architecture & Mechanics

### The Qubit Physical Layer

The abstract mathematical qubit has multiple physical implementations, each with distinct engineering tradeoffs. Superconducting qubits, used by IBM, Google, and Rigetti, operate by cooling a Josephson junction circuit to millikelvin temperatures where quantum effects dominate. The two lowest energy levels of this anharmonic oscillator define $|0\rangle$ and $|1\rangle$. Gate operations are microwave pulses tuned to the transition frequency, typically in the 4–8 GHz range. Coherence times on current devices range from tens to hundreds of microseconds for $T_1$ (energy relaxation) and comparable or shorter times for $T_2$ (dephasing). Trapped-ion qubits, used by IonQ and Quantinuum, encode quantum information in the hyperfine or optical energy levels of individual ions held in electromagnetic traps. They offer significantly longer coherence times (seconds to minutes) but slower gate operations (microsecond to millisecond range) and more complex physical scaling.

The architectural consequence for systems programmers is that every physical qubit has a **coherence budget**: a finite time window within which you must complete your circuit before decoherence destroys the quantum state. Circuit depth, the number of sequential gate layers, is the primary resource constraint, not just qubit count. A 1000-qubit device with shallow coherence time is strictly less capable than a 50-qubit device with deep coherence time for many algorithms. This is directly analogous to memory bandwidth constraints in classical NUMA systems: raw capacity matters less than accessible capacity within your latency budget.

### Quantum Gates and Unitary Evolution

Quantum gates are unitary matrices acting on the Hilbert space of one or more qubits. Unitarity ($U^\dagger U = I$) is the quantum mechanical expression of norm preservation: probabilities must sum to one after any evolution. This also means all quantum gates are inherently reversible, in direct contrast to classical logic gates like AND and OR. The reversibility is not merely a theoretical curiosity; it has thermodynamic implications via Landauer's principle and practical implications for circuit synthesis and optimization.

The fundamental single-qubit gates are the Pauli matrices and their derivatives. The Pauli-X gate is the quantum NOT:

$$X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$$

It maps $|0\rangle \to |1\rangle$ and $|1\rangle \to |0\rangle$, acting as a bit flip. The Pauli-Z gate introduces a phase flip:

$$Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$

mapping $|+\rangle \to |-\rangle$ where $|\pm\rangle = \frac{1}{\sqrt{2}}(|0\rangle \pm |1\rangle)$. The Hadamard gate creates uniform superposition:

$$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

mapping $|0\rangle \to |+\rangle$ and $|1\rangle \to |-\rangle$. It is the quantum Fourier transform on a single qubit and the foundational operation for creating superpositions from computational basis states. The phase rotation gate $R_\phi$ applies a relative phase:

$$R_\phi = \begin{pmatrix} 1 & 0 \\ 0 & e^{i\phi} \end{pmatrix}$$

This gate is critical for the quantum Fourier transform, which is in turn central to Shor's algorithm, quantum phase estimation, and quantum simulation.

The essential two-qubit gate is the Controlled-NOT (CNOT), which together with single-qubit gates forms a universal gate set. The CNOT acts on a control qubit and a target qubit: if the control is $|1\rangle$, it applies X to the target; otherwise, it leaves the target unchanged. In the two-qubit computational basis $\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}$:

$$\text{CNOT} = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}$$

The CNOT is the gate that creates entanglement from product states. Applying a Hadamard to qubit A followed by a CNOT with A as control and B as target transforms $|00\rangle$ into the Bell state $|\Phi^+\rangle$. This two-gate sequence is the canonical entanglement circuit and appears as a subroutine in quantum teleportation, superdense coding, and quantum error correction.

### Quantum Circuit Model Execution Flow

The circuit model of quantum computation follows a precise execution pipeline. Understanding this pipeline at the mechanical level is essential before working with any quantum SDK or simulator.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     QUANTUM CIRCUIT EXECUTION PIPELINE                       │
│                                                                               │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────┐   ┌────────────────┐  │
│  │  State   │   │   Unitary    │   │  Measurement   │   │  Classical     │  │
│  │  Prep    │──▶│  Evolution   │──▶│   (Collapse)   │──▶│  Post-Process  │  │
│  │  |0...0⟩ │   │  U₁U₂...Uₙ  │   │  Born Rule     │   │  (Bitstring)   │  │
│  └──────────┘   └──────────────┘   └────────────────┘   └────────────────┘  │
│                                                                               │
│  PHYSICAL LAYER:                                                              │
│                                                                               │
│  Qubit 0: ──H──────●──────────────────────M──                                │
│                    │                      │                                   │
│  Qubit 1: ─────────⊕──────Rφ─────────────M──                                │
│                    │                      │                                   │
│  Qubit 2: ─────────────────────●──────────M──                                │
│                                │                                              │
│  Qubit 3: ─────────────────────⊕──────────M──                                │
│                                                                               │
│  AMPLITUDE VECTOR (4 qubits = 16 complex numbers):                           │
│                                                                               │
│  |ψ⟩ = Σ αᵢ|i⟩,  i ∈ {0000,...,1111},  Σ|αᵢ|² = 1                         │
│                                                                               │
│  DECOHERENCE PRESSURE:                                                        │
│                                                                               │
│  Gate depth 0──────────────────────────────────▶ T₂ limit                   │
│  Fidelity  1.0 ════════════════╗                                             │
│                                 ╚══════════════▶ 0.0  (exponential decay)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

State preparation initializes all physical qubits to $|0\rangle$, which on superconducting devices means waiting for the qubits to relax to their ground state or applying an active reset pulse. Unitary evolution then applies the gate sequence, each gate consuming coherence time from the budget. Physical devices do not implement arbitrary two-qubit gates between all qubit pairs; the **connectivity graph** (or coupling map) defines which pairs of physical qubits can interact natively. Transpilation, the process of compiling a logical circuit to a physical circuit that respects the connectivity graph, is one of the central engineering challenges in current quantum software stacks, directly analogous to register allocation and instruction scheduling in classical compilers.

### Measurement and the Born Rule

Measurement in quantum mechanics is irreversible and destructive to superposition. When you measure a qubit in the computational basis, the quantum state collapses to either $|0\rangle$ or $|1\rangle$ with probabilities $|\alpha|^2$ and $|\beta|^2$ respectively, and the original superposition is permanently destroyed. This is not a limitation of measurement precision; it is a fundamental feature of quantum mechanics with no classical analog.

The engineering implication is that a quantum circuit must be run many times (shots) to reconstruct the probability distribution over outcomes. If you have an $n$-qubit circuit and you measure all qubits, each shot yields one $n$-bit string. The probability of observing a particular string $x$ is $|\langle x | \psi \rangle|^2$, the squared modulus of the corresponding amplitude. To estimate this distribution with statistical error $\epsilon$, you need $O(1/\epsilon^2)$ shots. For a circuit that has amplified one correct answer to have amplitude close to 1 (as in Grover's algorithm), a small number of shots suffices. For algorithms that produce a broad distribution, the shot budget becomes a significant cost driver.

Partial measurement introduces conditional quantum dynamics. Measuring only qubit A of the Bell state $|\Phi^+\rangle$ and obtaining outcome 0 collapses the joint state to $|00\rangle$; obtaining 1 collapses to $|11\rangle$. The unmeasured qubit B is left in a definite state conditioned on the classical measurement outcome of A. This measurement-conditioned state update is the operational mechanism underlying quantum teleportation and measurement-based quantum computation. For the systems programmer, it is the quantum analog of a conditional branch: a classical bit produced by measurement gates subsequent quantum operations.

### Simulating Quantum Systems in Software

Before working with real quantum hardware, practitioners build intuition and validate circuits using statevector simulators. A statevector simulator maintains the full $2^n$-dimensional complex vector explicitly in memory and applies gates as matrix multiplications. This is the ground truth reference implementation. The practical limit on a classical workstation with 64 GB of RAM is roughly 30 qubits, since $2^{30}$ double-precision complex numbers require $2^{30} \times 16 \approx 16$ GB.

The two dominant Python SDKs for circuit construction and simulation are Qiskit (IBM) and Cirq (Google). Both follow the same model: construct a circuit object by appending gate operations, then execute it against a backend that is either a local simulator or a cloud-connected quantum processor. The following complete Qiskit program constructs the Bell state, measures it, and executes 1024 shots against the statevector simulator:

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

# Construct Bell state circuit: 2 qubits, 2 classical bits
qc = QuantumCircuit(2, 2)

# Apply Hadamard to qubit 0: |00> -> (|00> + |10>) / sqrt(2)
qc.h(0)

# Apply CNOT with control=0, target=1: -> (|00> + |11>) / sqrt(2)
qc.cx(0, 1)

# Measure both qubits into classical register
qc.measure([0, 1], [0, 1])

# Run against the statevector simulator with 1024 shots
simulator = AerSimulator()
job = simulator.run(qc, shots=1024)
result = job.result()

counts = result.get_counts(qc)
print(counts)  # Expect roughly {'00': 512, '11': 512}
```

This program illustrates the full execution pipeline: circuit definition, backend selection, shot-based execution, and histogram extraction. The output distribution, approximately half $|00\rangle$ and half $|11\rangle$ with no $|01\rangle$ or $|10\rangle$ outcomes, is the definitive experimental signature of entanglement created by this specific Bell circuit. Any deviation from this pattern on real hardware is a direct measurement of gate error and decoherence.

For more detailed state inspection without measurement collapse, the statevector simulator supports extracting the full amplitude vector after circuit execution:

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# Save statevector before measurement
qc.save_statevector()

simulator = AerSimulator(method='statevector')
job = simulator.run(qc)
result = job.result()

sv = result.get_statevector(qc)
print("Amplitudes:", np.array(sv))
# Output: [0.707+0j, 0+0j, 0+0j, 0.707+0j]
# Corresponds to: 1/sqrt(2)|00> + 0|01> + 0|10> + 1/sqrt(2)|11>

# Verify normalization
print("Norm:", np.sum(np.abs(np.array(sv))**2))  # Must equal 1.0

# Compute density matrix for the reduced state of qubit 0
rho_full = np.outer(np.array(sv), np.conj(np.array(sv)))
# Partial trace over qubit 1
rho_A = rho_full[0:2, 0:2] + rho_full[2:4, 2:4]
print("Reduced density matrix of qubit 0:")
print(rho_A)
# Output: [[0.5, 0], [0, 0.5]] - maximally mixed, confirms entanglement
print("Purity Tr(rho^2):", np.trace(rho_A @ rho_A).real)
# Output: 0.5 - strictly less than 1, confirming mixed state from entanglement
```

The partial trace computation here is mechanically important. When you trace out qubit B from the entangled Bell state, you obtain a maximally mixed density matrix for qubit A: $\rho_A = \frac{1}{2}I$. The purity $\text{Tr}(\rho_A^2) = 0.5$ is strictly less than 1, which is the mathematical proof that the two qubits are entangled. A separable state would leave each qubit in a pure state after tracing out the other. This is the operational definition of entanglement from the systems perspective: the reduced state of one party is mixed if and only if it is entangled with the other party.

---

## 3. High-Performance Optimization & Failure Modes

### Coherence Time Management as a Resource Scheduling Problem

Working on current quantum hardware requires treating coherence time as a finite, non-renewable per-job resource, with the same discipline applied to memory budgets in embedded systems or time budgets in real-time scheduling. The two relevant timescales are $T_1$, the longitudinal relaxation time governing how long a qubit can hold excitation energy ($|1\rangle$ decaying to $|0\rangle$), and $T_2$, the transverse relaxation time governing how long phase coherence persists. For superconducting devices, $T_2 \leq 2T_1$ by fundamental Bloch equation constraints, and in practice $T_2$ is often the binding constraint.

The effective depth limit of a circuit is approximately $T_2 / t_{\text{gate}}$, where $t_{\text{gate}}$ is the duration of the slowest gate in your critical path. On IBM superconducting devices, two-qubit CNOT gate times are roughly 300–500 ns. With $T_2 \approx 100 \mu\text{s}$, the theoretical limit is around 200–300 two-qubit gate layers. Practical algorithms must stay well below this limit to maintain acceptable fidelity, because gate errors compound multiplicatively: a circuit of depth $d$ using gates with average error rate $\varepsilon$ per gate has total fidelity that scales roughly as $(1 - \varepsilon)^d$. At $\varepsilon = 0.1\%$ per two-qubit gate, 100 two-qubit gate layers yields fidelity around $0.999^{100} \approx 90\%$. At 1,000 layers, fidelity falls to $0.999^{1000} \approx 37\%$, well below the threshold for reliable computation.

Circuit optimization therefore becomes the critical performance engineering problem. The primary tools are gate cancellation (adjacent $U \cdot U^\dagger = I$ pairs), gate commutation (reordering gates that commute to reduce depth), and synthesis of multi-qubit operations into smaller gate counts. Qiskit's transpiler pipeline provides configurable optimization levels (`optimization_level=0` through `3`) that apply progressively more aggressive transformations. For production circuits, understanding what each level does and profiling the trade-off between compilation time and circuit depth is exactly the same workflow as profiling compiler optimization flags for a critical C hot path.

The following code demonstrates how to inspect and compare circuit depth before and after transpilation:

```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

# Build a GHZ state circuit for 5 qubits (Greenberger-Horne-Zeilinger)
# This creates maximally entangled state: (|00000> + |11111>) / sqrt(2)
n_qubits = 5
qc = QuantumCircuit(n_qubits, n_qubits)
qc.h(0)
for i in range(n_qubits - 1):
    qc.cx(i, i + 1)
qc.measure_all()

print(f"Original circuit depth: {qc.depth()}")
print(f"Original gate count: {qc.size()}")
print(f"CNOT count: {qc.count_ops().get('cx', 0)}")

# Use a fake backend that models a real IBM device topology and noise
backend = FakeManilaV2()

# Transpile at optimization level 1 (basic gate decomposition and routing)
qc_t1 = transpile(qc, backend=backend, optimization_level=1, seed_transpiler=42)
print(f"\nOptimization level 1 depth: {qc_t1.depth()}")
print(f"Optimization level 1 CNOT count: {qc_t1.count_ops().get('cx', 0)}")

# Transpile at optimization level 3 (full optimization: routing + rewriting)
qc_t3 = transpile(qc, backend=backend, optimization_level=3, seed_transpiler=42)
print(f"\nOptimization level 3 depth: {qc_t3.depth()}")
print(f"Optimization level 3 CNOT count: {qc_t3.count_ops().get('cx', 0)}")

# Run both transpiled circuits on the noisy simulator
from qiskit_aer import AerSimulator
noisy_sim = AerSimulator.from_backend(backend)

result_t1 = noisy_sim.run(qc_t1, shots=4096).result()
result_t3 = noisy_sim.run(qc_t3, shots=4096).result()

counts_t1 = result_t1.get_counts()
counts_t3 = result_t3.get_counts()

# Ideal GHZ state should show only '00000' and '11111'
# Error rate is fraction of shots in incorrect bitstrings
total = 4096
correct_t1 = counts_t1.get('00000', 0) + counts_t1.get('11111', 0)
correct_t3 = counts_t3.get('00000', 0) + counts_t3.get('11111', 0)

print(f"\nOptimization level 1 fidelity proxy: {correct_t1/total:.3f}")
print(f"Optimization level 3 fidelity proxy: {correct_t3/total:.3f}")
```

### Decoherence, Noise Models, and Error Characterization

Real quantum hardware does not implement perfect unitary evolution. Every gate has a finite error rate composed of coherent errors (systematic rotation miscalibrations) and incoherent errors (decoherence and measurement errors). Understanding the noise model of your target device is prerequisite to any meaningful circuit optimization, the same way understanding CPU cache hierarchy is prerequisite to optimizing memory-bound computation.

The standard noise characterization protocol is **randomized benchmarking (RB)**: apply sequences of random Clifford gates of increasing length, with each sequence designed to return to the identity, and measure the survival probability as a function of sequence length. The exponential decay of fidelity with sequence length yields the average error per Clifford gate. Interleaved RB isolates the error rate of a specific target gate by inserting it between random Clifford layers. These protocols are implemented in Qiskit Experiments:

```python
from qiskit_experiments.library import StandardRB, InterleavedRB
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_ibm_runtime.fake_provider import FakeManilaV2

backend = FakeManilaV2()

# Standard RB on qubit 0 to measure average Clifford gate fidelity
rb_exp = StandardRB(
    physical_qubits=(0,),
    lengths=list(range(1, 200, 20)),  # Clifford sequence lengths
    num_samples=10,                    # 10 random circuits per length
    seed=42
)

# Run the RB experiment on the noisy simulator
noisy_sim = AerSimulator.from_backend(backend)
rb_data = rb_exp.run(noisy_sim, shots=1024).block_for_results()

# Extract the fitted average error per Clifford gate
rb_result = rb_data.analysis_results("EPC")  # Error Per Clifford
print(f"Average error per Clifford: {rb_result.value:.4f} ± {rb_result.extra['stderr']:.4f}")

# Interleaved RB to isolate CNOT error on the (0,1) edge
from qiskit.circuit.library import CXGate
irb_exp = InterleavedRB(
    interleaved_element=CXGate(),
    physical_qubits=(0, 1),
    lengths=list(range(1, 100, 10)),
    num_samples=10,
    seed=42
)

irb_data = irb_exp.run(noisy_sim, shots=1024).block_for_results()
irb_result = irb_data.analysis_results("EPC")
print(f"CNOT error on (0,1): {irb_result.value:.4f}")
```

### Quantum State Tomography and Debugging Entanglement

When a circuit produces unexpected measurement statistics, the diagnostic workflow mirrors classical debugging but requires different tools. The quantum equivalent of inspecting memory state is **quantum state tomography (QST)**: measure the quantum state in multiple basis settings to reconstruct the density matrix. Full QST of an $n$-qubit system requires $O(4^n)$ distinct measurement settings and is exponentially expensive, but for small subsystems (2–3 qubits) it is the definitive debugging tool. Qiskit Experiments provides a complete implementation:

```python
from qiskit_experiments.library import StateTomography
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from qiskit import QuantumCircuit
import numpy as np

# Target: prepare Bell state and tomograph it to verify entanglement
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# State tomography on qubits (0, 1)
qst_exp = StateTomography(qc, measurement_indices=[0, 1])

backend = FakeManilaV2()
noisy_sim = AerSimulator.from_backend(backend)

tomo_data = qst_exp.run(noisy_sim, shots=4096).block_for_results()

# Extract the reconstructed density matrix
state_result = tomo_data.analysis_results("state")
rho = state_result.value

print("Reconstructed density matrix:")
print(np.round(rho.data, 3))

# Compute fidelity with ideal Bell state
ideal_bell = np.array([[0.5, 0, 0, 0.5],
                        [0,   0, 0, 0  ],
                        [0,   0, 0, 0  ],
                        [0.5, 0, 0, 0.5]])

# State fidelity: F(rho, sigma) = Tr(rho @ sigma) for one pure state
fidelity = np.real(np.trace(rho.data @ ideal_bell))
print(f"\nFidelity with ideal Bell state: {fidelity:.4f}")

# Concurrence as an entanglement measure: C = 0 (separable) to 1 (max entangled)
# Computed via eigenvalues of rho * (Y⊗Y) * rho* * (Y⊗Y)
Y = np.array([[0, -1j], [1j, 0]])
YY = np.kron(Y, Y)
R = rho.data @ YY @ np.conj(rho.data) @ YY
eigenvalues = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
eigenvalues = np.maximum(eigenvalues, 0)
sqrt_eigs = np.sqrt(eigenvalues)
concurrence = max(0, sqrt_eigs[0] - sqrt_eigs[1] - sqrt_eigs[2] - sqrt_eigs[3])
print(f"Concurrence (entanglement measure): {concurrence:.4f}")
# Ideal Bell state gives concurrence = 1.0; noise reduces it toward 0
```

### Failure Modes and Their Physical Origins

The most consequential failure modes in quantum circuit execution trace directly to physical mechanisms with specific signatures in measurement data.

**Bit flip errors** (X errors) cause $|0\rangle \leftrightarrow |1\rangle$ transitions and manifest as unexpected outcomes in the computational basis. They arise from residual coupling to thermal photons or control pulse imperfections. **Phase flip errors** (Z errors) introduce a $-1$ phase to $|1\rangle$ without changing the computational basis probability, making them invisible to Z-basis measurement but detectable by measuring in the X basis. **Leakage** is specific to multi-level physical systems like superconducting transmons: the state escapes the two-level computational subspace into higher energy levels ($|2\rangle$, $|3\rangle$). It manifests as measurement outcomes that appear neither 0 nor 1 in raw hardware readout. **Crosstalk** occurs when applying a gate to one qubit inadvertently shifts the phase or flips the state of a neighboring qubit through parasitic coupling; it appears as correlated errors between nearby qubits and is particularly damaging for circuit topologies that stress densely connected qubit clusters.

**Readout error**, the probability of measuring $|0\rangle$ when the qubit is in $|1\rangle$ or vice versa, is typically the largest single error source on current devices, often exceeding gate error rates by an order of magnitude. Readout mitigation, applying a correction matrix constructed from calibration circuits that prepare known states and measure them, is a standard technique and is available in Qiskit through the `mthree` package or the built-in `TwirledReadoutErrorExtinction` primitive. This correction is not quantum error correction; it is classical post-processing that corrects the probability distribution but cannot recover individual shot accuracy.

The boundary between what is tractable on current Noisy Intermediate-Scale Quantum (NISQ) devices and what requires fault-tolerant quantum computing with error correction is precisely the circuit depth at which the cumulative error rate exceeds the threshold for meaningful signal extraction. For most variational algorithms like the Variational Quantum Eigensolver (VQE) and the Quantum Approximate Optimization Algorithm (QAOA), the working hypothesis is that shallow circuits (depth 10–50) can produce useful approximate solutions before noise dominates. For algorithms like Shor's factoring, which requires circuit depths scaling polynomially with the number of bits to factor, the coherence and error requirements are many orders of magnitude beyond current NISQ hardware. Realizing those algorithms requires logical qubits encoded in quantum error-correcting codes, the surface code being the leading candidate, where many physical qubits cooperate to protect one logical qubit. At current physical error rates around $10^{-3}$ per gate, the surface code requires roughly 1,000 physical qubits per logical qubit to achieve logical error rates below $10^{-10}$. This is the central engineering challenge of the field, and it grounds every architectural decision from qubit technology selection to compiler design in a single governing constraint: reduce the physical error rate and increase the coherence time, or find algorithms shallow enough to run within the existing budget.
