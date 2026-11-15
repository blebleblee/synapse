# Operational Verification Labs: Quantum Computing

## Objective & Operational Lab Setup

The intersection of quantum computing and robotics represents one of the most computationally demanding frontiers in modern engineering. Quantum algorithms promise exponential speedups for combinatorial optimization problems that plague robotic path planning, sensor fusion, and multi-agent coordination. However, the practical deployment of quantum computing techniques in robotics requires rigorous operational verification across simulation environments, hybrid classical-quantum architectures, and noise-resilient algorithmic implementations. This laboratory guide grounds quantum computing theory in hands-on robotics applications, focusing on variational quantum eigensolvers (VQE), quantum approximate optimization algorithms (QAOA), and quantum machine learning circuits applied to real-world robotic control and perception problems.

The operational verification methodology adopted here maintains an 80/20 split between executable practice and theoretical foundation. You will construct quantum circuits using Qiskit, IBM's open-source quantum computing framework, and integrate them with classical robotics simulation environments including Gazebo and ROS 2. The analytical environment comprises a Linux workstation with Python 3.10 or later, Qiskit 0.45+, NumPy, SciPy, and the Robot Operating System 2 (ROS 2 Humble or Iron). Diagnostic instruments include quantum circuit fidelity metrics, gate error rates, decoherence time measurements, and classical-quantum interface latency profilers. The empirical audit framework tracks quantum advantage thresholds, comparing quantum algorithm performance against classical baselines in motion planning, inverse kinematics solving, and simultaneous localization and mapping (SLAM) optimization.

Quantum computing operates on qubits, which exist in superposition states described by complex probability amplitudes. A single qubit state vector takes the form $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ where $|\alpha|^2 + |\beta|^2 = 1$. Multi-qubit systems exhibit entanglement, enabling quantum algorithms to explore exponentially large solution spaces in parallel. Quantum gates manipulate qubit states through unitary transformations: the Hadamard gate creates superposition, Pauli X/Y/Z gates perform rotations, and controlled-NOT (CNOT) gates generate entanglement. Measurement collapses the quantum state into a classical bitstring with probabilities determined by the amplitude magnitudes. Real quantum hardware suffers from gate errors, decoherence (T1 relaxation and T2 dephasing times typically 50–200 microseconds), and readout errors, necessitating error mitigation strategies and verification protocols.

For robotics applications, quantum computing addresses NP-hard problems where classical algorithms scale poorly. Motion planning in high-dimensional configuration spaces with obstacle constraints maps to quadratic unconstrained binary optimization (QUBO) problems solvable by QAOA. Inverse kinematics for redundant manipulators with multiple solutions benefits from quantum sampling of solution manifolds. Sensor fusion in SLAM with loop closure constraints becomes a graph optimization problem where quantum annealing or variational algorithms can explore closure hypotheses in superposition. Machine learning tasks such as visual object classification leverage quantum neural networks with parameterized rotation gates trained via classical optimization loops.

The operational lab environment requires installation of Qiskit and ROS 2 with careful attention to Python virtual environment isolation. Begin by creating a dedicated conda environment to prevent dependency conflicts between quantum computing libraries and ROS 2 packages. Install Qiskit via pip, ensuring compatibility with the latest stable release. The Qiskit runtime provides both local simulation backends (Aer simulator with GPU acceleration support) and cloud access to IBM Quantum hardware. For robotics integration, install ROS 2 using the official Debian packages and source the workspace overlay. Create a custom ROS 2 package named `quantum_robotics` with Python nodes that instantiate quantum circuits, submit jobs to simulators or hardware, and publish results to ROS topics for consumption by motion planners or control loops.

Statistical models for operational verification include quantum circuit fidelity measurement comparing ideal statevector simulation against noisy hardware execution, cross-entropy benchmarking to detect coherent errors, and randomized benchmarking protocols that quantify average gate error rates. Empirical audit rubrics track quantum resource utilization: circuit depth (number of sequential gate layers), two-qubit gate count (primary noise source), qubit connectivity constraints, and total execution time including classical optimization overhead. For robotics metrics, assess path planning solution quality (path length, smoothness, obstacle clearance), inverse kinematics convergence rates, and SLAM map accuracy under varying quantum noise levels. Establish classical baseline performance using state-of-the-art solvers (RRT*, IPOPT, g2o) to quantify quantum advantage thresholds where quantum algorithms demonstrably outperform classical counterparts.

The analytical research environment setup proceeds as follows. Install Anaconda or Miniconda for Python environment management. Create a new environment with `conda create -n quantum_robotics python=3.10` and activate it. Install Qiskit core packages: `pip install qiskit qiskit-aer qiskit-ibm-runtime qiskit-optimization`. Install scientific computing dependencies: `pip install numpy scipy matplotlib pandas scikit-learn`. For ROS 2 integration on Ubuntu 22.04, add the ROS 2 apt repository and install the desktop configuration: `sudo apt install ros-humble-desktop`. Source the ROS 2 setup script in your `.bashrc` to enable ROS commands. Create a ROS 2 workspace: `mkdir -p ~/quantum_ros2_ws/src && cd ~/quantum_ros2_ws/src`. Generate the quantum_robotics package: `ros2 pkg create --build-type ament_python quantum_robotics --dependencies rclpy std_msgs geometry_msgs`. Within the package, create directories for quantum circuit definitions, optimization routines, and ROS node implementations.

Quantum circuit construction in Qiskit follows an object-oriented paradigm. Import the QuantumCircuit, QuantumRegister, and ClassicalRegister classes. Instantiate a quantum register with the desired number of qubits and a classical register for measurement outcomes. The QuantumCircuit object applies gates via method calls: `qc.h(0)` applies a Hadamard gate to qubit 0, `qc.cx(0, 1)` applies a CNOT with qubit 0 as control and qubit 1 as target. Parameterized circuits for variational algorithms use the Parameter class to define rotation angles that classical optimizers adjust. Circuit visualization employs `qc.draw('mpl')` to generate publication-quality matplotlib figures. Execution on simulators requires importing Aer backends and constructing a transpiled circuit: `transpiled_qc = transpile(qc, backend)`, followed by job submission: `job = backend.run(transpiled_qc, shots=1024)`. Result retrieval extracts measurement count dictionaries: `counts = job.result().get_counts()`, where keys are bitstring outcomes and values represent observed frequencies.

Noise modeling in Qiskit simulations replicates real quantum hardware imperfections. The Aer simulator accepts noise models constructed from device calibration data. Import `NoiseModel` and gate error constructors. Define single-qubit depolarizing errors with probability $p_1$ and two-qubit errors with probability $p_2$, typically $p_1 \approx 10^{-3}$ and $p_2 \approx 10^{-2}$ for current superconducting qubit systems. Thermal relaxation errors require T1 and T2 times, with gate durations determining error accumulation. Readout errors introduce bitflip probabilities extracted from device readout calibration matrices. Apply the noise model to the Aer simulator backend: `noisy_backend = AerSimulator(noise_model=noise_model)`. Comparative analysis between ideal statevector simulation and noisy simulation quantifies error mitigation requirements.

Integration with ROS 2 enables quantum algorithms to operate within robotic control loops. Create a ROS 2 Python node by subclassing `rclpy.node.Node`. In the constructor, instantiate publishers for quantum algorithm results and subscribers for incoming robotics tasks. The node's main computation method constructs quantum circuits based on received task parameters, executes them on a Qiskit backend, processes measurement outcomes, and publishes results. For example, a path planning node subscribes to a `geometry_msgs/PoseStamped` topic for goal poses, formulates a QUBO problem encoding obstacle constraints and path length objectives, maps it to a QAOA circuit, executes the quantum optimization, decodes the bitstring solution into waypoint coordinates, and publishes a `nav_msgs/Path` message. Timing analysis measures end-to-end latency from task receipt to solution publication, identifying bottlenecks in quantum job queuing, circuit execution, and classical postprocessing.

The diagnostic checklist for operational verification spans quantum-specific and robotics-specific metrics. Quantum circuit diagnostics include circuit depth analysis (shallow circuits reduce decoherence impact), gate count decomposition (two-qubit gates dominate error budgets), connectivity graph validation (ensuring qubit topology matches hardware constraints), and parameter optimization convergence (tracking cost function values across optimization iterations). Execute fidelity measurements by comparing ideal statevector amplitudes against sampled measurement distributions using quantum state tomography or direct fidelity estimation. For robotics diagnostics, validate that quantum-generated solutions satisfy hard constraints (collision-free paths, joint limits, kinematic feasibility) and compare soft objective values (path length, energy consumption, time optimality) against classical baselines. Statistical significance testing employs t-tests or Mann-Whitney U tests across multiple problem instances to confirm quantum advantage.

## Exercise 1: Foundational Practical Implementation

The foundational exercise establishes a complete workflow for applying quantum computing to a canonical robotics problem: motion planning for a 2D mobile robot in a grid environment with obstacles. This problem maps naturally to a quadratic unconstrained binary optimization formulation, which quantum approximate optimization algorithms solve by preparing quantum superpositions over feasible paths and iteratively refining amplitude distributions to favor low-cost solutions. The exercise constructs a QAOA circuit, executes it on both ideal and noisy simulators, decodes measurement outcomes into robot waypoints, and validates solution quality against a classical A* baseline.

Begin by defining the robotics problem instance. Consider a 5x5 grid where each cell represents a discrete position. The robot starts at cell (0,0) and must reach goal cell (4,4). Obstacles occupy cells (1,2), (2,2), (3,1), and (3,3). Each potential path from start to goal corresponds to a sequence of grid cells. For computational tractability, discretize time into four steps and encode the robot's position at each timestep as a binary variable. Specifically, introduce binary variables $x_{t,i,j}$ where $t \in \{0,1,2,3,4\}$ represents the timestep, and $(i,j)$ indexes the grid cell. The variable $x_{t,i,j} = 1$ indicates the robot occupies cell $(i,j)$ at time $t$.

Formulate the cost function as a sum of penalty terms enforcing physical constraints and optimizing path objectives. First, enforce that the robot occupies exactly one cell at each timestep: $\sum_{i,j} x_{t,i,j} = 1$ for all $t$. Second, penalize obstacle occupancy: add large penalty coefficients to terms $x_{t,i,j}$ where $(i,j)$ is an obstacle cell. Third, enforce motion continuity: the robot can only move to adjacent cells (including staying in place) between consecutive timesteps. This constraint translates to penalty terms for non-adjacent transitions: if $x_{t,i,j} = 1$ and $x_{t+1,i',j'} = 1$, penalize cases where $(i',j')$ is not in the four-connected neighborhood of $(i,j)$. Fourth, minimize path length by adding a small linear cost to each movement action. Convert these constraints into a quadratic unconstrained binary optimization form by expanding penalty products and collecting coefficients into a matrix $Q$ where the objective is $\sum_{k,l} Q_{kl} x_k x_l$.

