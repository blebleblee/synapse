# Lesson 4: Networked Multiplayer, Synchronization

## 1. First-Principles Intuition & Invariants

Networked multiplayer is fundamentally a problem of distributed state under adversarial latency. Every player in a shared game world holds a local simulation running forward in time, while the ground truth of that world lives somewhere on a server—or is collectively negotiated across peers—separated from each client by a network path that is non-deterministic, asymmetric, and occasionally silent. The challenge is not to eliminate this gap; physics forbids it. The speed of light imposes a floor of roughly 30ms round-trip time for a cross-continental connection even on a perfect medium, and real networks add jitter, packet loss, and head-of-line blocking on top of that physical minimum. The engineering challenge is to make the gap *invisible*, or at least *tolerable*, through a system of coordinated lies that feel like truth.

The first invariant every networked game architect must internalize is that **no two clients can share the same wall-clock view of the world**. This is not an engineering failure; it is a theorem. It follows directly from the impossibility of perfectly synchronized clocks across distributed nodes—a consequence of the same reasoning that underpins Lamport clocks and the CAP theorem in distributed databases. What we have instead are approximations: NTP-synchronized clocks accurate to within a few milliseconds on well-behaved networks, and logical clocks (tick counters, sequence numbers) that impose a partial order on events without requiring absolute time agreement.

The second invariant is that **local responsiveness must never be held hostage to network round-trip time**. A game that waits for server acknowledgment before showing the player the result of their own input will feel broken at 50ms and unplayable at 150ms. The human perception system is acutely sensitive to the gap between motor action and visual feedback—studies consistently place the threshold for perceived input lag around 50–100ms for fast reflex actions. This means every mechanism the game server uses to maintain authoritative state must be paired with a corresponding client-side mechanism that speculates forward in time, applying the player's input immediately to a local prediction of the world and reconciling that prediction against server truth when it arrives.

The third invariant is the tension between **consistency and availability** applied to game state. In database terms, most multiplayer games choose eventual consistency for the vast majority of their state. Two players' positions can transiently disagree across clients so long as they converge quickly. But certain state transitions—a player death, a loot pickup, a checkpoint crossing—are non-idempotent and cannot be allowed to diverge at all. These require authoritative server arbitration, often at the cost of perceived latency. Designing the boundary between "eventually consistent" and "strongly consistent" game state is one of the most consequential architectural decisions in multiplayer systems, and getting it wrong in either direction produces either phantom pickups or unresponsive combat.

Understanding these three invariants before writing a line of network code will prevent an enormous class of architectural mistakes. With them in place, we can examine the standard client-server architecture that most commercial multiplayer games use, and then work through the specific mechanisms—state replication, lag compensation, and client-side prediction—that make it function at production quality.

---

## 2. Core Architecture & Mechanics

### Client-Server Topology and the Authoritative Server Model

The dominant pattern in competitive and cooperative multiplayer is the **dedicated authoritative server** model, in which a headless server process owns the canonical simulation and all clients send input, receive state deltas, and render a locally interpolated approximation of that truth. This architecture exists primarily as a cheat-prevention strategy: if no client owns the simulation, no client can directly manipulate physics, hit detection, or inventory state without the server's consent. It trades raw simplicity for security and consistency.

```
┌──────────────────────────────────────────────────────────────────┐
│                         GAME SERVER                              │
│                                                                  │
│   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │  Input      │───▶│  Authoritative│───▶│  State Snapshot  │   │
│   │  Ring Buffer│    │  Simulation  │    │  Broadcaster     │   │
│   └─────────────┘    │  (Tick Loop) │    └──────────────────┘   │
│                       └──────────────┘              │            │
└─────────────────────────────────────────────────────┼────────────┘
                                                       │
           ┌───────────────────────────────────────────┤
           │                                           │
           ▼                                           ▼
┌──────────────────────┐                   ┌──────────────────────┐
│      CLIENT A        │                   │      CLIENT B        │
│                      │                   │                      │
│  Local Prediction    │                   │  Local Prediction    │
│  Render (interp.)    │                   │  Render (interp.)    │
│  Input → UDP frame   │                   │  Input → UDP frame   │
└──────────────────────┘                   └──────────────────────┘
```

