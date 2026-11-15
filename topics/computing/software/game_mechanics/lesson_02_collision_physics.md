# Lesson 2: Collision Detection, Physics Simulation

## 1. First-Principles Intuition & Invariants

Physics simulation in interactive software systems represents one of the most demanding real-time computational challenges in modern game development. Unlike offline rendering or batch processing workloads, physics engines must produce deterministic, stable, and physically plausible results within strict frame budgets—typically 16.67 milliseconds for 60 Hz gameplay or 8.33 milliseconds for 120 Hz competitive titles. This temporal constraint forces us to balance numerical accuracy against computational complexity, often sacrificing mathematical rigor for perceptual correctness.

At its foundation, a physics engine solves Newton's second law of motion across a collection of rigid bodies, soft bodies, and constraint relationships. The core simulation loop integrates forces into velocities and velocities into positions, detects interpenetrating geometry, resolves collisions through impulse-based mechanics or constraint satisfaction, and maintains invariants such as energy conservation and momentum preservation. These operations must occur in a stable numerical integration scheme that prevents catastrophic divergence even under extreme loading conditions—a falling stack of a thousand rigid bodies, explosive forces launching debris across a scene, or complex articulated ragdoll hierarchies collapsing under gravitational load.

The fundamental invariant underlying all collision detection is the separation axis theorem, which states that two convex polyhedra are disjoint if and only if there exists a separating axis along which their projections do not overlap. For three-dimensional convex hulls, candidate separating axes include the face normals of both polyhedra and the cross products of edge pairs. This mathematical foundation allows us to transform the continuous collision detection problem into a discrete set of projection tests, each reducible to scalar interval comparisons. However, the naïve application of this theorem scales quadratically with scene complexity—testing every object against every other object yields $O(n^2)$ collision pairs, which becomes computationally intractable for scenes containing thousands of dynamic entities.

Spatial partitioning structures break this quadratic barrier by exploiting temporal and spatial coherence. Objects in physical proximity in one frame tend to remain proximate in subsequent frames, and distant objects cannot collide without first passing through intermediate spatial regions. Broad-phase acceleration structures such as bounding volume hierarchies, spatial hash grids, and sweep-and-prune algorithms cull the potential collision set from $O(n^2)$ to typically $O(n \log n)$ or even $O(n)$ in well-distributed scenarios. The narrow-phase collision detection then operates only on these candidate pairs, applying precise geometric intersection tests such as GJK distance algorithms, SAT projection tests, or specialized primitives for sphere-sphere, capsule-capsule, and convex polyhedron tests.

Numerical integration of the equations of motion introduces additional complexity. Explicit Euler integration—the simplest scheme where $\mathbf{v}_{t+1} = \mathbf{v}_t + \mathbf{a}_t \Delta t$ and $\mathbf{x}_{t+1} = \mathbf{x}_t + \mathbf{v}_t \Delta t$—suffers from catastrophic instability under stiff constraints and large time steps. Energy accumulates rather than dissipates, causing orbiting bodies to spiral outward and constrained systems to explode. Semi-implicit Euler, also called symplectic Euler, reverses the order by updating velocity first and using the new velocity for position integration. This single change dramatically improves stability and energy behavior, making it the de facto standard for real-time physics. For higher accuracy requirements, Runge-Kutta methods (RK2, RK4) or Verlet integration schemes provide better energy conservation at the cost of additional force evaluations per timestep.

Constraint resolution forms the third pillar of physics simulation. Constraints represent geometric relationships that must be maintained despite applied forces—distance constraints hold ragdoll limbs at fixed lengths, hinge constraints restrict door rotation to a single axis, and contact constraints prevent interpenetration at collision surfaces. These constraints form a coupled system of equations that must be solved simultaneously to satisfy all relationships while respecting friction, restitution, and motor forces. Iterative solvers such as Sequential Impulse (SI) and Position-Based Dynamics (PBD) trade mathematical precision for computational efficiency, converging toward constraint satisfaction through repeated local corrections rather than solving the full linear system in one step.

Determinism represents a critical but often overlooked invariant in multiplayer and competitive game physics. Floating-point arithmetic is not associative—the order of operations affects the final result due to rounding errors. A physics simulation that processes collision pairs in hash table iteration order, which varies between executions due to memory allocator nondeterminism, will produce divergent trajectories across networked clients even with identical inputs. Achieving determinism requires careful attention to iteration order, floating-point reproducibility, and elimination of all sources of environmental entropy such as pointer addresses used as hash seeds or uninitialized memory used in comparison functions.

