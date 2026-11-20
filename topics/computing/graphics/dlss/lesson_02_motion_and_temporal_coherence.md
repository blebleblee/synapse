# Lesson 2: Motion Vectors, Temporal Accumulation, and Coherence Preservation

## 1. First-Principles Intuition & Invariants

Deep learning super-resolution operates under a fundamental constraint that distinguishes it from classical spatial upsampling: temporal coherence. When DLSS reconstructs a 4K frame from 1080p input, it does not view each frame as an isolated image problem. Instead, the neural network exploits the fact that consecutive frames in real-time rendering share substantial geometric and shading continuity. A surface visible at pixel coordinate (512, 384) in frame N will likely appear at a nearby coordinate in frame N+1, displaced only by camera motion, object animation, or dynamic lighting changes. This temporal locality creates an opportunity to accumulate high-frequency detail across multiple low-resolution observations, effectively synthesizing information that no single input frame contains.

The mathematical foundation for this accumulation strategy rests on the observation that aliasing in undersampled rendering is not merely a loss of detail but a systematic scrambling of high-frequency signal components into lower frequency bands. When a geometric edge intersects a pixel center at slightly different sub-pixel offsets across successive frames, the resulting intensity samples form a sequence of measurements that, when properly aligned and weighted, can reconstruct the true continuous signal at super-resolution. Classical temporal anti-aliasing techniques like TAA exploit this principle through exponential moving averages, but they operate in screen space without semantic understanding of scene geometry. DLSS extends this approach by coupling motion-compensated history buffers with a convolutional neural network trained to distinguish genuine sub-pixel detail from stochastic noise, reflections, and disocclusion artifacts.

Motion vectors serve as the geometric bridge between frames, encoding per-pixel screen-space velocity that describes how rendered geometry flows from one frame to the next. In modern graphics pipelines, these vectors are generated during vertex and pixel shading by computing the difference between current and previous frame positions for each surface point. The vertex shader transforms each vertex position using both the current view-projection matrix and the previous frame's cached matrix, outputting two clip-space coordinates. The rasterizer interpolates these coordinates across triangle faces, and the pixel shader writes the velocity delta to a dedicated motion vector buffer. This buffer typically uses a 16-bit floating-point RG texture format, storing signed horizontal and vertical displacements in normalized device coordinates. For a 1080p render target upscaling to 4K, each motion vector represents a screen-space derivative that DLSS uses to warp the previous frame's accumulated history into alignment with the current geometric configuration.

The invariant that governs all temporal accumulation schemes is the conservation of energy under motion compensation. When a pixel at coordinate (x, y) in frame N corresponds to coordinate (x + dx, y + dy) in frame N-1, the radiance values at these two locations should be identical in the absence of view-dependent effects, occlusion changes, or emissive variation. This assumption holds rigorously for diffuse surfaces under static lighting and approximately for specular surfaces when the view direction change is small relative to the BRDF lobe width. Violations of this invariant manifest as ghosting artifacts—translucent trails that persist when reprojected history fails to match current geometry. DLSS mitigates these failures through a three-stage validation process: motion vector confidence scoring, neighborhood color clamping, and neural disocclusion detection. The network learns to assign low confidence to pixels where reprojected history exhibits luminance discontinuities, texture mismatch, or geometric implausibility, triggering a graceful fallback to spatial reconstruction.

Temporal stability in neural super-resolution also depends on maintaining consistent jitter patterns across frames. DLSS operates on jittered input, where the projection matrix applies a sub-pixel offset that varies deterministically each frame according to a low-discrepancy sequence such as Halton or R2. This jitter distributes sampling locations across the super-resolution grid over time, ensuring that every output pixel eventually receives a direct input sample. For 2× upscaling, a 2×2 pixel quad in the output corresponds to a single input pixel, and a four-frame jitter cycle ensures each quadrant receives one centered sample. Without this coordinated jitter, the network would attempt to infer detail from input samples that systematically miss the same sub-pixel regions, leading to spatial frequency biases and shimmering. The jitter offset is fed to DLSS as an explicit input parameter, allowing the network to account for the known sampling shift when interpreting pixel intensities and gradients.