Implement the QUBO construction in Python. Create a function `construct_path_planning_qubo(grid_size, obstacles, start, goal, num_steps)` that returns the $Q$ matrix and a mapping from binary variable indices to $(t,i,j)$ tuples. Use NumPy arrays to represent $Q$, initializing with zeros and iterating over timesteps and grid cells to populate constraint penalties. For the uniqueness constraint at each timestep, add positive quadratic terms $Q_{k,k}$ and negative cross terms $Q_{k,l}$ for variables at the same timestep. For obstacle penalties, add large positive diagonal terms $Q_{k,k}$ where variable $k$ corresponds to an obstacle cell. For motion continuity, iterate over consecutive timestep pairs, identify all variable pairs representing non-adjacent transitions, and add positive quadratic penalties. The path length objective contributes negative diagonal terms to variables representing movement actions (non-diagonal transitions).

Translate the QUBO matrix into a QAOA quantum circuit. The QAOA algorithm alternates between problem Hamiltonian evolution and mixer Hamiltonian evolution, parameterized by angles $\gamma$ and $\beta$. The problem Hamiltonian encodes the QUBO cost function. Each term $Q_{kl} x_k x_l$ in the QUBO corresponds to a Pauli-Z operator product $Z_k Z_l$ in the quantum Hamiltonian. Diagonal terms $Q_{kk} x_k$ map to single-qubit $Z_k$ operators. The mixer Hamiltonian applies uniform superposition over all bitstrings, implemented via $X$ rotations. A single QAOA layer consists of applying the unitary $e^{-i\gamma H_P} e^{-i\beta H_M}$ where $H_P$ is the problem Hamiltonian and $H_M$ is the mixer Hamiltonian.

Construct the QAOA circuit in Qiskit. Begin by determining the number of qubits required: for a 5x5 grid over 5 timesteps, you need 25 qubits per timestep, totaling 125 qubits, which exceeds current hardware limits. Apply problem reduction by pruning the search space. Instead of encoding all grid cells at each timestep, restrict the robot to a corridor around the straight-line path from start to goal, reducing the number of candidate cells per timestep to approximately 5-7. This heuristic reduces the qubit count to 30-35, feasible for simulation. Re-index binary variables accordingly and reconstruct the QUBO matrix.

With the reduced QUBO in hand, implement the QAOA circuit construction function. Import necessary Qiskit components: `from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister; from qiskit.circuit import Parameter`. Define parameters for QAOA angles: `gamma = Parameter('γ'); beta = Parameter('β')`. Instantiate a quantum circuit with the appropriate number of qubits and classical bits: `n_qubits = Q.shape[0]; qr = QuantumRegister(n_qubits, 'q'); cr = ClassicalRegister(n_qubits, 'c'); qc = QuantumCircuit(qr, cr)`. Initialize all qubits in uniform superposition via Hadamard gates: `qc.h(range(n_qubits))`.

Implement the problem Hamiltonian evolution layer. Iterate over the QUBO matrix entries. For diagonal terms $Q_{kk}$, apply a parameterized $R_z$ rotation: `qc.rz(2 * gamma * Q[k, k], k)`. For off-diagonal terms $Q_{kl}$ with $k < l$, implement the two-qubit interaction $e^{-i\gamma Q_{kl} Z_k Z_l}$ using a CNOT-based decomposition: `qc.cx(k, l); qc.rz(2 * gamma * Q[k, l], l); qc.cx(k, l)`. This sequence applies a controlled-Z rotation conditioned on qubit $k$. After iterating over all QUBO terms, the problem Hamiltonian layer is complete.

Implement the mixer Hamiltonian layer by applying parameterized $R_x$ rotations to all qubits: `qc.rx(2 * beta, range(n_qubits))`. These $X$ rotations enable transitions between computational basis states, allowing the optimization to explore the solution space. For multi-layer QAOA (p-QAOA with $p$ layers), repeat the problem and mixer layers $p$ times with distinct parameter sets $(\gamma_1, \beta_1), \ldots, (\gamma_p, \beta_p)$. In practice, $p=1$ or $p=2$ often suffices for moderate-sized problems.

Append measurement operations to the circuit: `qc.measure(qr, cr)`. The complete QAOA circuit is now defined with symbolic parameters. To execute, bind concrete parameter values. For initial parameter selection, use heuristics from the literature: $\gamma \in [0, \pi]$ and $\beta \in [0, \pi/2]$. Implement a classical optimization loop that repeatedly binds parameters, executes the circuit, computes the expectation value of the cost function from measurement outcomes, and updates parameters using a gradient-free optimizer such as COBYLA or Nelder-Mead.

Code the expectation value computation. After circuit execution, retrieve the measurement counts dictionary. For each bitstring outcome, decode it into binary variable values $x_k$, evaluate the QUBO cost function $\sum_{k,l} Q_{kl} x_k x_l$, and weight by the measurement probability (count divided by total shots). Sum over all outcomes to obtain the expectation value: `expectation = sum(counts[bitstring] / shots * evaluate_qubo(Q, bitstring) for bitstring in counts)`. The `evaluate_qubo` function converts the bitstring to a NumPy array and computes the quadratic form.

Integrate this into a classical optimization loop using SciPy's minimize function. Define an objective function that takes parameter values, binds them to the QAOA circuit, executes on the Aer simulator, and returns the expectation value. Import `from scipy.optimize import minimize`. Call `result = minimize(objective_function, initial_params, method='COBYLA')`. After optimization converges, extract the optimal parameters and re-execute the circuit with a large shot count (e.g., 8192 shots) to obtain a high-fidelity sample of optimal bitstrings. Select the bitstring with the highest measurement count as the candidate solution.

Decode the optimal bitstring into a robot path. Each bit corresponds to a binary variable $x_{t,i,j}$. Extract the bits set to 1, map them to $(t,i,j)$ tuples using the variable index mapping, and construct the sequence of grid cells the robot visits at each timestep. Validate that the path satisfies constraints: exactly one cell occupied per timestep, no obstacle cells visited, and motion continuity (consecutive cells are adjacent). If the quantum solution violates constraints due to noise or insufficient optimization, apply a post-processing heuristic: select the nearest valid path by minimal Hamming distance to the quantum bitstring.

Visualize the solution path by plotting the 5x5 grid with obstacles marked, the start and goal cells highlighted, and the quantum-generated path drawn as a connected line. Compare against a classical A* pathfinding result. Compute path length for both solutions. For this small problem instance, classical A* should find the globally optimal path; quantum advantage is not expected. The objective here is operational verification: confirming that the quantum algorithm produces feasible solutions and the integration with robotics problem formulations is correct.

Extend the exercise by introducing noise modeling. Import `from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error`. Construct a noise model representative of IBM Quantum hardware. Define single-qubit depolarizing error with $p_1 = 0.001$ and two-qubit error with $p_2 = 0.01$. Add thermal relaxation errors with T1 = 100 microseconds and T2 = 80 microseconds. Apply the noise model to the Aer simulator: `noisy_backend = AerSimulator(noise_model=noise_model)`. Re-run the QAOA optimization on the noisy simulator. Observe degraded solution quality: the expectation value at optimal parameters increases (worse cost), and the most frequent bitstring may violate constraints. Implement error mitigation via zero-noise extrapolation: execute the circuit at multiple noise scaling factors (e.g., 1x, 2x, 3x noise rates), fit a polynomial to the expectation values versus noise level, and extrapolate to zero noise.

Document the complete workflow in a Jupyter notebook with code cells for QUBO construction, QAOA circuit creation, parameter optimization, and result visualization. Include markdown cells explaining each step's physical interpretation and connecting quantum operations to robotics objectives. Capture the output logs showing parameter convergence, final expectation values, and decoded paths. This notebook serves as a replicable template for applying QAOA to larger motion planning problems.

Complete Python implementation follows. Create a file `qaoa_path_planning.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

def construct_path_planning_qubo(grid_size, obstacles, start, goal, num_steps, corridor_width=2):
    """
    Construct QUBO matrix for robot path planning with corridor pruning.
    Returns Q matrix and variable index mapping.
    """
    # Prune grid cells to corridor around straight-line path
    def in_corridor(i, j):
        line_i = np.linspace(start[0], goal[0], num_steps + 1)
        line_j = np.linspace(start[1], goal[1], num_steps + 1)
        for t in range(num_steps + 1):
            if abs(i - line_i[t]) <= corridor_width and abs(j - line_j[t]) <= corridor_width:
                return True
        return False
    
    # Build variable index mapping
    var_to_idx = {}
    idx_to_var = {}
    idx = 0
    for t in range(num_steps + 1):
        for i in range(grid_size):
            for j in range(grid_size):
                if in_corridor(i, j):
                    var_to_idx[(t, i, j)] = idx
                    idx_to_var[idx] = (t, i, j)
                    idx += 1
    
    n_vars = len(var_to_idx)
    Q = np.zeros((n_vars, n_vars))
    
    # Constraint: exactly one cell per timestep
    penalty_unique = 10.0
    for t in range(num_steps + 1):
        timestep_vars = [v for v in var_to_idx if v[0] == t]
        for v1 in timestep_vars:
            i1 = var_to_idx[v1]
            Q[i1, i1] -= penalty_unique  # Linear term
            for v2 in timestep_vars:
                i2 = var_to_idx[v2]
                if i1 != i2:
                    Q[i1, i2] += 2 * penalty_unique  # Quadratic term
    
    # Penalty: obstacle cells
    penalty_obstacle = 50.0
    for v in var_to_idx:
        t, i, j = v
        if (i, j) in obstacles:
            idx = var_to_idx[v]
            Q[idx, idx] += penalty_obstacle
    
    # Penalty: non-adjacent transitions
    penalty_motion = 20.0
    for t in range(num_steps):
        current_vars = [v for v in var_to_idx if v[0] == t]
        next_vars = [v for v in var_to_idx if v[0] == t + 1]
        for v1 in current_vars:
            i1 = var_to_idx[v1]
            t1, x1, y1 = v1
            for v2 in next_vars:
                i2 = var_to_idx[v2]
                t2, x2, y2 = v2
                dist = abs(x2 - x1) + abs(y2 - y1)
                if dist > 1:  # Not adjacent
                    Q[i1, i2] += penalty_motion
    
    # Objective: minimize path length
    cost_movement = 0.1
    for t in range(num_steps):
        current_vars = [v for v in var_to_idx if v[0] == t]
        next_vars = [v for v in var_to_idx if v[0] == t + 1]
        for v1 in current_vars:
            i1 = var_to_idx[v1]
            t1, x1, y1 = v1
            for v2 in next_vars:
                i2 = var_to_idx[v2]
                t2, x2, y2 = v2
                if (x1, y1) != (x2, y2):  # Movement action
                    Q[i1, i2] -= cost_movement
    
    return Q, var_to_idx, idx_to_var

def create_qaoa_circuit(Q, gamma, beta):
    """
    Construct single-layer QAOA circuit for given QUBO matrix.
    """
    n_qubits = Q.shape[0]
    qr = QuantumRegister(n_qubits, 'q')
    cr = ClassicalRegister(n_qubits, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # Initial superposition
    qc.h(range(n_qubits))
    
    # Problem Hamiltonian layer
    for i in range(n_qubits):
        if Q[i, i] != 0:
            qc.rz(2 * gamma * Q[i, i], i)
    
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            if Q[i, j] != 0:
                qc.cx(i, j)
                qc.rz(2 * gamma * Q[i, j], j)
                qc.cx(i, j)
    
    # Mixer Hamiltonian layer
    qc.rx(2 * beta, range(n_qubits))
    
    # Measurement
    qc.measure(qr, cr)
    
    return qc

def evaluate_qubo(Q, bitstring):
    """
    Evaluate QUBO cost for a given bitstring.
    """
    x = np.array([int(b) for b in bitstring[::-1]])
    return x @ Q @ x

def qaoa_objective(params, Q, backend, shots=1024):
    """
    Compute expectation value of QUBO cost for given QAOA parameters.
    """
    gamma, beta = params
    qc = create_qaoa_circuit(Q, gamma, beta)
    transpiled = transpile(qc, backend)
    job = backend.run(transpiled, shots=shots)
    counts = job.result().get_counts()
    
    expectation = 0
    for bitstring, count in counts.items():
        cost = evaluate_qubo(Q, bitstring)
        expectation += (count / shots) * cost
    
    return expectation

def decode_path(bitstring, idx_to_var, num_steps):
    """
    Decode bitstring into robot path.
    """
    path = []
    for t in range(num_steps + 1):
        for idx, bit in enumerate(bitstring[::-1]):
            if bit == '1' and idx in idx_to_var:
                var = idx_to_var[idx]
                if var[0] == t:
                    path.append((var[1], var[2]))
                    break
    return path

# Main execution
grid_size = 5
obstacles = [(1, 2), (2, 2), (3, 1), (3, 3)]
start = (0, 0)
goal = (4, 4)
num_steps = 6

print("Constructing QUBO matrix...")
Q, var_to_idx, idx_to_var = construct_path_planning_qubo(grid_size, obstacles, start, goal, num_steps)
print(f"QUBO size: {Q.shape[0]} qubits")

# Run QAOA optimization
backend = AerSimulator()
initial_params = [np.pi / 4, np.pi / 8]

print("Running QAOA optimization...")
result = minimize(
    qaoa_objective,
    initial_params,
    args=(Q, backend, 1024),
    method='COBYLA',
    options={'maxiter': 50}
)

print(f"Optimal parameters: gamma={result.x[0]:.4f}, beta={result.x[1]:.4f}")
print(f"Final cost expectation: {result.fun:.4f}")

# Sample optimal solution
optimal_gamma, optimal_beta = result.x
qc_optimal = create_qaoa_circuit(Q, optimal_gamma, optimal_beta)
transpiled_optimal = transpile(qc_optimal, backend)
job_optimal = backend.run(transpiled_optimal, shots=8192)
counts_optimal = job_optimal.result().get_counts()

# Extract best bitstring
best_bitstring = max(counts_optimal, key=counts_optimal.get)
print(f"Best bitstring: {best_bitstring} (count: {counts_optimal[best_bitstring]})")

# Decode path
path = decode_path(best_bitstring, idx_to_var, num_steps)
print(f"Decoded path: {path}")

# Visualize
fig, ax = plt.subplots(figsize=(8, 8))
for i in range(grid_size):
    for j in range(grid_size):
        if (i, j) in obstacles:
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor='black'))
        else:
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor='white', edgecolor='gray'))

ax.plot([start[1] + 0.5], [start[0] + 0.5], 'go', markersize=15, label='Start')
ax.plot([goal[1] + 0.5], [goal[0] + 0.5], 'ro', markersize=15, label='Goal')

if len(path) == num_steps + 1:
    path_x = [p[1] + 0.5 for p in path]
    path_y = [p[0] + 0.5 for p in path]
    ax.plot(path_x, path_y, 'b-o', linewidth=2, markersize=8, label='Quantum Path')

ax.set_xlim(0, grid_size)
ax.set_ylim(0, grid_size)
ax.set_aspect('equal')
ax.legend()
ax.set_title('QAOA Path Planning Solution')
plt.gca().invert_yaxis()
plt.savefig('qaoa_path.png', dpi=150)
print("Path visualization saved to qaoa_path.png")
```

