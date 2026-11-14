# Lesson 5: Texture Mapping Theory

## 1. First-Principles Intuition & Invariants

Texture mapping solves the fundamental problem of representing high-frequency surface detail on low-polygon geometric primitives. Consider a brick wall in a real-time game engine: modeling individual bricks, mortar lines, surface imperfections, and weathering patterns as explicit geometry would require millions of triangles and overwhelm both vertex processing pipelines and memory bandwidth. Texture mapping decouples geometric complexity from surface detail by storing visual information as discrete two-dimensional image arrays—textures—and establishing a mathematical correspondence between three-dimensional surface points and two-dimensional texture coordinates.

This correspondence is the texture mapping function, which transforms barycentric coordinates within a triangle or parametric coordinates on a curved surface into normalized texture space coordinates traditionally denoted as $(u, v)$ where both components span the interval $[0, 1]$. The elegance of this approach lies in its algebraic simplicity: once the mapping is established at vertices, the rasterizer can linearly interpolate texture coordinates across triangle interiors using the same perspective-correct interpolation machinery that handles vertex colors, normals, and other varying attributes. The fragment shader then samples the texture at the interpolated coordinates, retrieving color or other material properties that modulate the fragment's appearance.

The foundational invariant of texture mapping is the decoupling of sampling rate from geometric resolution. A single triangle spanning thousands of screen pixels can exhibit arbitrarily complex surface detail if its texture contains sufficient information. Conversely, a highly tessellated mesh can reference a low-resolution texture without requiring dense geometry. This separation of concerns enables scalable rendering architectures where artists control geometric level-of-detail independently from texture budgets, and where runtime systems can adapt texture resolution to viewing distance without modifying geometry.

However, this separation introduces profound signal processing challenges. When we project a three-dimensional curved surface onto a two-dimensional texture domain, we inevitably distort distances, angles, and areas. A square region in texture space might map to a highly stretched or compressed region on the geometric surface, creating anisotropy—directional variation in the texture-to-surface ratio. When the camera moves relative to textured surfaces, the screen-space footprint of a single texture sample varies wildly: textures viewed head-on at close range are magnified, while oblique surfaces recede into the distance and exhibit minification where many texture samples (texels) project onto individual screen pixels (fragments). Naive point sampling at these varying scales produces aliasing artifacts: shimmering, Moiré patterns, and temporal instability as the camera moves.

Modern texture mapping systems are therefore sophisticated signal reconstruction filters operating in a multi-resolution pyramid structure. They must solve three interrelated problems: establishing the geometric-to-texture correspondence (UV parameterization), reconstructing continuous signals from discrete texel grids (filtering), and efficiently querying appropriate resolution levels (mipmapping and anisotropic filtering). The solutions to these problems determine not only visual quality but also memory bandwidth utilization, cache coherency, and ultimately frame time budgets in real-time rendering.

The mathematical foundation rests on the Nyquist-Shannon sampling theorem, which requires sampling frequency to exceed twice the highest frequency component of the signal being reconstructed. In texture mapping, the "signal" is the two-dimensional image, and the sampling frequency is determined by the screen-space derivative of texture coordinates—how rapidly $u$ and $v$ change per pixel. When these derivatives exceed the Nyquist limit, aliasing is inevitable without prefiltering the texture. Mipmapping addresses this by constructing a Gaussian pyramid of progressively lower-resolution texture levels, allowing the sampler to select prefiltered versions appropriate to the viewing distance. Anisotropic filtering extends this by accounting for non-uniform scaling and rotation of the texture footprint.

Beyond simple color mapping, modern rendering exploits texture maps to encode arbitrary surface properties: tangent-space normal perturbations (normal mapping), height displacements that offset surface points (displacement mapping), scalar roughness and metalness parameters for physically-based shading, ambient occlusion factors, and even procedurally generated noise functions baked into textures for runtime efficiency. Each of these applications inherits the same filtering and parameterization requirements as color textures, but failure modes differ—incorrectly filtered normal maps produce lighting discontinuities rather than color shimmer, and improperly parameterized displacement maps create geometric tearing.