## 2. Core Architecture & Mechanics

The motion vector generation pipeline begins in the vertex shader, where each vertex receives transformation by both current and previous frame matrices. The vertex structure includes a world-space position, and the shader maintains a per-draw-call uniform buffer containing the current view-projection matrix alongside a cached copy from the prior frame. For animated geometry, skeletal or blend-shape transformations must be applied using both current and previous pose data, requiring dual bone matrix palettes or morph target weights. The shader computes two clip-space positions: the current frame position via standard transformation, and the previous frame position by applying the cached matrix to the previous vertex state. These positions are written to separate interpolants and passed to the pixel shader.

```text
// Vertex shader motion vector generation
struct VertexInput {
    float3 position : POSITION;
    float3 previousPosition : TEXCOORD0;
    uint4 boneIndices : BLENDINDICES;
    float4 boneWeights : BLENDWEIGHTS;
};

struct VertexOutput {
    float4 positionCS : SV_POSITION;
    float4 currentClip : TEXCOORD0;
    float4 previousClip : TEXCOORD1;
};

cbuffer FrameConstants : register(b0) {
    float4x4 viewProjection;
    float4x4 previousViewProjection;
    float4x4 boneMatrices[256];
    float4x4 previousBoneMatrices[256];
};

VertexOutput VSMain(VertexInput input) {
    VertexOutput output;
    
    // Skinning for current frame
    float4x4 skinMatrix = 
        boneMatrices[input.boneIndices.x] * input.boneWeights.x +
        boneMatrices[input.boneIndices.y] * input.boneWeights.y +
        boneMatrices[input.boneIndices.z] * input.boneWeights.z +
        boneMatrices[input.boneIndices.w] * input.boneWeights.w;
    
    float3 skinnedPosition = mul(skinMatrix, float4(input.position, 1.0)).xyz;
    
    // Skinning for previous frame
    float4x4 prevSkinMatrix = 
        previousBoneMatrices[input.boneIndices.x] * input.boneWeights.x +
        previousBoneMatrices[input.boneIndices.y] * input.boneWeights.y +
        previousBoneMatrices[input.boneIndices.z] * input.boneWeights.z +
        previousBoneMatrices[input.boneIndices.w] * input.boneWeights.w;
    
    float3 prevSkinnedPosition = mul(prevSkinMatrix, float4(input.previousPosition, 1.0)).xyz;
    
    // Project to clip space
    output.currentClip = mul(viewProjection, float4(skinnedPosition, 1.0));
    output.previousClip = mul(previousViewProjection, float4(prevSkinnedPosition, 1.0));
    output.positionCS = output.currentClip;
    
    return output;
}
```

In the pixel shader, the interpolated clip-space coordinates undergo perspective division to yield normalized device coordinates (NDC), where X and Y range from -1 to +1. The motion vector is computed as the difference between current and previous NDC positions, scaled by 0.5 to convert from the symmetric [-1, 1] range to a [0, 1] texture coordinate space. For surfaces that were occluded in the previous frame or did not exist, the pixel shader must write a sentinel value or zero vector, signaling to DLSS that no valid history exists at this location. Depth testing complications arise when a surface is visible in the current frame but was occluded previously—the depth buffer from frame N-1 may contain a different surface's depth, making the reprojected coordinate geometrically invalid. Some engines resolve this by writing motion vectors before depth testing, while others use a depth comparison threshold to invalidate vectors where the reprojected depth differs significantly from the stored history depth.

```text
// Pixel shader motion vector output
struct PixelInput {
    float4 positionCS : SV_POSITION;
    float4 currentClip : TEXCOORD0;
    float4 previousClip : TEXCOORD1;
};

struct PixelOutput {
    float2 motionVector : SV_Target0;
};

PixelOutput PSMain(PixelInput input) {
    PixelOutput output;
    
    // Perspective divide to get NDC positions
    float2 currentNDC = input.currentClip.xy / input.currentClip.w;
    float2 previousNDC = input.previousClip.xy / input.previousClip.w;
    
    // Compute velocity in NDC space, scale to [0, 1] texture coordinates
    float2 velocity = (currentNDC - previousNDC) * 0.5;
    
    output.motionVector = velocity;
    return output;
}
```

