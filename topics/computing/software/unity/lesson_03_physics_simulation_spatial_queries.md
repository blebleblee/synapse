# Lesson 3: Physics Simulation, Collision Detection, Spatial Queries

## 1. First-Principles Intuition & Invariants

Every game object that moves, falls, slides, or collides in Unity ultimately obeys a system of differential equations that Newton wrote down three centuries ago. What Unity adds on top of that mathematics is an industrial-grade constraint-satisfaction layer, a broadphase indexing structure, a contact manifold cache, and a deterministic solver—all wrapped in a component abstraction thin enough that a single `AddComponent<Rigidbody>()` call opts an object into the full simulation pipeline. Understanding what that call actually does, and why it costs what it costs, is the difference between a physics implementation that scales to hundreds of simulated actors and one that grinds to 12 FPS at forty.

Unity delegates its physics simulation to NVIDIA PhysX, currently at the 4.x API surface for Unity 2022 LTS and the experimental PhysX 5 integration appearing in Unity 6. PhysX is a rigid-body dynamics engine built around the concept of a *scene*, which is a spatially partitioned collection of actors, shapes, and materials. Every `GameObject` with a `Rigidbody` and at least one `Collider` component maps to a PhysX *dynamic actor* (a `PxRigidDynamic`) backed by one or more `PxShape` instances. Static geometry—terrain, walls, floors—maps to `PxRigidStatic`, which carries no mass or velocity state and exists solely to generate contacts. Unity maintains a one-way synchronization loop: the Transform hierarchy is the authoritative representation for the editor and rendering pipeline, but during simulation the PhysX scene owns the state. The job of `FixedUpdate` is to close that loop, writing back PhysX actor poses into Unity's Transform components after each substep.

The simulation pipeline executes on a fixed timestep, controlled by `Time.fixedDeltaTime`, which defaults to 0.02 seconds (50 Hz). This fixed rate is architecturally non-negotiable for a reason rooted in numerical integration theory. The standard integrator used by PhysX is *semi-implicit Euler* (also called symplectic Euler), where velocity is updated with forces first, then position is updated using the new velocity. Symplectic Euler conserves energy in a bounded fashion for stable timesteps—it neither bleeds energy like explicit Euler nor artificially adds it like some implicit methods—but its stability bound is proportional to `sqrt(k/m)` for a spring of stiffness `k` and mass `m`. Halving the timestep does not halve the error; it quarters it, because the method is first-order. This is why Unity's physics settings expose a *maximum allowed timestep*, which caps how many `FixedUpdate` calls Unity will issue to catch up after a frame spike: uncapped catchup produces a feedback loop where long frames cause many substeps, which cause longer frames.

A `Rigidbody` carries six degrees of freedom: three translational and three rotational. Its inertia tensor—the rotational equivalent of mass—is computed automatically by PhysX from the aggregate of attached collider shapes and their densities. For a `BoxCollider` of half-extents `(hx, hy, hz)` and mass `m`, the principal moments of inertia are `I_x = (m/3)(hy² + hz²)` and cyclically, which is the standard solid-box formula from rigid-body mechanics textbooks. When you use a `MeshCollider` set to convex, PhysX runs a convex hull computation (via its V-HACD pipeline or its own quickhull variant) and approximates the inertia tensor by decomposing the hull into tetrahedra, summing their contributions. The accuracy of this approximation matters: a miscalculated inertia tensor produces physically wrong torque responses to off-center impacts, and the failure mode is subtle—the object just tumbles oddly, never triggering an exception.

The collision detection pipeline has three distinct phases: broadphase, midphase, and narrowphase. Each phase filters the contact candidate set progressively, so that the expensive per-shape computations of the narrowphase run on the smallest possible set of pairs. The broadphase operates on axis-aligned bounding boxes (AABBs) inflated by a *contact offset*, a per-shape scalar that creates a small skin around each shape. PhysX offers two broadphase algorithms selectable at the scene level: *SAP* (Sweep and Prune) and *ABP* (Automatic Box Pruning, the default). SAP maintains three sorted arrays of AABB endpoints along each world axis and uses insertion sort updates on each frame, exploiting frame-to-frame coherence—since most objects move slowly relative to the sort order, almost all insertions are nearly in-place. ABP partitions the world into regions and runs a parallel SAP per region, scaling better than global SAP when object counts are high. The midphase applies only to triangle-mesh and heightfield shapes, using a BVH (Bounding Volume Hierarchy) to prune individual triangle candidates before the narrowphase sees them. For convex shapes there is no midphase; the AABB overlap from the broadphase passes directly to the GJK/EPA narrowphase.

