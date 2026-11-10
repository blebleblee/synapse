# Foundation: Trigonometry

## 1. Conceptual Mental Model (Core intuition, analogies, and first principles)

Trigonometry is fundamentally the study of **angular relationships** and their **periodic manifestations** in geometric space. At its core, it arises from the need to quantify how ratios of line segments in a circle relate to the *angle* that subtends them.  

**Core intuition**: Imagine a unit circle (radius = 1) centered at the origin. As an angle θ increases from 0 to 2π radians, a point moves along the circumference. The *x*-coordinate of this point is the cosine of θ, and the *y*-coordinate is the sine of θ. This creates a direct mapping between **angles** and **coordinate pairs** that encodes all trigonometric relationships.  

**Key analogy**: Think of the unit circle as a *universal coordinate system for angles*. Just as Cartesian coordinates describe position in 2D space, trigonometric functions describe *directional relationships* in circular motion. The circle itself is the "fundamental object" that unifies all angles into a continuous, periodic framework.  

**First principles**:  
- Angles are defined by *rotation* (not just "size" of a triangle).  
- Trigonometric functions are **periodic** (repeating after 2π radians).  
- All functions are defined *via the unit circle* for all real angles (not just acute triangles).  

> 💡 *Why this matters*: This model avoids the restrictive "right triangle" paradigm that confuses beginners. It reveals trigonometry as the *algebraic structure* of circular motion—a concept critical for physics, engineering, and advanced calculus.

---

## 2. Essential Terminology & Taxonomy

| Term                | Formal Definition                                                                 | Critical Role in Trigonometry                                  |
|---------------------|--------------------------------------------------------------------------------|----------------------------------------------------------------|
| **Angle (θ)**       | A measure of rotation from a fixed reference line (e.g., positive x-axis) in the plane. | Fundamental input to trigonometric functions. Defined via unit circle. |
| **Radian**          | The angle subtended at the center of a circle by an arc equal in length to the radius. | Standard unit for angles in pure mathematics (avoids degree-based approximations). |
| **Unit Circle**     | Circle of radius 1 centered at the origin in the Cartesian plane.                 | The *defining geometric object* for all trigonometric functions. |
| **Sine (sin θ)**    | y-coordinate of the point where angle θ intersects the unit circle.              | Primary function encoding vertical displacement in circular motion. |
| **Cosine (cos θ)**  | x-coordinate of the point where angle θ intersects the unit circle.              | Primary function encoding horizontal displacement in circular motion. |
| **Periodicity**     | The property that sin θ = sin(θ + 2πn) and cos θ = cos(θ + 2πn) for all integers n. | Defines the *repeating nature* of trigonometric functions. |

> ⚠️ *Why these terms?* These 6 terms capture the *minimal formal structure* required to derive all trigonometric identities, solve equations, and model periodic phenomena without ambiguity.

---

## 3. Architecture & Core Workflow

```mermaid
flowchart TD
    A[Angle θ] --> B[Unit Circle]
    B --> C{Point P(x,y) on Circle}
    C --> D[x = cos θ]
    C --> E[y = sin θ]
    D --> F[cos θ: Horizontal displacement]
    E --> G[sin θ: Vertical displacement]
    F --> H[Periodicity: cos(θ + 2π) = cos θ]
    G --> I[Periodicity: sin(θ + 2π) = sin θ]
    H --> J[Trigonometric Functions]
    I --> J
    J --> K[All Trigonometric Identities]
    K --> L[Equations & Applications]
```

**Workflow Explanation**:  
1. **Input**: An angle θ (measured in radians).  
2. **Geometric Mapping**: θ defines a unique point (x, y) on the unit circle.  
3. **Function Definition**:  
   - `x = cos θ` (horizontal component)  
   - `y = sin θ` (vertical component)  
4. **Periodicity**: The circle repeats every 2π radians → `sin θ` and `cos θ` are periodic with period 2π.  
5. **Output**: Trigonometric functions (sin, cos, tan, etc.) and their identities.  

> ✅ *This diagram shows the *unified formal structure*—not a computational algorithm but a *geometric-logical framework*.*

---

## 4. Common Misconceptions & Mental Traps

| Misconception                          | Formal Correction                                                                 | Why It Matters                                                                 |
|----------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| "Trigonometry only applies to right triangles" | Trigonometric functions are defined for **all real angles** via the unit circle. | Restricts understanding to acute triangles → misses wave phenomena, complex numbers, and calculus. |
| "Radians are just a unit like degrees" | Radians are **dimensionless** and defined by the circle's geometry (arc length = radius). | Degrees are arbitrary; radians are *fundamental* to calculus (e.g., derivatives of sin/cos). |
| "sin θ and cos θ are ratios of sides" | They are **coordinates** on the unit circle (not side ratios). Side ratios only apply to *right triangles* (a subset of the unit circle model). | Confuses the *geometric definition* with *special cases* → leads to errors in non-right contexts. |

> 🔍 *Critical insight*: The unit circle resolves all these by making trigonometry a **global property of rotation**, not a local triangle measurement.

---

## 5. Socratic Discussion Starters

1. **Why does the unit circle *unify* all angles (not just acute ones) into a single mathematical framework?**  
   *(Probes the geometric foundation of trigonometry beyond right triangles)*

2. **If sine and cosine are defined via the unit circle, why do we still need the Pythagorean identity `sin²θ + cos²θ = 1`?**  
   *(Explores the relationship between geometric constraints and algebraic identities)*

3. **How does the periodicity of trigonometric functions (period = 2π) emerge *naturally* from the unit circle, without arbitrary assumptions?**  
   *(Connects geometry to the fundamental property of repetition in wave phenomena)*

> 💡 *These questions force the student to move from "what" to "why" and "how"—the essence of formal scientific reasoning*.