The texture sampling pipeline is a critical performance bottleneck in GPU architectures. Texture units must fetch potentially dozens of texels per fragment, apply complex filtering kernels, and maintain massive texture caches to hide memory latency. Cache miss rates directly impact fragment throughput, and texture bandwidth often saturates before arithmetic units reach peak utilization. Understanding the hardware texture cache hierarchy—typically organized as tag-based line caches with swizzled addressing for spatial locality—is essential for optimizing texture layouts, atlas packing strategies, and UV parameterization to maximize cache reuse.

## 2. Core Architecture & Mechanics

### UV Parameterization and Coordinate Systems

UV parameterization establishes the bijective mapping between three-dimensional surface geometry and two-dimensional texture space. For parametric surfaces such as quadrics, NURBS, or subdivision surfaces, this mapping is intrinsic—the surface is already defined by parameters $(s, t)$ that naturally serve as texture coordinates. For arbitrary triangle meshes, however, artists and algorithms must explicitly construct the parameterization by assigning $(u, v)$ coordinates to each vertex such that triangles in three-dimensional space correspond to triangles in texture space.

The quality of a UV parameterization is measured by several geometric distortion metrics. Conformal mappings preserve local angles but allow area distortion, meaning circles on the surface map to circles in texture space, though with varying radii. Equiareal mappings preserve surface area ratios, ensuring that equal regions on the mesh consume equal texture space, but may introduce severe angular distortion. Isometric mappings preserve both angles and areas, but exist only for developable surfaces—those that can be unrolled onto a plane without stretching, such as cylinders and cones. Most meshes require compromises that minimize distortion according to application-specific criteria.

Discrete conformal parameterization algorithms operate by constructing a sparse linear system whose solution minimizes the Dirichlet energy—the integral of the squared gradient of the mapping function. For a triangle mesh, this reduces to minimizing the sum of squared edge lengths in texture space weighted by cotangent angles. The resulting system is symmetric positive-definite and can be solved efficiently with conjugate gradient or Cholesky factorization. Boundary vertices are typically constrained to lie on a convex polygon in texture space, and the interior vertices relax to minimize distortion.

Parameterization inevitably introduces cuts—boundaries where the mesh is partitioned into topological disks. Spheres, tori, and higher-genus surfaces cannot be flattened without cutting, as their fundamental groups are non-trivial. Cuts create UV seams where texture coordinates are discontinuous across shared geometric edges. Careful seam placement along edges with high curvature or occluded regions minimizes visible artifacts, but seams complicate mipmapping because texture samples across a seam are spatially distant in texture memory despite being geometrally adjacent on the surface. Modern GPU texture samplers provide wrap modes—repeat, clamp, mirror—to handle boundary conditions, but these cannot fully eliminate seam artifacts in all filtering scenarios.

```
Mesh Vertex Data Structure:
┌────────────────────────────────────┐
│ Vertex Position (x, y, z)          │ ← World-space or object-space coordinates
│ Vertex Normal (nx, ny, nz)         │ ← Interpolated for shading
│ Texture Coordinates (u, v)         │ ← Per-vertex UV assignment
│ Tangent Vector (tx, ty, tz)        │ ← For tangent-space normal mapping
│ Bitangent Vector (bx, by, bz)      │ ← Orthogonal to tangent and normal
└────────────────────────────────────┘
         │
         ▼ Vertex Shader: Perspective-Correct Interpolation
┌────────────────────────────────────┐
│ Screen Position (x_s, y_s, z_s, w) │ ← Clip-space coordinates
│ Interpolated UV (u', v') / w       │ ← Divide by w for perspective correction
│ Interpolated Normal (n')           │
└────────────────────────────────────┘
         │
         ▼ Rasterization: Per-Fragment Interpolation
┌────────────────────────────────────┐
│ Fragment UV = (u'/w) / (1/w)       │ ← Perspective-correct reconstruction
│ Screen-Space Derivatives:          │
│   ∂u/∂x, ∂u/∂y, ∂v/∂x, ∂v/∂y     │ ← Computed via finite differences
└────────────────────────────────────┘
         │
         ▼ Fragment Shader: Texture Sampling
┌────────────────────────────────────┐
│ Compute Mip Level λ from gradients │
│ Fetch Texels from Cache/Memory     │
│ Apply Filtering Kernel (Bilinear,  │
│   Trilinear, Anisotropic)          │
│ Modulate with Lighting/Material    │
└────────────────────────────────────┘
```