The temporal accumulation buffer forms the core of DLSS's history management. This buffer stores the previously reconstructed super-resolution frame at full output resolution—4K for a 1080p input rendering at 2× scale. During each frame's DLSS invocation, the network reads both the current low-resolution input and the warped history buffer, blending them according to learned confidence weights. The warping operation uses the motion vector texture to sample the history buffer at offset coordinates: for each output pixel (x, y), the shader reads the motion vector at the corresponding input pixel coordinate (x/2, y/2), scales it to output resolution, and samples the history buffer at (x - dx, y - dy). This reprojection step requires bilinear filtering to handle sub-pixel motion vector precision, as motion vectors are generated at the lower input resolution but applied at the higher output resolution.

```text
// Temporal history reprojection
Texture2D<float4> historyBuffer : register(t0);
Texture2D<float2> motionVectors : register(t1);
SamplerState linearSampler : register(s0);

float4 ReprojectHistory(float2 outputUV, float2 upscaleFactor) {
    // Convert output UV to input resolution UV
    float2 inputUV = outputUV;
    
    // Sample motion vector at input resolution
    float2 motion = motionVectors.SampleLevel(linearSampler, inputUV, 0);
    
    // Convert motion vector from normalized coordinates to texture UV offset
    // Motion vectors are in [-1, 1] NDC space, scaled by 0.5 to [-0.5, 0.5]
    float2 historyUV = outputUV - motion;
    
    // Clamp to valid texture bounds
    if (historyUV.x < 0.0 || historyUV.x > 1.0 || 
        historyUV.y < 0.0 || historyUV.y > 1.0) {
        return float4(0.0, 0.0, 0.0, 0.0); // Invalid history
    }
    
    // Sample reprojected history
    return historyBuffer.SampleLevel(linearSampler, historyUV, 0);
}
```

DLSS's neural network architecture processes this reprojected history alongside the current input through a U-Net style encoder-decoder with residual connections. The encoder progressively downsamples the concatenated input (current frame, history, motion vectors, depth, and exposure metadata) through strided convolutions, extracting multi-scale features that capture both local texture detail and global scene context. The decoder upsamples these features back to output resolution using transposed convolutions or nearest-neighbor upsampling followed by refinement convolutions. Crucially, the network includes temporal fusion layers that compute per-pixel blending weights between the upsampled current frame and the reprojected history. These weights are not hand-tuned heuristics but learned functions that respond to input features indicating motion discontinuities, disocclusions, or lighting changes. The final output is a weighted blend that maximizes temporal stability where history is valid and gracefully falls back to spatial reconstruction where history is unreliable.

The confidence metric for temporal blending derives from multiple geometric and photometric cues. Geometric confidence is highest when the motion vector magnitude is small relative to the pixel size, indicating minimal camera or object motion. Photometric confidence is computed by comparing the luminance of the reprojected history pixel to the neighborhood of current frame pixels in a 3×3 or 5×5 window around the corresponding input location. If the reprojected color falls outside the min-max range of this neighborhood—a condition known as color clamping violation—it signals that the history does not match current scene content, likely due to disocclusion or a specular highlight change. DLSS also incorporates reactive masks, which are optional artist-authored or procedurally generated per-pixel flags indicating regions where temporal accumulation should be reduced, such as alpha-tested foliage, transparent effects, or HUD elements that move independently of the 3D scene.

