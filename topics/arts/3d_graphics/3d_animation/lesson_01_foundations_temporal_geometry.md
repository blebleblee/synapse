# Lesson 1: Foundations of Temporal Geometry

## 1. First-Principles Intuition & Invariants

Animation is temporal geometry—the art of describing how position, rotation, scale, and shape evolve across time. Unlike static modeling, where a single mesh exists in a frozen moment, animation requires us to think in four dimensions: the three spatial axes plus the fourth axis of time. The fundamental problem is deceptively simple: given a starting state at frame 0 and an ending state at frame N, how do we compute the intermediate frames that make motion appear fluid, natural, and intentional to human perception?

At its core, keyframe animation rests on a principle borrowed from classical animation and cel painting: the animator defines key poses at important moments, and the computer interpolates the frames between them. This interpolation—the mathematical bridge across temporal gaps—is where temporal geometry begins. The quality of that bridge determines whether motion feels alive or robotic, whether a character's gesture reads as confident or hesitant, whether a camera pan feels cinematic or jarring.

Before diving into mathematics, we must establish the perceptual constraints that govern all animation. The human eye perceives continuous motion at approximately 24 frames per second in cinema, 30 fps in broadcast video, and 60 fps in interactive media. This is not arbitrary. At 24 fps, frame intervals are 41.67 milliseconds apart. Our visual system integrates these discrete images into the illusion of smooth continuity through a phenomenon called apparent motion. Below 18 fps, most viewers consciously perceive flicker rather than motion. Above 60 fps, the perceptual gain diminishes steeply—the investment in rendering additional frames yields minimal improvement in perceived smoothness. This constraint shapes every interpolation decision we make.

Temporal geometry also inherits a critical principle from physics: the distinction between position (where an object is), velocity (how fast it is moving), and acceleration (how quickly velocity changes). These three properties are not independent. A keyframe specifies position at a moment in time, but the animator's intent may encode velocity or acceleration information through the choice of interpolation curve. A linear interpolation between two keyframes implies constant velocity—the object moves at a uniform speed from start to finish. A curved interpolation implies variable velocity: the object might accelerate initially, decelerate near the end, or follow a complex velocity profile. The animator's choice of curve type encodes intention about the quality of motion.

The mathematical foundation of temporal geometry rests on parametric curves. A parametric curve is a function that maps a single parameter—in our case, time normalized to a range [0, 1]—to a three-dimensional position or rotation value. Rather than describing y as a function of x, we describe position as a function of time. This elegance allows us to define motion in a coordinate-independent way: the same curve equation can describe motion in any direction through three-dimensional space.

Consider a simple example. At keyframe 0, a character's hand is at position (0, 0, 0). At keyframe 10, the hand is at position (10, 5, 0). We need to animate the hand's path from start to finish across 10 frames. If we use linear interpolation, the hand moves at constant velocity: each frame, it advances by exactly (1, 0.5, 0). The motion is predictable and mechanical. If instead we use a smooth curve that accelerates initially and decelerates near the end, the hand feels alive—it reaches the destination with weight and intention, as if pulled by intention rather than pushed by constant force.

This distinction between interpolation types is not merely aesthetic. It directly impacts the perceived purpose and personality of motion. Linear motion feels mechanical or robotic. Ease-in, ease-out motion (acceleration at the start, deceleration at the end) feels natural and intentional. Overshoot motion (oscillating slightly past the destination before settling) feels playful or elastic. The animator's choice of curve is a vocabulary for expressing intent through mathematics.

The second critical invariant concerns the Nyquist theorem adapted to temporal sampling. In signal processing, the Nyquist frequency states that a signal sampled at frequency f can only accurately represent content up to f/2. Applied to animation, this means that at 24 fps, the minimum oscillation we can represent is one complete cycle every 2 frames (a frequency of 12 Hz). If a motion contains higher-frequency content—rapid jitter, subtle vibration, or noise—sampling at 24 fps will alias that motion into false lower-frequency artifacts. This is why motion capture data from live actors, which contains imperceptible high-frequency tremor, must be filtered or smoothed before animation; unfiltered, it creates an uncanny, twitchy appearance. The animator must be aware of the temporal bandwidth available at the chosen frame rate and compose motion accordingly.