The narrowphase is where actual contact points are generated. For convex pairs, PhysX uses the *Gilbert–Johnson–Keerthi* (GJK) algorithm to compute the minimum distance between two convex polyhedra in O(n) iterations on the support-function dimension, with the *Expanding Polytope Algorithm* (EPA) as the fallback when the shapes are found to be penetrating, to extract the minimum translation vector. The output of a narrowphase contact is a *contact manifold*: up to four contact points, each carrying a world-space position, a contact normal, and a penetration depth. These manifolds feed directly into the constraint solver.

The constraint solver is the heart of the dynamics engine. PhysX uses a *Projected Gauss-Seidel* (PGS) iterative solver, which operates on a system of velocity-level constraints. Each contact manifold generates a *non-penetration constraint* (enforcing that relative velocity along the contact normal satisfies the restitution condition) and two *friction constraints* (enforcing Coulomb friction in the two tangential directions). Joint components—`HingeJoint`, `ConfigurableJoint`, `FixedJoint`—inject additional equality or inequality constraints into the same solver pass. PGS iterates over all constraints in sequence, projecting each solution onto its feasible set (the friction cone for contact friction, the bounds for joint limits), and loops for a configurable number of solver iterations (default is 6 position and 1 velocity iteration). Increasing solver iterations improves constraint fidelity at linear cost; a stack of twenty boxes requires more iterations than a single bouncing sphere because constraint errors propagate up the stack.

The *Layer Collision Matrix*, exposed in Project Settings → Physics, is not a simulation-time filter: it is a broadphase filter. When two layers are unchecked, their `PxShape` instances are assigned non-overlapping `simulationFilterData` words, and the PhysX broadphase discards their AABB overlap without generating a narrowphase pair. This means filtering at the layer matrix level is essentially free—it prunes work before the expensive stages. Filtering via `Physics.IgnoreCollision` is more granular but operates at the narrowphase level by writing a suppress flag into a per-pair filter callback, which is more expensive than layer-level filtering because the broadphase still generates the pair.

The trigger semantic is architecturally distinct from collider contact. When a `Collider` has `isTrigger = true`, its underlying `PxShape` is flagged as a *trigger shape* in PhysX terminology. PhysX does not generate contact manifolds for trigger overlaps—it generates *overlap events* instead. No forces, no friction, no restitution: the solver never sees a trigger shape. This is a critical invariant. `OnTriggerEnter`, `OnTriggerStay`, and `OnTriggerExit` are callbacks driven by overlap state changes tracked by the PhysX overlap detection subsystem, not by the contact reporting path. The practical consequence is that two trigger shapes can overlap each other and both will receive callbacks, but neither will deflect the other's trajectory, because no constraint is generated. If you need a volume that reports overlaps without affecting dynamics, a trigger is correct. If you need one that blocks movement, it must be a collider, not a trigger—even if you do not want restitution, the contact constraint must exist to prevent interpenetration.

---

## 2. Core Architecture & Mechanics

The execution graph below shows how Unity's main thread and physics thread interleave across a single rendered frame, illustrating why `FixedUpdate` can fire zero, one, or multiple times per frame.

```
Frame N (render loop, 16ms wall-clock target)
│
├─ Accumulate dt into physics accumulator
│    accumulator += Time.unscaledDeltaTime
│
├─ While accumulator >= fixedDeltaTime:
│   │
│   ├─ [Physics substep]
│   │   ├─ Unity → PhysX: apply pending force/velocity mutations from script
│   │   ├─ PhysX Broadphase (SAP/ABP on AABBs + contact offset)
│   │   ├─ PhysX Midphase  (BVH on triangle mesh shapes)
│   │   ├─ PhysX Narrowphase (GJK / EPA → contact manifolds)
│   │   ├─ Constraint build  (contacts + joints → PGS constraint rows)
│   │   ├─ Solver iterations (PGS, default 6 pos + 1 vel)
│   │   ├─ Integration        (semi-implicit Euler: v += a*dt, x += v*dt)
│   │   └─ PhysX → Unity: write actor poses to Transform
│   │
│   ├─ FixedUpdate() fires here (all MonoBehaviours)
│   └─ accumulator -= fixedDeltaTime
│
└─ Update() → LateUpdate() → Rendering
```

