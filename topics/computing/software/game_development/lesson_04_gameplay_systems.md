# Lesson 4: Gameplay Systems

## 1. First-Principles Intuition & Invariants

Every game, regardless of genre, engine, or platform, is fundamentally a real-time simulation of state. A fighting game tracks player health, combo counters, and hitbox activation windows measured in frames. A role-playing game maintains hundreds of interdependent variables: inventory weights, faction reputation deltas, skill cooldown timers, and dialog graph traversal history. Even the simplest puzzle game is managing a board configuration, an undo stack, and a win condition predicate. The craft of gameplay systems engineering is the discipline of modeling this state correctly, evolving it at a stable and deterministic rate, and projecting it onto screen, speakers, and haptic actuators without the simulation ever becoming aware of how it is being observed.

This last sentence contains the central architectural invariant of professional game development: **the simulation must be decoupled from its presentation**. This is not merely good software hygiene in the abstract sense that a web developer separates business logic from UI. In a game, the simulation runs at one frequency — perhaps 60 Hz for physics, or 20 Hz for AI pathfinding — while the renderer runs at a different, dynamically varying frequency. The audio engine consumes state asynchronously on a dedicated low-latency thread. The animation system blends between poses on its own timeline, interpolating between keyframes at whatever rate the display demands. If any of these concerns reach into the simulation and mutate state directly, the result is non-determinism, desync in networked games, and debugging nightmares that manifest only at specific frame rates.

The mental model that resolves this tension is the **update-then-render** pipeline, formalized as a strict temporal ordering. Each game loop tick gathers input, advances the simulation by a fixed or variable timestep, and then separately projects that simulated state into every output channel. The simulation owns no pointers into the renderer. The renderer holds a snapshot or a read view of the simulation state. This is not a performance optimization; it is a correctness invariant. Without it, gameplay systems cannot be unit-tested, replayed, or deterministically simulated, all of which are prerequisites for shipping a production game.

The historical route to this understanding was painful. Early arcade games, running on single-purpose hardware, wrote directly to video memory from within game logic. When hardware gained layers of abstraction, developers who carried this habit forward produced spaghetti architectures where `drawSprite()` calls were interspersed with `updateHealth()` calls in the same function. As games scaled in complexity through the 1990s, studios learned through failed shipping attempts that separating update from render was not optional. The id Software Quake engine (1996) made this separation explicit in its main loop, and virtually every professional engine since has preserved it.

Understanding this history matters because it explains why the patterns described in this lesson are not academic abstractions. Each one emerged as a direct response to a category of shipping failure. Hierarchical state machines exist because flat switch-case logic for player characters became unmaintainable at scale. The command pattern for input exists because raw key-polling coupled directly to behavior makes remapping, replay, and AI control impossible. Data-driven animation graphs exist because hardcoding blend trees in C++ made iteration by designers prohibitively expensive. Each pattern carries the scar tissue of a production lesson.

Before examining these patterns in depth, it is worth establishing the physical invariants that constrain all gameplay systems. Time in a game is discrete. The simulation advances in ticks, and every tick must complete within its budget — typically 16.6ms at 60 Hz. If any single system overshoots this budget, the frame is missed and the player perceives a stutter. This hard real-time constraint means that gameplay systems must be designed for predictable worst-case execution time, not just amortized average performance. A garbage collector pause, an uncached asset load, or a quadratic loop over dynamic game objects can all violate this constraint catastrophically. The engineering discipline required is closer to embedded systems programming than to typical server-side software, and senior engineers from those backgrounds adapt quickly once they internalize the frame budget as the fundamental unit of correctness.

---

## 2. Core Architecture & Mechanics

### The Game Loop and Timestep Models

The game loop is the heartbeat of every game, and its design determines the correctness and reproducibility of every system built on top of it. The naive implementation polls input, updates state, and renders in a free-running loop as fast as the hardware allows. This produces variable-rate simulation, where a character's jump height depends on the host machine's CPU speed — a category of bug that shipped in several early Windows ports of DOS games when clock speeds increased unexpectedly.

The fixed-timestep accumulator pattern, described precisely by Glenn Fiedler and now standard in production engines, resolves this by decoupling the simulation rate from the render rate. The loop accumulates real elapsed time and consumes it in fixed increments:

```c
/* Fixed-timestep game loop — production pattern */
#include <stdint.h>
#include <stdbool.h>

#define FIXED_DT_NS   16666667ULL   /* 60 Hz simulation tick, nanoseconds */
#define MAX_CATCHUP   5             /* prevent spiral-of-death on slow frames */

typedef struct {
    uint64_t accumulator_ns;
    uint64_t last_time_ns;
    uint32_t tick;
} GameClock;

typedef struct GameState GameState;

uint64_t platform_time_ns(void);   /* platform-specific monotonic clock     */
void     gather_input(GameState *gs);
void     simulate(GameState *gs, float dt);
void     render(const GameState *prev, const GameState *curr, float alpha);

void game_loop(GameState *gs) {
    GameClock clk = { .last_time_ns = platform_time_ns() };
    GameState prev_state = *gs;

    while (!gs->quit) {
        uint64_t now      = platform_time_ns();
        uint64_t frame_dt = now - clk.last_time_ns;
        clk.last_time_ns  = now;

        /* Clamp to prevent spiral-of-death after debugger pause or OS suspend */
        if (frame_dt > FIXED_DT_NS * MAX_CATCHUP)
            frame_dt = FIXED_DT_NS * MAX_CATCHUP;

        clk.accumulator_ns += frame_dt;

        gather_input(gs);

        while (clk.accumulator_ns >= FIXED_DT_NS) {
            prev_state          = *gs;
            simulate(gs, (float)FIXED_DT_NS * 1e-9f);
            clk.accumulator_ns -= FIXED_DT_NS;
            clk.tick++;
        }

        /* Alpha in [0,1) describes how far between ticks the render frame falls */
        float alpha = (float)clk.accumulator_ns / (float)FIXED_DT_NS;
        render(&prev_state, gs, alpha);
    }
}
```

The `alpha` value passed to `render` is the interpolation factor between the previous and current simulation snapshots. The renderer uses this to linearly interpolate all visual quantities — position, rotation, color — producing smooth animation even when the simulation runs at a fixed 60 Hz on a 144 Hz display. The simulation state remains completely deterministic because it only advances in exact fixed increments; the renderer is a pure function of two adjacent states and an interpolation parameter, with no side effects on simulation data.

The `MAX_CATCHUP` clamp deserves attention. Without it, if the system falls behind — say, an asset is paged in from disk mid-frame — the accumulator grows without bound, and the simulation attempts to run dozens of catchup ticks in a single frame, which makes the problem worse rather than better. This positive feedback loop is called the spiral of death, and the clamp breaks it by accepting that some simulation time was lost rather than allowing unbounded compensation.

### Hierarchical State Machines for Player Logic

A player character in a third-person action game might have hundreds of distinct behavioral states: idle, walk, run, sprint, jump, fall, land, attack_light, attack_heavy, hit_stun, knockdown, roll, climb, swim, die. The naive approach is a flat enumeration with a switch statement, which degenerates in maintainability as soon as states share transitions. The correct abstraction is a **hierarchical finite state machine (HFSM)**, in which states are organized in a tree and child states inherit the transitions of their parents.

The key invariant of an HFSM is that a transition defined on a parent state applies to all descendant states unless explicitly overridden. This means the `die` transition from "receive lethal damage" can be defined once at the root, rather than duplicated across the dozens of states from which death is reachable. Similarly, the `take_hit` transition that interrupts movement can live at the `Locomotion` parent node rather than being replicated in `walk`, `run`, and `sprint` individually.