The third invariant concerns continuity. At a keyframe transition, the interpolated curve must maintain positional continuity—the position at the end of one curve must equal the position at the start of the next curve, with no discontinuous jump. More subtly, animators often demand velocity continuity (the curve's first derivative is continuous across keyframes) to avoid sudden jerks in motion. The most demanding constraint is acceleration continuity (the curve's second derivative is continuous), which produces motion that feels mathematically smooth and natural. The level of continuity required depends on the context: a simple sliding object might need only positional continuity; a character's limb motion typically requires velocity continuity; a camera's motion often demands acceleration continuity to avoid perceptible hitches.

## 2. Core Architecture & Mechanics

### Keyframes as State Vectors

A keyframe in modern animation software is not simply a timestamp and a position. It is a complete encapsulation of an object's transformation state at a moment in time. This state includes position (three floats for x, y, z), rotation (typically stored as a quaternion, four floats), and scale (three floats, one for each axis unless uniform scaling). Additional properties—material color, opacity, shape deformation weights—can be keyframed too. At its most abstract, a keyframe is a point in a high-dimensional configuration space: the space of all possible object states.

When the animator sets two keyframes 10 frames apart, they are creating a temporal interval in which the object transitions from one point in configuration space to another. The interpolation routine must travel through that space according to a chosen path. The simplest path is a straight line: linear interpolation. More sophisticated paths curve through space according to the animator's specifications via control points or curve parameters.

The mathematical representation of a transformation state typically uses a 4×4 homogeneous transformation matrix:

```text
[ R_xx  R_xy  R_xz  T_x ]
[ R_yx  R_yy  R_yz  T_y ]
[ R_zx  R_zy  R_zz  T_z ]
[   0     0     0     1  ]
```

Here, the 3×3 submatrix R encodes rotation and scale (scale appears as the magnitude of each row), and the rightmost column encodes translation. This matrix can be applied to any point: multiplying the matrix by a point vector yields the point's transformed position. However, directly interpolating matrix elements frame-by-frame produces incorrect results. If you linearly interpolate between two rotation matrices, intermediate frames contain skewing and non-uniform scaling artifacts. Instead, we must decompose the transformation into its components—translation, rotation, and scale—interpolate each separately using appropriate curves, and recompose the matrix each frame.

### Linear Interpolation: The Foundation

Linear interpolation is the simplest and most fundamental curve type. Given two keyframe values v0 at time t0 and v1 at time t1, linear interpolation at time t (where t0 ≤ t ≤ t1) is:

v(t) = v0 + (v1 - v0) × (t - t0) / (t1 - t0)

This formula is so common that it has a standard abbreviation: lerp(v0, v1, α), where α = (t - t0) / (t1 - t0) ranges from 0 to 1. When α = 0, the result is v0. When α = 1, the result is v1. In between, the value advances linearly.

Linear interpolation has several properties. First, it guarantees positional continuity: the curve passes through both keyframes exactly. Second, it is computationally trivial—a single multiply-add operation per component. Third, it produces constant velocity: an object moving along a linear interpolation travels the same distance each frame. This last property is why linear motion feels mechanical. In nature, objects rarely sustain constant velocity without external force; they accelerate, reach a desired speed, and decelerate. Linear motion violates human intuition about how forces work.