Execute this script in your quantum_robotics conda environment. Monitor the optimization progress via printed log messages. The COBYLA optimizer typically converges within 30-50 iterations for this problem size. The final expectation value should be negative if the algorithm successfully minimizes the cost function. The decoded path should connect start to goal while avoiding obstacles. If the path contains constraint violations (non-adjacent transitions or obstacle collisions), increase penalty coefficients in the QUBO construction and re-run.

For operational verification, vary problem parameters and assess robustness. Increase the grid size to 7x7 and adjust corridor width to maintain feasible qubit counts. Add additional obstacles to create more complex navigation scenarios. Test different QAOA depth parameters (p=2 or p=3) by duplicating problem and mixer layers with independent parameter sets. Compare solution quality versus circuit depth and gate count, identifying the optimal tradeoff for your computational budget.

Integrate with ROS 2 by wrapping the QAOA execution in a service node. Create a ROS 2 service definition `QuantumPathPlanning.srv` with request fields for start pose, goal pose, and obstacle positions, and response field for the computed path as a sequence of waypoints. Implement the service callback to construct the QUBO, run QAOA optimization, and return the decoded path. Test the service using the ROS 2 CLI: `ros2 service call /quantum_path_planning quantum_robotics/srv/QuantumPathPlanning "{start: {x: 0, y: 0}, goal: {x: 4, y: 4}, obstacles: [{x: 1, y: 2}, {x: 2, y: 2}]}"`. Measure end-to-end latency from service request to response, identifying quantum execution time as the dominant component.

## Exercise 2: Parameter Variation & Empirical Analysis

The second exercise investigates the sensitivity of quantum algorithm performance to hyperparameter choices, noise characteristics, and problem instance complexity. Systematic parameter sweeps establish operational design guidelines for deploying quantum computing in robotics applications, identifying regimes where quantum advantage emerges and quantifying the resource requirements (qubit count, circuit depth, shot count) necessary for reliable solutions. The focus shifts to a more complex robotics problem: inverse kinematics for a 6-DOF manipulator with redundancy resolution via quantum sampling.

Inverse kinematics (IK) solves for joint angles that position a robot end-effector at a desired pose. For manipulators with more than six degrees of freedom, the solution space is under-constrained, admitting infinitely many joint configurations. Classical IK solvers apply optimization or analytical methods to select a single solution based on secondary objectives like minimizing joint displacement or avoiding singularities. Quantum computing offers an alternative approach: formulate IK as a constraint satisfaction problem, encode it into a quantum circuit, and sample multiple valid solutions in superposition. Post-selection or amplitude amplification biases the samples toward solutions satisfying secondary objectives.

The manipulator model used here is a simplified 6R (six revolute joints) serial chain resembling a UR5 collaborative robot. Each joint has range $[-\pi, \pi]$ and the end-effector pose is defined by a 3D position and 3D orientation (represented as Euler angles or quaternion). The forward kinematics map joint angles $\theta = (\theta_1, \ldots, \theta_6)$ to end-effector pose via Denavit-Hartenberg (DH) transformations. The inverse kinematics problem takes a target pose $(x_d, y_d, z_d, \phi_d, \theta_d, \psi_d)$ and seeks joint angles $\theta$ satisfying the forward kinematics within tolerance $\epsilon$.

Discretize each joint angle into $k$ bits, enabling $2^k$ discrete values over the range $[-\pi, \pi]$. For $k=3$ bits per joint, each joint has 8 possible angles, and the total configuration space has $8^6 \approx 262,000$ states, requiring 18 qubits to encode. Define a cost function penalizing pose errors: $C(\theta) = \|f(\theta) - (x_d, y_d, z_d)\|^2 + \lambda \|\text{orientation\_error}\|^2$, where $f(\theta)$ is the forward kinematics position output and $\lambda$ weights orientation error. Convert this cost into a QUBO by evaluating $C(\theta)$ over all $2^{18}$ configurations (infeasible for classical enumeration but structured for quantum search).

However, directly encoding a 6-DOF IK problem as a QUBO on 18 qubits results in a cost function with $18^2 = 324$ quadratic terms, many with negligible coefficients. Instead, employ a hybrid variational approach: use a variational quantum eigensolver (VQE) to minimize the cost function. VQE constructs a parameterized quantum circuit (ansatz) that prepares candidate solution states, measures the cost function expectation value, and uses classical optimization to adjust ansatz parameters until convergence.

Construct the VQE ansatz for the IK problem. The ansatz should enable exploration of the 18-qubit Hilbert space with sufficient expressiveness to represent diverse joint configurations. A hardware-efficient ansatz consists of layers of single-qubit rotations ($R_y$ and $R_z$ gates) and entangling CNOT gates arranged in a brick pattern. Each layer has 18 rotation parameters (one per qubit) and 17 CNOTs (linear connectivity). Stack 4-6 layers to achieve adequate depth.

Implement forward kinematics evaluation within the cost function computation. Given a bitstring representing discretized joint angles, decode each joint's binary value, map it to a continuous angle via linear interpolation over $[-\pi, \pi]$, construct the DH transformation matrices, multiply them sequentially, and extract the end-effector position and orientation. Use NumPy for matrix operations: define a function `forward_kinematics(joint_angles)` returning a 4x4 homogeneous transformation matrix. Extract position as the first three elements of the fourth column and orientation as Euler angles from the rotation submatrix via `scipy.spatial.transform.Rotation.from_matrix(...).as_euler('xyz')`.

The VQE cost function measures the squared pose error. After circuit execution yields a measurement count dictionary, iterate over bitstrings, decode joint angles, compute forward kinematics, calculate pose error, and weight by measurement probability. The expectation value aggregates errors across sampled configurations: `expectation = sum(counts[bs] / shots * pose_error(decode(bs), target) for bs in counts)`.

Parameter variation analysis begins with ansatz depth sweeps. Implement VQE with ansatz depths $d \in \{2, 4, 6, 8, 10\}$ and fixed classical optimizer (COBYLA with 100 iterations). For each depth, run 10 IK instances with randomly generated target poses within the workspace. Record final expectation value, optimization convergence history, circuit gate count, and solution accuracy (whether the decoded joint angles achieve pose error below threshold $\epsilon = 0.01$ meters for position and $0.05$ radians for orientation). Plot expectation value versus ansatz depth, identifying the depth where diminishing returns set in (typically around $d=6$ for hardware-efficient ansatzes).

Shot count variation reveals the tradeoff between sampling precision and computational cost. Repeat VQE optimization for fixed ansatz depth with shot counts $s \in \{128, 256, 512, 1024, 2048, 4096\}$. Lower shot counts introduce measurement noise, causing expectation value estimates to fluctuate and potentially misleading the classical optimizer. Higher shot counts improve precision but increase execution time linearly. Quantify this tradeoff by plotting optimization wall-clock time and final pose error versus shot count. The empirical sweet spot typically lies around 1024 shots, balancing accuracy and efficiency.

Noise parameter sweeps assess quantum algorithm resilience under hardware imperfections. Construct noise models with varying depolarizing error rates: $p_2 \in \{0.001, 0.005, 0.01, 0.02, 0.05\}$ for two-qubit gates, holding single-qubit errors fixed at $p_1 = p_2 / 10$. For each noise level, execute VQE on the noisy Aer simulator and measure solution degradation. Plot pose error versus gate error rate, identifying the noise threshold beyond which solutions become unreliable (typically around $p_2 = 0.02$ for shallow circuits). Implement error mitigation techniques (zero-noise extrapolation, probabilistic error cancellation) and compare mitigated versus raw results, quantifying the improvement in solution quality.