```c
/* Minimal HFSM implementation suitable for player character logic */
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#define MAX_TRANSITIONS  16
#define MAX_CHILDREN     16
#define MAX_STATES       64

typedef uint32_t StateID;
#define STATE_INVALID  ((StateID)~0u)

typedef struct GameState GameState;

typedef struct {
    bool (*predicate)(const GameState *gs);
    StateID target;
    int     priority;    /* higher priority transitions evaluated first */
} Transition;

typedef struct HSMState {
    StateID      id;
    StateID      parent;
    StateID      children[MAX_CHILDREN];
    uint32_t     child_count;
    StateID      default_child;    /* entered when this state is entered */

    void (*on_enter)(GameState *gs);
    void (*on_update)(GameState *gs, float dt);
    void (*on_exit)(GameState *gs);

    Transition   transitions[MAX_TRANSITIONS];
    uint32_t     transition_count;
} HSMState;

typedef struct {
    HSMState  states[MAX_STATES];
    uint32_t  state_count;
    StateID   active;             /* deepest active leaf state */
} HSM;

/* Walk up the ancestor chain collecting transitions, evaluate highest-priority match */
static StateID hsm_evaluate_transitions(const HSM *hsm, const GameState *gs) {
    StateID cur = hsm->active;
    while (cur != STATE_INVALID) {
        const HSMState *s = &hsm->states[cur];
        for (uint32_t i = 0; i < s->transition_count; i++) {
            if (s->transitions[i].predicate(gs))
                return s->transitions[i].target;
        }
        cur = s->parent;
    }
    return STATE_INVALID;
}

static void hsm_exit_to_lca(HSM *hsm, GameState *gs, StateID lca) {
    StateID cur = hsm->active;
    while (cur != lca && cur != STATE_INVALID) {
        if (hsm->states[cur].on_exit)
            hsm->states[cur].on_exit(gs);
        cur = hsm->states[cur].parent;
    }
}

static void hsm_enter_from(HSM *hsm, GameState *gs, StateID target) {
    /* Enter the target state, then descend to its default leaf */
    StateID cur = target;
    while (cur != STATE_INVALID) {
        if (hsm->states[cur].on_enter)
            hsm->states[cur].on_enter(gs);
        StateID def = hsm->states[cur].default_child;
        if (def == STATE_INVALID) break;
        cur = def;
    }
    /* cur is now the deepest default leaf of target */
    hsm->active = cur;
}

void hsm_update(HSM *hsm, GameState *gs, float dt) {
    StateID next = hsm_evaluate_transitions(hsm, gs);
    if (next != STATE_INVALID) {
        /* Compute LCA by walking both paths — omitted here for brevity, */
        /* in production use a depth-annotated ancestor table             */
        hsm_exit_to_lca(hsm, gs, STATE_INVALID);
        hsm_enter_from(hsm, gs, next);
    }

    /* Execute update callbacks from root down to active leaf */
    StateID chain[MAX_STATES];
    uint32_t depth = 0;
    StateID cur = hsm->active;
    while (cur != STATE_INVALID) {
        chain[depth++] = cur;
        cur = hsm->states[cur].parent;
    }
    /* Reverse: root-first */
    for (int32_t i = (int32_t)depth - 1; i >= 0; i--) {
        if (hsm->states[chain[i]].on_update)
            hsm->states[chain[i]].on_update(gs, dt);
    }
}
```

This implementation reflects the production pattern used in engines like Unreal Engine's gameplay state machines and in custom action game engines. The transition evaluation walks up the ancestor chain so that parent-level transitions always fire regardless of which leaf state is currently active. The LCA (lowest common ancestor) calculation during transitions ensures that only the states between the active leaf and the branch point are exited and re-entered, preserving the state of sibling subtrees — critically important when a character temporarily enters a hit-stun state and then resumes locomotion without reinitializing sprint velocity.

### Input Handling: The Command Pattern

Raw input polling — reading keyboard scancodes or gamepad button bits directly in gameplay logic — creates a tight coupling that destroys three important capabilities: control remapping, input replay for debugging and competitive integrity, and AI-driven input injection. The command pattern replaces this with a layer of indirection that converts physical input events into semantic gameplay commands, which are then executed against the game state.

The architecture has three layers. The first is the **input source**, which could be a physical device, a network stream of opponent inputs, or an AI controller. The second is the **input binding table**, which maps physical events to abstract command identifiers, and which is serializable to disk for remapping support. The third is the **command queue**, a fixed-capacity ring buffer of command frames that the gameplay simulation consumes during its update.

