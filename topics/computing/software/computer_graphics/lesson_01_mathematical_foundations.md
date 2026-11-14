# Lesson 1: Mathematical Foundations of Graphics

## 1. First-Principles Intuition & Invariants

Computer graphics rests on a precise mathematical substrate that transforms abstract geometric descriptions into pixel arrays rendered on display hardware. At its core, this transformation chain requires expressing spatial relationships, geometric primitives, and coordinate systems through linear algebra structures that compose cleanly and compute efficiently on modern vector processors. The discipline emerged from disparate roots in computational geometry, projective geometry developed for Renaissance perspective art, and quaternion algebra invented by Hamilton in 1843, converging into a unified framework optimized for real-time rendering pipelines and GPU parallel execution models.

The fundamental abstraction is the affine transformation, which preserves parallel lines and ratios of distances along those lines. Affine transformations encompass translation, rotation, scaling, and shearing—the core operations required to position, orient, and deform geometric objects within a scene. However, translation poses an algebraic challenge: while rotation and scaling are linear transformations representable as matrix multiplication, translation is not. The addition of a constant offset vector breaks the closure property of linear operators. This heterogeneity would require separate code paths for different transformation types, fragmenting the rendering pipeline and preventing composition through simple matrix multiplication.

Homogeneous coordinates resolve this asymmetry by embedding affine space into a higher-dimensional projective space. A three-dimensional point $(x, y, z)$ becomes the four-dimensional homogeneous vector $(x, y, z, 1)$, where the additional coordinate encodes the distinction between points and vectors. Vectors, representing directions without position, use a homogeneous coordinate of zero: $(x, y, z, 0)$. This encoding allows translation to be expressed as matrix multiplication, unifying all affine transformations into a single algebraic operation. The w-coordinate also naturally represents perspective division in projective transformations, where points at infinity correspond to w approaching zero.

The rendering pipeline processes millions of vertices per frame, transforming them through multiple coordinate spaces: object space (local model coordinates), world space (global scene coordinates), view space (camera-relative coordinates), clip space (post-projection coordinates), and normalized device coordinates (screen-space coordinates). Each transformation is a 4×4 matrix multiplication. The composition property of matrices means the entire transformation chain can be precomputed into a single matrix, reducing per-vertex computation to one matrix-vector multiply—sixteen multiplications and twelve additions for four-dimensional homogeneous vectors. Modern GPUs execute these operations in parallel across thousands of shader cores, achieving throughput measured in billions of vertices per second.

Rotations introduce additional complexity. While 3×3 rotation matrices provide an exact representation, they suffer from gimbal lock when composed from Euler angles and accumulate floating-point error under repeated composition, gradually losing orthogonality. The matrix requires nine scalar values to represent three degrees of freedom, consuming memory bandwidth and cache. Quaternions, four-dimensional hypercomplex numbers generalizing complex numbers, represent rotations with four scalars in a form that interpolates smoothly, never exhibits gimbal lock, and composes efficiently through quaternion multiplication. A quaternion $q = w + xi + yj + zk$ encodes a rotation of angle $\theta$ around axis $\mathbf{v}$ as $q = \cos(\theta/2) + \sin(\theta/2)\mathbf{v}$. The half-angle formulation ensures unit quaternions form a double cover of SO(3), the group of three-dimensional rotations, providing numerically stable interpolation and composition.

Barycentric coordinates provide the final critical primitive. Given a triangle with vertices $\mathbf{v}_0, \mathbf{v}_1, \mathbf{v}_2$, any point $\mathbf{p}$ inside the triangle can be expressed as $\mathbf{p} = \alpha\mathbf{v}_0 + \beta\mathbf{v}_1 + \gamma\mathbf{v}_2$ where $\alpha + \beta + \gamma = 1$ and $\alpha, \beta, \gamma \geq 0$. These coordinates enable linear interpolation of vertex attributes—colors, texture coordinates, normals—across the triangle surface during rasterization. The constraints define a convex combination, ensuring interpolated values remain bounded by the vertex values. Rasterizers compute barycentric coordinates for every pixel fragment overlapping a triangle, using them to interpolate perspective-correct texture coordinates and evaluate fragment shaders.