## 2. Core Architecture & Mechanics

A production physics engine decomposes into several tightly coupled subsystems, each operating on shared object state through carefully orchestrated phases. The simulation pipeline typically follows this execution model:

```
┌─────────────────────────────────────────────────────────────┐
│                    Physics Tick (Δt)                        │
├─────────────────────────────────────────────────────────────┤
│  1. Force Accumulation                                      │
│     • Apply gravity, springs, motors, user forces           │
│     • Compute torques from force application points         │
│     • Clear previous frame's accumulated impulses           │
├─────────────────────────────────────────────────────────────┤
│  2. Integration (Semi-Implicit Euler)                       │
│     • v = v + (F/m) * Δt                                   │
│     • ω = ω + (I⁻¹ * τ) * Δt                              │
│     • x = x + v * Δt                                       │
│     • q = q + 0.5 * ω_quat * q * Δt                       │
├─────────────────────────────────────────────────────────────┤
│  3. Broad Phase (Spatial Acceleration)                      │
│     • Update AABB positions in acceleration structure       │
│     • Query overlapping AABB pairs                          │
│     • Output candidate collision pairs                      │
├─────────────────────────────────────────────────────────────┤
│  4. Narrow Phase (Geometric Intersection)                   │
│     • Precise collision detection per candidate pair        │
│     • Generate contact manifolds (points, normals, depth)   │
│     • Persistent contact tracking for warm-starting         │
├─────────────────────────────────────────────────────────────┤
│  5. Constraint Resolution (Iterative Solver)                │
│     • Solve contact constraints (non-penetration)           │
│     • Solve joint constraints (distance, hinge, etc.)       │
│     • Apply corrective impulses over N iterations           │
├─────────────────────────────────────────────────────────────┤
│  6. Integration Finalization                                │
│     • Commit final velocities to body state                 │
│     • Update transformation matrices for rendering          │
│     • Invoke collision callbacks for gameplay logic         │
└─────────────────────────────────────────────────────────────┘
```

The rigid body representation encapsulates all dynamic state required for simulation. A minimal rigid body structure contains position, orientation (stored as a unit quaternion for numerical stability and singularity-free interpolation), linear velocity, angular velocity, mass, and the inverse inertia tensor. The inertia tensor describes resistance to rotational acceleration about each principal axis, transforming applied torques into angular accelerations. Since this tensor rotates with the body, we typically store the inverse inertia tensor in local body space and transform it to world space each frame through the rotation matrix: $I_{world}^{-1} = R \cdot I_{local}^{-1} \cdot R^T$.

```c
typedef struct RigidBody {
    vec3 position;
    quat orientation;
    vec3 linear_velocity;
    vec3 angular_velocity;
    
    float mass;
    float inv_mass;
    mat3 inv_inertia_local;
    mat3 inv_inertia_world;
    
    vec3 force_accumulator;
    vec3 torque_accumulator;
    
    uint32_t collision_mask;
    uint32_t collision_group;
    void* user_data;
} RigidBody;

void rigid_body_update_inertia(RigidBody* body) {
    mat3 rotation = quat_to_mat3(body->orientation);
    body->inv_inertia_world = mat3_multiply(
        mat3_multiply(rotation, body->inv_inertia_local),
        mat3_transpose(rotation)
    );
}

void rigid_body_apply_force(RigidBody* body, vec3 force, vec3 point) {
    body->force_accumulator = vec3_add(body->force_accumulator, force);
    vec3 offset = vec3_sub(point, body->position);
    vec3 torque = vec3_cross(offset, force);
    body->torque_accumulator = vec3_add(body->torque_accumulator, torque);
}

void rigid_body_integrate(RigidBody* body, float dt) {
    // Semi-implicit Euler: velocity first, then position
    vec3 acceleration = vec3_scale(body->force_accumulator, body->inv_mass);
    body->linear_velocity = vec3_add(body->linear_velocity, 
                                     vec3_scale(acceleration, dt));
    
    vec3 angular_accel = mat3_mul_vec3(body->inv_inertia_world, 
                                       body->torque_accumulator);
    body->angular_velocity = vec3_add(body->angular_velocity, 
                                      vec3_scale(angular_accel, dt));
    
    body->position = vec3_add(body->position, 
                              vec3_scale(body->linear_velocity, dt));
    
    // Quaternion integration via angular velocity
    quat omega_quat = {body->angular_velocity.x, 
                       body->angular_velocity.y,
                       body->angular_velocity.z, 0.0f};
    quat derivative = quat_multiply(omega_quat, body->orientation);
    derivative = quat_scale(derivative, 0.5f * dt);
    body->orientation = quat_add(body->orientation, derivative);
    body->orientation = quat_normalize(body->orientation);
    
    rigid_body_update_inertia(body);
    
    // Clear accumulators for next frame
    body->force_accumulator = vec3_zero();
    body->torque_accumulator = vec3_zero();
}
```