```c
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

typedef enum {
    CMD_MOVE_LEFT  = 0,
    CMD_MOVE_RIGHT = 1,
    CMD_JUMP       = 2,
    CMD_ATTACK     = 3,
    CMD_ROLL       = 4,
    CMD_MAX        = 32
} CommandID;

typedef struct {
    uint32_t  frame;                   /* simulation tick this input belongs to */
    uint32_t  pressed;                 /* bitmask: bit N set if CMD_N pressed    */
    uint32_t  held;                    /* bitmask: bit N set if CMD_N held       */
    uint32_t  released;                /* bitmask: bit N set if CMD_N released   */
    int16_t   axis_x;                  /* analog: -32768..32767                  */
    int16_t   axis_y;
} InputFrame;

#define INPUT_QUEUE_CAPACITY  128      /* power-of-two for fast masking          */

typedef struct {
    InputFrame  frames[INPUT_QUEUE_CAPACITY];
    uint32_t    write_head;
    uint32_t    read_head;
} InputQueue;

static inline uint32_t iq_count(const InputQueue *q) {
    return q->write_head - q->read_head;
}

void iq_push(InputQueue *q, const InputFrame *f) {
    if (iq_count(q) == INPUT_QUEUE_CAPACITY) return;  /* drop if full */
    q->frames[q->write_head & (INPUT_QUEUE_CAPACITY - 1)] = *f;
    q->write_head++;
}

bool iq_pop(InputQueue *q, InputFrame *out) {
    if (iq_count(q) == 0) return false;
    *out = q->frames[q->read_head & (INPUT_QUEUE_CAPACITY - 1)];
    q->read_head++;
    return true;
}

/* Binding table: maps physical button index to CommandID */
typedef struct {
    uint32_t   physical_button;
    CommandID  command;
} Binding;

#define MAX_BINDINGS 64

typedef struct {
    Binding    bindings[MAX_BINDINGS];
    uint32_t   count;
    uint32_t   prev_physical;          /* physical bitmask from last frame      */
} InputMapper;

InputFrame input_mapper_process(InputMapper *m, uint32_t physical_now,
                                int16_t ax, int16_t ay, uint32_t tick) {
    InputFrame f = { .frame = tick, .axis_x = ax, .axis_y = ay };
    uint32_t changed = physical_now ^ m->prev_physical;

    for (uint32_t i = 0; i < m->count; i++) {
        uint32_t  bit = 1u << m->bindings[i].physical_button;
        CommandID cmd = m->bindings[i].command;
        uint32_t  mask = 1u << (uint32_t)cmd;

        if (physical_now & bit)       f.held    |= mask;
        if (changed & physical_now & bit) f.pressed  |= mask;
        if (changed & ~physical_now & bit) f.released |= mask;
    }

    m->prev_physical = physical_now;
    return f;
}
```

The `InputFrame` struct is the atom of gameplay input. Because it is a plain-old-data structure with no pointers, it can be serialized directly to a replay file, transmitted over a network connection for peer-to-peer multiplayer, or generated algorithmically by an AI controller. The gameplay simulation has no knowledge of which source produced the frame; it only consumes the queue. This decoupling is what makes deterministic replay possible: recording every `InputFrame` for an entire session and feeding it back into the simulation on the same hardware will reproduce every game event exactly, which is invaluable for reproducing reported bugs.

### Audio Systems: Threading, Buffering, and Game State Coupling

Audio in games is fundamentally a real-time scheduling problem. The audio hardware requires a steady stream of mixed PCM samples, typically in 256- or 512-sample chunks at 48 kHz, delivered to the driver every 5 to 10 milliseconds. If the callback misses its deadline even once, the user hears a pop or glitch. The game's main thread, which is performing physics, AI, and rendering in its frame budget, cannot be allowed to block the audio callback, nor can the audio callback afford to block waiting for game state reads.

The production solution is a **producer-consumer ring buffer** with lock-free semantics, combined with a **sound command queue** that the main thread writes and the audio thread reads. The main thread never calls audio APIs directly. Instead, when a gameplay event fires — a sword strike, an explosion, a dialog line — it enqueues a `SoundCommand` into the ring buffer. The audio thread dequeues these commands asynchronously, instantiates voice allocations from a pool, mixes the resulting streams into the output buffer, and applies a spatializer if the game is 3D.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <string.h>

/* Audio system: lock-free command queue for main-thread -> audio-thread comms */

