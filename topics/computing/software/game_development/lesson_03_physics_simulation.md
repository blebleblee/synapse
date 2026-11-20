# Lesson 3: Physics Simulation

## 1. First-Principles Intuition & Invariants

At its foundation, a physics simulation engine mediates the temporal evolution of a collection of rigid bodies through discrete time steps, transforming continuous differential equations into numerically stable iterative approximations that preserve invariant properties under the constraints of finite-precision arithmetic and bounded computational budgets. Unlike analytical solutions to classical mechanics problems—which yield exact trajectories through phase space—game physics operates in a regime where accuracy trades against determinism, performance, and perceptual plausibility. The simulation must answer a deceptively simple question at each tick: given the current configuration of positions, orientations, velocities, and external forces, what will the world state become in the next frame?

The rigid body abstraction simplifies reality by treating objects as non-deformable masses with fixed internal geometry. This assumption collapses six degrees of freedom per body in three-dimensional space: three translational coordinates describing the center of mass and three rotational coordinates parameterizing orientation. Each body carries linear momentum $\mathbf{p} = m\mathbf{v}$ and angular momentum $\mathbf{L} = I\boldsymbol{\omega}$, where $I$ represents the inertia tensor—a symmetric positive-definite matrix encoding how mass distributes about the body's principal axes. The inertia tensor transforms under rotation, necessitating careful bookkeeping as bodies spin through space. For a body with orientation quaternion $\mathbf{q}$ and local-space inertia tensor $I_{\text{local}}$, the world-space tensor becomes $I_{\text{world}} = R(\mathbf{q}) \, I_{\text{local}} \, R(\mathbf{q})^T$, where $R(\mathbf{q})$ denotes the rotation matrix derived from the quaternion.

Newton's second law governs translational dynamics: $\mathbf{F} = m\mathbf{a} = \frac{d\mathbf{p}}{dt}$. Euler's equations govern rotational dynamics: $\boldsymbol{\tau} = I\boldsymbol{\alpha} + \boldsymbol{\omega} \times (I\boldsymbol{\omega})$, where the cross-product term captures gyroscopic effects arising from angular momentum precession. These coupled ordinary differential equations admit straightforward integration when forces and torques remain constant over small time intervals. The challenge emerges when bodies interact through contact forces, joint constraints, and collision impulses—phenomena that introduce discontinuities, stiffness, and ill-conditioned linear systems into the temporal integration process.

Collision detection decomposes into two conceptually distinct phases that exploit different algorithmic trade-offs. The broad phase culls the quadratic space of potential body pairs $(N^2 / 2)$ down to a small candidate set likely to intersect, leveraging spatial coherence through bounding volume hierarchies, spatial hashing, or sweep-and-prune algorithms that track axis-aligned interval overlaps. The narrow phase then computes exact contact manifolds between candidate pairs using geometric algorithms that extract penetration depth, contact normals, and support points from underlying shape representations—convex hulls, triangle meshes, implicit surfaces, or analytic primitives like spheres, capsules, and boxes.

The simulation timestep introduces a fundamental tension between stability and responsiveness. Explicit integrators like forward Euler or Runge-Kutta advance state variables using current-frame derivatives, yielding simple, parallelizable update rules that spiral into instability when constraint forces spike or time steps grow too large. Implicit methods like backward Euler embed future-state derivatives into the integration equations, producing unconditionally stable schemes at the cost of solving nonlinear systems per timestep. Game engines typically employ semi-implicit or symplectic integrators—variants that preserve energy invariants over long simulations by carefully ordering velocity and position updates. The velocity Verlet scheme, for instance, updates velocity at the midpoint between position evaluations, damping numerical drift that would otherwise accumulate under naive integration.