Broad-phase acceleration structures exploit the spatial distribution of objects to cull non-colliding pairs before expensive narrow-phase tests. The sweep-and-prune algorithm maintains sorted lists of axis-aligned bounding box (AABB) endpoints along each coordinate axis. As objects move, their AABBs slide along these sorted lists, with overlap events triggering collision pair insertion and separation events triggering removal. This approach achieves $O(n)$ performance when objects move coherently but degenerates to $O(n^2)$ under pathological distributions where all objects span the entire axis range.

Spatial hash grids partition space into a uniform grid of cells, hashing each object's AABB into the cells it overlaps. Collision queries then only test objects within the same cells or neighboring cells. The hash function maps three-dimensional integer grid coordinates $(i, j, k)$ into a one-dimensional hash bucket:

```c
typedef struct SpatialHash {
    HashBucket* buckets;
    size_t bucket_count;
    float cell_size;
    float inv_cell_size;
} SpatialHash;

static inline uint32_t hash_grid_coord(int32_t x, int32_t y, int32_t z) {
    // Knuth multiplicative hash
    const uint32_t PRIME1 = 73856093;
    const uint32_t PRIME2 = 19349663;
    const uint32_t PRIME3 = 83492791;
    return (x * PRIME1) ^ (y * PRIME2) ^ (z * PRIME3);
}

void spatial_hash_insert(SpatialHash* hash, RigidBody* body, AABB aabb) {
    int32_t min_x = (int32_t)floorf(aabb.min.x * hash->inv_cell_size);
    int32_t min_y = (int32_t)floorf(aabb.min.y * hash->inv_cell_size);
    int32_t min_z = (int32_t)floorf(aabb.min.z * hash->inv_cell_size);
    int32_t max_x = (int32_t)floorf(aabb.max.x * hash->inv_cell_size);
    int32_t max_y = (int32_t)floorf(aabb.max.y * hash->inv_cell_size);
    int32_t max_z = (int32_t)floorf(aabb.max.z * hash->inv_cell_size);
    
    for (int32_t x = min_x; x <= max_x; x++) {
        for (int32_t y = min_y; y <= max_y; y++) {
            for (int32_t z = min_z; z <= max_z; z++) {
                uint32_t hash_key = hash_grid_coord(x, y, z);
                uint32_t bucket_idx = hash_key % hash->bucket_count;
                hash_bucket_add(&hash->buckets[bucket_idx], body);
            }
        }
    }
}

void spatial_hash_query_pairs(SpatialHash* hash, CollisionPair* pairs, 
                              size_t* pair_count) {
    *pair_count = 0;
    for (size_t i = 0; i < hash->bucket_count; i++) {
        HashBucket* bucket = &hash->buckets[i];
        // Check all pairs within this bucket
        for (size_t j = 0; j < bucket->count; j++) {
            for (size_t k = j + 1; k < bucket->count; k++) {
                if (aabb_overlaps(bucket->bodies[j]->aabb, 
                                  bucket->bodies[k]->aabb)) {
                    pairs[(*pair_count)++] = (CollisionPair){
                        .body_a = bucket->bodies[j],
                        .body_b = bucket->bodies[k]
                    };
                }
            }
        }
    }
}
```

The choice of cell size critically impacts performance. Cells too large cause excessive collision pair candidates; cells too small fragment objects across many cells, increasing insertion and query overhead. A common heuristic sets cell size to the median object diameter, ensuring most objects occupy one or two cells.

Narrow-phase collision detection computes precise geometric intersection information for each broad-phase candidate pair. For convex polyhedra, the Gilbert-Johnson-Keerthi (GJK) algorithm provides a general-purpose distance computation by iteratively constructing a simplex in Minkowski difference space. The Minkowski difference $A \ominus B = \{a - b : a \in A, b \in B\}$ represents the set of all vector differences between points in shape A and shape B. Two shapes intersect if and only if their Minkowski difference contains the origin.