## 2. Core Architecture & Mechanics

### Vector Spaces and Linear Transformations

A vector space over the real numbers $\mathbb{R}$ consists of a set of vectors supporting addition and scalar multiplication satisfying eight axioms: associativity and commutativity of addition, additive identity and inverses, distributivity of scalar multiplication over vector addition and scalar addition, associativity of scalar multiplication, and multiplicative identity. The Euclidean spaces $\mathbb{R}^2$ and $\mathbb{R}^3$ provide the intuitive foundation, where vectors represent positions or directions in physical space. In graphics, we extend this to $\mathbb{R}^4$ through homogeneous coordinates.

Linear transformations $T: \mathbb{R}^n \rightarrow \mathbb{R}^m$ are functions preserving vector addition and scalar multiplication: $T(\mathbf{u} + \mathbf{v}) = T(\mathbf{u}) + T(\mathbf{v})$ and $T(c\mathbf{v}) = cT(\mathbf{v})$. Every linear transformation can be represented as matrix multiplication. For a transformation $T: \mathbb{R}^3 \rightarrow \mathbb{R}^3$, we construct a $3 \times 3$ matrix $M$ where the columns are the transformed basis vectors: $M = [T(\mathbf{e}_1) \quad T(\mathbf{e}_2) \quad T(\mathbf{e}_3)]$. Applying the transformation to vector $\mathbf{v} = (x, y, z)^T$ is then $T(\mathbf{v}) = M\mathbf{v}$.

Consider a rotation by angle $\theta$ around the z-axis. The basis vector $\mathbf{e}_1 = (1, 0, 0)$ rotates to $(\cos\theta, \sin\theta, 0)$, and $\mathbf{e}_2 = (0, 1, 0)$ rotates to $(-\sin\theta, \cos\theta, 0)$, while $\mathbf{e}_3 = (0, 0, 1)$ remains unchanged. This yields the rotation matrix:

$$R_z(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta & 0 \\ \sin\theta & \cos\theta & 0 \\ 0 & 0 & 1 \end{bmatrix}$$

Rotation matrices are orthogonal, meaning $R^T R = I$ and $\det(R) = 1$. Orthogonality preserves dot products and vector lengths, making rotations rigid transformations. Scaling matrices are diagonal, with scale factors along the diagonal: $S(s_x, s_y, s_z) = \text{diag}(s_x, s_y, s_z)$. Reflection matrices have determinant $-1$, distinguishing them from rotations. Shear matrices are non-diagonal with off-diagonal elements introducing skew.

### Homogeneous Coordinates and Affine Transformations

Affine transformations combine linear transformations with translation: $\mathbf{p}' = M\mathbf{p} + \mathbf{t}$. This additive term prevents composition through pure matrix multiplication. Homogeneous coordinates embed affine space into projective space, representing three-dimensional point $(x, y, z)$ as four-dimensional $(x, y, z, 1)$ and direction vector as $(x, y, z, 0)$. Affine transformations become $4 \times 4$ matrices with the structure:

$$A = \begin{bmatrix} M_{3\times3} & \mathbf{t}_{3\times1} \\ \mathbf{0}_{1\times3} & 1 \end{bmatrix}$$

The upper-left $3 \times 3$ block encodes rotation, scale, and shear. The upper-right column encodes translation. The bottom row $(0, 0, 0, 1)$ ensures points transform correctly. Multiplying this matrix by homogeneous point $(x, y, z, 1)$ produces:

$$\begin{bmatrix} M & \mathbf{t} \\ \mathbf{0} & 1 \end{bmatrix} \begin{bmatrix} x \\ y \\ z \\ 1 \end{bmatrix} = \begin{bmatrix} M\mathbf{p} + \mathbf{t} \\ 1 \end{bmatrix}$$

Direction vectors with $w = 0$ ignore translation: $A\begin{bmatrix} x \\ y \\ z \\ 0 \end{bmatrix} = \begin{bmatrix} M\mathbf{v} \\ 0 \end{bmatrix}$, which is geometrically correct since directions have no position.

Composition of transformations becomes matrix multiplication. To rotate then translate, compute $T(t_x, t_y, t_z) \cdot R(\theta)$. Note the order: transformations apply right-to-left, so the rightmost matrix applies first. This convention follows from function composition $(f \circ g)(\mathbf{x}) = f(g(\mathbf{x}))$. Matrix multiplication is associative but not commutative: $AB \neq BA$ in general. Rotating then translating produces a different result than translating then rotating, which is physically intuitive.

A complete object-to-world transformation often composes scaling, rotation, and translation in that order: $M = T \cdot R \cdot S$. This ordering ensures scaling occurs in the object's local axes before rotation reorients it, and translation positions the rotated, scaled object in world space. Precomputing this composition into a single matrix eliminates redundant transformations during rendering.

### Projective Transformations and Perspective Division

Projective transformations generalize affine transformations by allowing the $w$ coordinate to vary, enabling perspective projection. The general $4 \times 4$ projective matrix has no restrictions on the bottom row:

$$P = \begin{bmatrix} m_{11} & m_{12} & m_{13} & m_{14} \\ m_{21} & m_{22} & m_{23} & m_{24} \\ m_{31} & m_{32} & m_{33} & m_{34} \\ m_{41} & m_{42} & m_{43} & m_{44} \end{bmatrix}$$

After multiplying by this matrix, the homogeneous point $(x', y', z', w')$ must be normalized by dividing by $w'$ to obtain the Cartesian point $(x'/w', y'/w', z'/w')$. This perspective division introduces the nonlinearity required for realistic perspective rendering, where distant objects appear smaller.

The perspective projection matrix transforms view-space coordinates (camera at origin, looking down negative z-axis) into clip space. For a symmetric perspective frustum with vertical field of view $\theta$, aspect ratio $a$, near plane $n$, and far plane $f$, the projection matrix is:

$$P = \begin{bmatrix} \frac{1}{a\tan(\theta/2)} & 0 & 0 & 0 \\ 0 & \frac{1}{\tan(\theta/2)} & 0 & 0 \\ 0 & 0 & \frac{f+n}{n-f} & \frac{2fn}{n-f} \\ 0 & 0 & -1 & 0 \end{bmatrix}$$

The $z$ row is carefully constructed to map the near plane to $-1$ and far plane to $+1$ after perspective division (in OpenGL conventions), providing normalized depth values for the depth buffer. The bottom row $[0, 0, -1, 0]$ causes $w' = -z$, so dividing by $w'$ scales coordinates inversely with depth, producing the perspective foreshortening.

Clip-space coordinates then undergo clipping against the canonical view volume $[-1, 1]^3$, and viewport transformation maps them to screen coordinates. The depth value $z'$ is stored in the depth buffer for hidden surface removal. Perspective-correct interpolation of vertex attributes requires dividing attributes by $w$ before interpolation, then multiplying the interpolated result by the interpolated $1/w$, ensuring texture coordinates and colors vary correctly across perspective-distorted triangles.

### Quaternion Algebra and Rotation Representation

A quaternion is a four-dimensional hypercomplex number $q = w + xi + yj + zk$ where $i^2 = j^2 = k^2 = ijk = -1$. The quaternion product is defined by these relations and distributivity. For quaternions $q_1 = w_1 + x_1i + y_1j + z_1k$ and $q_2 = w_2 + x_2i + y_2j + z_2k$, their product is:

$$q_1 q_2 = (w_1w_2 - x_1x_2 - y_1y_2 - z_1z_2) + (w_1x_2 + x_1w_2 + y_1z_2 - z_1y_2)i + (w_1y_2 - x_1z_2 + y_1w_2 + z_1x_2)j + (w_1z_2 + x_1y_2 - y_1x_2 + z_1w_2)k$$

This non-commutative multiplication encodes rotation composition. A unit quaternion (magnitude 1) represents a rotation. To rotate by angle $\theta$ around unit axis $\mathbf{v} = (v_x, v_y, v_z)$, construct:

$$q = \cos(\theta/2) + \sin(\theta/2)(v_x i + v_y j + v_z k)$$

The half-angle ensures the quaternion double-covers SO(3): $q$ and $-q$ represent the same rotation. To rotate vector $\mathbf{p} = (x, y, z)$ by quaternion $q$, embed the vector as pure quaternion $p = 0 + xi + yj + zk$ and compute:

$$p' = qpq^{-1}$$

where $q^{-1} = \bar{q}/|q|^2$ is the quaternion inverse and $\bar{q} = w - xi - yj - zk$ is the conjugate. For unit quaternions, $q^{-1} = \bar{q}$. This "sandwich" product rotates the vector, producing a pure quaternion whose imaginary coefficients are the rotated coordinates.

Composing rotations is quaternion multiplication: rotating by $q_1$ then $q_2$ is $q_2q_1$ (note the order). Quaternion multiplication requires sixteen multiplications and twelve additions, comparable to $3 \times 3$ matrix multiplication but with four values instead of nine. Converting a quaternion to a $3 \times 3$ rotation matrix for final application is straightforward:

$$R(q) = \begin{bmatrix} 1 - 2(y^2 + z^2) & 2(xy - wz) & 2(xz + wy) \\ 2(xy + wz) & 1 - 2(x^2 + z^2) & 2(yz - wx) \\ 2(xz - wy) & 2(yz + wx) & 1 - 2(x^2 + y^2) \end{bmatrix}$$

This conversion is performed once per object per frame. Quaternions excel at interpolation. Spherical linear interpolation (slerp) between unit quaternions $q_1$ and $q_2$ is:

$$\text{slerp}(q_1, q_2, t) = \frac{\sin((1-t)\Omega)}{\sin\Omega}q_1 + \frac{\sin(t\Omega)}{\sin\Omega}q_2$$

where $\Omega = \arccos(q_1 \cdot q_2)$ is the angle between them on the unit hypersphere. This produces constant angular velocity rotation, critical for smooth animation. Euler angles, by contrast, interpolate poorly: the path between $(0, 0, 0)$ and $(180°, 0, 0)$ is ambiguous, and interpolation can introduce unwanted rotation around other axes. Quaternions avoid these artifacts entirely.

### Barycentric Coordinates and Triangle Interpolation

A triangle with vertices $\mathbf{v}_0, \mathbf{v}_1, \mathbf{v}_2$ defines a two-dimensional affine subspace in three-dimensional space. Any point $\mathbf{p}$ in the plane containing the triangle can be expressed as:

$$\mathbf{p} = \alpha\mathbf{v}_0 + \beta\mathbf{v}_1 + \gamma\mathbf{v}_2$$

with $\alpha + \beta + \gamma = 1$. The coefficients $(\alpha, \beta, \gamma)$ are barycentric coordinates. The point lies inside the triangle if and only if $\alpha, \beta, \gamma \geq 0$. These coordinates are affine invariant: they remain unchanged under translation, rotation, scaling, and shearing of the triangle.

Computing barycentric coordinates for point $\mathbf{p}$ relative to triangle $(\mathbf{v}_0, \mathbf{v}_1, \mathbf{v}_2)$ uses signed triangle areas. Define vectors $\mathbf{e}_1 = \mathbf{v}_1 - \mathbf{v}_0$ and $\mathbf{e}_2 = \mathbf{v}_2 - \mathbf{v}_0$. The area of the triangle is $A = \frac{1}{2}|\mathbf{e}_1 \times \mathbf{e}_2|$. The barycentric coordinate $\alpha$ equals the ratio of the area of the sub-triangle formed by $\mathbf{p}, \mathbf{v}_1, \mathbf{v}_2$ to the total area:

$$\alpha = \frac{\text{Area}(\mathbf{p}, \mathbf{v}_1, \mathbf{v}_2)}{\text{Area}(\mathbf{v}_0, \mathbf{v}_1, \mathbf{v}_2)}$$

Similarly for $\beta$ and $\gamma$. Using the cross product:

$$\beta = \frac{|(\mathbf{p} - \mathbf{v}_0) \times \mathbf{e}_2|}{|\mathbf{e}_1 \times \mathbf{e}_2|}$$

$$\gamma = \frac{|\mathbf{e}_1 \times (\mathbf{p} - \mathbf{v}_0)|}{|\mathbf{e}_1 \times \mathbf{e}_2|}$$

$$\alpha = 1 - \beta - \gamma$$

In two-dimensional screen space, the cross product reduces to a determinant. For screen-space vertices $(x_0, y_0), (x_1, y_1), (x_2, y_2)$ and point $(x, y)$:

$$\beta = \frac{(y_0 - y_2)x + (x_2 - x_0)y + x_0y_2 - x_2y_0}{(y_0 - y_2)x_1 + (x_2 - x_0)y_1 + x_0y_2 - x_2y_0}$$

Rasterizers precompute the denominators and edge equations during triangle setup, then incrementally update barycentric coordinates as they scan across pixels. For every fragment at $(x, y)$, the interpolated vertex attribute is:

$$A(x, y) = \alpha A_0 + \beta A_1 + \gamma A_2$$

This linear interpolation is not perspective-correct. Perspective projection is a nonlinear transformation that distorts the uniform parameter space of the triangle. To interpolate correctly, each attribute must be divided by the clip-space $w$ coordinate before interpolation, and the result divided by the interpolated $1/w$:

$$A_{\text{correct}} = \frac{\alpha(A_0/w_0) + \beta(A_1/w_1) + \gamma(A_2/w_2)}{\alpha(1/w_0) + \beta(1/w_1) + \gamma(1/w_2)}$$

Modern GPUs perform this automatically for texture coordinates, but shader code interpolating custom attributes must handle perspective correction explicitly when required. Barycentric coordinates also enable geometric queries: point-in-triangle tests, ray-triangle intersection (Möller-Trumbore algorithm), and triangle clipping.

## 3. High-Performance Optimization & Failure Modes

### SIMD Vectorization and Cache Optimization

Modern CPUs provide SIMD (Single Instruction, Multiple Data) instruction sets like AVX2 and AVX-512, executing four or eight floating-point operations per instruction. Graphics code leverages SIMD by processing four homogeneous coordinates as a single 128-bit register (SSE) or eight as a 256-bit register (AVX). Matrix-vector multiplication for a $4 \times 4$ matrix and four-dimensional vector becomes four dot products, each computing four multiplications and three additions simultaneously.

```c
#include <immintrin.h>

// 4x4 matrix stored row-major, vector as __m128 (x, y, z, w)
__m128 mat_vec_mult_sse(__m128 row0, __m128 row1, __m128 row2, __m128 row3, __m128 vec) {
    __m128 prod0 = _mm_mul_ps(row0, vec);
    __m128 prod1 = _mm_mul_ps(row1, vec);
    __m128 prod2 = _mm_mul_ps(row2, vec);
    __m128 prod3 = _mm_mul_ps(row3, vec);
    
    // Horizontal add: sum elements within each register
    __m128 sum01 = _mm_hadd_ps(prod0, prod1);
    __m128 sum23 = _mm_hadd_ps(prod2, prod3);
    __m128 result = _mm_hadd_ps(sum01, sum23);
    
    return result;
}
```

This code performs a $4 \times 4$ matrix-vector multiply in twelve SIMD instructions plus overhead, significantly faster than scalar code requiring sixteen multiplications and twelve additions sequentially. Batching multiple vertices for transformation in a loop allows the CPU to pipeline instructions and hide memory latency.

Cache coherency is critical. Storing matrices in row-major order aligns with C array layout, but column-major order (OpenGL convention) can provide better cache behavior when multiplying matrices. Structure-of-arrays (SoA) layout separates x, y, z, w coordinates into separate arrays, enabling vectorized processing without gather/scatter:

```c
typedef struct {
    float *x, *y, *z, *w;
    size_t count;
} Vec4Array;

void transform_vertices_soa(float *mat4x4, Vec4Array *in, Vec4Array *out) {
    for (size_t i = 0; i < in->count; i += 4) {
        __m128 vx = _mm_loadu_ps(&in->x[i]);
        __m128 vy = _mm_loadu_ps(&in->y[i]);
        __m128 vz = _mm_loadu_ps(&in->z[i]);
        __m128 vw = _mm_loadu_ps(&in->w[i]);
        
        // Transpose to get four vectors
        _MM_TRANSPOSE4_PS(vx, vy, vz, vw);
        
        // Apply transformation (simplified, expand per-row)
        // ... matrix multiplication ...
        
        _mm_storeu_ps(&out->x[i], vx);
        _mm_storeu_ps(&out->y[i], vy);
        _mm_storeu_ps(&out->z[i], vz);
        _mm_storeu_ps(&out->w[i], vw);
    }
}
```

Aligning data structures to 16-byte or 32-byte boundaries eliminates unaligned load penalties. Allocating vertex buffers with `aligned_alloc(32, size)` ensures efficient SIMD access.

### Numerical Stability and Precision

Floating-point arithmetic introduces rounding error that accumulates through repeated transformations. Rotation matrices should remain orthogonal, but finite precision causes drift. After composing many rotations, the matrix columns cease to be unit length and orthogonal, distorting geometry. Gram-Schmidt orthogonalization reorthogonalizes the matrix:

```c
void orthogonalize_matrix(float mat[3][3]) {
    float x[3] = {mat[0][0], mat[1][0], mat[2][0]};
    float y[3] = {mat[0][1], mat[1][1], mat[2][1]};
    float z[3] = {mat[0][2], mat[1][2], mat[2][2]};
    
    // Normalize x
    float len = sqrtf(x[0]*x[0] + x[1]*x[1] + x[2]*x[2]);
    x[0] /= len; x[1] /= len; x[2] /= len;
    
    // y = y - (y·x)x
    float dot_yx = y[0]*x[0] + y[1]*x[1] + y[2]*x[2];
    y[0] -= dot_yx*x[0]; y[1] -= dot_yx*x[1]; y[2] -= dot_yx*x[2];
    len = sqrtf(y[0]*y[0] + y[1]*y[1] + y[2]*y[2]);
    y[0] /= len; y[1] /= len; y[2] /= len;
    
    // z = x × y
    z[0] = x[1]*y[2] - x[2]*y[1];
    z[1] = x[2]*y[0] - x[0]*y[2];
    z[2] = x[0]*y[1] - x[1]*y[0];
    
    mat[0][0] = x[0]; mat[1][0] = x[1]; mat[2][0] = x[2];
    mat[0][1] = y[0]; mat[1][1] = y[1]; mat[2][1] = y[2];
    mat[0][2] = z[0]; mat[1][2] = z[1]; mat[2][2] = z[2];
}
```

Applying this every few frames prevents visible distortion. Quaternions naturally maintain unit length through normalization, avoiding cumulative error in rotation representation. Normalizing a quaternion after composition is a single square root and four divisions:

```c
void quat_normalize(float q[4]) {
    float len = sqrtf(q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3]);
    q[0] /= len; q[1] /= len; q[2] /= len; q[3] /= len;
}
```

Depth buffer precision is non-uniform. The perspective projection matrix maps view-space $z$ to clip-space $z'$ non-linearly. Near the near plane, depth values are densely packed; near the far plane, they are sparse. This causes z-fighting artifacts where coplanar surfaces have similar depth values that round differently per pixel. Placing the near plane as far from the camera as acceptable and using a reversed depth buffer (mapping near to 1.0 and far to 0.0) with floating-point depth improves precision distribution.

### Quaternion Interpolation and Singularities

Spherical linear interpolation (slerp) between quaternions can exhibit unexpected behavior when the quaternions are nearly opposite. The dot product $q_1 \cdot q_2$ approaches $-1$, making $\Omega \approx \pi$ and $\sin\Omega \approx 0$, causing division by near-zero. The solution is to negate one quaternion if the dot product is negative, ensuring interpolation takes the short arc on the four-dimensional hypersphere:

```c
void quat_slerp(const float q1[4], const float q2[4], float t, float result[4]) {
    float dot = q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3];
    float q2_adjusted[4] = {q2[0], q2[1], q2[2], q2[3]};
    
    if (dot < 0.0f) {
        dot = -dot;
        q2_adjusted[0] = -q2[0];
        q2_adjusted[1] = -q2[1];
        q2_adjusted[2] = -q2[2];
        q2_adjusted[3] = -q2[3];
    }
    
    if (dot > 0.9995f) {
        // Quaternions nearly identical, use linear interpolation
        result[0] = q1[0] + t*(q2_adjusted[0] - q1[0]);
        result[1] = q1[1] + t*(q2_adjusted[1] - q1[1]);
        result[2] = q1[2] + t*(q2_adjusted[2] - q1[2]);
        result[3] = q1[3] + t*(q2_adjusted[3] - q1[3]);
        quat_normalize(result);
        return;
    }
    
    float omega = acosf(dot);
    float sin_omega = sinf(omega);
    float a = sinf((1.0f - t)*omega) / sin_omega;
    float b = sinf(t*omega) / sin_omega;
    
    result[0] = a*q1[0] + b*q2_adjusted[0];
    result[1] = a*q1[1] + b*q2_adjusted[1];
    result[2] = a*q1[2] + b*q2_adjusted[2];
    result[3] = a*q1[3] + b*q2_adjusted[3];
}
```

For high-frequency animation or camera control, normalized linear interpolation (nlerp) provides a computationally cheaper approximation: linearly interpolate the quaternion components and renormalize. This produces non-constant angular velocity but is often imperceptible and avoids transcendental functions.

### Barycentric Coordinate Edge Cases

Computing barycentric coordinates involves division by the triangle area, which is zero for degenerate triangles (collinear vertices). Robust rasterizers detect this during triangle setup and cull degenerate triangles before processing. For ray-triangle intersection, division by zero indicates the ray is parallel to the triangle plane. Epsilon thresholds guard against near-degenerate cases:

```c
bool ray_triangle_intersect(const float origin[3], const float dir[3],
                            const float v0[3], const float v1[3], const float v2[3],
                            float *t, float *u, float *v) {
    float edge1[3] = {v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]};
    float edge2[3] = {v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]};
    
    float h[3] = {dir[1]*edge2[2] - dir[2]*edge2[1],
                  dir[2]*edge2[0] - dir[0]*edge2[2],
                  dir[0]*edge2[1] - dir[1]*edge2[0]};
    
    float a = edge1[0]*h[0] + edge1[1]*h[1] + edge1[2]*h[2];
    if (fabsf(a) < 1e-8f) return false;  // Ray parallel to triangle
    
    float f = 1.0f / a;
    float s[3] = {origin[0]-v0[0], origin[1]-v0[1], origin[2]-v0[2]};
    *u = f * (s[0]*h[0] + s[1]*h[1] + s[2]*h[2]);
    if (*u < 0.0f || *u > 1.0f) return false;
    
    float q[3] = {s[1]*edge1[2] - s[2]*edge1[1],
                  s[2]*edge1[0] - s[0]*edge1[2],
                  s[0]*edge1[1] - s[1]*edge1[0]};
    
    *v = f * (dir[0]*q[0] + dir[1]*q[1] + dir[2]*q[2]);
    if (*v < 0.0f || *u + *v > 1.0f) return false;
    
    *t = f * (edge2[0]*q[0] + edge2[1]*q[1] + edge2[2]*q[2]);
    return *t > 1e-8f;  // Intersection in front of ray origin
}
```

The epsilon threshold `1e-8f` prevents false positives from floating-point error. Adjusting this value trades off between rejecting valid near-grazing intersections and accepting spurious intersections from rounding.

### Matrix Decomposition and Inverse Computation

Extracting translation, rotation, and scale from a composed transformation matrix enables editing or analysis. Translation is the right column of a $4 \times 4$ affine matrix. Scale factors are the lengths of the upper-left $3 \times 3$ block's column vectors. Extracting rotation requires removing scale:

```c
void decompose_transform(const float mat[4][4], float trans[3], float rot[3][3], float scale[3]) {
    trans[0] = mat[0][3];
    trans[1] = mat[1][3];
    trans[2] = mat[2][3];
    
    scale[0] = sqrtf(mat[0][0]*mat[0][0] + mat[1][0]*mat[1][0] + mat[2][0]*mat[2][0]);
    scale[1] = sqrtf(mat[0][1]*mat[0][1] + mat[1][1]*mat[1][1] + mat[2][1]*mat[2][1]);
    scale[2] = sqrtf(mat[0][2]*mat[0][2] + mat[1][2]*mat[1][2] + mat[2][2]*mat[2][2]);
    
    rot[0][0] = mat[0][0] / scale[0];
    rot[1][0] = mat[1][0] / scale[0];
    rot[2][0] = mat[2][0] / scale[0];
    
    rot[0][1] = mat[0][1] / scale[1];
    rot[1][1] = mat[1][1] / scale[1];
    rot[2][1] = mat[2][1] / scale[1];
    
    rot[0][2] = mat[0][2] / scale[2];
    rot[1][2] = mat[1][2] / scale[2];
    rot[2][2] = mat[2][2] / scale[2];
}
```

Inverting a $4 \times 4$ transformation matrix naively requires computing the determinant and cofactor matrix, which is computationally expensive. For affine transformations with known structure, the inverse is:

$$A^{-1} = \begin{bmatrix} M^{-1} & -M^{-1}\mathbf{t} \\ \mathbf{0} & 1 \end{bmatrix}$$

If $M$ is a rotation matrix (orthogonal), $M^{-1} = M^T$, reducing inversion to a matrix transpose and vector multiply:

```c
void invert_rigid_transform(const float mat[4][4], float inv[4][4]) {
    // Transpose upper-left 3x3
    inv[0][0] = mat[0][0]; inv[0][1] = mat[1][0]; inv[0][2] = mat[2][0];
    inv[1][0] = mat[0][1]; inv[1][1] = mat[1][1]; inv[1][2] = mat[2][1];
    inv[2][0] = mat[0][2]; inv[2][1] = mat[1][2]; inv[2][2] = mat[2][2];
    
    // Compute -M^T * t
    inv[0][3] = -(inv[0][0]*mat[0][3] + inv[0][1]*mat[1][3] + inv[0][2]*mat[2][3]);
    inv[1][3] = -(inv[1][0]*mat[0][3] + inv[1][1]*mat[1][3] + inv[1][2]*mat[2][3]);
    inv[2][3] = -(inv[2][0]*mat[0][3] + inv[2][1]*mat[1][3] + inv[2][2]*mat[2][3]);
    
    inv[3][0] = 0.0f; inv[3][1] = 0.0f; inv[3][2] = 0.0f; inv[3][3] = 1.0f;
}
```

This assumes no scale or shear. For general affine transformations including scale, the $3 \times 3$ inverse must be computed explicitly. Using LU decomposition or cofactor expansion adds complexity but handles all cases. Graphics engines often store inverse matrices alongside forward matrices to avoid recomputation during rendering, trading memory for speed.

### Coordinate System Handedness

Left-handed and right-handed coordinate systems differ in cross-product sign and rotation conventions. OpenGL uses a right-handed system with z-axis pointing toward the viewer in view space, while DirectX historically used left-handed coordinates with z-axis pointing into the screen. This affects perspective matrix construction: the sign of the z-mapping terms flips between conventions. Mixing conventions within a pipeline produces incorrect transformations and requires careful matrix adjustments at API boundaries. Modern practice favors right-handed coordinates for consistency with mathematical conventions, though DirectX 12 and Vulkan support both through explicit projection matrix configuration.