The server runs a fixed-timestep simulation loop, commonly at 20–128 ticks per second depending on the game genre. A first-person shooter demands tighter tick rates (64–128 Hz) because precise hit detection requires fine temporal resolution; a turn-based strategy game might run at 20 Hz or synchronize only on player actions. At each tick, the server processes all buffered inputs from connected clients, advances the simulation, and broadcasts a state update. The state update may be a full snapshot of relevant world state or a delta-encoded diff against the last acknowledged snapshot—a distinction with enormous bandwidth implications.

Clients run at their own render frame rate, which is decoupled from the server tick rate. This decoupling is essential: a client rendering at 144 FPS does not receive 144 state updates per second from a 64-tick server. Instead, it interpolates smoothly between the last two received server snapshots, extrapolating or holding the last known state for entities when packets arrive late. The client renders a world that is therefore always slightly in the past relative to server truth—typically 1–2 server ticks behind, to maintain a buffer against jitter.

### The Snapshot-Delta Protocol and State Representation

The network protocol between server and client must solve two problems simultaneously: it must transmit enough state for clients to render an accurate world, and it must do so within the bandwidth budgets of consumer internet connections (typically 1–5 Mbps upstream for game clients, with hard latency budgets around 50–100ms). Full-world snapshots on every tick are prohibitively expensive. The standard solution is **delta compression against an acknowledged baseline**.

The server maintains a per-client record of the most recently acknowledged snapshot. When constructing the next outbound packet, it encodes only the entities that changed since that baseline, using the difference from known client state. The client acknowledges received snapshots by embedding the sequence number of the last-received server frame into every input packet it sends back. If a packet is lost, the server falls back to diffing against an older baseline—the protocol degrades gracefully rather than stalling.

A production state replication system structures each entity as a flat, versioned property bag. Each field that participates in replication carries a dirty bit, and the serializer walks the entity list comparing current tick values against the baseline snapshot. Consider the following C structure representing a replicated player state:

```c
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#define MAX_PLAYERS 64
#define HISTORY_SIZE 128  /* must be power of two */

typedef struct {
    float    x, y, z;          /* world position    */
    float    vel_x, vel_y, vel_z;
    float    yaw, pitch;
    uint8_t  health;
    uint8_t  flags;             /* grounded, crouching, etc. */
    uint16_t animation_state;
} PlayerState;

typedef struct {
    uint32_t    tick;
    PlayerState players[MAX_PLAYERS];
    bool        active[MAX_PLAYERS];
} WorldSnapshot;

/* Ring buffer of snapshots for delta baseline selection */
typedef struct {
    WorldSnapshot frames[HISTORY_SIZE];
    uint32_t      head;         /* next write index  */
} SnapshotHistory;

static inline uint32_t snapshot_slot(uint32_t tick) {
    return tick & (HISTORY_SIZE - 1);
}

void snapshot_store(SnapshotHistory *hist, const WorldSnapshot *snap) {
    uint32_t slot = snapshot_slot(snap->tick);
    memcpy(&hist->frames[slot], snap, sizeof(WorldSnapshot));
    hist->head = slot;
}

const WorldSnapshot *snapshot_get(const SnapshotHistory *hist, uint32_t tick) {
    uint32_t slot = snapshot_slot(tick);
    if (hist->frames[slot].tick != tick) return NULL; /* evicted */
    return &hist->frames[slot];
}

/*
 * Writes a delta-encoded player list into `out`.
 * Returns the number of bytes written.
 * `baseline` may be NULL to request a full snapshot.
 */
size_t encode_snapshot_delta(
    uint8_t *out, size_t out_max,
    const WorldSnapshot *current,
    const WorldSnapshot *baseline)
{
    uint8_t *p = out;
    uint8_t *end = out + out_max;

    /* Header: current tick, baseline tick (0 if full snapshot) */
    uint32_t base_tick = baseline ? baseline->tick : 0;
    memcpy(p, &current->tick, 4); p += 4;
    memcpy(p, &base_tick, 4);     p += 4;

    for (int i = 0; i < MAX_PLAYERS; i++) {
        if (!current->active[i]) continue;

        bool changed = !baseline
            || !baseline->active[i]
            || memcmp(&current->players[i],
                      &baseline->players[i],
                      sizeof(PlayerState)) != 0;

        if (!changed) continue;
        if (p + 1 + sizeof(PlayerState) >= end) break; /* overflow guard */

        *p++ = (uint8_t)i;  /* player index as entity key */
        memcpy(p, &current->players[i], sizeof(PlayerState));
        p += sizeof(PlayerState);
    }

    *p++ = 0xFF; /* sentinel: end of entity list */
    return (size_t)(p - out);
}
```