For rotations, direct linear interpolation of matrix elements fails catastrophically. Instead, rotations are typically represented as quaternions, and quaternion interpolation (called slerp for spherical linear interpolation) is used. A quaternion represents a rotation as a unit vector in four-dimensional space: (w, x, y, z), where w is the scalar part and (x, y, z) is the vector part. Spherical linear interpolation interpolates along the arc of a four-dimensional unit sphere, ensuring that the rotation maintains constant angular velocity and that the magnitude of the quaternion (which encodes the rotation's validity) is preserved.

### Bézier Curves: Animator's Language

Bézier curves are the animators' tool of choice because they offer an intuitive visual and mathematical interface. A cubic Bézier curve is defined by four control points: two endpoints (P0 and P3, which the curve passes through) and two control handles (P1 and P2, which shape the curve's curvature). The curve is defined parametrically as:

B(t) = (1-t)³ P0 + 3(1-t)²t P1 + 3(1-t)t² P2 + t³ P3

where t ranges from 0 to 1. At t=0, the curve is at P0. At t=1, the curve is at P3. The control points P1 and P2 never lie on the curve itself; instead, they exert magnetic influence over the curve's path. The closer P1 is to P0, and the closer P2 is to P3, the straighter the curve becomes. When P1 is far from P0 and P2 is far from P3, the curve bulges dramatically toward the control points.

Animators interact with Bézier curves through visual handles in the curve editor. In software like Blender, Maya, or Cinema 4D, each keyframe displays two handles—the in-handle and out-handle—that control the curve's slope approaching and leaving the keyframe. By dragging these handles, animators shape the motion without thinking about mathematics. The underlying representation is still a Bézier curve, but the interface is pure geometry.

A critical property of Bézier curves is their local control: moving a control point affects only the curve segment adjacent to that point. Moving P1 changes the curve between P0 and P3 but does not affect other segments. This locality is essential for practical animation workflows; animators adjust individual keyframe transitions without accidentally rippling changes through the entire timeline.

Bézier curves offer another advantage: they provide an intuitive encoding of velocity. The tangent vector of the Bézier curve at any point is proportional to the curve's first derivative. This tangent direction and magnitude encode the velocity: direction tells us which way the object is moving, and magnitude tells us how fast. By adjusting the handle lengths, animators directly modulate velocity. A longer handle means steeper slope, which means higher velocity. A shorter handle means lower velocity. This is why Bézier curves feel like a natural language for animation: the visual geometry directly encodes kinematic information.

The Bézier curve naturally maintains positional continuity at keyframe boundaries (the curve passes through the endpoints by definition). If the animator wants velocity continuity—ensuring no jerk at the transition—the out-handle of one keyframe must be collinear with the in-handle of the next keyframe, and they should have proportional lengths. Most animation software offers an auto-tangent mode that enforces this constraint automatically, producing smooth transitions between keyframes without animator intervention.

### Spline Curves: Extended Smoothness

While Bézier curves offer local control, they become tedious when animating across many keyframes. Each keyframe requires two handle adjustments, and maintaining smooth transitions across numerous keyframes is labor-intensive. Spline curves—particularly cubic splines and B-splines—offer an alternative. A spline is a piecewise polynomial curve composed of multiple cubic segments, where each segment shares control points with its neighbors in a way that automatically enforces smoothness.

Catmull-Rom splines are particularly popular in animation software. A Catmull-Rom curve passes through all its control points (unlike B-splines, which are approximating curves that generally do not pass through control points). The advantage is intuitive: keyframes are control points that the curve must hit. The curve is constructed so that the curvature between any four consecutive points P0, P1, P2, P3 is automatically smooth—the curve passes through P1 at one end and P2 at the other, with curvature influenced by P0 and P3.

Mathematically, a cubic Catmull-Rom segment between P1 and P2 (influenced by P0 and P3) is defined as:

P(t) = 0.5 × [ 2P1 + (-P0 + P2)t + (2P0 - 5P1 + 4P2 - P3)t² + (-P0 + 3P1 - 3P2 + P3)t³ ]