The indirection between `FixedUpdate` and `Update` is intentional: rendering runs at the display frame rate while physics advances in fixed increments. Unity interpolates `Transform` positions for rendering using the `Rigidbody.interpolation` setting, which buffers one or two previous physics poses and blends them against the current render fraction. Without interpolation, rigid bodies exhibit the characteristic jitter of a 50 Hz signal displayed at 60+ Hz.

### Rigidbody State Machine and Component Wiring

A `Rigidbody` can be in one of three PhysX actor states that map loosely to Unity concepts.

```
                    ┌─────────────────────┐
                    │   Dynamic (default) │◄────── AddComponent<Rigidbody>()
                    │  PxRigidDynamic     │        mass > 0, gravity on
                    └────────┬────────────┘
                             │ isKinematic = true
                             ▼
                    ┌─────────────────────┐
                    │     Kinematic       │   Driven by Transform/MovePosition
                    │  PxRigidDynamic     │   Generates contacts but ignores forces
                    │  (kinematic flag)   │
                    └────────┬────────────┘
                             │ Rigidbody removed
                             ▼
                    ┌─────────────────────┐
                    │      Static         │   No velocity, no mass
                    │  PxRigidStatic      │   Terrain, walls
                    └─────────────────────┘
```

A kinematic body is architecturally significant: it participates in contact generation and pushes dynamic bodies, but it is not subject to solver forces. This makes it ideal for driven platforms, doors, and character controllers—objects that need to block dynamic actors without being deflected by them. The critical failure mode with kinematic bodies is teleportation: setting `transform.position` directly on a kinematic `Rigidbody` bypasses PhysX's swept motion tracking, which means no contacts are generated along the swept path. `Rigidbody.MovePosition`, by contrast, instructs PhysX to move the kinematic actor along a linear sweep within the substep, enabling swept contact generation.

### Continuous Collision Detection

Discrete collision detection—the default mode—checks overlap at the beginning and end of each timestep without considering the trajectory between samples. For a bullet traveling 50 m/s with a 20 ms timestep, the per-step displacement is 1 meter. A wall 0.1 m thick will be tunneled through entirely. PhysX and Unity address this with Continuous Collision Detection (CCD), which is a two-phase mechanism.

The first phase is *Conservative Advancement*: PhysX computes the time-of-impact (TOI) for each dynamic actor flagged for CCD by advancing the actors conservatively—meaning each step forward is guaranteed not to introduce interpenetration—until contact is detected or the timestep is consumed. The TOI computation uses support functions on the convex shapes and a GJK-based root-finding process. At the detected TOI, a *CCD contact* is generated and the actor's motion is clipped, preventing tunneling.

Unity exposes three CCD modes on `Rigidbody`. `Discrete` performs no swept test. `Continuous` enables swept tests between this dynamic body and static geometry only. `ContinuousDynamic` enables swept tests against other dynamic bodies as well, and is the most expensive. `ContinuousSpeculative` takes a different approach: instead of a TOI search, it speculatively expands each shape's contact offset by the magnitude of the per-step motion, inflating the AABB to cover the entire swept volume. This is cheaper than Conservative Advancement because it reuses the existing broadphase without TOI iteration, but it can produce *ghost collisions*—spurious contacts generated by the speculative inflation that would not have occurred if the actual trajectory were traced precisely.

The following `Rigidbody` configuration represents a production baseline for a fast-moving projectile:

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody), typeof(SphereCollider))]
public sealed class Projectile : MonoBehaviour
{
    [SerializeField] private float _speed = 60f;
    [SerializeField] private float _mass  = 0.01f;

    private Rigidbody _rb;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody>();

        // Mass in kg. At 0.01 kg a 60 m/s projectile has 0.6 N·s of momentum,
        // which will deflect light dynamic objects but not knock over heavy ones.
        _rb.mass                    = _mass;
        _rb.useGravity              = false;
        _rb.collisionDetectionMode  = CollisionDetectionMode.ContinuousDynamic;
        _rb.interpolation           = RigidbodyInterpolation.Interpolate;

        // Lock all rotation: a bullet should not tumble from contact torques.
        _rb.constraints = RigidbodyConstraints.FreezeRotation;