This is a simplified but architecturally faithful encoding scheme. Production engines like Valve's Source engine and Epic's Unreal replicate properties at field granularity rather than per-entity granularity, using compile-time-generated property descriptors to serialize only the specific fields that changed. The principle is identical: compare current against baseline, emit only deltas, include enough framing to reconstruct the full state if any intermediate packet is lost.

### Client-Side Prediction and Input Acknowledgment

Client-side prediction is the mechanism by which a client applies its own input locally—advancing its own character's position, velocity, and state—without waiting for the server's response. The client maintains a local copy of the simulation for the player's own entity, running it forward at the same fixed timestep as the server. When an input is generated (a keypress, a mouse movement), the client both sends that input to the server and immediately applies it to the local simulation, rendering the result at the next frame.

The critical correctness requirement is that the client's local simulation must be **bit-for-bit identical** to the server's simulation given the same input sequence. Any divergence in floating-point behavior, physics step order, or random number generation will cause the prediction to drift from server truth, requiring larger corrections. This is why networked game physics engines go to great lengths to ensure deterministic simulation: fixed-point arithmetic, deterministic physics solvers, and seeded random number generators that are synchronized with the server.

Each input the client sends is tagged with the client's local tick counter. The server processes these inputs, advances its authoritative simulation, and echoes back the acknowledged tick in every outgoing state packet. When the client receives a server state update, it compares the acknowledged tick against its own prediction history. If the server's authoritative state at tick *T* matches the client's locally predicted state at tick *T*, the prediction was correct and nothing need change. If they differ—because another player collided with our character, or because the server corrected our velocity—the client must **re-simulate** all input from tick *T* forward to the current local tick, overwriting its prediction history.