Constraint solving represents the algorithmic heart of physical realism. Contacts, joints, motors, and springs all express themselves as equality or inequality constraints on position and velocity variables. At each timestep, the solver must find impulse magnitudes that enforce these constraints without violating momentum conservation or introducing energy artifacts. Iterative methods like Sequential Impulses or Projected Gauss-Seidel decompose the global constraint problem into per-constraint subproblems, repeatedly sweeping through the constraint graph and applying corrective impulses until the system converges to a feasible configuration. Each iteration adjusts body velocities and angular velocities to satisfy one constraint, accepting that this adjustment may temporarily violate others—yet empirical evidence demonstrates rapid convergence for typical contact stacks and joint assemblies.

Determinism emerges as a nonnegotiable requirement for networked multiplayer games and replay systems. Floating-point arithmetic obeys associative and commutative laws only approximately, meaning that summation order, compiler optimizations, and SIMD instruction scheduling all introduce divergence between nominally identical computations. Achieving deterministic physics demands fixed-point arithmetic, carefully controlled evaluation order, disabled speculative execution of floating-point paths, and reproducible transcendental function implementations. Many professional engines run physics on a separate fixed-rate tick independent of rendering frame rate, decoupling simulation fidelity from display refresh variability and enabling deterministic integration across heterogeneous client hardware.

## 2. Core Architecture & Mechanics

The physics engine organizes itself around a **world** object that aggregates rigid bodies, collision shapes, constraints, and persistent contact state. Each rigid body encapsulates mass properties, kinematic variables (position, orientation, linear velocity, angular velocity), and pointers to attached collision geometry. The collision geometry itself decouples from the body, allowing multiple bodies to share immutable shape definitions—a memory optimization that proves essential when thousands of identical crates or bullets populate the scene.

```text
World
├── RigidBody[] bodies
│   ├── Transform { position: vec3, orientation: quat }
│   ├── Velocity { linear: vec3, angular: vec3 }
│   ├── MassProperties { mass: f32, inv_mass: f32, inertia_local: mat3, inv_inertia_local: mat3 }
│   ├── CollisionShape* shapes[]
│   └── UserData* user_ptr
├── BroadPhase
│   ├── AABB[] bounds_cache
│   ├── SpatialHash or BVH or SweepAndPrune
│   └── CollisionPair[] candidates
├── NarrowPhase
│   ├── ContactManifold[] manifolds
│   └── ShapeDispatch table[ShapeType, ShapeType]
├── ConstraintSolver
│   ├── ContactConstraint[] contact_constraints
│   ├── JointConstraint[] joint_constraints
│   └── IterationCount, WarmStartingBuffer
└── IntegrationContext
    ├── dt: f32
    ├── gravity: vec3
    └── substep_count: u32
```

The timestep begins with external force accumulation. User scripts apply forces and torques to bodies—gravity, wind, thruster impulses, magnetic fields. These forces integrate into velocity changes through $\Delta \mathbf{v} = \frac{\mathbf{F}}{m} \Delta t$ and $\Delta \boldsymbol{\omega} = I^{-1}(\boldsymbol{\tau} - \boldsymbol{\omega} \times (I\boldsymbol{\omega})) \Delta t$. Careful implementations compute the world-space inverse inertia tensor $I_{\text{world}}^{-1}$ once per body per frame, caching the result to avoid redundant matrix multiplications during constraint solving.

Broad-phase collision detection updates bounding volumes and queries the spatial acceleration structure for overlapping pairs. A common implementation employs a grid-based spatial hash where each body's axis-aligned bounding box (AABB) hashes into one or more grid cells. The hash function $h(x, y, z) = ((x \cdot p_1) \oplus (y \cdot p_2) \oplus (z \cdot p_3)) \mod N$ distributes cells uniformly when the prime constants $p_1, p_2, p_3$ are chosen appropriately. Bodies that hash into the same cell become candidates for narrow-phase testing. An alternative sweep-and-prune algorithm sorts AABB endpoints along a single axis, maintaining active interval sets and detecting overlaps when intervals open and close. This approach leverages temporal coherence: if the active set changes little between frames, sorting nearly-sorted arrays completes in linear time.