        // Solver iterations: default 6/1 is sufficient for a single-shape actor.
        _rb.solverIterations         = 6;
        _rb.solverVelocityIterations = 1;
    }

    private void FixedUpdate()
    {
        // Drive via velocity, not position, so CCD has a valid swept path.
        _rb.linearVelocity = transform.forward * _speed;
    }

    private void OnCollisionEnter(Collision collision)
    {
        // ContactPoint carries position, normal, and impulse.
        ContactPoint contact = collision.GetContact(0);

        Debug.DrawRay(contact.point, contact.normal * 0.5f, Color.red, 2f);

        // Apply an impulse at the exact contact point to simulate impact force
        // on the struck rigidbody, independent of the solver's restitution.
        if (collision.rigidbody != null)
        {
            Vector3 impulse = -contact.normal * collision.impulse.magnitude;
            collision.rigidbody.AddForceAtPosition(impulse, contact.point,
                                                   ForceMode.Impulse);
        }

        Destroy(gameObject);
    }
}
```

### Spatial Query Architecture: Raycasting, Overlaps, and Sweeps

Raycasting in Unity is a spatial query against the PhysX scene's broadphase and BVH structures, not a physics simulation step. It does not advance time, generate contacts, or interact with the solver. The mental model is a point-query on the static scene graph, executed synchronously on the main thread against PhysX's internal scene representation, which may be one substep behind the rendered Transform state depending on the interpolation mode.

PhysX exposes three spatial query types. A *raycast* casts a zero-radius ray from an origin along a direction. A *sweep* casts a shape (sphere, capsule, box, or convex mesh) along a direction, computing the first TOI where the shape would contact any scene actor. A *overlap* query reports all shapes whose AABBs and geometry overlap a given test shape at a point without any direction component. Unity wraps these as `Physics.Raycast`, `Physics.SphereCast`/`Physics.BoxCast`/`Physics.CapsuleCast`, and `Physics.OverlapSphere`/`Physics.OverlapBox`/`Physics.OverlapCapsule`.

The allocation profile of these queries matters for performance. Every variant that returns an array—`Physics.RaycastAll`, `Physics.OverlapSphere`—allocates a managed array on the heap per call, which creates GC pressure in hot paths like weapon hitscan or AI line-of-sight checks running on dozens of agents per frame. The `NonAlloc` variants (`Physics.RaycastNonAlloc`, `Physics.OverlapSphereNonAlloc`) accept a pre-allocated `RaycastHit[]` or `Collider[]` buffer and return the count of populated entries, eliminating per-call allocation. For any spatial query executed more than a handful of times per frame, the `NonAlloc` variant is not an optimization—it is the correct default.

```csharp
using UnityEngine;

public sealed class SensorComponent : MonoBehaviour
{
    [SerializeField] private float    _sightRadius  = 15f;
    [SerializeField] private float    _sightAngle   = 120f;
    [SerializeField] private int      _maxTargets   = 32;
    [SerializeField] private LayerMask _targetMask;
    [SerializeField] private LayerMask _obstructionMask;

    // Pre-allocated buffers: zero heap allocation per query frame.
    private readonly Collider[]    _overlapBuffer = new Collider[32];
    private readonly RaycastHit[]  _losBuffer     = new RaycastHit[1];