Classical baseline comparison establishes whether quantum approaches offer advantage. Implement a classical iterative IK solver using the Jacobian pseudoinverse method: initialize joint angles randomly, compute forward kinematics, calculate pose error, linearize via the Jacobian matrix, solve for joint angle increments, and iterate until convergence or iteration limit. Run the classical solver on the same 10 random target poses used in the quantum experiments. Compare success rates (percentage of poses solved within tolerance), average iteration counts, and computation time. For the problem size considered here (6 DOF, 18 qubits), classical methods will outperform quantum due to the noisy intermediate-scale quantum (NISQ) limitations. However, the exercise demonstrates the operational workflow and positions future scaling experiments where quantum advantage may emerge (e.g., 10+ DOF manipulators requiring 30+ qubits).

Statistical significance testing validates observed performance differences. Use paired t-tests to compare pose errors between quantum and classical methods across problem instances. Compute effect sizes (Cohen's d) to quantify practical significance. When noise mitigation is applied, perform ANOVA to test whether mitigation technique, noise level, and their interaction significantly affect solution quality, identifying the most effective mitigation strategy under different noise regimes.

Implement parameter sweeps with automated experiment orchestration. Create a Python script that iterates over parameter combinations, executes VQE, logs results to a CSV file, and generates summary plots. Use the `multiprocessing` library to parallelize independent VQE runs across CPU cores, accelerating the parameter sweep. For each run, log metadata (timestamp, parameter values, random seed) and performance metrics (expectation value, pose error, circuit depth, gate count, wall-clock time). After sweep completion, load the CSV into pandas and generate publication-quality plots with matplotlib or seaborn.

Complete implementation for VQE-based inverse kinematics with parameter sweeps:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.circuit import ParameterVector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from multiprocessing import Pool
import itertools
import time

# Simplified 6-DOF manipulator DH parameters (UR5-like)
DH_PARAMS = [
    {'a': 0.0, 'd': 0.0892, 'alpha': np.pi/2},
    {'a': -0.425, 'd': 0.0, 'alpha': 0},
    {'a': -0.3922, 'd': 0.0, 'alpha': 0},
    {'a': 0.0, 'd': 0.109, 'alpha': np.pi/2},
    {'a': 0.0, 'd': 0.093, 'alpha': -np.pi/2},
    {'a': 0.0, 'd': 0.082, 'alpha': 0}
]

def dh_transform(theta, d, a, alpha):
    """Compute DH transformation matrix."""
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st*ca, st*sa, a*ct],
        [st, ct*ca, -ct*sa, a*st],
        [0, sa, ca, d],
        [0, 0, 0, 1]
    ])

def forward_kinematics# Operational Verification Labs: Quantum Computing

## Objective & Operational Lab Setup

The operational intersection of quantum computing and robotics represents an emerging frontier in computational control systems, optimization algorithms for trajectory planning, and sensor fusion architectures that exploit quantum mechanical phenomena. While fault-tolerant universal quantum computers remain largely confined to laboratory research environments, near-term intermediate-scale quantum (NISQ) devices and quantum-inspired classical algorithms have begun to influence robotics in three critical domains: combinatorial optimization for path planning and task scheduling, quantum-enhanced machine learning for perception pipelines, and hybrid classical-quantum control architectures for multi-agent coordination. This laboratory sequence trains robotics practitioners to operationally verify quantum algorithm prototypes, validate hybrid quantum-classical workflows, and benchmark quantum-inspired heuristics against classical baselines using simulation frameworks and cloud-accessible quantum hardware.

The practitioner must understand that quantum computing in robotics is not a wholesale replacement of classical control theory but rather a specialized computational accelerator for NP-hard optimization problems that plague multi-robot systems at scale. The operational workflow mirrors embedded systems validation: define the problem in a domain-specific language, compile to quantum gate sequences or classical surrogate models, execute on target hardware or high-fidelity simulators, and extract actionable metrics through statistical post-processing. The laboratory environment leverages Qiskit (IBM's open-source quantum development kit), PennyLane (Xanadu's differentiable quantum programming framework), and D-Wave Ocean SDK for quantum annealing, all of which provide Python bindings that integrate seamlessly with ROS2 (Robot Operating System 2) computational graphs and NumPy-based control pipelines.

### Laboratory Environment Configuration

Establish a Python 3.10+ virtual environment with quantum simulation libraries and robotics interoperability tools. The installation sequence ensures compatibility between quantum circuit simulation backends and classical optimization libraries commonly deployed in robotic motion planning stacks. Begin by creating an isolated environment to prevent dependency conflicts with existing ROS2 or PyTorch installations.

```bash
python3.10 -m venv ~/quantum_robotics_lab
source ~/quantum_robotics_lab/bin/activate
pip install --upgrade pip setuptools wheel
pip install qiskit==0.45.0 qiskit-aer==0.13.0 qiskit-ibm-runtime==0.15.0
pip install pennylane==0.33.0 pennylane-qiskit==0.33.0
pip install dwave-ocean-sdk==6.7.0
pip install numpy==1.24.3 scipy==1.11.3 matplotlib==3.8.0
pip install networkx==3.2 python-constraint==1.4.0
```

The Qiskit Aer backend provides local noiseless and noisy quantum circuit simulation with configurable noise models derived from real IBM Quantum hardware calibration data. The `qiskit-ibm-runtime` package enables remote execution on IBM Cloud quantum processors, though all exercises in this laboratory sequence can be completed using local simulation to ensure deterministic reproducibility. PennyLane serves as a hardware-agnostic quantum machine learning framework with automatic differentiation, allowing gradient-based optimization of parameterized quantum circuits (variational quantum algorithms). The D-Wave Ocean SDK targets quantum annealing hardware, a specialized architecture for quadratic unconstrained binary optimization (QUBO) problems that map directly to robotic task assignment and graph partitioning.

Validate the installation by querying available quantum backends and verifying circuit transpilation capabilities. The following diagnostic script confirms that the quantum compiler can decompose arbitrary unitary gates into native gate sets supported by real hardware, a critical prerequisite for operational deployment.

```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import numpy as np

# Initialize noiseless simulator backend
simulator = AerSimulator()

# Construct a trivial Bell state circuit to verify toolchain
qc = QuantumCircuit(2, 2)
qc.h(0)  # Hadamard gate on qubit 0
qc.cx(0, 1)  # CNOT gate with control=0, target=1
qc.measure([0, 1], [0, 1])

# Transpile to simulator's native gate set
compiled_circuit = transpile(qc, simulator)

# Execute and extract measurement statistics
job = simulator.run(compiled_circuit, shots=1024)
result = job.result()
counts = result.get_counts()

print("Bell State Measurement Counts:", counts)
assert len(counts) == 2, "Expected bipartite distribution |00⟩ and |11⟩"
assert abs(counts.get('00', 0) - counts.get('11', 0)) < 100, "Statistical deviation exceeds tolerance"
```

Successful execution produces approximately equal counts for bitstrings `00` and `11`, confirming that the quantum simulator correctly implements entanglement operations. The assertion checks verify that the measurement distribution exhibits the expected correlation structure of a maximally entangled Bell state, where measuring the first qubit instantaneously determines the second qubit's state due to quantum superposition collapse.

### Domain-Specific Problem Formulation: Robotic Task Assignment as QUBO

Quantum annealing and variational quantum eigensolvers (VQE) excel at solving combinatorial optimization problems encoded as quadratic unconstrained binary optimization (QUBO) instances. In robotics, the multi-robot task assignment problem exemplifies this class: given `N` robots and `M` tasks with pairwise costs representing travel distances, collision risks, or energy expenditure, find the binary assignment matrix that minimizes total system cost. This maps directly to the graph partitioning and maximum cut problems that quantum annealers solve natively.

The QUBO formulation encodes decision variables as binary qubits `x_i ∈ {0, 1}` and constructs an objective function `H = Σᵢⱼ Qᵢⱼ xᵢ xⱼ` where the matrix `Q` encapsulates problem structure. For robotics practitioners, the translation procedure converts a task assignment instance into a QUBO matrix through constraint penalization: hard constraints (exactly one robot per task) become large-coefficient quadratic penalty terms, while soft constraints (minimize travel cost) contribute weighted cost terms. The operational verification laboratory focuses on this encoding process and subsequent solution validation rather than quantum hardware operation, as the latter remains largely abstracted by vendor SDKs.

Establish a reference problem instance representing a warehouse scenario with four autonomous mobile robots (AMRs) and four picking tasks spatially distributed across the facility. The cost matrix represents Euclidean distances between robot starting positions and task locations, measured in meters. This small-scale instance allows exhaustive classical enumeration for ground-truth validation while remaining sufficiently complex to demonstrate quantum algorithm behavior.

```python
import numpy as np
from itertools import permutations

# Cost matrix: rows = robots, columns = tasks (Euclidean distances in meters)
cost_matrix = np.array([
    [5.2, 8.1, 3.7, 9.4],  # Robot 0 to Tasks 0-3
    [7.3, 4.8, 6.1, 5.9],  # Robot 1 to Tasks 0-3
    [3.9, 7.2, 8.5, 4.3],  # Robot 2 to Tasks 0-3
    [6.7, 5.4, 4.6, 7.8]   # Robot 3 to Tasks 0-3
])

def classical_exhaustive_search(costs):
    """Brute-force enumeration of all valid assignments."""
    n_robots, n_tasks = costs.shape
    assert n_robots == n_tasks, "Non-square assignment problems require reduction"
    
    best_cost = float('inf')
    best_assignment = None
    
    for perm in permutations(range(n_tasks)):
        total_cost = sum(costs[robot, task] for robot, task in enumerate(perm))
        if total_cost < best_cost:
            best_cost = total_cost
            best_assignment = perm
    
    return best_assignment, best_cost

optimal_assignment, optimal_cost = classical_exhaustive_search(cost_matrix)
print(f"Classical Optimal Assignment: {optimal_assignment}")
print(f"Classical Optimal Cost: {optimal_cost:.2f} meters")
```

The exhaustive search establishes ground truth for the four-robot scenario, typically completing in under one second due to the modest 4! = 24 permutation space. For operationally relevant fleet sizes (N > 10 robots), the factorial growth renders classical enumeration intractable, motivating quantum or quantum-inspired heuristics. The practitioner must internalize that quantum advantage emerges not from solving small toy problems but from asymptotic scaling behavior on instances where classical algorithms exhaust computational budgets.

## Exercise 1: Foundational Practical Implementation

### Quantum Annealing for Task Assignment via D-Wave Ocean SDK

Quantum annealing hardware, exemplified by D-Wave Systems' superconducting flux qubit processors, solves optimization problems by physically encoding the QUBO objective function into qubit coupling strengths and allowing the system to thermally anneal toward the ground state. The operational workflow translates the robotics task assignment problem into a binary quadratic model (BQM), submits it to a simulated annealing solver (or real quantum hardware if cloud credits are available), and decodes the bitstring solution back into robot-task pairings. This exercise builds the complete pipeline from problem definition through solution validation, emphasizing the quantum-classical interface where domain expertise must ensure correct problem encoding.

The D-Wave Ocean SDK uses a graph-based abstraction where qubits correspond to binary decision variables and edges represent quadratic coupling terms. For an N×N task assignment, we construct N² binary variables `x[i][j]` indicating whether robot `i` services task `j`. The QUBO must enforce two constraint classes: each robot assigned exactly one task (row constraints) and each task assigned exactly one robot (column constraints). These equality constraints convert to quadratic penalty terms by expanding `(Σⱼ x[i][j] - 1)²` and collecting coefficients.