Narrow-phase algorithms dispatch to specialized routines based on shape-pair types. Sphere-sphere collision reduces to a single distance check; if the centers lie closer than the sum of radii, penetration depth equals radius sum minus center distance, and the contact normal points along the center-to-center vector. Sphere-box tests project the sphere center onto the box's closest surface point, then measure distance from that point back to the center. Convex polyhedra employ the Separating Axis Theorem (SAT): two convex shapes fail to intersect if and only if a separating plane exists. Candidate axes include face normals from both shapes and cross products of edge pairs. For each axis, we project both shapes onto the axis and check for interval overlap. If any axis yields separated intervals, the shapes do not collide. When all axes show overlap, the axis with minimum penetration defines the contact normal, and Sutherland-Hodgman clipping extracts the contact manifold—the set of points where the shapes touch.

Triangle mesh collisions present special challenges due to non-convexity and high geometric complexity. A hierarchical bounding volume tree decomposes the mesh into a binary tree of AABBs, with leaf nodes holding small triangle clusters. Collision queries traverse the tree recursively, pruning branches when their bounding volumes do not intersect the query shape. Leaf-level triangle tests proceed via edge-edge separating axes and point-in-triangle barycentric coordinate checks. To prevent tunneling—where fast-moving objects pass through thin geometry—continuous collision detection (CCD) sweeps shapes along their velocity vectors, solving for the time-of-impact by root-finding on the separating distance function.

The constraint solver receives contact manifolds and joint definitions, constructing a system of linear complementarity problems (LCP) or quadratic programming constraints. A contact constraint enforces non-penetration ($\mathbf{n} \cdot (\mathbf{x}_A - \mathbf{x}_B) \geq 0$) and Coulomb friction ($|\mathbf{f}_t| \leq \mu |\mathbf{f}_n|$), where $\mathbf{n}$ denotes the contact normal, $\mathbf{f}_n$ the normal force, $\mathbf{f}_t$ the tangential friction force, and $\mu$ the friction coefficient. The Sequential Impulse method linearizes these constraints in velocity space, computing impulse magnitudes that satisfy each constraint while preserving momentum. For a contact between bodies A and B at world-space point $\mathbf{p}$, the relative velocity at the contact is:

$$
\mathbf{v}_{\text{rel}} = (\mathbf{v}_A + \boldsymbol{\omega}_A \times (\mathbf{p} - \mathbf{x}_A)) - (\mathbf{v}_B + \boldsymbol{\omega}_B \times (\mathbf{p} - \mathbf{x}_B))
$$

The contact constraint requires $\mathbf{v}_{\text{rel}} \cdot \mathbf{n} \geq 0$ for non-penetration. If the constraint is violated, we compute an impulse $\lambda$ along $\mathbf{n}$ that zeroes the normal velocity component. Applying this impulse updates velocities via:

$$
\mathbf{v}_A \leftarrow \mathbf{v}_A + \frac{\lambda \mathbf{n}}{m_A}, \quad \boldsymbol{\omega}_A \leftarrow \boldsymbol{\omega}_A + I_A^{-1}((\mathbf{p} - \mathbf{x}_A) \times (\lambda \mathbf{n}))
$$

and symmetrically for body B with negated impulse direction. Friction constraints decompose into two orthogonal tangent directions, each clamped to the friction cone defined by the normal impulse magnitude.

Joints—hinges, sliders, ball-and-socket, motors—express themselves as equality constraints on relative positions and orientations. A ball-and-socket joint constrains two anchor points to coincide: $\mathbf{x}_A + R_A \mathbf{r}_A = \mathbf{x}_B + R_B \mathbf{r}_B$, where $\mathbf{r}_A$ and $\mathbf{r}_B$ denote anchor positions in each body's local frame. Differentiating this constraint yields a velocity-level equation that the solver must satisfy. Motors add a target velocity or angular velocity to the constraint, driving the joint toward a desired configuration.

The solver iterates through constraints multiple times per timestep—typically five to ten iterations for interactive games, trading perfect convergence for bounded latency. Warm-starting accelerates convergence by initializing each frame's impulse magnitudes with the solution from the previous frame, exploiting temporal coherence. This technique reduces iteration counts by 50% or more in practice.