GJK builds a simplex—a point, line segment, triangle, or tetrahedron—that encloses the origin, using a support function that returns the furthest point in a given direction. Each iteration selects a search direction toward the origin, computes the support point in that direction, and updates the simplex. If the new support point fails to pass the origin along the search direction, the shapes do not intersect. Otherwise, the simplex grows until it contains the origin or reduces to a lower-dimensional feature closest to the origin.

```c
typedef struct SupportPoint {
    vec3 point_a;  // Point on shape A
    vec3 point_b;  // Point on shape B
    vec3 point;    // Minkowski difference point (point_a - point_b)
} SupportPoint;

SupportPoint support(const ConvexMesh* mesh_a, const ConvexMesh* mesh_b,
                     vec3 direction) {
    vec3 point_a = convex_mesh_support(mesh_a, direction);
    vec3 point_b = convex_mesh_support(mesh_b, vec3_negate(direction));
    return (SupportPoint){
        .point_a = point_a,
        .point_b = point_b,
        .point = vec3_sub(point_a, point_b)
    };
}

bool gjk_intersect(const ConvexMesh* mesh_a, const ConvexMesh* mesh_b) {
    vec3 direction = vec3_normalize(vec3_sub(mesh_b->center, mesh_a->center));
    SupportPoint simplex[4];
    size_t simplex_size = 1;
    
    simplex[0] = support(mesh_a, mesh_b, direction);
    direction = vec3_negate(simplex[0].point);
    
    for (int iteration = 0; iteration < 32; iteration++) {
        SupportPoint new_point = support(mesh_a, mesh_b, direction);
        
        if (vec3_dot(new_point.point, direction) < 0.0f) {
            return false;  // Cannot reach origin
        }
        
        simplex[simplex_size++] = new_point;
        
        if (simplex_contains_origin(simplex, &simplex_size, &direction)) {
            return true;
        }
    }
    
    return false;
}
```

When GJK detects intersection, the Expanding Polytope Algorithm (EPA) extracts penetration depth and collision normal by expanding the final GJK simplex until its closest face to the origin represents the minimum separating distance. This face normal becomes the collision normal, and the distance to the origin yields penetration depth.

Contact manifold generation aggregates multiple contact points from a collision into a stable set that accurately represents the contact surface. For box-box collisions, clipping algorithms project the collision feature of one box onto the reference face of the other, generating up to four contact points at the clipped vertices. Persistent contact tracking maintains contact point identity across frames through feature IDs or spatial proximity matching, enabling warm-starting of the constraint solver with cached impulses from the previous frame. This dramatically improves solver convergence by leveraging temporal coherence—contacts that existed in the previous frame likely persist with similar constraint forces.

Constraint resolution transforms contact manifolds and joint constraints into corrective impulses that separate interpenetrating bodies and maintain joint relationships. The Sequential Impulse method iterates over all constraints, computing and applying impulses one at a time. For a contact constraint, the impulse magnitude $\lambda$ that prevents penetration and respects friction obeys the complementarity condition: either the bodies separate (zero contact force) or they remain in contact (positive normal force).

The impulse applied to resolve a contact constraint at point $\mathbf{r}_a$ on body A and $\mathbf{r}_b$ on body B follows:

```c
typedef struct ContactConstraint {
    RigidBody* body_a;
    RigidBody* body_b;
    vec3 point_a;      // Contact point in world space on A
    vec3 point_b;      // Contact point in world space on B
    vec3 normal;       // From A toward B
    float penetration;
    float accumulated_normal_impulse;
    float accumulated_tangent_impulse[2];
} ContactConstraint;

void solve_contact_constraint(ContactConstraint* contact, float dt) {
    vec3 ra = vec3_sub(contact->point_a, contact->body_a->position);
    vec3 rb = vec3_sub(contact->point_b, contact->body_b->position);
    
    vec3 va = vec3_add(contact->body_a->linear_velocity,
                       vec3_cross(contact->body_a->angular_velocity, ra));
    vec3 vb = vec3_add(contact->body_b->linear_velocity,
                       vec3_cross(contact->body_b->angular_velocity, rb));
    vec3 relative_velocity = vec3_sub(vb, va);
    
    float velocity_along_normal = vec3_dot(relative_velocity, contact->normal);
    
    // Baumgarte stabilization: bias velocity to resolve penetration
    const float BAUMGARTE = 0.2f;
    const float SLOP = 0.01f;
    float bias = (BAUMGARTE / dt) * fmaxf(contact->penetration - SLOP, 0.0f);
    
    vec3 ra_cross_n = vec3_cross(ra, contact->normal);
    vec3 rb_cross_n = vec3_cross(rb, contact->normal);
    
    float inv_mass_sum = contact->body_a->inv_mass + contact->body_b->inv_mass;
    float angular_factor_a = vec3_dot(ra_cross_n, 
        mat3_mul_vec3(contact->body_a->inv_inertia_world, ra_cross_n));
    float angular_factor_b = vec3_dot(rb_cross_n,
        mat3_mul_vec3(contact->body_b->inv_inertia_world, rb_cross_n));
    
    float effective_mass = 1.0f / (inv_mass_sum + angular_factor_a + 
                                    angular_factor_b);
    
    float lambda = effective_mass * (-velocity_along_normal + bias);
    
    // Clamp accumulated impulse to be non-negative (no pulling)
    float old_impulse = contact->accumulated_normal_impulse;
    contact->accumulated_normal_impulse = fmaxf(old_impulse + lambda, 0.0f);
    lambda = contact->accumulated_normal_impulse - old_impulse;
    
    vec3 impulse = vec3_scale(contact->normal, lambda);
    
    contact->body_a->linear_velocity = vec3_sub(
        contact->body_a->linear_velocity,
        vec3_scale(impulse, contact->body_a->inv_mass)
    );
    contact->body_a->angular_velocity = vec3_sub(
        contact->body_a->angular_velocity,
        mat3_mul_vec3(contact->body_a->inv_inertia_world,
                      vec3_cross(ra, impulse))
    );
    
    contact->body_b->linear_velocity = vec3_add(
        contact->body_b->linear_velocity,
        vec3_scale(impulse, contact->body_b->inv_mass)
    );
    contact->body_b->angular_velocity = vec3_add(
        contact->body_b->angular_velocity,
        mat3_mul_vec3(contact->body_b->inv_inertia_world,
                      vec3_cross(rb, impulse))
    );
}
```

Baumgarte stabilization introduces a position correction term into the velocity constraint, gradually pushing apart penetrating bodies over multiple frames. The slop threshold prevents jitter by allowing small overlaps that do not generate corrective impulses. Friction constraints operate similarly but clamp impulses to the Coulomb friction cone: the tangential impulse magnitude cannot exceed $\mu$ times the normal impulse, where $\mu$ represents the coefficient of friction.

Joint constraints maintain geometric relationships between bodies. A distance constraint enforces fixed separation between two points, a hinge constraint restricts relative rotation to a single axis, and a motor constraint drives relative velocity toward a target. Each constraint type derives its own effective mass matrix and bias term, but the solution structure remains identical—compute impulse magnitude from relative velocity and effective mass, clamp according to constraint limits, and apply impulses to both bodies.

## 3. High-Performance Optimization & Failure Modes

Real-time physics simulation at scale demands aggressive optimization across multiple dimensions: spatial data structures, numerical stability, cache coherency, and parallelization strategies. The naive $O(n^2)$ collision detection baseline becomes computationally prohibitive beyond a few hundred dynamic bodies, while numerical integration errors accumulate over time, causing constraint drift, energy gain, and catastrophic simulation explosions.

Spatial partitioning optimization begins with profiling the broad-phase collision detection to identify whether bucket distribution in spatial hashing remains uniform or whether certain cells accumulate excessive objects. Hash collisions cause linear chains within buckets, degrading query performance from $O(1)$ to $O(k)$ where $k$ represents the chain length. Monitoring maximum bucket occupancy and average bucket size across frames reveals pathological distributions. When maximum occupancy exceeds a threshold—typically 16 to 32 objects per cell—either the cell size requires tuning or the hash function exhibits poor distribution characteristics.

Dynamic spatial hash resizing adapts to changing object distributions by monitoring load factor and rehashing when insertion density crosses thresholds. However, rehashing imposes a frame-time spike as all objects reinsert into the new structure. Incremental rehashing amortizes this cost by spreading reinsertion across multiple frames, maintaining both old and new hash tables during the transition and gradually migrating objects. This approach trades memory overhead for temporal stability, preventing frame-rate hitches in production gameplay.

Bounding volume hierarchy (BVH) construction represents an alternative spatial acceleration strategy that often outperforms spatial hashing for sparse or clustered object distributions. A BVH recursively partitions objects into a binary tree of axis-aligned bounding boxes, with leaf nodes containing individual objects and internal nodes containing the union of their children's bounds. Top-down construction algorithms such as Surface Area Heuristic (SAH) select split planes that minimize expected traversal cost:

```c
typedef struct BVHNode {
    AABB bounds;
    union {
        struct {
            struct BVHNode* left;
            struct BVHNode* right;
        } internal;
        struct {
            RigidBody** bodies;
            uint32_t body_count;
        } leaf;
    };
    bool is_leaf;
} BVHNode;

float compute_sah_cost(AABB left_bounds, uint32_t left_count,
                       AABB right_bounds, uint32_t right_count) {
    float left_area = aabb_surface_area(left_bounds);
    float right_area = aabb_surface_area(right_bounds);
    return left_area * left_count + right_area * right_count;
}

BVHNode* build_bvh(RigidBody** bodies, uint32_t count, int depth) {
    BVHNode* node = allocate_bvh_node();
    node->bounds = compute_union_aabb(bodies, count);
    
    if (count <= 4 || depth > 32) {
        node->is_leaf = true;
        node->leaf.bodies = bodies;
        node->leaf.body_count = count;
        return node;
    }
    
    int best_axis = -1;
    float best_pos = 0.0f;
    float best_cost = FLT_MAX;
    
    for (int axis = 0; axis < 3; axis++) {
        for (uint32_t i = 0; i < count; i++) {
            float split_pos = aabb_center(bodies[i]->aabb).v[axis];
            
            AABB left_bounds = aabb_empty();
            AABB right_bounds = aabb_empty();
            uint32_t left_count = 0, right_count = 0;
            
            for (uint32_t j = 0; j < count; j++) {
                float center = aabb_center(bodies[j]->aabb).v[axis];
                if (center < split_pos) {
                    left_bounds = aabb_union(left_bounds, bodies[j]->aabb);
                    left_count++;
                } else {
                    right_bounds = aabb_union(right_bounds, bodies[j]->aabb);
                    right_count++;
                }
            }
            
            if (left_count > 0 && right_count > 0) {
                float cost = compute_sah_cost(left_bounds, left_count,
                                              right_bounds, right_count);
                if (cost < best_cost) {
                    best_cost = cost;
                    best_axis = axis;
                    best_pos = split_pos;
                }
            }
        }
    }
    
    RigidBody** left_bodies = malloc(count * sizeof(RigidBody*));
    RigidBody** right_bodies = malloc(count * sizeof(RigidBody*));
    uint32_t left_count = 0, right_count = 0;
    
    for (uint32_t i = 0; i < count; i++) {
        float center = aabb_center(bodies[i]->aabb).v[best_axis];
        if (center < best_pos) {
            left_bodies[left_count++] = bodies[i];
        } else {
            right_bodies[right_count++] = bodies[i];
        }
    }
    
    node->is_leaf = false;
    node->internal.left = build_bvh(left_bodies, left_count, depth + 1);
    node->internal.right = build_bvh(right_bodies, right_count, depth + 1);
    
    return node;
}
```

Dynamic BVH maintenance incrementally updates the tree structure as objects move rather than rebuilding from scratch each frame. When an object's AABB expands beyond its leaf node's bounds, the tree reinserts the object by traversing from the root and selecting the child with minimum volume increase at each level. This greedy insertion strategy maintains reasonable tree quality without global restructuring, though periodic full rebuilds (every few hundred frames) prevent degeneration from accumulated suboptimal insertions.

Numerical stability in constraint solvers critically depends on iteration count and warm-starting. Insufficient iterations leave constraints under-resolved, causing visible interpenetration, jitter, and energy gain. Production physics engines typically execute 10 to 20 solver iterations per frame for general gameplay and 30 to 50 iterations for precision-critical scenarios such as stacking simulations or articulated character ragdolls. Warm-starting accelerates convergence by initializing each constraint's accumulated impulse from the previous frame's solution. Since contact configurations change slowly frame-to-frame, the previous solution provides an excellent initial guess, often halving required iteration count.

Constraint drift—the gradual accumulation of error causing joint constraints to violate their limits—arises from iterative solver approximations and numerical integration error. Projection-based corrections explicitly enforce constraint limits by computing positional adjustments that snap bodies back to valid configurations. Position-Based Dynamics (PBD) makes this the primary solution mechanism, directly manipulating positions rather than solving for impulses. This approach trades physical accuracy for unconditional stability, making it popular for soft-body simulation, cloth, and hair where visual plausibility matters more than momentum conservation.

Continuous collision detection (CCD) prevents fast-moving objects from tunneling through thin geometry by computing time-of-impact for object trajectories. Swept volume tests extrude AABBs along velocity vectors, detecting potential collisions earlier in the frame. For each candidate pair, binary search or root-finding algorithms compute the precise impact time $t \in [0, \Delta t]$ where surfaces first touch. The simulation then substeps integration up to impact time, resolves the collision, and continues integration for the remaining time. This process repeats until all impacts within the frame are handled.