```text
// Temporal confidence evaluation
float ComputeTemporalConfidence(
    float3 currentColor,
    float3 reprojectedColor,
    float2 motionVector,
    Texture2D<float3> currentInput,
    float2 inputUV,
    SamplerState pointSampler)
{
    // Geometric confidence: penalize large motion
    float motionMagnitude = length(motionVector);
    float geometricConfidence = saturate(1.0 - motionMagnitude * 10.0);
    
    // Photometric confidence: neighborhood color clamping
    float3 colorMin = float3(1e6, 1e6, 1e6);
    float3 colorMax = float3(-1e6, -1e6, -1e6);
    
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            float2 offset = float2(dx, dy) / float2(1920.0, 1080.0); // Input resolution
            float3 neighborColor = currentInput.SampleLevel(pointSampler, inputUV + offset, 0);
            colorMin = min(colorMin, neighborColor);
            colorMax = max(colorMax, neighborColor);
        }
    }
    
    // Check if reprojected color is within neighborhood bounds
    float3 colorDelta = max(reprojectedColor - colorMax, colorMin - reprojectedColor);
    float colorError = max(colorDelta.r, max(colorDelta.g, colorDelta.b));
    float photometricConfidence = saturate(1.0 - colorError * 5.0);
    
    return geometricConfidence * photometricConfidence;
}
```

The network's training process exposes it to thousands of hours of rendered game content, where ground truth super-resolution targets are generated by rendering at native 4K resolution with high sample counts and temporal anti-aliasing. Training pairs consist of jittered 1080p input frames, their corresponding motion vectors, depth, and history buffers, alongside the 4K reference output. The loss function combines perceptual metrics like LPIPS (Learned Perceptual Image Patch Similarity), which uses VGG feature distances to measure high-level texture similarity, with pixel-wise L1 or L2 losses that enforce color accuracy. Temporal stability is explicitly regularized by including consecutive frame pairs in the training batches and penalizing perceptual flicker metrics that measure high-frequency temporal variation in static regions. This multi-objective optimization teaches the network to balance spatial sharpness against temporal coherence, avoiding the over-sharpening artifacts that plague naive spatial upsampling while suppressing the ghosting that undermines pure temporal accumulation.

## 3. High-Performance Optimization & Failure Modes

Temporal accumulation introduces latency and memory bandwidth constraints that critically impact DLSS's real-time performance profile. The history buffer must be read and written every frame at full output resolution, translating to 3840×2160×4 bytes (RGBA8) or approximately 33 MB per frame at 4K. At 60 Hz, this represents nearly 2 GB/s of memory traffic before accounting for motion vector reads, depth buffer access, and the neural network's internal activations. GPU memory bandwidth on contemporary high-end cards reaches 600-900 GB/s, but this capacity is shared among all rendering operations, texture sampling, and framebuffer writes. DLSS mitigates this pressure through aggressive texture compression—using BC6H or BC7 formats for the history buffer where applicable—and by leveraging GPU cache hierarchies. The reprojection shader exhibits good spatial locality because consecutive output pixels typically sample nearby history buffer locations due to motion vector coherence, allowing the L2 cache to absorb repeated accesses.

Disocclusion represents the most challenging failure mode for temporal techniques. When a previously occluded surface becomes visible—such as an object emerging from behind a wall during camera rotation—no valid history exists for the newly exposed pixels. The motion vector at the disoccluded location points to the occluder's surface in the previous frame, causing the reprojection to sample incorrect color data. Classical TAA handles this through aggressive color clamping, which constrains the reprojected history to lie within the current frame's neighborhood color distribution. However, strict clamping discards valuable temporal information and reintroduces aliasing. DLSS addresses disocclusion through learned disocclusion masks, where the network detects geometric inconsistencies between the current depth buffer and the reprojected depth derived from the previous frame's depth and motion vectors. When depth mismatch exceeds a threshold, the network reduces the history contribution and relies more heavily on spatial hallucination from the current frame's texture gradients and learned priors.

```text
// Disocclusion detection via depth comparison
float DetectDisocclusion(
    float currentDepth,
    float2 outputUV,
    float2 motionVector,
    Texture2D<float> previousDepthBuffer,
    SamplerState linearSampler)
{
    // Reproject current depth to previous frame's screen space
    float2 previousUV = outputUV - motionVector;
    
    if (previousUV.x < 0.0 || previousUV.x > 1.0 || 
        previousUV.y < 0.0 || previousUV.y > 1.0) {
        return 0.0; // Off-screen in previous frame, definite disocclusion
    }
    
    // Sample depth at reprojected location
    float previousDepth = previousDepthBuffer.SampleLevel(linearSampler, previousUV, 0);
    
    // Compare depths: if current surface is significantly closer than expected,
    // it was likely occluded in the previous frame
    float depthThreshold = 0.01; // Scene-dependent tuning required
    float depthDifference = abs(currentDepth - previousDepth);
    
    return (depthDifference < depthThreshold) ? 1.0 : 0.0;
}
```