Position-based dynamics (PBD) offers an alternative formulation that directly corrects positions rather than integrating impulses into velocities. PBD iteratively projects bodies out of penetration by moving them along the contact normal proportional to their inverse masses. This approach guarantees collision-free states and remains stable under large time steps, though it exhibits less physical accuracy than impulse-based solvers because it does not explicitly conserve momentum.

Numerical integration closes the simulation loop, advancing positions and orientations based on updated velocities. Semi-implicit Euler integrates velocity first, then uses the new velocity to update position:

```c
// Semi-implicit Euler integration
void integrate_body(RigidBody* body, f32 dt) {
    // Apply accumulated forces and torques to velocities
    body->linear_velocity += body->force * body->inv_mass * dt;
    body->angular_velocity += body->inv_inertia_world * body->torque * dt;
    
    // Integrate velocities into positions (using updated velocities)
    body->position += body->linear_velocity * dt;
    
    // Integrate angular velocity into orientation quaternion
    quat omega_quat = quat(0.0f, 
                           body->angular_velocity.x, 
                           body->angular_velocity.y, 
                           body->angular_velocity.z);
    quat q_dot = 0.5f * omega_quat * body->orientation;
    body->orientation += q_dot * dt;
    body->orientation = normalize(body->orientation);
    
    // Recompute world-space inertia tensor from updated orientation
    mat3 R = quat_to_mat3(body->orientation);
    body->inv_inertia_world = R * body->inv_inertia_local * transpose(R);
    
    // Clear accumulated forces
    body->force = vec3(0.0f);
    body->torque = vec3(0.0f);
}
```

Quaternion integration requires normalization after each step because floating-point drift accumulates error that violates the unit-norm constraint. Some engines renormalize every frame; others track the quaternion's magnitude and renormalize only when it drifts beyond a threshold.

Substeps partition the frame time into smaller intervals, integrating multiple times per rendered frame. This approach prevents tunneling and stabilizes stiff constraints at the cost of proportionally increased CPU budget. A typical configuration runs physics at 60 Hz while rendering at variable frame rates, accumulating leftover time between physics ticks:

```c
void tick_physics(PhysicsWorld* world, f32 frame_dt) {
    static f32 accumulator = 0.0f;
    const f32 fixed_dt = 1.0f / 60.0f;  // 60 Hz physics rate
    
    accumulator += frame_dt;
    
    while (accumulator >= fixed_dt) {
        // Broad phase
        update_broadphase(world);
        
        // Narrow phase
        detect_collisions(world);
        
        // Constraint solving
        solve_constraints(world, fixed_dt);
        
        // Integration
        for (u32 i = 0; i < world->body_count; ++i) {
            integrate_body(&world->bodies[i], fixed_dt);
        }
        
        accumulator -= fixed_dt;
    }
    
    // Render interpolation: blend between previous and current state
    // proportional to (accumulator / fixed_dt)
}
```

This fixed-timestep loop ensures deterministic behavior independent of rendering frame rate. The interpolation factor allows smooth rendering between discrete physics states, preventing visual stuttering when the frame rate exceeds the physics rate.

## 3. High-Performance Optimization & Failure Modes

Physics simulation consumes substantial CPU resources in games with hundreds or thousands of active bodies. Profiling invariably reveals that constraint solving and narrow-phase collision detection dominate execution time. Broad-phase queries typically account for less than 10% of the budget when spatial structures are properly tuned, while integration costs remain negligible. Optimization therefore focuses on minimizing constraint iterations, reducing contact manifold sizes, and exploiting parallelism across independent body islands.

Sleeping mechanisms deactivate bodies that remain stationary or nearly motionless for several consecutive frames. A body enters sleep when its kinetic energy $\frac{1}{2}m|\mathbf{v}|^2 + \frac{1}{2}\boldsymbol{\omega}^T I \boldsymbol{\omega}$ falls below a threshold and remains there for a defined grace period—typically 0.5 to 1.0 seconds. Sleeping bodies skip integration and collision detection, reactivating only when external forces or collisions from active bodies disturb them. This optimization yields order-of-magnitude speedups in scenes with large static or settled regions, such as stacked crate piles that have stabilized.