Begin by encoding the cost matrix into linear and quadratic QUBO coefficients. The linear terms `h[i]` represent single-qubit biases (cost contributions from individual assignments), while quadratic terms `J[i][j]` represent two-qubit couplings (interaction penalties for constraint violations). The constraint penalty weight `λ` must substantially exceed the maximum cost matrix entry to ensure the annealer prioritizes feasibility over cost optimization.

```python
from dimod import BinaryQuadraticModel
from neal import SimulatedAnnealingSampler
import numpy as np

def task_assignment_to_qubo(cost_matrix, constraint_penalty=100.0):
    """
    Convert task assignment problem to QUBO formulation.
    
    Variables: x[i*N + j] indicates robot i assigned to task j
    Objective: minimize Σᵢⱼ cost[i][j] * x[i][j]
    Constraints: Σⱼ x[i][j] = 1 for all i (each robot gets one task)
                 Σᵢ x[i][j] = 1 for all j (each task gets one robot)
    """
    n_robots, n_tasks = cost_matrix.shape
    assert n_robots == n_tasks, "Require square assignment matrix"
    N = n_robots
    
    # Initialize QUBO dictionary
    Q = {}
    
    # Add cost terms (linear coefficients)
    for i in range(N):
        for j in range(N):
            var = i * N + j
            Q[(var, var)] = cost_matrix[i, j]
    
    # Add row constraint penalties: (Σⱼ x[i][j] - 1)² = Σⱼ x[i][j]² - 2Σⱼ x[i][j] + 1
    # Since x² = x for binary variables, this becomes: Σⱼ x[i][j] + 2Σⱼ<ₖ x[i][j]*x[i][k] - 2Σⱼ x[i][j] + 1
    for i in range(N):
        for j in range(N):
            var = i * N + j
            Q[(var, var)] += constraint_penalty * (-1.0)  # -2 term becomes -1 after simplification
        
        for j in range(N):
            for k in range(j + 1, N):
                var1 = i * N + j
                var2 = i * N + k
                Q[(var1, var2)] = Q.get((var1, var2), 0) + 2 * constraint_penalty
    
    # Add column constraint penalties: (Σᵢ x[i][j] - 1)²
    for j in range(N):
        for i in range(N):
            var = i * N + j
            Q[(var, var)] += constraint_penalty * (-1.0)
        
        for i in range(N):
            for k in range(i + 1, N):
                var1 = i * N + j
                var2 = k * N + j
                Q[(var1, var2)] = Q.get((var1, var2), 0) + 2 * constraint_penalty
    
    return Q

def decode_assignment_solution(sample, n_robots):
    """Extract robot-task assignment from binary solution."""
    assignment = []
    for i in range(n_robots):
        for j in range(n_robots):
            var = i * n_robots + j
            if sample.get(var, 0) == 1:
                assignment.append((i, j))
    return assignment

# Encode the warehouse task assignment problem
qubo_dict = task_assignment_to_qubo(cost_matrix, constraint_penalty=150.0)

# Convert to BinaryQuadraticModel
bqm = BinaryQuadraticModel.from_qubo(qubo_dict)

# Execute on classical simulated annealing solver
sampler = SimulatedAnnealingSampler()
sampleset = sampler.sample(bqm, num_reads=100, num_sweeps=1000)

# Extract best solution
best_sample = sampleset.first.sample
best_energy = sampleset.first.energy

assignment_pairs = decode_assignment_solution(best_sample, n_robots=4)
print(f"\nQuantum Annealing Solution:")
for robot, task in sorted(assignment_pairs):
    print(f"  Robot {robot} → Task {task} (Cost: {cost_matrix[robot, task]:.2f}m)")

quantum_total_cost = sum(cost_matrix[r, t] for r, t in assignment_pairs)
print(f"Quantum Total Cost: {quantum_total_cost:.2f} meters")
print(f"Classical Optimal Cost: {optimal_cost:.2f} meters")
print(f"Optimality Gap: {quantum_total_cost - optimal_cost:.2f} meters")
```

The simulated annealing solver performs thermal Monte Carlo sampling over the QUBO energy landscape, iteratively proposing bit flips and accepting them probabilistically based on energy change. The `num_reads` parameter controls how many independent annealing runs execute, allowing statistical aggregation of solutions since the heuristic is non-deterministic. The `num_sweeps` parameter governs the annealing schedule length—higher values increase runtime but improve solution quality by allowing slower thermal cooling. Operational tuning of these parameters follows the same empirical methodology as PID controller gain scheduling: start with conservative defaults, measure performance metrics, then incrementally adjust based on observed convergence behavior.

The solution validation step decodes the binary variable assignment back into robot-task pairings and computes the total travel cost. For a correctly encoded QUBO with sufficient constraint penalty weight, the solver should always return a feasible assignment (each robot assigned exactly one task, each task assigned exactly one robot). If the decoded solution violates constraints, the practitioner must increase the penalty weight, as this indicates the annealer prioritized cost minimization over feasibility. The optimality gap quantifies solution quality: a gap of zero indicates the quantum solver matched classical exhaustive search, while positive gaps reveal suboptimality inherent to the heuristic nature of annealing.

### Operational Diagnostics and Failure Mode Analysis

The quantum annealing approach introduces several failure modes absent from deterministic classical algorithms. First, insufficient constraint penalties allow the annealer to settle in infeasible regions of solution space where constraint violations reduce total energy more than respecting constraints. Second, shallow annealing schedules (low `num_sweeps`) trap the system in local minima, yielding suboptimal but feasible solutions. Third, the discretization of continuous problem parameters into integer QUBO coefficients introduces quantization errors that accumulate in large-scale instances.

Diagnose constraint violations by computing the residual for each constraint class. For row constraints, verify that each robot's assignment variables sum to exactly one; for column constraints, verify each task receives exactly one robot. Any deviation from unity indicates constraint violation and mandates penalty weight adjustment.

```python
def validate_assignment_constraints(sample, n_robots):
    """Compute constraint violation metrics."""
    row_violations = []
    col_violations = []
    
    for i in range(n_robots):
        row_sum = sum(sample.get(i * n_robots + j, 0) for j in range(n_robots))
        row_violations.append(abs(row_sum - 1))
    
    for j in range(n_robots):
        col_sum = sum(sample.get(i * n_robots + j, 0) for i in range(n_robots))
        col_violations.append(abs(col_sum - 1))
    
    max_row_violation = max(row_violations)
    max_col_violation = max(col_violations)
    
    return max_row_violation, max_col_violation

row_viol, col_viol = validate_assignment_constraints(best_sample, n_robots=4)
print(f"\nConstraint Violation Metrics:")
print(f"  Maximum Row Violation: {row_viol}")
print(f"  Maximum Column Violation: {col_viol}")

if row_viol > 0 or col_viol > 0:
    print("WARNING: Solution violates assignment constraints. Increase penalty weight.")
else:
    print("Solution satisfies all assignment constraints.")
```

Operational best practice dictates running a parameter sweep over constraint penalty weights to empirically determine the minimum value that consistently produces feasible solutions. This sweep emulates the calibration procedures used in embedded control systems, where gains are tuned through systematic experimentation rather than analytical derivation. For the four-robot warehouse scenario, penalty weights in the range [100, 200] typically suffice, but larger instances may require dynamic scaling proportional to problem size.

## Exercise 2: Parameter Variation & Empirical Analysis

### Variational Quantum Eigensolver for Trajectory Optimization

Variational quantum algorithms (VQAs) represent the second major quantum computing paradigm accessible to robotics practitioners. Unlike quantum annealing, which encodes the optimization problem directly into hardware Hamiltonian couplings, VQAs employ parameterized quantum circuits as function approximators and optimize circuit parameters through classical gradient descent. The operational workflow mirrors neural network training: initialize circuit parameters randomly, execute the quantum circuit to measure an objective function (the "energy" of a quantum state), compute gradients with respect to parameters, and update parameters to minimize the objective. In robotics, VQAs apply to trajectory optimization problems where the objective encodes kinematic constraints, obstacle avoidance penalties, and energy minimization.

This exercise implements a simplified trajectory optimization using the Variational Quantum Eigensolver (VQE) to find minimum-energy paths for a planar robotic arm. The quantum circuit encodes joint angle configurations as quantum states, and the Hamiltonian operator represents the system's potential energy landscape including collision penalties and goal-reaching rewards. The practitioner must understand that this approach scales poorly to high-dimensional configuration spaces, making it more pedagogically valuable than operationally deployable, yet it establishes the quantum-classical hybrid workflow pattern now prevalent in near-term quantum applications.

The problem setup considers a two-link planar arm with joint angles `θ₁` and `θ₂` discretized into four configurations each, yielding a 4×4=16 dimensional state space. The Hamiltonian matrix encodes energy costs: low energy for configurations approaching the goal, high energy for self-collision or workspace boundary violations. The VQE searches for the quantum state that minimizes the expectation value of this Hamiltonian, which corresponds to the minimum-energy arm configuration.

```python
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
import numpy as np

def construct_trajectory_hamiltonian(goal_config, obstacle_configs):
    """
    Build Hamiltonian for 2-link arm trajectory optimization.
    
    State space: 4 qubits encode 16 possible joint configurations
    Energy landscape: low near goal, high near obstacles
    """
    n_qubits = 4
    dim = 2**n_qubits
    
    # Initialize energy matrix
    energy_matrix = np.zeros((dim, dim))
    
    # Enumerate all 16 configurations (4 bits = 16 states)
    for state_idx in range(dim):
        # Decode bitstring to joint angles (simplified discrete angles)
        theta1_discrete = (state_idx >> 2) & 0x3  # Upper 2 bits
        theta2_discrete = state_idx & 0x3         # Lower 2 bits
        
        config = (theta1_discrete, theta2_discrete)
        
        # Goal-reaching energy (quadratic penalty from goal)
        goal_distance = abs(config[0] - goal_config[0]) + abs(config[1] - goal_config[1])
        goal_energy = 10.0 * goal_distance**2
        
        # Obstacle avoidance energy
        obstacle_energy = 0.0
        for obs_config in obstacle_configs:
            obs_distance = abs(config[0] - obs_config[0]) + abs(config[1] - obs_config[1])
            if obs_distance < 2:
                obstacle_energy += 50.0 / (obs_distance + 0.1)
        
        # Workspace boundary penalty (favor middle configurations)
        boundary_energy = 5.0 * (abs(config[0] - 1.5)**2 + abs(config[1] - 1.5)**2)
        
        total_energy = goal_energy + obstacle_energy + boundary_energy
        energy_matrix[state_idx, state_idx] = total_energy
    
    return energy_matrix

# Define goal and obstacle configurations in discrete joint space
goal_configuration = (3, 2)  # Target joint angles (discretized)
obstacle_configurations = [(1, 1), (2, 3)]  # Forbidden configurations

hamiltonian_matrix = construct_trajectory_hamiltonian(goal_configuration, obstacle_configurations)

# Convert dense matrix to sparse Pauli operator representation
from qiskit.quantum_info import Operator
hamiltonian_op = SparsePauliOp.from_operator(Operator(hamiltonian_matrix))

# Construct parameterized ansatz circuit (hardware-efficient trial state)
ansatz = TwoLocal(num_qubits=4, rotation_blocks='ry', entanglement_blocks='cx', 
                  entanglement='linear', reps=2)

# Initialize VQE with classical optimizer
optimizer = SLSQP(maxiter=100)
estimator = Estimator()

vqe = VQE(estimator=estimator, ansatz=ansatz, optimizer=optimizer)

# Execute VQE optimization
result = vqe.compute_minimum_eigenvalue(hamiltonian_op)

print(f"\nVQE Trajectory Optimization Results:")
print(f"Minimum Energy Found: {result.eigenvalue.real:.4f}")
print(f"Optimal Parameters: {result.optimal_point}")
print(f"Optimizer Evaluations: {result.cost_function_evals}")

# Decode optimal quantum state to configuration
optimal_state_vector = result.eigenstate
if optimal_state_vector is not None:
    probabilities = np.abs(optimal_state_vector)**2
    most_probable_config = np.argmax(probabilities)
    theta1 = (most_probable_config >> 2) & 0x3
    theta2 = most_probable_config & 0x3
    print(f"Most Probable Configuration: θ₁={theta1}, θ₂={theta2}")
    print(f"Goal Configuration: θ₁={goal_configuration[0]}, θ₂={goal_configuration[1]}")
```