The vertex shader transforms positions into clip space and computes perspective-corrected texture coordinates by dividing by the homogeneous coordinate $w$. The rasterizer linearly interpolates these divided values across the triangle and reconstructs the correct texture coordinates at each fragment by dividing by the interpolated reciprocal of $w$. This perspective correction is essential because linear interpolation in screen space does not correspond to linear interpolation in world space under perspective projection—a texture mapped onto a receding surface would appear compressed without it.

### Texture Filtering and Reconstruction Kernels

Texture filtering reconstructs a continuous signal from the discrete texel grid when the sampling location does not align with texel centers. The simplest filter, point sampling or nearest-neighbor filtering, selects the texel whose center is closest to the sampling point. This zero-order hold reconstruction treats each texel as a constant-valued square, producing blocky magnification artifacts and severe aliasing under minification because it violates the Nyquist criterion.

Bilinear filtering computes a weighted average of the four texels surrounding the sample point, using the fractional components of the texture coordinates as interpolation weights. Let $(u_s, v_s)$ be the sampling coordinates, and let $(i, j) = (\lfloor u_s \cdot W \rfloor, \lfloor v_s \cdot H \rfloor)$ be the integer texel indices for a texture of dimensions $W \times H$. The fractional offsets are $f_u = u_s \cdot W - i$ and $f_v = v_s \cdot H - j$. Bilinear filtering computes:

$$
C_{\text{bilinear}} = (1 - f_u)(1 - f_v) T[i, j] + f_u(1 - f_v) T[i+1, j] + (1 - f_u) f_v T[i, j+1] + f_u f_v T[i+1, j+1]
$$

This separable filter first interpolates horizontally between adjacent texels in the same row, then vertically between the two resulting values. Bilinear filtering is a tent kernel with a compact support of two texels in each dimension, eliminating blocky magnification but still inadequate for minification because it samples only the base mipmap level and cannot prefilter high frequencies.

Trilinear filtering extends bilinear filtering to two adjacent mipmap levels and linearly interpolates between them. Mipmaps are precomputed texture pyramids where each level is half the resolution of the previous level in both dimensions, typically generated by box filtering or Gaussian filtering during asset preprocessing. Level zero is the original texture, and subsequent levels continue halving until reaching a single-pixel texture. For an $N \times N$ texture, the mipmap chain contains $\log_2 N + 1$ levels and consumes only $\frac{4}{3}$ the memory of the base texture—a modest cost for dramatic quality improvement.

The mip level $\lambda$ is computed from the screen-space derivatives of the texture coordinates:

$$
\lambda = \frac{1}{2} \log_2\left(\max\left(\left(\frac{\partial u}{\partial x}\right)^2 + \left(\frac{\partial v}{\partial x}\right)^2, \left(\frac{\partial u}{\partial y}\right)^2 + \left(\frac{\partial v}{\partial y}\right)^2\right)\right)
$$

This formula estimates the texture-space footprint of a screen-space pixel by taking the maximum of the horizontal and vertical gradients, approximating the footprint as an isotropic circle. GPUs compute these derivatives implicitly using finite differences across adjacent fragments in $2 \times 2$ pixel quads, which is why dynamic branching in shaders disables texture sampling—the quad structure is needed for derivative calculation.

Trilinear filtering samples the two mip levels $\lfloor \lambda \rfloor$ and $\lceil \lambda \rceil$ with bilinear filtering and interpolates between them using the fractional part of $\lambda$. This requires eight texel fetches (four per level) and three linear interpolations (bilinear within each level, plus one between levels), but effectively eliminates temporal aliasing as the camera moves and $\lambda$ varies smoothly.