where t ranges from 0 to 1. The formula automatically encodes smoothness: consecutive segments share velocity continuity because the formula is constructed to ensure the tangent at P1 from the left segment matches the tangent at P1 from the right segment.

The beauty of spline curves is their global coherence: adjusting a single control point influences all adjacent segments, creating waves of adjustment that feel natural for organic motion. Splines are less intuitive to understand than Bézier curves because the control point is not visually connected to the curve via handles; instead, the curve's shape emerges from the configuration of four points. However, once animators internalize the spline model, many prefer it for long animation sequences because it reduces the number of parameters to adjust.

### Interpolation Mode Decisions

The choice of interpolation curve is not arbitrary; it encodes the animator's intent about the quality of motion. An animation software typically offers several modes for each keyframe:

**Linear mode** interpolates using straight lines between keyframes. The velocity is constant within each interval. This mode is appropriate for mechanical motion, digital transitions, or motion that intentionally feels robotic. Linear mode is also computationally efficient and predictable.

**Smooth or Spline mode** (typically Catmull-Rom or similar) automatically interpolates with smooth curves that pass through all keyframes. The software derives the curve shape from neighboring keyframes without requiring animator handles. This mode is ideal for organic motion where the animator simply wants smooth transitions and does not want to fuss with individual handles.

**Bézier mode** provides full control through in and out handles for each keyframe. The animator can fine-tune the curve shape arbitrarily, achieving exact velocity profiles. This mode is used when precise motion timing is critical or when the animator wants specific ease-in and ease-out profiles.

**Stepped mode** holds the previous keyframe's value until the next keyframe, creating instant transitions. This mode is used for discrete properties (like visibility switches or material changes) that cannot meaningfully interpolate.

**Constant-speed or velocity-normalized modes** are less common but powerful for specific tasks. Instead of parameterizing the curve by normalized time (0 to 1 across the keyframe interval), these modes parameterize the curve by arc length, ensuring that the animated object travels at constant speed along the path regardless of curve shape. This is essential when animating a character walking along a curved path; without arc-length parameterization, the character speeds up when the path curves sharply and slows down on gentle sections, producing unnatural gait variation.

### The Transform Decomposition Pipeline

Animating a full 4×4 transformation matrix requires careful decomposition and recomposition each frame. The standard approach is:

1. Extract translation (the rightmost column of the matrix).
2. Extract scale (the magnitude of the column/row vectors of the upper-left 3×3 submatrix).
3. Extract rotation (by normalizing the upper-left 3×3 submatrix to remove the scale).
4. Interpolate each component separately using appropriate curve types.
5. Recompose: create a rotation matrix from the interpolated rotation, scale it by the interpolated scale, and add the interpolated translation.

This pipeline matters because direct matrix interpolation produces distorted intermediate frames. For example, linear interpolation between two rotation matrices can produce frames where the object appears to twist or skew—effects that violate the rigidity of rotation. By interpolating rotations as quaternions, we ensure that the interpolated value is always a valid rotation with no skewing.

The decomposition approach also allows mixed interpolation: translation might use a Bézier curve while rotation uses spherical linear interpolation, and scale might step linearly. This flexibility is powerful for achieving specific motion qualities.

### The Graph Editor Workspace

In modern animation software, the graph editor is where temporal geometry becomes tangible. The graph editor displays curves over time, with the horizontal axis representing time (measured in frames) and the vertical axis representing property value (position, rotation, scale, or any other animatable parameter). Each property of each object gets its own curve.

The workflow is fundamentally graphical: the animator draws curves by setting keyframes and shaping handles. The curve's shape directly encodes motion quality. A curve that rises steeply and then flattens encodes acceleration-then-deceleration: the animated value changes rapidly initially, then slows down. A curve that rises gently then steeply encodes the opposite: slow initially, then acceleration. A wavy or oscillating curve encodes bouncing or oscillating motion.