typedef uint32_t SoundAssetID;

typedef enum {
    SOUND_CMD_PLAY,
    SOUND_CMD_STOP,
    SOUND_CMD_SET_VOLUME,
    SOUND_CMD_SET_POSITION,
} SoundCmdType;

typedef struct {
    SoundCmdType  type;
    uint32_t      voice_id;         /* opaque handle, 0 means allocate new       */
    SoundAssetID  asset;
    float         volume;           /* 0.0 .. 1.0                                */
    float         pitch;            /* 1.0 = normal, 2.0 = octave up             */
    float         pos[3];           /* world-space position for 3D spatialization*/
    bool          loop;
    uint32_t      start_tick;       /* sim tick to synchronize sound onset       */
} SoundCommand;

#define AUDIO_CMD_QUEUE_SIZE  512   /* power of two */

typedef struct {
    SoundCommand        buf[AUDIO_CMD_QUEUE_SIZE];
    atomic_uint         write_head;
    atomic_uint         read_head;
} AudioCommandQueue;

/* Called from main thread — no locks, only atomic increments */
bool audio_enqueue(AudioCommandQueue *q, const SoundCommand *cmd) {
    uint32_t w = atomic_load_explicit(&q->write_head, memory_order_relaxed);
    uint32_t r = atomic_load_explicit(&q->read_head,  memory_order_acquire);
    if (w - r >= AUDIO_CMD_QUEUE_SIZE) return false;   /* queue full */
    q->buf[w & (AUDIO_CMD_QUEUE_SIZE - 1)] = *cmd;
    atomic_store_explicit(&q->write_head, w + 1, memory_order_release);
    return true;
}

/* Called from audio thread */
bool audio_dequeue(AudioCommandQueue *q, SoundCommand *out) {
    uint32_t r = atomic_load_explicit(&q->read_head, memory_order_relaxed);
    uint32_t w = atomic_load_explicit(&q->write_head, memory_order_acquire);
    if (r == w) return false;
    *out = q->buf[r & (AUDIO_CMD_QUEUE_SIZE - 1)];
    atomic_store_explicit(&q->read_head, r + 1, memory_order_release);
    return true;
}

/* Minimal voice mixer: accumulates samples from active voices into output */
#define MAX_VOICES         64
#define AUDIO_SAMPLE_RATE  48000

typedef struct {
    SoundAssetID  asset;
    uint32_t      cursor;           /* sample offset into asset PCM data         */
    float         volume;
    float         pitch_ratio;
    float         pan_l, pan_r;
    bool          active;
    bool          loop;
} Voice;

typedef struct {
    Voice         voices[MAX_VOICES];
    uint32_t      voice_count;
    AudioCommandQueue *cmd_queue;
} AudioMixer;

/* Returns PCM data for a loaded asset — provided by asset system */
const float *audio_asset_samples(SoundAssetID id, uint32_t *out_len);