```c
#define INPUT_BUFFER_SIZE 256   /* ring buffer of unacknowledged inputs */

typedef struct {
    uint32_t tick;
    float    move_forward;      /* -1.0 to 1.0 */
    float    move_right;
    float    yaw_delta;
    float    pitch_delta;
    uint8_t  buttons;           /* jump, crouch, fire bitmask */
} ClientInput;

typedef struct {
    float x, y, z;
    float vel_x, vel_y, vel_z;
    float yaw, pitch;
    bool  grounded;
} LocalPlayerState;

typedef struct {
    ClientInput      inputs[INPUT_BUFFER_SIZE];
    LocalPlayerState predicted[INPUT_BUFFER_SIZE]; /* state *after* applying input[i] */
    uint32_t         oldest_unacked_tick;
    uint32_t         local_tick;
} PredictionBuffer;

static inline uint32_t pbuf_slot(uint32_t tick) {
    return tick & (INPUT_BUFFER_SIZE - 1);
}

/*
 * Apply a single input to a player state using a fixed timestep.
 * This function MUST be identical to the server-side simulation step.
 */
void simulate_step(
    LocalPlayerState *state,
    const ClientInput *input,
    float dt)
{
    const float accel  = 20.0f;
    const float gravity = -20.0f;
    const float jump_vel = 7.0f;

    state->yaw   += input->yaw_delta;
    state->pitch += input->pitch_delta;

    float cos_yaw = cosf(state->yaw);
    float sin_yaw = sinf(state->yaw);

    float wish_x = cos_yaw * input->move_forward - sin_yaw * input->move_right;
    float wish_z = sin_yaw * input->move_forward + cos_yaw * input->move_right;

    state->vel_x += wish_x * accel * dt;
    state->vel_z += wish_z * accel * dt;

    if (!state->grounded)
        state->vel_y += gravity * dt;

    if (state->grounded && (input->buttons & 0x01)) {
        state->vel_y = jump_vel;
        state->grounded = false;
    }

    state->x += state->vel_x * dt;
    state->y += state->vel_y * dt;
    state->z += state->vel_z * dt;

    /* Simplified ground plane */
    if (state->y <= 0.0f) {
        state->y = 0.0f;
        state->vel_y = 0.0f;
        state->grounded = true;
    }
}

/*
 * Called when a server authoritative state arrives for `acked_tick`.
 * Corrects local prediction by re-simulating from the acked tick forward.
 */
void reconcile_prediction(
    PredictionBuffer *pbuf,
    const LocalPlayerState *server_state,
    uint32_t acked_tick,
    float dt)
{
    uint32_t slot = pbuf_slot(acked_tick);

    /* Check if our prediction matched server truth (fast path) */
    LocalPlayerState *our_pred = &pbuf->predicted[slot];
    if (memcmp(our_pred, server_state, sizeof(LocalPlayerState)) == 0) {
        pbuf->oldest_unacked_tick = acked_tick + 1;
        return;
    }

    /* Mismatch: overwrite with server state and re-simulate forward */
    LocalPlayerState corrected = *server_state;
    uint32_t resim_tick = acked_tick + 1;

    while (resim_tick <= pbuf->local_tick) {
        uint32_t rslot = pbuf_slot(resim_tick);
        simulate_step(&corrected, &pbuf->inputs[rslot], dt);
        pbuf->predicted[rslot] = corrected;
        resim_tick++;
    }

    pbuf->oldest_unacked_tick = acked_tick + 1;
}
```

The reconciliation path is the heart of the prediction system. Notice that it re-simulates every tick from the correction point to the present local tick—this loop can span 50–100 ticks if round-trip latency is 100–200ms at a 60-tick server. For simple character movement, this is cheap. For complex physics objects with rigid body dynamics, re-simulation cost can become a performance concern, which is why production engines aggressively limit what entities participate in client-side prediction.

### Lag Compensation for Hit Detection

Client-side prediction solves the problem of *your own* responsiveness. It does not solve the problem of shooting *other players*. Consider the geometry of the problem: when a player fires their weapon, their client renders other players at a position that is 50–150ms in the past (the interpolation delay plus network latency). If the server were to validate the shot against current server positions, the shot would appear to miss even though the player's crosshair was squarely on the target from their perspective. This would be strictly correct from a simulation standpoint but would feel profoundly wrong to the player.

Lag compensation resolves this by maintaining a **rewind buffer** of world state on the server. When a fire event arrives from a client, the server notes the client's estimated latency and rewinds all other entities to where they were at the moment the client fired. It then performs hit detection in that rewound state, attributing a hit if the projectile intersects any entity in the historical world snapshot. After the hit check, the server snaps back to the current tick and applies the damage.

```c
#define REWIND_BUFFER_TICKS 128

typedef struct {
    float x, y, z;
    float hitbox_half_w;
    float hitbox_half_h;
} EntityHitbox;

typedef struct {
    uint32_t     tick;
    EntityHitbox entities[MAX_PLAYERS];
    bool         active[MAX_PLAYERS];
} HitboxSnapshot;

typedef struct {
    HitboxSnapshot frames[REWIND_BUFFER_TICKS];
} RewindBuffer;

static inline uint32_t rewind_slot(uint32_t tick) {
    return tick & (REWIND_BUFFER_TICKS - 1);
}

void rewind_store(RewindBuffer *rb, const HitboxSnapshot *snap) {
    memcpy(&rb->frames[rewind_slot(snap->tick)], snap, sizeof(HitboxSnapshot));
}

/*
 * Perform lag-compensated hit detection.
 * `fire_origin` and `fire_dir` are in world space.
 * `client_tick` is the tick the client believed the shot occurred at.
 * Returns the index of the hit player, or -1 if none.
 */
int lag_compensated_raycast(
    const RewindBuffer *rb,
    uint32_t client_tick,
    int shooter_index,
    float origin_x, float origin_y, float origin_z,
    float dir_x,    float dir_y,    float dir_z)
{
    uint32_t slot = rewind_slot(client_tick);
    const HitboxSnapshot *snap = &rb->frames[slot];

    if (snap->tick != client_tick) return -1; /* snapshot evicted */

    for (int i = 0; i < MAX_PLAYERS; i++) {
        if (!snap->active[i] || i == shooter_index) continue;

        const EntityHitbox *box = &snap->entities[i];

        /* Axis-aligned slab intersection (simplified AABB ray test) */
        float dx = box->x - origin_x;
        float dy = box->y - origin_y;
        float dz = box->z - origin_z;

        /* Project ray against box extents — full AABB test omitted for brevity */
        float dot = dx * dir_x + dy * dir_y + dz * dir_z;
        if (dot < 0.0f) continue;

        float dist_sq = (dx*dx + dy*dy + dz*dz) - dot*dot;
        float r = box->hitbox_half_w;
        if (dist_sq < r * r) return i;
    }

    return -1;
}
```