Reading curves requires intuition. A flat horizontal segment means no change: that property is static during that time range. A steep segment means rapid change. A curve's slope at any point is the velocity: steeper slope means higher velocity. The curve's curvature (second derivative) represents acceleration: a curve that bends upward (concave up) represents positive acceleration; bending downward represents negative acceleration (deceleration).

## 3. High-Performance Optimization & Failure Modes

### Temporal Aliasing and the Nyquist Constraint

When motion contains frequencies higher than half the frame rate, aliasing occurs. Imagine an object oscillating back and forth 30 times per second, but the animation is sampled at only 24 frames per second. The higher-frequency oscillation cannot be fully represented; instead, it aliases into a lower-frequency false motion, creating an uncanny jittering appearance. This is particularly common in motion capture data, where the actor's natural muscle tremor and breathing induce high-frequency noise.

Mitigation requires low-pass filtering: applying a filter that attenuates high frequencies while preserving low-frequency motion content. A simple approach is moving-average smoothing: each frame's value is replaced by the average of itself and its neighbors. More sophisticated approaches use Gaussian blur in the temporal domain or apply proper digital filters (like Butterworth or Chebyshev filters) designed to smoothly roll off high frequencies while preserving motion integrity.

The animator must also be aware of temporal aliasing when designing motion. If motion happens very rapidly—a quick twitch or snap—and the frame rate is low, that rapid motion may alias into false patterns. The solution is either to increase frame rate (expensive) or to adjust animation timing to avoid frequencies near or above the Nyquist limit.

### Gimbal Lock and Rotation Representation

Rotations in three dimensions present a subtle but critical problem. When rotations are represented using Euler angles (three angles about three axes, like pitch, yaw, and roll), a configuration called gimbal lock can occur. At gimbal lock, two of the three rotation axes align, and the system loses a degree of freedom; certain rotations become impossible to perform smoothly.

Quaternions solve this problem. A quaternion is a four-component representation of rotation that avoids gimbal lock entirely. However, quaternion interpolation requires care. Simple linear interpolation of quaternion components does not preserve the quaternion's magnitude and produces distorted rotations. Instead, spherical linear interpolation (slerp) must be used. Slerp interpolates along the geodesic (shortest path) on the four-dimensional unit sphere, ensuring a valid rotation at every interpolated frame.

Another rotation representation, axis-angle (an axis of rotation and an angle about that axis), also avoids gimbal lock but is less convenient for interpolation and composition.

For animators, the practical implication is simple: use the software's built-in rotation curves, which typically handle quaternion interpolation automatically. Never manually interpolate individual Euler angle components, as this will produce gimbal lock and unnatural twists.

### Handle Continuity and Motion Hitches

When adjacent keyframes have mismatched handle slopes, a subtle hitch appears: the curve's tangent (velocity) changes discontinuously. If both keyframes use Bézier curves and the out-handle of the first keyframe and in-handle of the second keyframe are not collinear, the curve's first derivative has a jump discontinuity at the keyframe. This produces a perceptible snap in velocity, even though position is continuous.

Most animation software offers tangent continuity modes: options like "Aligned" or "Auto" that ensure handles are automatically positioned to maintain tangent continuity. With aligned handles, moving one handle automatically adjusts the other to maintain collinearity, ensuring smooth velocity. This is why default-mode animation in professional software often produces smooth motion without manual tweaking: the software maintains continuity automatically.

For hand-crafted curves where the animator explicitly adjusts handles, mismatched tangents are a common source of unnatural motion. A quick review of the graph editor—checking that adjacent handles are collinear—catches these errors early.

### Frame Rate and Perception Thresholds

The choice of frame rate has profound implications for motion design. At 24 fps (cinema), each frame interval is 41.67 milliseconds. At 30 fps (broadcast), intervals are 33.33 milliseconds. At 60 fps (interactive), intervals are 16.67 milliseconds. These are not merely sampling rates; they define the temporal grain of the animation.