Island detection partitions the constraint graph into connected components, identifying groups of bodies that interact through contacts or joints but remain isolated from other groups. Each island solves its constraints independently, enabling parallel execution across islands without synchronization hazards. A union-find data structure tracks connectivity: each contact or joint merges the bodies' disjoint sets, and after processing all constraints, each set corresponds to one island. Large simulations with thousands of bodies often decompose into dozens of islands, each containing tens of bodies—granularity well-suited to modern multicore processors.

SIMD vectorization exploits data parallelism within physics computations. Broad-phase AABB tests naturally vectorize: four or eight AABB pairs can overlap-test simultaneously using SSE or AVX instructions. Constraint solving vectorizes less cleanly because sequential iterations couple constraints through shared bodies, preventing naive SIMD parallelism. However, careful reordering can expose vectorizable subsets: if four contacts involve disjoint body pairs, their impulses can compute in parallel within one SIMD lane.

Memory layout profoundly impacts cache efficiency. Structure-of-arrays (SoA) layouts separate each field into contiguous arrays, improving SIMD load efficiency and prefetch effectiveness:

```c
// Array-of-structures (AoS): poor cache utilization
struct RigidBody {
    vec3 position;
    quat orientation;
    vec3 linear_velocity;
    vec3 angular_velocity;
    // ... many more fields
};
RigidBody bodies[MAX_BODIES];

// Structure-of-arrays (SoA): better cache and SIMD access
struct RigidBodyArray {
    vec3* positions;
    quat* orientations;
    vec3* linear_velocities;
    vec3* angular_velocities;
    // ... parallel arrays
    u32 count;
};
```

When integrating positions, the SoA layout loads positions, velocities, and delta-time into contiguous memory regions, enabling the CPU to prefetch subsequent elements while computing current elements. AoS layouts scatter accesses across cache lines, thrashing the L1 cache and stalling the pipeline.

Contact reduction eliminates redundant or low-contribution contacts from manifolds, trading slight accuracy loss for solver performance. A typical box-box collision can generate four to eight contact points along shared edges or faces. Solving all eight contacts provides no practical benefit over solving the four most influential points—those with maximum penetration or positioned at manifold extremes. Contact reduction algorithms select a representative subset using convex hull computation on the contact point cloud or greedy farthest-point sampling.

Failure modes in physics simulation often manifest as instability, tunneling, or jittering. Instability arises when integration time steps exceed the Nyquist limit for the highest-frequency oscillations in the system, causing numerical resonance that amplifies errors exponentially. Stiff springs, lightweight bodies, and high restitution contacts all reduce the stable time step, sometimes forcing impractically small values. Implicit integration or constraint stabilization mitigates instability but increases per-step cost.

Tunneling occurs when discrete time steps allow fast-moving bodies to pass through thin geometry without generating contacts. Continuous collision detection addresses this by sweeping shapes along their velocity vectors and solving for time-of-impact. Conservative advancement iteratively steps forward in time by the smallest safe increment, checking for new contacts at each substep. Time-of-impact solvers use root-finding on the signed distance function, typically via bisection or regula falsi, converging to collision within a tolerance of 1mm or less.

Jittering—visible oscillation or vibration—results from fighting constraints or insufficient solver iterations. When two contacts push a body in opposite directions, or a joint constraint conflicts with a contact constraint, the solver may fail to converge fully within the iteration budget, leaving residual constraint violation. Increasing iteration counts, adding contact damping, or tuning Baumgarte stabilization parameters often resolves jitter. Baumgarte stabilization blends position-level constraint correction into the velocity solver, proportionally pushing bodies out of penetration each frame:

$$
\dot{C} + \beta C = 0
$$

where $C$ represents the position-level constraint error (penetration depth), $\dot{C}$ the velocity-level error, and $\beta$ a stabilization gain. Typical values for $\beta$ range from 0.1 to 0.3, tuned empirically for the scene's characteristic dynamics.