The VQE ansatz circuit, instantiated as a `TwoLocal` hardware-efficient template, consists of alternating layers of single-qubit rotation gates (`RY` gates parameterized by angles) and two-qubit entangling gates (`CX` CNOT gates). The `reps=2` parameter specifies two repetitions of this layer structure, yielding a parameterized quantum circuit with approximately 16 tunable parameters. The classical optimizer, Sequential Least Squares Programming (SLSQP), iteratively adjusts these parameters to minimize the expectation value `⟨ψ(θ)|H|ψ(θ)⟩` where `|ψ(θ)⟩` is the quantum state produced by the ansatz and `H` is the Hamiltonian operator encoding the trajectory optimization objective.

The operational practitioner must recognize that VQE's performance critically depends on ansatz expressibility and entangling structure. Shallow circuits with insufficient entanglement cannot represent complex energy landscapes, while excessively deep circuits suffer from barren plateaus—exponentially vanishing gradients that stall optimization. The `linear` entanglement topology, where qubit `i` entangles only with qubit `i+1`, balances expressibility and gradient propagation for small problems, but larger instances require topology engineering informed by problem structure.

### Parameter Sensitivity Analysis: Ansatz Depth and Optimizer Configuration

Operational validation of quantum algorithms demands systematic parameter sweeps analogous to control system gain tuning. This exercise sweeps ansatz depth (`reps` parameter) and optimizer iteration limits to empirically determine convergence characteristics and solution quality tradeoffs. The practitioner constructs a grid search over parameter space, executes VQE for each configuration, and aggregates convergence metrics to identify robust operating points.

```python
from qiskit_algorithms.optimizers import COBYLA
import pandas as pd

def vqe_parameter_sweep(hamiltonian_op, goal_config, reps_range, maxiter_range):
    """
    Systematic parameter sweep for VQE trajectory optimization.
    
    Returns DataFrame with convergence metrics for each configuration.
    """
    results = []
    
    for reps in reps_range:
        for maxiter in maxiter_range:
            # Construct ansatz with specified depth
            ansatz = TwoLocal(num_qubits=4, rotation_blocks='ry', 
                            entanglement_blocks='cx', entanglement='linear', reps=reps)
            
            # Use COBYLA for comparison (derivative-free optimizer)
            optimizer = COBYLA(maxiter=maxiter)
            estimator = Estimator()
            
            vqe = VQE(estimator=estimator, ansatz=ansatz, optimizer=optimizer)
            result = vqe.compute_minimum_eigenvalue(hamiltonian_op)
            
            # Decode solution
            if result.eigenstate is not None:
                probabilities = np.abs(result.eigenstate)**2
                most_probable_config = np.argmax(probabilities)
                theta1 = (most_probable_config >> 2) & 0x3
                theta2 = most_probable_config & 0x3
                config_error = abs(theta1 - goal_config[0]) + abs(theta2 - goal_config[1])
            else:
                config_error = float('inf')
            
            results.append({
                'ansatz_depth': reps,
                'max_iterations': maxiter,
                'final_energy': result.eigenvalue.real,
                'evaluations': result.cost_function_evals,
                'config_error': config_error
            })
            
            print(f"Completed: depth={reps}, maxiter={maxiter}, energy={result.eigenvalue.real:.4f}")
    
    return pd.DataFrame(results)

# Execute parameter sweep
sweep_results = vqe_parameter_sweep(
    hamiltonian_op,
    goal_configuration,
    reps_range=[1, 2, 3],
    maxiter_range=[50, 100, 150]
)

print("\nParameter Sweep Summary:")
print(sweep_results.to_string(index=False))

# Identify Pareto-optimal configurations (minimize energy and evaluations)
print("\nBest Configuration by Final Energy:")
best_energy_config = sweep_results.loc[sweep_results['final_energy'].idxmin()]
print(best_energy_config)

print("\nBest Configuration by Computational Efficiency (evaluations):")
best_efficiency_config = sweep_results.loc[sweep_results['evaluations'].idxmin()]
print(best_efficiency_config)
```

The parameter sweep reveals empirical tradeoffs between solution quality and computational cost. Deeper ansatz circuits (higher `reps`) increase expressibility, potentially finding lower-energy solutions, but multiply the number of parameters and thus the optimization landscape dimensionality. Classical optimizers like COBYLA (Constrained Optimization BY Linear Approximations) require more function evaluations to navigate high-dimensional parameter spaces, increasing the total quantum circuit execution count. For robotics practitioners operating under real-time constraints, the optimal configuration minimizes the product of solution suboptimality and computational latency rather than either metric in isolation.

The DataFrame output enables filtering for configurations that meet operational requirements. For instance, a real-time motion planning system might impose a hard constraint of fewer than 500 quantum circuit evaluations per trajectory query, requiring selection from the constrained subset of sweep results. This operational methodology directly parallels embedded systems engineering, where algorithm parameters are tuned empirically within hardware resource budgets rather than optimized in isolation.

### Noise Model Integration and Hardware-Realistic Simulation

Near-term quantum hardware suffers from gate errors, decoherence, and measurement noise that degrade computational fidelity. Operational verification must account for these imperfections by simulating quantum algorithms under realistic noise models derived from hardware calibration data. Qiskit provides noise model construction utilities that ingest device specifications and synthesize probabilistic error channels approximating real quantum processor behavior. This exercise augments the VQE trajectory optimization with a noise model emulating IBM Quantum hardware, revealing how algorithmic performance degrades under operational conditions.

```python
from qiskit_aer.noise import NoiseModel
from qiskit_aer.noise import depolarizing_error, thermal_relaxation_error
from qiskit_aer import AerSimulator

def construct_realistic_noise_model():
    """
    Build noise model approximating IBM Quantum hardware characteristics.
    
    Error rates based on typical qubit T1/T2 times and gate fidelities.
    """
    noise_model = NoiseModel()
    
    # Single-qubit gate error: depolarizing channel with 0.1% error rate
    single_qubit_error = depolarizing_error(0.001, 1)
    noise_model.add_all_qubit_quantum_error(single_qubit_error, ['rx', 'ry', 'rz', 'h'])
    
    # Two-qubit gate error: depolarizing channel with 1% error rate (10x worse)
    two_qubit_error = depolarizing_error(0.01, 2)
    noise_model.add_all_qubit_quantum_error(two_qubit_error, ['cx'])
    
    # Measurement error: bit-flip with 2% probability
    measurement_error = depolarizing_error(0.02, 1)
    noise_model.add_all_qubit_quantum_error(measurement_error, ['measure'])
    
    # Thermal relaxation (T1=50μs, T2=70μs, gate_time=100ns)
    t1 = 50e3  # Relaxation time in nanoseconds
    t2 = 70e3  # Dephasing time in nanoseconds
    gate_time = 100  # Gate duration in nanoseconds
    
    relaxation_error = thermal_relaxation_error(t1, t2, gate_time)
    noise_model.add_all_qubit_quantum_error(relaxation_error, ['rx', 'ry', 'rz'])
    
    return noise_model

# Construct noisy simulator backend
noise_model = construct_realistic_noise_model()
noisy_simulator = AerSimulator(noise_model=noise_model)

# Re-run VQE with noisy simulation
ansatz_noisy = TwoLocal(num_qubits=4, rotation_blocks='ry', entanglement_blocks='cx',
                       entanglement='linear', reps=2)
optimizer_noisy = SLSQP(maxiter=100)

# Note: For noisy simulation, must use different primitive approach
from qiskit.primitives import BackendEstimator
noisy_estimator = BackendEstimator(backend=noisy_simulator)

vqe_noisy = VQE(estimator=noisy_estimator, ansatz=ansatz_noisy, optimizer=optimizer_noisy)
result_noisy = vqe_noisy.compute_minimum_eigenvalue(hamiltonian_op)

print(f"\nNoisy VQE Results:")
print(f"Noiseless Minimum Energy: {result.eigenvalue.real:.4f}")
print(f"Noisy Minimum Energy: {result_noisy.eigenvalue.real:.4f}")
print(f"Energy Degradation: {result_noisy.eigenvalue.real - result.eigenvalue.real:.4f}")

# Statistical validation: run multiple noisy trials
noisy_energies = []
for trial in range(10):
    vqe_trial = VQE(estimator=noisy_estimator, ansatz=ansatz_noisy, optimizer=SLSQP(maxiter=100))
    result_trial = vqe_trial.compute_minimum_eigenvalue(hamiltonian_op)
    noisy_energies.append(result_trial.eigenvalue.real)

print(f"\nNoisy Energy Statistics (10 trials):")
print(f"Mean: {np.mean(noisy_energies):.4f}")
print(f"Std Dev: {np.std(noisy_energies):.4f}")
print(f"Range: [{np.min(noisy_energies):.4f}, {np.max(noisy_energies):.4f}]")
```

The noise model incorporates three primary error mechanisms: depolarizing errors that randomly flip quantum states, thermal relaxation that causes qubits to decay toward ground states, and measurement errors that produce incorrect bitstring readouts. The depolarizing channel error rate of 0.1% for single-qubit gates and 1% for two-qubit gates reflects contemporary superconducting qubit hardware performance. The thermal relaxation parameters `T1` (energy relaxation time) and `T2` (dephasing time) govern how quickly quantum information decoheres, with typical values in the 50-100 microsecond range for state-of-the-art transmon qubits.

The noisy simulation results quantify algorithmic robustness: small increases in minimum energy indicate graceful degradation, while large deviations or optimization convergence failures signal sensitivity to hardware imperfections. The statistical validation across multiple trials captures the stochastic nature of noisy quantum computation, where identical circuit executions yield different measurement outcomes due to probabilistic error channels. For operational deployment on real quantum hardware, the practitioner must establish confidence intervals on solution quality by aggregating results from many noisy runs, analogous to Monte Carlo validation in classical stochastic optimization.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Scalability Analysis: Quantum Resource Estimation for Fleet-Scale Robotics