Low frame rates (12-15 fps) produce a staccato, hand-drawn appearance. Motion appears as discrete jumps rather than continuous flow. This is acceptable (sometimes desirable) for stylized animation or motion graphics with very slow motion. Standard frame rates (24-30 fps) are the cinematic norm; motion appears smooth to most viewers without excessive data. High frame rates (60 fps and above) are necessary for fast-motion content or interactive media where viewer responsiveness is critical.

The frame rate also affects interpolation strategy. At 24 fps, interpolation errors accumulate more noticeably because fewer frames bridge a given time span. At 60 fps, curves can be slightly less refined and still appear smooth due to the increased sampling.

### Temporal Resolution and the Production Pipeline

Frame rate selection is thus a design constraint that cascades through the entire production pipeline. At lower frame rates, motion must be choreographed more carefully—aggressive acceleration or direction changes within a single frame produce jarring discontinuities that higher frame rates would mask through denser sampling. This is why animators working at 24 fps often use "smear frames" or motion blur to bridge large displacements, creating the perceptual illusion of continuity where discrete sampling would otherwise reveal gaps. Conversely, high-frame-rate animation permits tighter temporal control but demands proportionally more computational resources and storage. The animator must balance perceptual smoothness against production constraints, recognizing that frame rate is not a post-hoc rendering choice but a foundational parameter that shapes keyframe placement, tangent tuning, and interpolation strategy from the outset.

Understanding these temporal mechanics—keyframe topology, interpolation continuity, and sampling thresholds—establishes the invariant foundations upon which all animation is built. Mastery of these principles enables the animator to diagnose motion artifacts at their root cause, whether the issue is C⁰ discontinuity at a keyframe boundary, tangent misalignment producing velocity spikes, or frame-rate mismatch creating perceptual aliasing. With these tools in hand, the animator moves from intuitive trial-and-error to rigorous geometric reasoning, transforming the animation graph from an opaque black box into a legible, controllable mathematical object.

## Summary & Verification Matrix

| **Invariant/Principle** | **Mathematical Form / Criterion** | **Diagnostic Indicator** | **Common Failure Mode** |
|-------------------------|-----------------------------------|--------------------------|-------------------------|
| **Positional Continuity (C⁰)** | lim_{t→t₀⁻} p(t) = lim_{t→t₀⁺} p(t) = p(t₀) | Smooth passage through keyframe without spatial jump | Duplicate keyframes at same time with different values; curve segment endpoint mismatch |
| **Velocity Continuity (C¹)** | lim_{t→t₀⁻} p'(t) = lim_{t→t₀⁺} p'(t) | No instantaneous change in speed/direction; tangent handles collinear | Misaligned Bézier handles; non-collinear incoming/outgoing tangents at keyframe |
| **Interpolation Method** | Linear: p(t) = p₀ + t(p₁ - p₀); Cubic: Hermite/Bézier with four control points | Linear produces constant velocity; cubic allows ease-in/ease-out | Using linear interpolation for organic motion; insufficient handle tuning in cubic mode |
| **Temporal Sampling (Frame Rate)** | Δt = 1/fps; nyquist criterion: sample at ≥2× highest motion frequency | Motion appears continuous when frame interval < perceptual fusion threshold (~50ms) | Frame rate too low for fast motion (aliasing, strobing); excessive keyframe density at high frame rates |
| **Ease Functions & Acceleration** | a(t) = p''(t); smooth acceleration requires C² continuity | Gradual velocity change; no "pops" in motion profile | Step discontinuities in acceleration graph; ease-in without matching ease-out creating unbalanced motion |
| **Handle Geometry in Bézier Curves** | Tangent vector at p₀: T₀ = 3(p₁ - p₀); tangent at p₃: T₃ = 3(p₃ - p₂) | Collinear handles at keyframe maintain C¹; handle length controls ease strength | Automatic handles overridden without maintaining collinearity; handle length too short (abrupt) or too long (overshoot) |