```c
bool swept_aabb_intersect(AABB a, vec3 velocity_a, AABB b, vec3 velocity_b,
                          float* t_first, float* t_last) {
    vec3 relative_velocity = vec3_sub(velocity_a, velocity_b);
    
    *t_first = 0.0f;
    *t_last = 1.0f;
    
    for (int axis = 0; axis < 3; axis++) {
        if (fabsf(relative_velocity.v[axis]) < 1e-6f) {
            // Parallel to axis - check if overlapping
            if (a.max.v[axis] < b.min.v[axis] || a.min.v[axis] > b.max.v[axis]) {
                return false;
            }
        } else {
            float inv_vel = 1.0f / relative_velocity.v[axis];
            float t1 = (b.min.v[axis] - a.max.v[axis]) * inv_vel;
            float t2 = (b.max.v[axis] - a.min.v[axis]) * inv_vel;
            
            if (t1 > t2) {
                float temp = t1; t1 = t2; t2 = temp;
            }
            
            *t_first = fmaxf(*t_first, t1);
            *t_last = fminf(*t_last, t2);
            
            if (*t_first > *t_last) {
                return false;
            }
        }
    }
    
    return *t_first <= 1.0f;
}

void physics_tick_with_ccd(PhysicsWorld* world, float dt) {
    float remaining_time = dt;
    
    while (remaining_time > 1e-4f) {
        // Find earliest collision
        float min_toi = remaining_time;
        CollisionPair* earliest_pair = NULL;
        
        for (size_t i = 0; i < world->body_count; i++) {
            RigidBody* body_a = &world->bodies[i];
            AABB swept_a = aabb_expand(body_a->aabb, 
                                       vec3_scale(body_a->linear_velocity, 
                                                  remaining_time));
            
            for (size_t j = i + 1; j < world->body_count; j++) {
                RigidBody* body_b = &world->bodies[j];
                
                float t_first, t_last;
                if (swept_aabb_intersect(body_a->aabb, body_a->linear_velocity,
                                         body_b->aabb, body_b->linear_velocity,
                                         &t_first, &t_last)) {
                    float toi = t_first * remaining_time;
                    if (toi < min_toi) {
                        min_toi = toi;
                        earliest_pair = create_collision_pair(body_a, body_b);
                    }
                }
            }
        }
        
        // Integrate up to time of impact
        for (size_t i = 0; i < world->body_count; i++) {
            rigid_body_integrate(&world->bodies[i], min_toi);
        }
        
        if (earliest_pair) {
            // Resolve earliest collision
            resolve_collision(earliest_pair);
        }
        
        remaining_time -= min_toi;
    }
}
```

Cache coherency optimization exploits spatial and temporal locality to minimize memory bandwidth. Storing rigid body state in a structure-of-arrays layout rather than array-of-structures improves SIMD vectorization and cache line utilization. Processing collision pairs in spatial order rather than arbitrary hash table order increases the likelihood that accessed bodies remain cache-resident from previous iterations. Memory pool allocators for contact constraints and collision pairs reduce allocation overhead and improve memory locality by allocating contiguous blocks rather than scattered heap allocations.

Deterministic physics for networked multiplayer requires eliminating all sources of nondeterminism: floating-point rounding mode changes, uninitialized memory, pointer-based hash functions, and multithreaded race conditions. Compilation with consistent floating-point flags (`-ffp-contract=off` to disable fused multiply-add reordering, `-fno-associative-math` to prevent associativity transformations) ensures reproducible arithmetic across platforms. Replacing standard library transcendental functions (sin, cos, sqrt) with deterministic fixed-precision implementations or lookup tables eliminates platform-specific implementations. Sorting collision pairs by a deterministic key (body ID pairs) before processing ensures iteration order independence from memory addresses.

Parallelization of physics simulation exploits data parallelism in broad-phase queries, narrow-phase collision detection, and constraint solving. Broad-phase spatial hash queries partition the hash table across threads, with each thread processing a subset of buckets. Narrow-phase collision detection parallelizes over collision pairs since each pair's geometric test operates independently. Constraint solving presents greater challenges due to coupling—two constraints sharing a body cannot solve simultaneously without synchronization. Graph coloring algorithms partition constraints into independent sets where no two constraints share a body, allowing each set to solve in parallel. Iterative constraint solving then alternates between parallel solver passes over each color set and global synchronization barriers.