Operational quantum computing systems face severe resource constraints: qubit counts, gate depths, and coherence times limit the size and complexity of tractable problems. This exercise quantifies the quantum resource requirements for scaling the task assignment problem from four robots to operationally relevant fleet sizes of 10, 20, and 50 robots. The analysis reveals the exponential resource growth characteristic of quantum advantage claims and establishes operational boundaries beyond which current and near-term quantum hardware cannot provide solutions.

The resource estimation workflow computes three critical metrics: the number of qubits required to encode the problem, the circuit depth (sequential gate count) needed to implement the algorithm, and the total gate count that determines execution time and accumulated error. For the QUBO-encoded task assignment, qubit count scales as `N²` for `N` robots (since we need one binary variable per robot-task pair), while circuit depth in quantum annealing scales with problem connectivity and annealing schedule length.

```python
def estimate_quantum_resources(n_robots, encoding='qubo'):
    """
    Compute quantum resource requirements for N-robot task assignment.
    
    Returns qubit count, estimated circuit depth, and total gate count.
    """
    if encoding == 'qubo':
        # QUBO encoding: N² variables for N×N assignment
        n_qubits = n_robots ** 2
        
        # D-Wave quantum annealer: depth determined by annealing schedule (typically 20μs)
        # For gate-based quantum computers, depth scales with problem connectivity
        estimated_depth = 10 * n_robots  # Heuristic: linear in problem size
        
        # Gate count for variational ansatz: O(qubits × depth × layers)
        ansatz_layers = 3
        gates_per_layer = n_qubits * 2  # Single-qubit rotations + entangling gates
        total_gate_count = estimated_depth * gates_per_layer * ansatz_layers
        
    elif encoding == 'binary_tree':
        # Logarithmic encoding: log₂(N) qubits per robot
        qubits_per_entity = int(np.ceil(np.log2(n_robots)))
        n_qubits = 2 * n_robots * qubits_per_entity
        
        estimated_depth = 20 * qubits_per_entity
        total_gate_count = n_qubits * estimated_depth * 3
    
    else:
        raise ValueError(f"Unknown encoding: {encoding}")
    
    # Estimate execution time on hardware (assuming 100ns gate time)
    gate_time_ns = 100
    execution_time_us = (total_gate_count * gate_time_ns) / 1000
    
    return {
        'n_robots': n_robots,
        'n_qubits': n_qubits,
        'circuit_depth': estimated_depth,
        'total_gates': total_gate_count,
        'execution_time_us': execution_time_us
    }

# Compute resource requirements for increasing fleet sizes
fleet_sizes = [4, 10, 20, 50, 100]
resource_estimates = [estimate_quantum_resources(n) for n in fleet_sizes]

print("Quantum Resource Scaling Analysis:")
print("-" * 80)
for est in resource_estimates:
    print(f"Fleet Size: {est['n_robots']:3d} robots")
    print(f"  Qubits Required: {est['n_qubits']:6d}")
    print(f"  Circuit Depth: {est['circuit_depth']:6d}")
    print(f"  Total Gates: {est['total_gates']:10d}")
    print(f"  Execution Time: {est['execution_time_us']:8.2f} μs")
    print()

# Compare against current hardware capabilities
print("Hardware Capability Boundaries:")
print(f"IBM Quantum Eagle (2023): 127 qubits, ~1000 gate depth budget")
print(f"  Maximum Tractable Fleet Size: ~11 robots (121 qubits)")
print()
print(f"D-Wave Advantage (2024): 5000+ qubits (annealing), limited connectivity")
print(f"  Maximum Tractable Fleet Size: ~70 robots (4900 qubits, sparse connectivity)")
print()
print(f"Error-Corrected Quantum Computer (projected 2030s): 1000+ logical qubits")
print(f"  Maximum Tractable Fleet Size: ~31 robots (961 qubits)")
```

The resource scaling analysis exposes the fundamental bottleneck: qubit count grows quadratically with fleet size, rapidly exhausting available quantum hardware. IBM's latest superconducting quantum processors approach 1000 physical qubits, but without error correction, these systems tolerate only shallow circuits of a few hundred gates before accumulated noise overwhelms signal. The coherence time constraint—how long qubits maintain quantum information before decoherence—imposes a strict deadline on circuit execution, typically in the range of 100 microseconds for current hardware. Deep circuits that exceed this window produce garbage outputs.

The practitioner must internalize that quantum advantage for robotics problems remains conditional on three converging trends: qubit count growth through improved fabrication, gate fidelity improvements via error mitigation, and algorithmic innovation reducing circuit depth requirements. For operational deployment in 2025, hybrid quantum-classical algorithms that offload subproblems to quantum processors while classical systems handle coordination and high-level planning represent the pragmatic approach.

### Failure Mode Injection: Constraint Violation and Infeasibility Handling

Robust operational systems must gracefully handle failure modes including constraint violations, infeasible problem instances, and solution quality degradation under noise. This exercise deliberately injects pathological problem instances into the quantum task assignment pipeline and implements recovery protocols that detect failures and fallback to classical solvers when quantum methods fail to converge. The methodology mirrors fault-tolerant embedded systems design, where runtime monitors detect anomalies and trigger failsafe procedures.

Construct a stress-test scenario with conflicting constraints: a robot-task assignment where certain robots cannot service certain tasks (hard exclusions due to payload capacity or reachability constraints), and task priorities create soft preferences. The QUBO encoding must incorporate these additional constraints, increasing the penalty term complexity and potentially rendering the problem over-constrained if exclusions eliminate all feasible solutions.

```python
def task_assignment_with_exclusions(cost_matrix, exclusions, constraint_penalty=150.0):
    """
    Encode task assignment with hard exclusion constraints.
    
    exclusions: list of (robot_idx, task_idx) tuples representing forbidden pairings
    """
    n_robots, n_tasks = cost_matrix.shape
    N = n_robots
    
    Q = {}
    
    # Add cost terms
    for i in range(N):
        for j in range(N):
            if (i, j) not in exclusions:
                var = i * N + j
                Q[(var, var)] = cost_matrix[i, j]
            else:
                # Exclusion: add massive penalty to prevent this pairing
                var = i * N + j
                Q[(var, var)] = 1e6
    
    # Add row/column constraint penalties (same as before)
    for i in range(N):
        for j in range(N):
            var = i * N + j
            Q[(var, var)] = Q.get((var, var), 0) + constraint_penalty * (-1.0)
        for j in range(N):
            for k in range(j + 1, N):
                var1 = i * N + j
                var2 = i * N + k
                Q[(var1, var2)] = Q.get((var1, var2), 0) + 2 * constraint_penalty
    
    for j in range(N):
        for i in range(N):
            var = i * N + j
            Q[(var, var)] = Q.get((var, var), 0) + constraint_penalty * (-1.0)
        for i in range(N):
            for k in range(i + 1, N):
                var1 = i * N + j
                var2 = k * N + j
                Q[(var1, var2)] = Q.get((var1, var2), 0) + 2 * constraint_penalty
    
    return Q

# Stress test: exclude multiple robot-task pairings
stress_exclusions = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)]  # Heavy exclusions

qubo_stress = task_assignment_with_exclusions(cost_matrix, stress_exclusions, constraint_penalty=200.0)
bqm_stress = BinaryQuadraticModel.from_qubo(qubo_stress)

# Attempt solution with quantum annealer
sampler_stress = SimulatedAnnealingSampler()
sampleset_stress = sampler_stress.sample(bqm_stress, num_reads=200, num_sweeps=2000)

best_sample_stress = sampleset_stress.first.sample
assignment_stress = decode_assignment_solution(best_sample_stress, n_robots=4)

# Validate constraints
row_viol_stress, col_viol_stress = validate_assignment_constraints(best_sample_stress, n_robots=4)

print("Stress Test Results (Heavy Exclusions):")
print(f"Constraint Violations: Row={row_viol_stress}, Col={col_viol_stress}")

# Check exclusion violations
exclusion_violations = sum(1 for r, t in assignment_stress if (r, t) in stress_exclusions)
print(f"Exclusion Violations: {exclusion_violations}")

if row_viol_stress > 0 or col_viol_stress > 0 or exclusion_violations > 0:
    print("FAILURE: Quantum solver returned infeasible solution.")
    print("Triggering classical fallback...")
    
    # Classical fallback: constraint satisfaction + greedy assignment
    from python_constraint import Problem, AllDifferentConstraint
    
    problem = Problem()
    for robot in range(4):
        available_tasks = [t for t in range(4) if (robot, t) not in stress_exclusions]
        problem.addVariable(f"robot_{robot}", available_tasks)
    
    problem.addConstraint(AllDifferentConstraint())
    
    solutions = problem.getSolutions()
    if solutions:
        # Select solution minimizing total cost
        best_classical_solution = min(
            solutions,
            key=lambda sol: sum(cost_matrix[r, sol[f"robot_{r}"]] for r in range(4))
        )
        
        classical_assignment = [(r, best_classical_solution[f"robot_{r}"]) for r in range(4)]
        classical_cost = sum(cost_matrix[r, t] for r, t in classical_assignment)
        
        print(f"\nClassical Fallback Solution:")
        for r, t in sorted(classical_assignment):
            print(f"  Robot {r} → Task {t} (Cost: {cost_matrix[r, t]:.2f}m)")
        print(f"Classical Total Cost: {classical_cost:.2f} meters")
    else:
        print("CRITICAL: Problem is over-constrained. No feasible solution exists.")
else:
    print("SUCCESS: Quantum solver returned feasible solution despite exclusions.")
```

The stress test deliberately over-constrains the problem by excluding six out of sixteen possible robot-task pairings, pushing the annealer toward infeasible regions of solution space. The validation logic checks both assignment constraints (each robot assigned exactly one task) and exclusion constraints (no forbidden pairings selected). If the quantum solver fails—indicated by nonzero constraint violations—the system triggers a classical fallback using constraint satisfaction programming (CSP). The `python-constraint` library exhaustively enumerates all valid assignments respecting exclusions and selects the minimum-cost feasible solution.

This hybrid quantum-classical architecture with runtime fallback mirrors fault-tolerant control systems in safety-critical robotics applications. The quantum solver serves as a speculative accelerator: when it succeeds, it potentially outperforms classical methods, but when it fails, the classical solver guarantees correctness at the cost of higher latency. The operational practitioner must instrument both pathways with telemetry to measure quantum solver success rates and inform adaptive algorithm selection policies.

### Boundary Case Analysis: Zero-Cost Assignments and Degenerate Solutions

Operational robustness requires testing boundary cases where problem structure induces degenerate solution spaces—multiple optimal solutions with identical costs. For task assignment, consider a symmetric cost matrix where all entries are equal, yielding `N!` optimal solutions (any permutation achieves the same total cost). Quantum optimization algorithms, which inherently sample from solution distributions, should ideally produce uniform probability over all optima, but biases in ansatz initialization or annealing schedules may favor certain solutions. This exercise quantifies solution distribution bias and validates that the quantum solver explores the full optimal subspace.