Lag compensation is the source of the classic "shot-around-corners" phenomenon that competitive players have debated for decades. Because the server validates shots against a historical position, a player can be killed by a shot fired by someone who, from the shooter's perspective, had a valid line of sight, but from the victim's perspective the shooter had already moved behind cover. Both perspectives are locally correct; the server chose the shooter's perspective as authoritative. Most games accept this trade-off because it makes aiming feel responsive to the shooter, and the overwhelming majority of players are shooters more often than they are the target being shot.

### Interpolation and Entity Smoothing

For entities other than the local player, clients cannot predict future positions (they receive no input from those entities) and so must interpolate between received server snapshots. The standard approach is to maintain a small delay—typically 100–150ms, covering one to two jitter spans—and render entities at a point in time that always has at least two surrounding known snapshots. This converts the choppy, irregular cadence of network packet arrival into a smooth visual trajectory.

```c
typedef struct {
    uint32_t tick;
    float    x, y, z;
    float    yaw, pitch;
} RemoteEntitySample;

#define INTERP_BUFFER_SIZE 32

typedef struct {
    RemoteEntitySample samples[INTERP_BUFFER_SIZE];
    int                count;
    int                head;
} EntityInterpBuffer;

void interp_push(EntityInterpBuffer *buf, const RemoteEntitySample *s) {
    buf->samples[buf->head % INTERP_BUFFER_SIZE] = *s;
    buf->head++;
    if (buf->count < INTERP_BUFFER_SIZE) buf->count++;
}

/*
 * Returns interpolated position for a render timestamp expressed as a
 * fractional tick (e.g., tick 1042.37 means 37% of the way between
 * tick 1042 and tick 1043).
 */
bool interp_sample(
    const EntityInterpBuffer *buf,
    float render_tick,
    float *out_x, float *out_y, float *out_z)
{
    uint32_t tick_lo = (uint32_t)render_tick;
    uint32_t tick_hi = tick_lo + 1;
    float    alpha   = render_tick - (float)tick_lo;

    const RemoteEntitySample *lo = NULL, *hi = NULL;

    int start = buf->head - buf->count;
    for (int i = start; i < buf->head; i++) {
        const RemoteEntitySample *s = &buf->samples[i % INTERP_BUFFER_SIZE];
        if (s->tick == tick_lo) lo = s;
        if (s->tick == tick_hi) hi = s;
    }

    if (!lo || !hi) return false; /* insufficient data, hold or extrapolate */

    *out_x = lo->x + alpha * (hi->x - lo->x);
    *out_y = lo->y + alpha * (hi->y - lo->y);
    *out_z = lo->z + alpha * (hi->z - lo->z);
    return true;
}
```

The interpolation delay is a tunable parameter with a direct trade-off: larger delay produces smoother motion at the cost of rendering a more out-of-date world. Shorter delay produces more reactive but potentially jittery rendering. Modern engines dynamically adjust this delay based on measured jitter variance, stretching the buffer during periods of high jitter and shrinking it when the connection stabilizes.