Anisotropic filtering addresses the fundamental limitation of mipmaps: they assume isotropic texture footprints and select mip levels based on the larger gradient, discarding directional information. When a textured surface is viewed at a steep angle, the texture footprint becomes an elongated ellipse rather than a circle, with major and minor axes differing by orders of magnitude. Mipmaps over-blur in the minor axis direction to prevent aliasing along the major axis, sacrificing detail.

Ripmaps extend mipmaps to rectangular prefiltered textures, storing every power-of-two aspect ratio, but memory cost becomes prohibitive at $3 \times$ the base texture. Production anisotropic filtering approximates elliptical footprints by taking multiple mipmap samples along the major axis of anisotropy and averaging them. The implementation computes the anisotropy ratio $\rho = \sqrt{\max_{\text{grad}} / \min_{\text{grad}}}$ and takes $\min(\rho, \text{max\_aniso})$ samples spaced along the major axis direction, where $\text{max\_aniso}$ is typically 16. Each sample uses trilinear filtering, so 16× anisotropic filtering performs up to 128 texel fetches per fragment—a significant bandwidth cost justified by the dramatic improvement in oblique surface clarity.

### Normal Mapping and Tangent-Space Transformations

Normal mapping encodes high-frequency surface detail as perturbations to the interpolated vertex normal, creating the illusion of geometric complexity without additional polygons. A normal map stores normalized three-component vectors in RGB texture channels, typically encoded in tangent space—a local coordinate system where the surface normal is aligned with the Z-axis, the U-axis of the parameterization is aligned with the X-axis (tangent), and the V-axis is aligned with the Y-axis (bitangent).

Tangent-space encoding allows the same normal map to be applied to different surfaces with varying orientations because the tangent-space normal is always expressed relative to the local surface frame, not world space. To transform the sampled tangent-space normal $\mathbf{n}_t$ into world space for lighting calculations, the fragment shader constructs the tangent-to-world matrix from the interpolated tangent $\mathbf{T}$, bitangent $\mathbf{B}$, and normal $\mathbf{N}$:

$$
\mathbf{TBN} = \begin{bmatrix} T_x & B_x & N_x \\ T_y & B_y & N_y \\ T_z & B_z & N_z \end{bmatrix}
$$

The world-space perturbed normal is then $\mathbf{n}_w = \mathbf{TBN} \cdot \mathbf{n}_t$. The tangent and bitangent vectors must be computed per-vertex, either offline during asset processing or online in the vertex shader. The standard derivation computes tangents from UV gradients across triangle edges. For a triangle with vertices $\mathbf{p}_0, \mathbf{p}_1, \mathbf{p}_2$ and corresponding texture coordinates $(u_0, v_0), (u_1, v_1), (u_2, v_2)$, we have:

$$
\mathbf{e}_1 = \mathbf{p}_1 - \mathbf{p}_0, \quad \mathbf{e}_2 = \mathbf{p}_2 - \mathbf{p}_0
$$

$$
\Delta u_1 = u_1 - u_0, \quad \Delta v_1 = v_1 - v_0, \quad \Delta u_2 = u_2 - u_0, \quad \Delta v_2 = v_2 - v_0
$$

$$
\mathbf{T} = \frac{1}{\Delta u_1 \Delta v_2 - \Delta u_2 \Delta v_1} \left(\Delta v_2 \mathbf{e}_1 - \Delta v_1 \mathbf{e}_2\right)
$$

$$
\mathbf{B} = \frac{1}{\Delta u_1 \Delta v_2 - \Delta u_2 \Delta v_1} \left(-\Delta u_2 \mathbf{e}_1 + \Delta u_1 \mathbf{e}_2\right)
$$

The denominator is the determinant of the UV edge matrix and represents the signed area of the triangle in texture space. When UV parameterization is degenerate or flipped, this determinant approaches zero, causing numerical instability. Robust implementations accumulate tangents across all incident triangles at each vertex and orthogonalize the resulting vectors using Gram-Schmidt to ensure $\mathbf{T}$, $\mathbf{B}$, and $\mathbf{N}$ form an orthonormal frame.