```python
def generate_symmetric_cost_matrix(n_robots, base_cost=5.0):
    """Generate cost matrix with uniform entries (degenerate optimum)."""
    return np.full((n_robots, n_robots), base_cost)

symmetric_costs = generate_symmetric_cost_matrix(4, base_cost=6.0)

# Encode and solve with quantum annealer
qubo_symmetric = task_assignment_to_qubo(symmetric_costs, constraint_penalty=150.0)
bqm_symmetric = BinaryQuadraticModel.from_qubo(qubo_symmetric)

sampler_symmetric = SimulatedAnnealingSampler()
sampleset_symmetric = sampler_symmetric.sample(bqm_symmetric, num_reads=1000, num_sweeps=1000)

# Collect all feasible solutions
feasible_solutions = []
for sample in sampleset_symmetric.samples():
    assignment = decode_assignment_solution(sample, n_robots=4)
    row_v, col_v = validate_assignment_constraints(sample, n_robots=4)
    
    if row_v == 0 and col_v == 0 and len(assignment) == 4:
        # Encode as tuple for hashing
        assignment_tuple = tuple(sorted(assignment))
        feasible_solutions.append(assignment_tuple)

# Count unique solutions and their frequencies
from collections import Counter
solution_counts = Counter(feasible_solutions)

print("Symmetric Cost Matrix (Degenerate Optimum):")
print(f"Total Samples: {len(sampleset_symmetric)}")
print(f"Feasible Samples: {len(feasible_solutions)}")
print(f"Unique Feasible Solutions: {len(solution_counts)}")
print(f"Expected Unique Solutions (4! permutations): 24")
print()

print("Solution Distribution (Top 10):")
for solution, count in solution_counts.most_common(10):
    probability = count / len(feasible_solutions)
    print(f"  {solution}: {count} occurrences ({probability:.2%})")

# Compute distribution entropy to quantify uniformity
probabilities = np.array([count / len(feasible_solutions) for count in solution_counts.values()])
entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
max_entropy = np.log2(len(solution_counts))

print(f"\nDistribution Entropy: {entropy:.4f} bits")
print(f"Maximum Entropy (uniform): {max_entropy:.4f} bits")
print(f"Uniformity Ratio: {entropy / max_entropy:.2%}")
```

The entropy metric quantifies solution distribution uniformity: maximum entropy occurs when all feasible solutions appear with equal probability, indicating unbiased sampling, while low entropy indicates the sampler concentrates on a small subset of optima. For symmetric cost matrices, an ideal quantum optimizer should approach maximum entropy, demonstrating thorough exploration of the degenerate solution space. Deviation from uniformity reveals algorithmic bias, which may advantage or disadvantage certain operational scenarios.

In practice, robotic task assignment often exhibits near-degeneracy where multiple solutions have similar costs differing by negligible amounts. The quantum solver's ability to sample diverse near-optimal solutions provides operational flexibility: the robotics system can select from multiple equivalent plans based on secondary criteria not encoded in the cost function, such as robot battery state, communication link quality, or human operator preferences. This capability distinguishes quantum optimization from deterministic classical solvers that return a single arbitrary optimum.

## Operational Reference Guide & Diagnostic Checklist

### Quantum Algorithm Selection Decision Tree

The operational practitioner must select appropriate quantum computing approaches based on problem characteristics, hardware availability, and latency constraints. This decision tree codifies the selection logic validated through laboratory exercises.

**Problem Type: Combinatorial Optimization (Task Assignment, Path Planning, Scheduling)**
- Problem Size: N < 100 variables → Use quantum annealing (D-Wave) or simulated annealing
- Problem Size: N ≥ 100 variables → Classical integer programming or heuristic solvers (quantum overhead exceeds benefit)
- Constraint Complexity: Few constraints → QUBO encoding viable
- Constraint Complexity: Many interdependent constraints → Classical CSP or SAT solvers

**Problem Type: Continuous Optimization (Trajectory Optimization, Control Policy Search)**
- Dimensionality: D < 10 degrees of freedom → VQE with hardware-efficient ansatz
- Dimensionality: D ≥ 10 degrees of freedom → Classical gradient descent or evolutionary algorithms
- Gradient Availability: Analytical gradients available → Classical adjoint methods
- Gradient Availability: Black-box objective → Consider VQE with parameter-shift gradients

**Hardware Constraints:**
- Qubit Count: Available qubits < Required qubits → Problem decomposition or classical solver
- Coherence Time: Circuit depth × Gate time > T2 → Reduce circuit depth or use error mitigation
- Connectivity: Problem graph matches hardware topology → Direct embedding
- Connectivity: Sparse qubit connectivity → Use graph minor embedding (adds overhead)

### Diagnostic Checklist for Quantum Algorithm Failures

**Symptom: Solution violates problem constraints**
- Diagnosis: Insufficient constraint penalty weight in QUBO encoding
- Remedy: Increase penalty by factor of 2-10× and rerun
- Validation: Verify all constraint residuals equal zero

**Symptom: Optimization does not converge (VQE stuck at high energy)**
- Diagnosis: Ansatz expressibility insufficient or barren plateau encountered
- Remedy: Increase ansatz depth (more `reps`) or switch to problem-inspired ansatz
- Validation: Plot energy vs. iteration; expect monotonic decrease

**Symptom: High variability in repeated runs (large solution standard deviation)**
- Diagnosis: Shallow annealing schedule or insufficient sampling
- Remedy: Increase `num_sweeps` (annealing) or `num_reads` (sampling) by 10×
- Validation: Compute coefficient of variation; target < 0.1 for operational stability

**Symptom: Classical solver outperforms quantum solver**
- Diagnosis: Problem size below quantum advantage threshold
- Remedy: Reserve quantum methods for N > 50 variables or accept classical solution
- Validation: Profile runtimes; quantum overhead justified only if classical intractable

**Symptom: Noisy simulation produces garbage outputs**
- Diagnosis: Circuit depth exceeds coherence time under realistic noise
- Remedy: Apply error mitigation (zero-noise extrapolation) or reduce circuit depth
- Validation: Compare noiseless vs. noisy energy; deviation should be < 20%

### Quantum Resource Budget Calculator

Estimate computational costs before executing quantum algorithms on cloud hardware, where billing is per-shot (circuit execution). The following formula computes the total quantum processing unit (QPU) time required for a complete optimization run.

```
Total QPU Time = (Circuit Depth × Gate Time) × Shots × Optimization Iterations

For VQE trajectory optimization (Exercise 2):
  Circuit Depth: ~50 gates
  Gate Time: 100 ns
  Shots per evaluation: 1024
  Optimization Iterations: 100
  Total QPU Time: 50 × 100e-9 × 1024 × 100 = 0.512 seconds

For quantum annealing task assignment (Exercise 1):
  Annealing Time: 20 μs (fixed by hardware)
  Samples: 1000
  Total QPU Time: 20e-6 × 1000 = 0.020 seconds
```

IBM Quantum public access systems impose monthly QPU time quotas (typically 10 minutes for free tier). Operational workflows must batch problem instances and cache solutions to remain within allocation limits. For production deployment, reserved hardware access or on-premise quantum computers eliminate queuing latency but require capital investment exceeding $10M for current-generation systems.

### Hybrid Quantum-Classical Workflow Template

Operational integration of quantum algorithms into robotic systems requires structured interfaces between quantum circuit execution and classical control loops. The following Python class template encapsulates this pattern, providing a unified API for quantum solvers with built-in fallback logic.

```python
class HybridQuantumTaskAssigner:
    """Production-grade task assignment with quantum acceleration and classical fallback."""
    
    def __init__(self, cost_matrix, quantum_backend='simulator', fallback_enabled=True):
        self.cost_matrix = cost_matrix
        self.n_robots = cost_matrix.shape[0]
        self.quantum_backend = quantum_backend
        self.fallback_enabled = fallback_enabled
        
        # Performance telemetry
        self.quantum_attempts = 0
        self.quantum_successes = 0
        self.fallback_invocations = 0
    
    def solve(self, exclusions=None, timeout_ms=5000):
        """Execute hybrid quantum-classical task assignment."""
        self.quantum_attempts += 1
        
        try:
            # Attempt quantum solution
            assignment = self._quantum_solve(exclusions, timeout_ms)
            
            # Validate feasibility
            if self._is_feasible(assignment, exclusions):
                self.quantum_successes += 1
                return assignment, 'quantum'
            else:
                raise ValueError("Quantum solution infeasible")
        
        except Exception as e:
            if self.fallback_enabled:
                self.fallback_invocations += 1
                assignment = self._classical_fallback(exclusions)
                return assignment, 'classical'
            else:
                raise e
    
    def _quantum_solve(self, exclusions, timeout_ms):
        """Quantum annealing implementation."""
        qubo = task_assignment_with_exclusions(
            self.cost_matrix, 
            exclusions or [], 
            constraint_penalty=200.0
        )
        bqm = BinaryQuadraticModel.from_qubo(qubo)
        sampler = SimulatedAnnealingSampler()
        sampleset = sampler.sample(bqm, num_reads=100, num_sweeps=1000)
        
        return decode_assignment_solution(sampleset.first.sample, self.n_robots)
    
    def _classical_fallback(self, exclusions):
        """Classical CSP solver."""
        from python_constraint import Problem, AllDifferentConstraint
        problem = Problem()
        
        for robot in range(self.n_robots):
            available = [t for t in range(self.n_robots) 
                        if not exclusions or (robot, t) not in exclusions]
            problem.addVariable(f"r{robot}", available)
        
        problem.addConstraint(AllDifferentConstraint())
        solutions = problem.getSolutions()
        
        best = min(solutions, 
                  key=lambda s: sum(self.cost_matrix[r, s[f"r{r}"]] 
                                   for r in range(self.n_robots)))
        
        return [(r, best[f"r{r}"]) for r in range(self.n_robots)]
    
    def _is_feasible(self, assignment, exclusions):
        """Validate assignment feasibility."""
        if len(assignment) != self.n_robots:
            return False
        
        robots = set(r for r, t in assignment)
        tasks = set(t for r, t in assignment)
        
        if len(robots) != self.n_robots or len(tasks) != self.n_robots:
            return False
        
        if exclusions:
            if any((r, t) in exclusions for r, t in assignment):
                return False
        
        return True
    
    def get_telemetry(self):
        """Return performance statistics."""
        success_rate = self.quantum_successes / self.quantum_attempts if self.quantum_attempts > 0 else 0
        return {
            'quantum_attempts': self.quantum_attempts,
            'quantum_successes': self.quantum_successes,
            'quantum_success_rate': success_rate,
            'fallback_invocations': self.fallback_invocations
        }

# Operational usage example
assigner = HybridQuantumTaskAssigner(cost_matrix, quantum_backend='simulator')

assignment, solver_type = assigner.solve(exclusions=[(0, 0), (1, 1)])
print(f"Solution obtained via {solver_type} solver:")
for robot, task in sorted(assignment):
    print(f"  Robot {robot} → Task {task}")

telemetry = assigner.get_telemetry()
print(f"\nSystem Telemetry: {telemetry}")
```

This operational template embeds quantum computing within a fault-tolerant control architecture, isolating quantum execution behind a well-defined interface with timeout handling, validation checks, and performance monitoring. The telemetry system tracks quantum solver reliability, enabling adaptive policies that progressively shift from quantum to classical methods as success rates decline under operational stress. This design philosophy—quantum acceleration as a best-effort optimization layer with guaranteed classical fallback—represents the pragmatic path to deploying quantum computing in production robotic systems given current hardware limitations.