    // Called by an AIDirector on a fixed interval, not every FixedUpdate.
    public int QueryVisibleTargets(Transform[] results, int maxResults)
    {
        int overlapped = Physics.OverlapSphereNonAlloc(
            transform.position, _sightRadius, _overlapBuffer, _targetMask,
            QueryTriggerInteraction.Ignore);

        int found = 0;
        for (int i = 0; i < overlapped && found < maxResults; i++)
        {
            Transform candidate = _overlapBuffer[i].transform;
            Vector3   toTarget  = candidate.position - transform.position;

            // Angle cull: dot product against forward is cheaper than Angle().
            float dot = Vector3.Dot(transform.forward, toTarget.normalized);
            if (dot < Mathf.Cos(_sightAngle * 0.5f * Mathf.Deg2Rad))
                continue;

            // Line-of-sight: single-result NonAlloc raycast beats RaycastAll.
            int hits = Physics.RaycastNonAlloc(
                transform.position, toTarget.normalized,
                _losBuffer, toTarget.magnitude,
                _obstructionMask, QueryTriggerInteraction.Ignore);

            if (hits == 0)
                results[found++] = candidate;
        }
        return found;
    }
}
```

The layermask on `OverlapSphere` limits the broadphase traversal to relevant actors only. The subsequent raycast uses the obstruction mask—which should be a *different* set of layers than the target mask—to test for occluding geometry without hitting the targets themselves. Using the wrong mask here is a common failure mode that causes line-of-sight raycasts to self-terminate on the target's own collider.

### Shape Complexity and the Physics Material

`PhysicsMaterial` (note: `PhysicMaterial` in older Unity API, the extra 's' was added in 2022) encodes two scalar pairs that parameterize the solver's contact response. `dynamicFriction` and `staticFriction` control the Coulomb friction coefficients in the two tangential constraint directions. `bounciness` (coefficient of restitution, 0–1) scales the relative normal velocity in the restitution constraint: `v_post = -bounciness * v_pre`. The `frictionCombine` and `bounceCombine` enumerations control how the two materials on contacting shapes are merged—`Average`, `Minimum`, `Maximum`, or `Multiply`—with `Minimum` being the physically correct choice for most surface combinations (the softer material governs).

A common failure mode is setting `bounciness = 1.0f` expecting perfectly elastic collisions and finding instead that objects gain energy over time. This occurs because PhysX applies restitution only when the relative normal velocity exceeds a *restitution threshold* (configurable in Physics settings, default 1 m/s). Below this threshold, the contact is treated as inelastic to prevent jitter from solver oscillation. If your bounce energy source is a collision at 0.5 m/s, the threshold suppresses the restitution entirely regardless of the material coefficient.

---

## 3. High-Performance Optimization & Failure Modes

The PhysX simulation cost scales with three quantities: the number of active dynamic actors, the number of narrowphase contact pairs, and the solver constraint count. Each of these has a distinct mitigation strategy, and conflating them leads to optimizations that address the wrong bottleneck.

### Sleeping and Deactivation

The most effective optimization in rigid-body simulation is not running it. PhysX implements a *sleeping* mechanism: an actor whose linear and angular velocity remain below configurable thresholds (`sleepThreshold` on `Rigidbody`, measured in kinetic energy units) for a configurable number of substeps is marked asleep. Sleeping actors are excluded from broadphase pair generation and solver processing entirely. The cost of a sleeping actor is bounded by its AABB entry in the broadphase structure—effectively zero compared to an active actor.

The practical implication is that densely packed static-ish environments—rubble piles, furniture, crates—should allow objects to sleep as aggressively as possible. Setting `Rigidbody.sleepThreshold` higher than the default (0.005) accelerates sleep onset at the cost of objects appearing to freeze while still visibly moving. Setting it lower risks sleep never occurring in environments with persistent low-amplitude vibration from solver residuals. A value between 0.01 and 0.05 works well for most game objects; test with `Rigidbody.IsSleeping()` in a diagnostics overlay.

Waking a sleeping actor via `Rigidbody.WakeUp()` is cheap. The PhysX sleeping subsystem uses an island-based wake propagation: when one actor in a contact island is woken, all connected actors are woken through the contact graph. This means a single dynamic actor landing on a sleeping pile can wake every object in the pile simultaneously, spiking the solver cost by the number of newly active actors in that frame. This is the canonical physics performance spike in destruction simulations, and the mitigation is not to prevent waking—it is to cap the number of simulated actors using an *object pooling* strategy that destroys or replaces distant or non-visible fragments with static decals once their kinetic energy falls below a visual relevance threshold.

### Layer Matrix Design

The collision layer matrix is a 32×32 boolean matrix, and its design has a direct multiplier effect on broadphase cost. Consider an environment with player characters, enemy characters, projectiles, environment geometry, and UI raycasts. If projectiles are on the same layer as enemies, every projectile-to-enemy and every enemy-to-enemy pair is evaluated. Segregating projectiles onto a dedicated layer and enabling only the projectile-vs-player and projectile-vs-environment matrix entries reduces the broadphase pair count multiplicatively.

The architectural rule is to design layers around *interaction semantics*, not *object categories*. Two objects that should never interact should never share a layer pair entry, regardless of what they are. The 32-layer limit is a PhysX constraint (filter group bits are 32-bit words), not a Unity policy, and it is worth reserving several layers for specialized query-only uses: a "RaycastOnly" layer for invisible hit-detection volumes, an "AIVision" layer for sensors, and a "PhysicsIgnore" layer for objects that need a collider for trigger queries but must not interact with any dynamic body.

### QueryTriggerInteraction and the Dual-Shape Anti-Pattern

A recurring architecture error is placing both a trigger and a collider on the same `GameObject` to handle different interaction types simultaneously—for example, a character capsule that needs to block movement *and* report entry into hazard zones. The correct pattern is not a dual-shape design but a *nested trigger child*: a child `GameObject` with its own trigger collider, configured on a separate layer that only overlaps with the hazard detection layer. The parent retains the physics collider on the character layer. This separates the two concerns into two PhysX shapes with independent filter masks, avoiding the ambiguity of `QueryTriggerInteraction` flags and preventing the solver from accidentally generating contact constraints involving trigger shapes in edge cases involving kinematic actors.

### Measuring Physics Cost: The Profiler Path

The Unity Profiler's CPU timeline exposes the physics pipeline at the granularity of PhysX task groups. The key markers to track are `Physics.Processing` (the full substep cost, including broadphase through integration), `Physics.FetchResults` (the synchronization step where PhysX writes poses back to Unity Transforms and fires collision callbacks), and `FixedUpdate.ScriptRunBehaviourFixedUpdate` (time spent in user `FixedUpdate` and physics callbacks). A disproportionately large `FetchResults` relative to `Processing` indicates that collision callback handlers (`OnCollisionEnter`, `OnTriggerStay`) are themselves expensive—a common issue when database lookups, LINQ queries, or large dictionary iterations appear inside callback code.

For granular contact-level profiling, the PhysX Visual Debugger (PVD) connects to a running Unity editor build via `UnityEngine.Physics` PVD API hooks available in development builds. PVD visualizes contact manifolds, sleeping state, and constraint graphs per-frame at a resolution not available in Unity's own profiler. Its contact count histogram per actor is the fastest way to identify a mesh collider with degenerate triangle topology generating hundreds of spurious contacts per frame—a failure mode that presents as unexplained `Physics.Processing` spikes on otherwise simple scenes.

### The MeshCollider Convex Constraint

Non-convex `MeshCollider` shapes (convex unchecked) can only generate contacts against other static actors—PhysX prohibits dynamic-vs-concave-mesh contacts. Attempting to place a non-convex `MeshCollider` on a `Rigidbody` without the convex flag will cause PhysX to either ignore the shape or log a warning and fall back to the convex hull, depending on Unity version. The correct decomposition strategy for a concave dynamic object is *Approximate Convex Decomposition* (VHACD), which splits the mesh into a union of convex pieces. Unity exposes this in the mesh import settings under "Generate Convex" with a decomposition quality slider. For runtime-generated geometry, the `PhysicsShapeAuthoring` component in the Unity Physics package (DOTS) provides programmatic VHACD access, but in the classic PhysX pipeline the decomposition must happen at import time or be pre-computed offline.

The constraint solver's iteration count deserves explicit attention in complex joint chains. A ragdoll with twelve joints connected in a chain requires far more than the default six solver iterations to converge: errors in the shoulder joint propagate down to the wrist through six intervening constraints, and each PGS pass resolves only one layer of that propagation. The standard heuristic is `iterations ≈ joint_chain_depth * 2`, so a twelve-joint ragdoll benefits from twelve to sixteen position iterations. This is set per-`Rigidbody` via `solverIterations`, and in a ragdoll context it should be set on every bone, not just the root, because PhysX solves constraints per *island* and each bone's body is an island member.

The final failure mode worth internalizing is *constraint fighting*: two physics systems attempting to control the same degree of freedom simultaneously. The most common case is an animation system driving bone Transforms while a ragdoll solver constrains them. When an animator writes to a `Transform` and PhysX simultaneously resolves a contact on the same bone, the result is solver blow-up: exponentially growing oscillation that sends the bone to infinity within two or three substeps. The correct architecture separates these regimes completely—full kinematic (animation-driven) and full dynamic (ragdoll-driven)—with a transition that blends pose targets over several frames while switching the kinematic flag atomically at the physics level. The `Rigidbody.isKinematic` flag can be toggled mid-simulation safely; PhysX deactivates the velocity state on the transition frame and re-activates it clean on the next.