Normal map textures typically store values in the range $[-1, 1]$ encoded as $[0, 1]$ by the transformation $(x + 1) / 2$. The fragment shader must decode by $2x - 1$ before transformation. Additionally, normal maps should be stored in linear color space, never gamma-corrected, because the values represent geometric directions, not perceptual intensities. Applying gamma correction to normal data produces incorrect lighting.

Filtering normal maps introduces subtle correctness issues. Bilinear filtering averages the encoded vector components, but averaging unnormalized vectors does not preserve length—the filtered normal must be explicitly renormalized in the shader. More fundamentally, averaging tangent-space normals from distant mip levels represents averaging surface orientations, which is geometrically questionable. At extreme minification, a normal map collapses to a single averaged normal, effectively becoming a constant normal map that loses all detail. This is typically acceptable because at such distances, pixel size exceeds surface detail, but it explains why normal-mapped surfaces lose apparent roughness at distance.

### Displacement Mapping and Tessellation

Displacement mapping extends normal mapping by actually offsetting surface geometry rather than merely perturbing lighting normals. A displacement map encodes scalar height values that offset vertices along their normal directions, creating genuine silhouette changes and self-occlusion that normal mapping cannot achieve. However, displacement requires sufficient geometric resolution to represent the displaced detail, as vertices can only be moved, not created.

Modern displacement mapping leverages hardware tessellation stages available in Direct3D 11 and OpenGL 4.0 onward. The tessellation control shader (hull shader in Direct3D) computes tessellation factors that determine how finely to subdivide input patches, typically based on screen-space projected edge length or distance from the camera. The fixed-function tessellator generates barycentric coordinates for new vertices within the patch domain, and the tessellation evaluation shader (domain shader) samples the displacement map at these coordinates to compute final vertex positions.

Adaptive tessellation avoids wasting geometry on distant or back-facing surfaces. The tessellation control shader computes per-edge tessellation factors $T_e$ based on projected screen-space length:

$$
T_e = \text{clamp}\left(L_{\text{screen}} \cdot k, T_{\min}, T_{\max}\right)
$$

where $L_{\text{screen}}$ is the edge length in pixels, $k$ is a density scaling factor, and $T_{\min}, T_{\max}$ are minimum and maximum tessellation levels to prevent over- or under-tessellation. The tessellator subdivides patch edges according to these factors, creating a smooth level-of-detail transition as the camera moves, though fractional tessellation factors introduce popping artifacts when vertices appear or disappear.

Displacement shader sampling must account for the same filtering concerns as color textures. Sampling a displacement map without mipmapping produces temporal aliasing as fine height details alias against the tessellated mesh resolution. However, mipmapping displacement maps is more complex than color because height values represent absolute offsets—averaging two height values of 0.1 and 0.9 yields 0.5, which may not correspond to any actual surface feature. Production displacement mapping therefore often uses handcrafted mip chains where artists manually filter height maps to preserve silhouette features at lower resolutions.

Displacement boundaries at UV seams require careful handling. If displacement values differ across a seam, the displaced surface tears, creating visible gaps. Artists must ensure displacement maps are continuous across seams, often by padding seam texels or using seamless tiling patterns. Alternatively, displacement can be restricted to interior vertices, leaving seam edges undisplaced to maintain continuity.

### Procedural Textures and Noise Functions

Procedural textures generate texture data algorithmically rather than sampling precomputed images, offering infinite resolution, zero storage cost, and parametric control over appearance. Perlin noise and its variants form the foundation of procedural texture synthesis, providing controllable pseudo-random functions with tunable frequency characteristics.