```rust
use rayon::prelude::*;

pub struct PhysicsWorld {
    bodies: Vec<RigidBody>,
    constraints: Vec<ContactConstraint>,
    constraint_graph: ConstraintGraph,
}

impl PhysicsWorld {
    pub fn solve_constraints_parallel(&mut self, iterations: usize) {
        let colors = self.constraint_graph.compute_coloring();
        
        for _ in 0..iterations {
            for color in &colors {
                // All constraints in this color are independent
                color.par_iter().for_each(|&constraint_idx| {
                    let constraint = &mut self.constraints[constraint_idx];
                    solve_contact_constraint(constraint, DT);
                });
            }
        }
    }
    
    pub fn broad_phase_parallel(&self) -> Vec<CollisionPair> {
        let spatial_hash = &self.spatial_hash;
        let bucket_count = spatial_hash.bucket_count;
        
        (0..bucket_count)
            .into_par_iter()
            .flat_map(|bucket_idx| {
                let bucket = &spatial_hash.buckets[bucket_idx];
                let mut pairs = Vec::new();
                
                for i in 0..bucket.len() {
                    for j in (i + 1)..bucket.len() {
                        if aabb_overlaps(&bucket[i].aabb, &bucket[j].aabb) {
                            pairs.push(CollisionPair {
                                body_a: bucket[i].id,
                                body_b: bucket[j].id,
                            });
                        }
                    }
                }
                
                pairs
            })
            .collect()
    }
    
    pub fn narrow_phase_parallel(&self, pairs: Vec<CollisionPair>) 
        -> Vec<ContactManifold> {
        pairs
            .par_iter()
            .filter_map(|pair| {
                let body_a = &self.bodies[pair.body_a];
                let body_b = &self.bodies[pair.body_b];
                
                if gjk_intersect(&body_a.shape, &body_b.shape) {
                    Some(generate_contact_manifold(body_a, body_b))
                } else {
                    None
                }
            })
            .collect()
    }
}
```

The Rust implementation leverages the `rayon` crate for work-stealing parallelism, automatically distributing iterations across available CPU cores. The borrow checker enforces safe concurrent access—constraint solving receives mutable references to distinct bodies since the graph coloring guarantees no sharing, while broad-phase and narrow-phase queries operate on immutable world state.

Failure mode analysis identifies catastrophic simulation behaviors and their mitigation strategies. Energy gain occurs when numerical integration errors cause total system energy to increase rather than dissipate, often manifesting as jittering contacts or objects spontaneously accelerating. Semi-implicit Euler integration provides better energy behavior than explicit Euler, while velocity damping (scaling velocities by 0.98 to 0.995 each frame) acts as a safety valve against runaway motion. Position-based post-stabilization applies small corrective impulses when constraints exceed tolerance thresholds, preventing drift accumulation.

Constraint explosion happens when solver iterations fail to converge, causing corrective impulses to oscillate rather than stabilize. This typically arises from over-constrained systems where conflicting constraints have no simultaneous solution, or from excessive stiffness where required impulse magnitudes exceed numerical precision. Diagnostic tools include per-constraint convergence metrics (tracking impulse magnitude changes across iterations) and visualization of constraint forces overlaid on the simulation. Mitigation strategies include increasing solver iterations, reducing constraint stiffness, or decomposing complex joints into multiple softer constraints.

Tunneling represents a geometric rather than numerical failure mode—fast-moving objects passing through thin geometry without collision detection. Continuous collision detection provides the complete solution but at substantial computational cost. Cheaper mitigation strategies include inflating collision geometry by a small margin (adding a "skin" thickness to AABBs), clamping maximum velocity magnitudes, or using implicit collision thickness where contact constraints activate before surfaces actually touch. For gameplay-critical scenarios such as projectile impacts, applying CCD selectively to high-velocity objects balances accuracy against performance.

Rigid body sleeping optimizes computational load by deactivating bodies that remain nearly stationary for multiple frames. A body enters sleep state when its linear and angular velocities fall below thresholds and remain there for a timeout period (typically 0.5 to 1.0 seconds). Sleeping bodies skip integration and collision detection entirely, participating only as immovable collision geometry. Waking occurs when a sleeping body receives an impulse from an active body or when an external force applies. Island tracking groups connected bodies through joints and contacts, allowing entire islands to sleep or wake atomically. This dramatically reduces active constraint count in large static environments where thousands of objects rest on terrain but only a handful experience active forces.