void audio_mixer_callback(AudioMixer *mx, float *out_l, float *out_r,
                          uint32_t frames) {
    memset(out_l, 0, frames * sizeof(float));
    memset(out_r, 0, frames * sizeof(float));

    /* Drain the command queue before mixing this buffer */
    SoundCommand cmd;
    while (audio_dequeue(mx->cmd_queue, &cmd)) {
        if (cmd.type == SOUND_CMD_PLAY) {
            for (uint32_t i = 0; i < MAX_VOICES; i++) {
                if (!mx->voices[i].active) {
                    mx->voices[i] = (Voice){
                        .asset       = cmd.asset,
                        .cursor      = 0,
                        .volume      = cmd.volume,
                        .pitch_ratio = cmd.pitch,
                        .pan_l       = 0.707f,
                        .pan_r       = 0.707f,
                        .active      = true,
                        .loop        = cmd.loop,
                    };
                    break;
                }
            }
        } else if (cmd.type == SOUND_CMD_STOP) {
            for (uint32_t i = 0; i < MAX_VOICES; i++) {
                if (mx->voices[i].asset == cmd.asset)
                    mx->voices[i].active = false;
            }
        }
    }

    /* Mix all active voices */
    for (uint32_t v = 0; v < MAX_VOICES; v++) {
        Voice *voice = &mx->voices[v];
        if (!voice->active) continue;

        uint32_t asset_len = 0;
        const float *samples = audio_asset_samples(voice->asset, &asset_len);
        if (!samples || asset_len == 0) { voice->active = false; continue; }

        for (uint32_t f = 0; f < frames; f++) {
            if (voice->cursor >= asset_len) {
                if (voice->loop) voice->cursor = 0;
                else { voice->active = false; break; }
            }
            float s    = samples[voice->cursor++] * voice->volume;
            out_l[f]  += s * voice->pan_l;
            out_r[f]  += s * voice->pan_r;
        }
    }
}
```

The `memory_order_release` on the write store and `memory_order_acquire` on the read load in `audio_enqueue` and `audio_dequeue` are not stylistic choices. They establish a happens-before relationship ensuring the audio thread never reads a partially-written `SoundCommand` struct. Because the buffer slots are written before the write-head is advanced, and the head is read with acquire semantics, the C11 memory model guarantees that the entire struct is visible to the audio thread by the time it reads the index. Replacing these with relaxed atomics would introduce a data race that manifests as corrupted asset IDs, typically infrequently and non-reproducibly — the class of bug that costs days to diagnose.

### Animation Blending: The State Machine as a Pose Graph

Modern character animation is not a sequence of sprites or hardcoded keyframes. It is a directed graph of **animation clips** connected by **blend nodes**, evaluated every render frame to produce a final pose — a hierarchical set of joint transforms from which the renderer derives the final skinned mesh. The key architectural insight is that this animation graph is entirely separate from the gameplay state machine described earlier. The gameplay HFSM decides what the character is *doing*. The animation graph decides how that is *visually expressed*, with smooth transitions, additive layering, and physics-driven procedural adjustment.

The fundamental operation is **linear blending** between two poses. For a skeleton with $N$ joints, each represented as a quaternion rotation and a 3D translation, the blend between pose $A$ and pose $B$ at parameter $t$ is:

$$q_i^{blended} = \text{slerp}(q_i^A, q_i^B, t), \quad \vec{p}_i^{blended} = \text{lerp}(\vec{p}_i^A, \vec{p}_i^B, t)$$

Spherical linear interpolation on the quaternion preserves unit norm and produces the shortest-path rotation arc, which linear quaternion interpolation followed by normalization approximates to first order but correctly handles numerically. In production, `nlerp` (normalized lerp) is often substituted for `slerp` on non-critical joints because it is significantly cheaper and the visual difference is imperceptible at frame rates above 30 Hz.

```c
#include <math.h>
#include <stdint.h>
#include <string.h>

typedef struct { float x, y, z, w; } Quat;
typedef struct { float x, y, z;    } Vec3;

typedef struct {
    Quat rotation;
    Vec3 translation;
} JointPose;

typedef struct {
    JointPose *joints;    /* pointer into a flat joint buffer */
    uint32_t   count;
} Pose;

static inline float quat_dot(Quat a, Quat b) {
    return a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w;
}

static inline Quat quat_negate(Quat q) {
    return (Quat){ -q.x, -q.y, -q.z, -q.w };
}

static Quat nlerp(Quat a, Quat b, float t) {
    /* Ensure shortest path by negating if dot product is negative */
    if (quat_dot(a, b) < 0.0f) b = quat_negate(b);
    float inv = 1.0f - t;
    Quat r = {
        inv*a.x + t*b.x, inv*a.y + t*b.y,
        inv*a.z + t*b.z, inv*a.w + t*b.w
    };
    float len = sqrtf(r.x*r.x + r.y*r.y + r.z*r.z + r.w*r.w);
    if (len < 1e-6f) return a;
    float inv_len = 1.0f / len;
    return (Quat){ r.x*inv_len, r.y*inv_len, r.z*inv_len, r.w*inv_len };
}

static Vec3 lerp3(Vec3 a, Vec3 b, float t) {
    return (Vec3){
        a.x + (b.x - a.x)*t,
        a.y + (b.y - a.y)*t,
        a.z + (b.z - a.z)*t
    };
}

void pose_blend(const Pose *a, const Pose *b, float t, Pose *out) {
    for
```