Perlin noise computes a smooth continuous function by interpolating random gradients at the integer lattice points of the input coordinates. For two-dimensional noise at position $(x, y)$, the algorithm hashes the four surrounding integer lattice points $(i, j), (i+1, j), (i, j+1), (i+1, j+1)$ to obtain random gradient vectors $\mathbf{g}_{00}, \mathbf{g}_{10}, \mathbf{g}_{01}, \mathbf{g}_{11}$. The fractional offsets $f_x = x - i, f_y = y - j$ define displacement vectors from each lattice point to the sample position. The noise value is computed by:

1. Taking the dot product of each gradient with its displacement vector: $d_{ij} = \mathbf{g}_{ij} \cdot (f_x - \Delta i, f_y - \Delta j)$
2. Interpolating horizontally using a smoothing function: $d_0 = \text{lerp}(d_{00}, d_{10}, s(f_x)), \quad d_1 = \text{lerp}(d_{01}, d_{11}, s(f_x))$
3. Interpolating vertically: $n = \text{lerp}(d_0, d_1, s(f_y))$

The smoothing function $s(t) = 3t^2 - 2t^3$ (cubic Hermite interpolation) ensures $C^1$ continuity—continuous first derivatives—eliminating the directional artifacts of linear interpolation. Improved Perlin noise uses a quintic polynomial $s(t) = 6t^5 - 15t^4 + 10t^3$ for $C^2$ continuity.

Simplex noise, Perlin's successor algorithm, improves computational efficiency and reduces directional artifacts by sampling from a simplex lattice (triangular in 2D, tetrahedral in 3D) rather than a hypercubic lattice. The number of vertices contributing to a sample grows linearly with dimension ($N+1$ for $N$-dimensional space) rather than exponentially ($2^N$ for hypercubes), making simplex noise preferable for high-dimensional noise.

Fractal Brownian Motion (fBM) constructs complex textures by summing octaves of noise at increasing frequencies and decreasing amplitudes:

$$
\text{fBM}(x) = \sum_{i=0}^{n-1} a^i \cdot \text{noise}(f^i \cdot x)
$$

where $f$ is the frequency multiplier (typically 2 for octave doubling), $a$ is the amplitude multiplier (typically 0.5 for $1/f$ noise), and $n$ is the number of octaves. This generates self-similar detail across scales, characteristic of natural phenomena like terrain, clouds, and wood grain. The Hurst exponent $H = -\log_f a$ controls roughness—higher $H$ yields smoother surfaces, lower $H$ produces rougher fractals.

Procedural texture shaders must balance computational cost against visual complexity. Evaluating multi-octave noise in the fragment shader consumes hundreds of arithmetic operations per pixel, easily becoming fragment-shader bound. Production implementations often bake procedural textures offline or use hybrid approaches where low-frequency components are computed procedurally and high-frequency detail is sampled from precomputed noise textures.

## 3. High-Performance Optimization & Failure Modes

### Texture Cache Optimization and Memory Layout

Texture sampling performance is dominated by memory bandwidth and cache hit rates. GPUs employ specialized texture caches organized as tag-based line caches with swizzled addressing to maximize spatial locality. Standard linear texture layout stores rows consecutively in memory, providing excellent cache performance for horizontal scanlines but poor locality for vertical access. Swizzled or tiled layouts rearrange texels into small square blocks (typically 4×4 or 8×8) stored contiguously, ensuring that nearby texels in both dimensions reside in the same cache line.

Compressed texture formats such as BCn (Block Compression) in Direct3D or ASTC (Adaptive Scalable Texture Compression) in Vulkan exploit this block structure by compressing entire 4×4 texel blocks into fixed-size bit patterns. BC1 (formerly DXT1) compresses RGB data to 4 bits per pixel by storing two RGB565 endpoint colors and a 2-bit per-pixel interpolation index, reducing memory bandwidth by 6× compared to uncompressed RGBA8. BC3 adds an 8-byte alpha channel stored separately, while BC5 optimizes for two-channel data like normal maps by storing only the X and Y components and reconstructing Z from $Z = \sqrt{1 - X^2 - Y^2}$.