---

## 3. High-Performance Optimization & Failure Modes

### Bandwidth Budgeting and Area-of-Interest Filtering

A naïve server that broadcasts all entity state to all clients scales as O(N²) in bandwidth—each of N clients receives updates about N entities. At 64 players, with each entity transmitting position, velocity, orientation, and animation state at 64 Hz, this produces tens of megabits per second of server egress. Production servers enforce **area-of-interest (AOI) filtering**: each client receives state only for entities within a relevance radius or visibility frustum. The server maintains a spatial index (typically a grid or k-d tree) over entity positions and, once per tick, queries each client's AOI to build its outbound entity set.

AOI filtering introduces a correctness hazard: if an entity moves into a client's AOI between the last tick and the current tick, the client has no baseline state for it. The server must transmit a full snapshot for newly relevant entities and handle the transition gracefully on the client, spawning or popping in the entity at its current position rather than interpolating from a nonexistent history. Conversely, when an entity leaves AOI, the server sends a "destroy" notification and the client removes it from its local world state.

Bandwidth can be further reduced through quantization. A 32-bit float position can be replaced with a fixed-point integer encoding covering only the game world's extent. If a world is 4096 units across and 16-bit integers are used, the resolution is 0.0625 units—sufficient for most game mechanics. Velocity and orientation are similarly quantizable. Valve's Source engine represents entity positions as 23-bit fixed-point values and angular components as 8–16-bit values, achieving significant compression over raw float transmission.

### Jitter Buffers, Packet Loss, and Connection Quality

UDP is the standard transport for game state because it delivers the best latency characteristics—there is no head-of-line blocking, no retransmission-induced stalls, and packet ordering is handled by the application. The cost is unreliability: packets can arrive out of order, be duplicated, or be lost entirely. The game network layer must handle all three cases explicitly.

Out-of-order and duplicate packets are handled by sequence numbers. Every packet carries a monotonically increasing sequence number; the receiver discards any packet whose sequence number is less than or equal to the highest already processed. Packet loss recovery is handled through redundancy rather than retransmission. Sending the last two or three input states in every outgoing client packet means that a single lost packet does not cause the server to lose a tick of input—it recovers from the next packet's redundant payload. This is far preferable to TCP's retransmission, which introduces a stall proportional to the round-trip time.

When packet loss is severe or the connection goes entirely silent, the simulation must not simply freeze. The server applies the last received input from the affected client for a small number of ticks (typically 2–8) before flagging the client as timed out and teleporting the character to a safe state or removing it from the world. On the client side, entities for which recent state has not arrived are extrapolated from their last known velocity for a brief window, then frozen or removed. Extrapolation produces visually smoother behavior than abrupt holds but can diverge badly if an entity reverses direction; most engines cap extrapolation to 100–200ms before switching to a hold.

### Clock Synchronization and Round-Trip Estimation

For the prediction and lag-compensation systems to function, both server and client must agree on a mapping between client ticks and server ticks. This requires the client to measure its round-trip time to the server and to estimate the offset between its local clock and the server's tick counter. The standard approach is a simple ping protocol: the client sends a timestamped probe, the server echoes it with the current server tick, and the client computes round-trip time as `local_receive_time - local_send_time`. The client's clock offset relative to the server is estimated as `server_tick - (local_send_tick + rtt / 2)`.

```c
typedef struct {
    uint32_t local_send_tick;
    uint32_t local_recv_tick;
    uint32_t server_tick_at_recv;
} PingSample;

typedef struct {
    int32_t  clock_offset;   /* server_tick - local_tick (smoothed) */
    uint32_t rtt_ticks;      /* smoothed round-trip in ticks        */
} ClockEstimate;

void update_clock_estimate(
    ClockEstimate *est,
    const PingSample *sample,
    float alpha)          /* EMA smoothing factor, e.g. 0.1 */
{
    uint32_t rtt  = sample->local_recv_tick - sample->local_send_tick;
    int32_t  offset = (int32_t)sample->server_tick_at_recv
                    - (int32_t)(sample->local_send_tick + rtt / 2);

    est->rtt_ticks  = (uint32_t)((1.0f - alpha) * est->rtt_ticks  + alpha * rtt);
    est->clock_offset = (int32_t)((1.0f - alpha) * est->clock_offset + alpha * offset);
}
```