Determinism breaks when floating-point evaluation order varies across platforms or invocations. Standard IEEE-754 arithmetic specifies bit-exact results for individual operations, but summation order affects rounding errors: $(a + b) + c \neq a + (b + c)$ in floating-point arithmetic when magnitudes differ significantly. Physics engines targeting deterministic replay or lockstep multiplayer must carefully control evaluation order, disable compiler reorderings, and sometimes resort to fixed-point arithmetic for critical computations. Fixed-point representations sacrifice range and precision for exact reproducibility, typically using 16.16 or 24.8 bit allocations for position and velocity variables.

Profiling tools reveal hotspots within the simulation pipeline. Constraint solving often consumes 40-60% of the physics budget, narrow-phase collision detection 20-40%, and broad-phase queries 5-15%. Within constraint solving, matrix-vector multiplications and impulse clamping dominate; within narrow-phase tests, the Separating Axis Theorem accounts for the majority of cycles when testing convex polyhedra. Optimizing the inner loops of these algorithms—unrolling, inlining, strength reduction, and manual vectorization—yields measurable gains. For instance, computing the world-space inverse inertia tensor involves two matrix multiplications; caching the result across all constraints referencing the same body eliminates redundant computation.

Collision margins introduce a small skin around each shape, allowing the solver to generate contacts slightly before true geometric intersection. This early contact generation provides the solver advance warning and stabilizes resting contacts by preventing instantaneous velocity reversals. A typical margin of 1-5mm remains imperceptible visually while significantly improving convergence.

Advanced engines employ constraint graph partitioning to maximize parallelism. The constraint dependency graph expresses which constraints share bodies: two constraints connected in the graph cannot solve simultaneously without race conditions. Graph coloring assigns constraints to non-conflicting batches, such that all constraints within a batch involve disjoint bodies and can execute in parallel. A greedy coloring algorithm typically produces four to six colors for dense contact stacks, enabling parallel execution across all cores with minimal synchronization overhead.

Profiling guided optimization on a realistic scene with 1000 rigid bodies and 4000 contacts typically reveals:

| Phase                  | Baseline Time | After SoA Layout | After Island Parallel | After Contact Reduction |
|------------------------|---------------|------------------|-----------------------|-------------------------|
| Broad Phase            | 0.8 ms        | 0.6 ms           | 0.3 ms                | 0.3 ms                  |
| Narrow Phase           | 2.1 ms        | 1.8 ms           | 0.9 ms                | 0.7 ms                  |
| Constraint Solving     | 5.4 ms        | 4.2 ms           | 1.8 ms                | 1.4 ms                  |
| Integration            | 0.3 ms        | 0.2 ms           | 0.1 ms                | 0.1 ms                  |
| **Total**              | **8.6 ms**    | **6.8 ms**       | **3.1 ms**            | **2.5 ms**              |

This progression demonstrates the cumulative impact of memory layout, parallelism, and algorithmic refinement—transforming an 8.6ms budget that struggles to meet 120 Hz frame deadlines into a 2.5ms budget that leaves ample headroom for rendering, AI, and game logic.

Production physics engines expose tuning parameters that trade fidelity for performance: iteration counts, contact margins, solver substeps, sleeping thresholds, and constraint stabilization gains. These parameters demand scene-specific tuning through empirical testing, as no universal optimum exists. Racing games favor aggressive sleeping and coarse collision geometry to maximize vehicle count; puzzle games demand high iteration counts and tight margins to prevent visible penetration of interlocking pieces. Understanding the mechanical implications of each parameter—how it affects convergence, stability, and perceptual quality—enables informed design choices that align simulation behavior with gameplay requirements.

The interplay between collision detection, constraint solving, and numerical integration forms a tightly coupled system where optimization in one phase enables or constrains optimization in others. Reducing contact manifold sizes accelerates constraint solving but may degrade collision accuracy; increasing substeps stabilizes stiff constraints but multiplies all per-step costs. Effective physics engineering requires holistic reasoning about the entire pipeline, profiling to identify bottlenecks, and iterative refinement guided by both performance metrics and perceptual testing in the target gameplay scenarios.