Texture atlasing—packing multiple logical textures into a single large texture—reduces draw call counts by allowing a single material to reference multiple texture regions via adjusted UV coordinates. However, atlasing interacts poorly with mipmapping at atlas seam boundaries. When a texel near the atlas boundary is sampled with bilinear filtering, the filter kernel bleeds into adjacent atlas regions, causing visible color contamination. The standard mitigation is to add a half-texel border of duplicated edge texels around each atlas entry, ensuring that bilinear filtering samples only within the intended region. Trilinear filtering requires borders to be present in all mip levels, and anisotropic filtering requires even wider borders proportional to the maximum anisotropy level.

Virtual texturing or sparse texture systems address the memory limitations of high-resolution textures by treating textures as virtual memory pages that are demand-paged from disk into a physical texture cache. The Mega Texture technique pioneered by id Software divides a massive world-space texture into a page table hierarchy where only visible pages are resident in GPU memory. Fragment shaders translate virtual texture coordinates into page table lookups that resolve to physical texture coordinates, indirecting through a small indirection texture. Page misses generate feedback that triggers asynchronous streaming of required pages from storage.

Virtual texturing fundamentally alters the texture filtering contract. Because adjacent virtual pages may not be contiguous in physical memory, filtering across page boundaries requires special handling. The standard solution restricts bilinear filtering to page interiors and disables filtering near borders, accepting minor discontinuities at page seams. Anisotropic filtering is particularly problematic because the elongated sampling footprint spans multiple pages, requiring multiple page fetches and severely complicating the streaming heuristic. Production virtual texturing systems therefore often limit anisotropy or use lower anisotropic levels near page boundaries.

### Derivative-Based Level-of-Detail and Shader Divergence

Accurate mip level selection depends on screen-space derivatives computed from $2 \times 2$ pixel quads. This architectural constraint creates several failure modes. Dynamic branching in fragment shaders causes quads to execute both branch paths if any pixel in the quad diverges, a behavior called SIMD divergence. When texture sampling occurs within a conditional branch, the quad structure required for derivative calculation may be disrupted if different pixels take different branches. Modern GPUs handle this by either masking inactive pixels but still computing derivatives across the full quad (increasing redundant work) or by disabling derivative-dependent operations like mipmapped texture sampling within divergent branches.

Shaders that compute texture coordinates from complex expressions must ensure continuity for accurate derivative estimation. Discontinuous functions like floor, modulo, or conditional operators break the finite-difference approximation, causing the computed derivatives to be incorrect or infinite. The resulting mip level selection is unstable, producing temporal aliasing or excessively blurred textures. Shader compilers cannot generally detect these discontinuities, so developers must manually ensure texture coordinate expressions are piecewise smooth.

Explicit derivatives provide an escape hatch via textureLod or textureGrad sampling functions. textureLod accepts an explicit mip level $\lambda$, bypassing derivative calculation entirely and allowing texture sampling in non-uniform control flow. textureGrad accepts explicit partial derivatives $\partial u / \partial x, \partial u / \partial y, \partial v / \partial x, \partial v / \partial y$, allowing the developer to compute derivatives analytically or propagate them through custom transformations. Explicitly computed derivatives enable advanced techniques like ray-traced texture filtering, where screen-space derivatives are meaningless and must instead be computed from ray differentials or beam-tracing extent.

### Normal Map Authoring and Filtering Pathologies

Normal map generation from high-resolution geometry involves projecting surface normals onto a low-resolution mesh and encoding them in tangent space. The baking process must account for UV seams, ensuring that normals on both sides of a seam point in consistent directions when transformed to tangent space. Seam discontinuities produce lighting artifacts visible as bright or dark bands along seams because the interpolated tangent-space frame differs on each side, causing the same encoded normal to transform to different world-space directions.

Normal map compression introduces quantization error that becomes visible in smooth gradients. BC5 compression stores only two channels at 8 bits per component, reconstructing the third from the unit length constraint. This quantization produces banding in low-frequency normal variations, particularly noticeable under strong directional lighting. ASTC compression offers finer control over bitrate and quality but is more expensive to decode. Production pipelines often store normal maps in higher-precision formats like BC5_UNORM or uncompressed RG16F for hero assets and compress background geometry more aggressively.