Specular aliasing and view-dependent effects challenge the motion vector paradigm because surface radiance varies with view direction in ways that pure geometric reprojection cannot capture. A glossy surface reflecting a bright light source will exhibit specular highlights that shift position relative to surface geometry as the camera moves. The motion vector describes the surface point's trajectory, but the highlight's position on that surface changes due to the altered reflection vector. When DLSS accumulates history based on geometric motion alone, these highlights smear and ghost, creating distracting temporal instability. Advanced engines address this by writing separate motion vectors for reflection rays, tracing the reflected view direction in both current and previous frames to compute where the reflection sample originated in screen space. This reflection motion vector is blended with geometric motion vectors according to surface roughness: smooth surfaces use reflection-based reprojection, while rough diffuse surfaces use geometric reprojection.

Particle effects and alpha-blended transparency break the assumption of surface permanence that underlies motion vector generation. A smoke particle or glass surface does not have a single well-defined depth or motion vector; instead, it represents a volume or a composite of multiple layers. Standard motion vector generation writes a single vector per pixel, which for transparent surfaces typically represents either the frontmost opaque layer or an artist-specified reference point. DLSS's reactive mask mechanism allows engines to mark these problematic regions, instructing the network to reduce temporal accumulation strength and rely more on per-frame spatial reconstruction. For particle systems, some engines render particles into a separate buffer with independent jitter and temporal accumulation tuned for volume effects, compositing this buffer onto the main DLSS output in a final pass.

Jitter pattern selection directly influences temporal stability and convergence speed. The Halton sequence, commonly used for its low-discrepancy properties, generates sample points that are well-distributed across the unit square over time. For a 2×2 output pixel quad corresponding to one input pixel, a four-frame jitter cycle based on Halton(2,3) ensures each quadrant receives an exact sample. However, periodic jitter patterns can create resonance artifacts when scene motion is correlated with the jitter frequency—for example, a camera panning at exactly one pixel per frame can cause the jitter to systematically miss certain spatial frequencies. Some engines employ stochastic jitter with a blue noise distribution to break periodicity, trading deterministic convergence for reduced pattern artifacts. DLSS itself is robust to various jitter patterns because the network learns to infer the jitter offset from input metadata and adapts its spatial reconstruction filters accordingly.

Temporal history buffer precision also impacts quality, particularly in high dynamic range rendering pipelines. A standard RGBA8 history buffer introduces quantization artifacts in dark regions where 8-bit precision cannot represent subtle gradients. High-end implementations use RGBA16F or RGB10A2 formats, trading increased memory bandwidth for reduced banding. The network's training data determines the expected precision: if DLSS was trained on 16-bit ground truth targets, deploying it with an 8-bit history buffer can degrade quality because the network's learned statistics no longer match the runtime input distribution. This mismatch manifests as over-sharpening in bright regions and loss of shadow detail, as the network attempts to compensate for noise it expects but that quantization has removed.

Ghosting suppression tuning represents a persistent challenge in production deployments. Overly aggressive history rejection preserves sharpness in disoccluded regions but sacrifices the temporal stability that DLSS provides, resulting in shimmering fine detail and unstable edges. Conversely, overly permissive history accumulation creates trailing artifacts on fast-moving objects and residual smearing after camera cuts. DLSS exposes tuning parameters for integration engineers to control this tradeoff, including a sharpness multiplier that adjusts the network's output post-processing filter, and a reset flag that clears history buffers on scene transitions. Some engines implement heuristic history invalidation, detecting large camera velocity changes or depth buffer discontinuities that indicate a cut, and signaling DLSS to discard history. The network's internal learned confidence mechanisms provide a baseline that works well across most content, but edge cases in specific games require manual tuning to align quality with artistic intent.