An exponential moving average smooths out per-sample noise. The client uses this estimate to stamp its outgoing inputs with a predicted server tick, allowing the server to place inputs into the correct simulation slot without large accumulation errors.

### Consistency Models for Shared World State

The deepest architectural failure mode in multiplayer game design is applying a uniform consistency model to state that has wildly different requirements. Character positions are amenable to eventual consistency—momentary disagreements between clients resolve within a tick or two and are imperceptible at reasonable latency. But shared resource state—loot drops, capture points, ammo pickups, door locks—is non-idempotent. If two clients each believe they picked up the same health pack, and both transitions are allowed to commit, the game economy is broken.

For these strongly-consistent transitions, the correct architecture is a **request-grant protocol**: the client displays optimistic feedback (a sound effect, a brief UI flash) but does not commit the state change until the server confirms it. If the server denies the request (because another client won the race), the client rolls back the optimistic state. The key is that the rollback must be visually forgiving—a brief animation or a "picked up by [player]" notification—rather than a jarring teleport or state reset.

A harder case is multiplayer physics: rigid bodies that multiple clients can interact with. Peer-to-peer shared physics is essentially an unsolved problem in real-time games at low latency. The practical engineering answer is to designate a single "physics owner" per dynamic object, typically the client currently in contact with it, and have that client run authoritative physics and replicate the result to others. Ownership transfers when a different client takes control, and the transition is smoothed with a brief interpolation window. This sacrifices strict consistency for responsiveness and is the approach used by most physics-rich multiplayer games.

### Cheating, Validation, and Trust Boundaries

The authoritative server model is a cheat-prevention strategy, but it only works if the server independently validates every client claim rather than trusting client-provided state. Clients send **inputs**, not **positions**. If a client sends a position update directly, the server must reject it. The server derives positions from inputs through its own simulation, and any deviation between client-reported state and server-derived state is evidence of tampering.

Speed hacking—injecting inputs at a higher rate than real time allows—is detected by tracking the ratio of simulated ticks to elapsed wall-clock time per client connection. A legitimate client advancing at 64 ticks per second will not, over a five-second window, have submitted 1,000 input frames. Rate anomalies trigger increasing scrutiny: at first, excess inputs are dropped; persistent violations trigger a disconnection and flag the account for review.

Aim assistance programs (aimbots) are significantly harder to detect server-side because they produce valid inputs—the mouse moves, the crosshair arrives on target, the fire button is pressed—at trajectories that happen to be inhumanly precise. Statistical analysis of aim trajectories, flick speed, and reaction time distributions can identify outliers, but this is ultimately a probabilistic defense requiring a continuous arms race with the cheating ecosystem. The network architecture can constrain the problem—by ensuring that client-side code has no access to other players' positions beyond what is needed to render them—but cannot eliminate it.

The final consideration is replay and anti-tamper integrity. Competitive games increasingly record full input streams server-side and can replay any match deterministically to verify that outcomes were physically plausible. This deterministic replay capability is valuable not only for anti-cheat but for debugging, spectating, and post-match analysis. It requires the same determinism invariant as client-side prediction: the simulation must produce identical output from identical input across all platforms and runtime environments. This is a demanding engineering constraint that rules out non-deterministic concurrency in the physics pipeline and demands careful management of floating-point modes, ordering guarantees, and random number state.

The systems described in this lesson—delta-compressed snapshot replication, client-side prediction with server reconciliation, lag-compensated hit detection, and AOI-filtered broadcast—constitute the standard toolkit that ships in every major commercial multiplayer game. Each mechanism exists as a direct engineering response to a physical or mathematical constraint, and each introduces its own failure mode that the adjacent mechanisms must absorb. The craft of multiplayer network architecture is in calibrating this system of compensating mechanisms so that the aggregate behavior produces a world that feels simultaneously fair, responsive, and consistent, despite the fundamental impossibility of making it truly any of those things.