Filtering normal maps at UV seams where tangent-space frames differ is geometrically incoherent. Averaging tangent-space normals expressed in different frames produces incorrect results. The only mathematically consistent solution is to transform normals to a common frame—typically world space or object space—before filtering, then transform the filtered result back to tangent space. However, object-space normal maps are not reusable across different meshes, and world-space filtering requires knowledge of the tangent frame during mipmap generation, which is unavailable offline. The practical compromise is to accept minor lighting discontinuities at seams in low mip levels, where they are less noticeable due to reduced screen-space resolution.

### Displacement Map Filtering and Silhouette Accuracy

Displacement mapping silhouette accuracy depends on tessellation density relative to displacement amplitude. If tessellation is too coarse, displaced geometry exhibits faceting and misses fine detail. If tessellation is too dense, vertex processing and memory bandwidth costs become prohibitive. Adaptive tessellation based on screen-space edge length provides a heuristic balance, but screen-space metrics alone cannot account for displacement amplitude—a surface with large displacement values requires denser tessellation than a surface with small displacements at the same screen-space scale.

Optimal tessellation factors require knowledge of the displacement map's frequency content. High-frequency displacement requires dense tessellation to avoid aliasing, while low-frequency displacement tolerates sparser geometry. Precomputed displacement metadata encoding maximum displacement gradients per mip level enables the tessellation control shader to compute provably sufficient tessellation factors, ensuring that no geometric aliasing occurs. However, this metadata is rarely generated in practice, leaving tessellation factors as artist-tuned parameters.

Displaced surfaces at glancing angles produce extreme tessellation factor anisotropy. An edge perpendicular to the view direction requires minimal tessellation, while an edge parallel to the view direction may span many pixels and require high tessellation. Isotropic tessellation—assigning the same factor to all edges of a patch—wastes geometry on edges that need less subdivision. Anisotropic tessellation addresses this by computing per-edge factors, but introduces T-junction vertices at patch boundaries where adjacent patches have different tessellation densities. These T-junctions create cracks in the displaced surface unless explicitly handled by constraining edge tessellation factors to be compatible across patches.

### Procedural Texture Aliasing and Domain Warping

Procedural noise functions alias when their frequency content exceeds the Nyquist limit, which occurs when the noise function is evaluated at scales smaller than the grid resolution. A 1D noise function with grid spacing 1.0 has a fundamental frequency of 1 cycle per unit. Evaluating this noise at a frequency of 10 cycles per unit by sampling at 0.1 unit intervals aliases the high-frequency components, producing Moiré patterns and temporal instability as the camera moves.

The solution is to dynamically adjust noise frequency based on screen-space derivatives, effectively computing a noise level-of-detail that matches the texture filtering concept. The noise function is evaluated at a base frequency $f_0 \cdot (1 / \max(\partial x / \partial x_s, \partial y / \partial y_s))$, where $\partial x / \partial x_s$ is the screen-space derivative of the world-space coordinate $x$. This scales the noise frequency inversely with the rate of change, ensuring that as surfaces recede and derivatives increase, the noise frequency decreases, preventing aliasing.

Domain warping—offsetting noise sample coordinates by other noise functions—produces intricate organic patterns but exacerbates aliasing because the domain distortion creates high-frequency discontinuities even when the underlying noise is band-limited. Filtering domain-warped noise requires prefiltering both the displacement and the base noise, which is computationally expensive and rarely practical in real-time shaders. Production implementations often bake warped procedural textures offline or limit domain warping to low-frequency components where aliasing is less severe.

Noise functions evaluated in texture space rather than world space create UV-dependent artifacts. If the UV parameterization is highly distorted, texture-space noise exhibits compressed and stretched regions that do not correspond to the geometric surface structure. World-space or object-space noise evaluation produces consistent detail independent of parameterization but breaks when objects are instanced or UV-mapped identically—all instances exhibit identical noise patterns. Randomizing the noise seed per instance or blending world-space and texture-space noise mitigates this at the cost of additional parameters and complexity.
