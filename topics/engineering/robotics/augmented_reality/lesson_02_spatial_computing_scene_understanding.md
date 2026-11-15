# Lesson 2: Spatial Computing—Scene Reconstruction, Semantic Understanding

## 1. First-Principles Intuition & Invariants

Spatial computing forms the perceptual foundation upon which autonomous robotic systems build situational awareness. Unlike passive computer vision, which merely classifies or detects objects in 2D imagery, spatial computing constructs a geometrically faithful, semantically enriched three-dimensional model of the environment—one that a robot can reason about, navigate through, and interact with in real time. This distinction is profound: a robot arm reaching toward an object must know not only *what* the object is (semantic label) but also *where* it exists in three-dimensional space, how it occludes other surfaces, and how that occlusion changes as the robot's viewpoint shifts.

The challenge arises because the physical world presents itself to robotic sensors as a torrent of raw measurements—RGB pixel streams, depth readings, inertial accelerations, and lidar point clouds—each carrying noise, ambiguity, and sensor-specific artifacts. Spatial computing must fuse these heterogeneous signals into a coherent geometric model while simultaneously extracting semantic meaning: identifying floors, walls, furniture, people, and task-relevant objects. This dual mandate—geometric reconstruction coupled with semantic understanding—defines the scope of modern robotic perception pipelines.

At the deepest level, spatial computing rests on the principle of *projective geometry*, which governs how three-dimensional points project onto camera sensors. When light from a scene point *P* (in world coordinates) passes through a camera's lens, it creates an image point *p* on the sensor array. This relationship, expressed through the camera intrinsic matrix **K** and extrinsic rotation-translation transformation **[R | t]**, establishes a deterministic but *underconstrained* mapping: many three-dimensional points project to the same pixel location. Resolving this ambiguity requires multiple viewpoints, depth measurements, or temporal coherence—the core reasoning behind multi-view geometry and time-sequential depth sensing.

The invariant constraint underlying all spatial reconstruction is *epipolar geometry*: given two camera views of the same scene, corresponding points must lie on conjugate epipolar lines. This principle, rooted in projective algebra, ensures that depth recovery algorithms can search efficiently along one-dimensional loci rather than traversing entire 2D images. For a robotic manipulator equipped with stereo cameras or a mobile platform carrying an RGB-D sensor, epipolar geometry becomes the mathematical scaffolding upon which real-time reconstruction unfolds.

Beyond geometric reconstruction, semantic understanding demands that the robot extract categorical meaning—not merely geometry. A robot tasked with clearing a table must distinguish between dishware, food remnants, and the table surface itself. This requires learning high-dimensional feature representations that capture both appearance (color, texture) and structural context (shape, size, spatial relationships). Modern robotic systems achieve this through learned representations—convolutional neural networks trained to map raw image patches into feature vectors that encode semantic categories. The union of these dense feature maps with geometric depth creates a *semantically annotated 3D model*, enabling robots to reason about task feasibility and object handling.

## 2. Core Architecture & Mechanics

### 2.1 Depth Acquisition Modalities and Signal Processing

A robotic spatial computing pipeline begins with depth acquisition. Three principal modalities dominate contemporary robotic systems: stereo vision, active structured light (time-of-flight and pattern projection), and lidar. Each trades off spatial resolution, temporal latency, operating range, and computational burden differently.

**Stereo Vision** operates on the principle of triangulation: two calibrated cameras with known baseline separation and intrinsic parameters observe the same scene point from different angles. The horizontal offset (disparity) between corresponding pixels encodes depth inversely: *Z = (f × b) / d*, where *f* is focal length, *b* is baseline, and *d* is disparity in pixels. The computational bottleneck lies in the correspondence problem—identifying which pixel in the left image corresponds to which in the right. Naive exhaustive search across all possible disparities (typically 0–255 pixels for indoor robotics) yields O(width × height × disparity_range) operations per frame. Modern implementations exploit the epipolar constraint to restrict the search to a one-dimensional line in the right image, reducing complexity to O(width × disparity_range). Further acceleration comes from semi-global matching (SGM) algorithms, which penalize disparity discontinuities while preserving object boundaries, delivering depth maps at 20–60 fps on commodity GPUs.

The raw stereo disparity map carries inherent noise: occlusion boundaries (where one camera sees an edge and the other does not), poorly textured regions (where correspondence fails), and sensor quantization artifacts. Post-processing via median filtering, bilateral upsampling, and temporal consistency checks (comparing consecutive frames and rejecting outliers exceeding a motion threshold) improves depth map stability. For a mobile manipulator operating at 10 Hz, temporal filtering becomes crucial: a single noisy depth spike can trigger a collision-avoidance response.

**Active Structured Light** systems project a coded pattern (grid, stripes, or pseudorandom dots) onto the scene, then observe the pattern deformation to infer depth. Time-of-flight (ToF) sensors modulate infrared light and measure the phase shift between emission and reflection; depth is proportional to the measured phase. Pattern-projection systems (like Kinect v1) encode spatial structure directly: each dot position in the reference pattern has a unique identity, so the correspondence problem becomes a lookup rather than a search. These approaches excel in textureless environments (white walls, reflective surfaces) where stereo stereo fails catastrophically. Their disadvantage is ambient light interference: bright sunlight or competing infrared projectors degrade signal quality. ToF sensors also suffer from multipath interference in specular environments, where light bounces multiple times before reaching the sensor, causing errant depth measurements at material boundaries. For robotic bin-picking in industrial settings with consistent artificial lighting, structured light is a workhorse; for outdoor mobile platforms, lidar dominates.

**Lidar (Light Detection and Ranging)** rotates a laser emitter and measures time-of-flight for each ray, producing a sparse 3D point cloud where density depends on angular resolution and rotation rate. A 16-channel automotive-grade lidar (Velodyne, Sick, etc.) scanning at 10 Hz with 0.2° angular resolution yields roughly 300K points per frame. Unlike passive stereo or structured light, lidar is immune to ambient light and texture; a mirror finish returns strong returns just as effectively as matte surfaces. The tradeoff is sparse sampling relative to dense stereo: a small robot hand might be invisible to lidar due to insufficient angular resolution, yet visible in stereo depth maps. Modern robotic platforms fuse multiple modalities: a lidar provides rapid, long-range environmental scanning for navigation, while stereo or RGB-D cameras on the manipulator arm furnish dense, high-resolution depth for grasping and object interaction.

### 2.2 3D Reconstruction: From Depth Maps to Structured Representations

Once depth measurements are acquired, the next challenge is organizing them into structures amenable to spatial reasoning. Raw depth maps are two-dimensional arrays of depth values; this format supports efficient filtering and registration but is unsuitable for semantic queries ("what objects are within 0.5 meters of the end-effector?") or collision checking. Three principal data structures dominate robotic spatial computing: point clouds, volumetric voxel grids, and implicit surface representations (signed distance fields).

**Point Cloud Representation** converts each pixel of a depth map into a 3D Euclidean coordinate via *back-projection*:

$$
\begin{bmatrix} X \\ Y \\ Z \end{bmatrix} = Z \cdot K^{-1} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}
$$

where *[u, v]* are pixel coordinates and **K** is the camera intrinsic matrix. For a depth map at 640×480 resolution with 30 fps capture, this yields 9.2 million 3D points per second per camera—manageable on modern hardware but demanding careful memory layout. Point clouds preserve geometric fidelity but are inherently sparse; no explicit topology connects neighboring points. Spatial queries require acceleration structures: octrees partition the point cloud into recursive cubes, enabling logarithmic-time neighbor searches. The ROS (Robot Operating System) ecosystem provides Point Cloud Library (PCL), which implements octree insertion, radius queries, voxel downsampling, and planar surface fitting optimized for robotics workflows.

Voxel grids discretize space into uniform cubes of fixed side length (e.g., 5 cm per voxel for a 5-meter workspace). Each voxel stores occupancy state: occupied, free, or unknown. This representation is computationally efficient for collision checking (a simple array lookup) and supports rapid spatial propagation algorithms (like wavefront planning). The tradeoff is resolution: doubling spatial extent (5 meters to 10 meters) increases grid size eightfold. For a fine-grained 1 cm voxel grid covering a 10-meter cube, memory consumption reaches 1 billion voxels; typical implementations use hierarchical structures (octrees or truncated signed distance field grids) to compress free-space regions.

**Hierarchical Octrees** subdivide occupied regions recursively, storing occupancy only where geometric detail demands it. An octree representing a robotic arm in free space uses minimal memory, allocating fine resolution only near the gripper and payload. Modern implementations like OctoMap (an ROS standard) support efficient ray-casting for line-of-sight queries and probabilistic occupancy updates when sensors provide conflicting measurements (e.g., one camera shows a voxel as occupied, another as free).

**Implicit Surface Representations**, specifically Truncated Signed Distance Fields (TSDFs), encode geometry as a continuous scalar field. Each spatial coordinate *(x, y, z)* maps to a scalar value: negative in free space, positive in occupied space, with magnitude representing distance to the nearest surface. TSDFs are particularly powerful for real-time dense reconstruction: as successive depth maps arrive from a moving camera, TSDF values update incrementally via running averages. When the reconstruction is complete, the zero-level set of the TSDF defines the implicit surface, extractable via marching cubes or screened Poisson reconstruction. TSDFs excel in dense, real-time settings; a collaborative robot scanning a bin of parts over multiple passes progressively refines the TSDF model without explicit point cloud registration.

### 2.3 Multi-View Registration and Simultaneous Localization and Mapping (SLAM)

A single depth measurement provides local geometry but no global context. A robot surveying a room must fuse depth maps from dozens of viewpoints into a coherent world model. This fusion process, termed *registration*, aligns point clouds or depth maps expressed in different coordinate frames into a single global coordinate system.

**Iterative Closest Point (ICP)** remains the canonical registration algorithm despite its age. Given two point clouds (source and target), ICP iteratively associates nearest-neighbor correspondences and solves for the rigid transformation (rotation and translation) minimizing point-to-point distance. Formally, it minimizes:

$$
E = \sum_{i=1}^{N} \| T(\mathbf{p}_i) - \mathbf{q}_i \|^2
$$

where *T* is a rigid transformation (6 degrees of freedom: 3 rotation, 3 translation) and each source point *p_i* is paired with its nearest target point *q_i*. ICP alternates between correspondence estimation (nearest-neighbor search, typically accelerated via KD-trees) and transformation estimation (solved via Singular Value Decomposition or Procrustes analysis). Convergence is guaranteed to a local minimum, but the basin of attraction is small: initial misalignment exceeding ~15 cm typically causes divergence. Practical robotic systems initialize ICP using odometry estimates or prior loop constraints to ensure alignment.

**Pose-Graph Optimization** extends registration to multi-view scenarios. As a robot moves through an environment, it acquires depth frames at distinct poses (position and orientation). Each consecutive pair of poses generates a relative transformation estimate via ICP. Crucially, when the robot revisits a previously-mapped region, loop closure detection algorithms identify revisit events and add geometric constraints linking distant poses. The pose graph becomes overconstrained; optimization via factor graphs (implemented in libraries like iSAM2 or g2o) solves for the maximum-likelihood pose estimates that best satisfy all pairwise constraints. This process corrects drift: odometry integration alone accumulates error proportional to path length, but loop closure anchors distant poses and redistributes error globally.

The tight coupling between depth acquisition, pose estimation, and map refinement defines Simultaneous Localization and Mapping (SLAM). Visual SLAM systems extract sparse feature keypoints (corner, edge, or blob detectors), track feature correspondences across frames, estimate camera motion via epipolar geometry, and triangulate landmarks. Dense SLAM variants, crucial for robotic manipulation, operate directly on depth maps, leveraging photometric consistency and depth gradients to drive camera pose estimation. The ORB-SLAM3 system, widely adopted in robotics, achieves sub-centimeter accuracy over hundreds-of-meters trajectories by integrating inertial measurements with visual tracking.

### 2.4 Occlusion Handling and Temporal Coherence

A critical challenge in spatial computing arises from *occlusion*: when one object blocks another from the camera's viewpoint, the occluded region receives no direct depth measurement. In robotic grasping, occlusion is ubiquitous—a pile of parts occludes the table surface; a gripper occludes the manipulated object. Naive reconstruction interpolates across occlusions, introducing topologically invalid geometry. Robust systems employ several strategies.

**Temporal Accumulation** fuses measurements across multiple frames, exploiting camera motion to view occluded regions from alternative angles. As a robot arm sweeps around an object, previously-hidden surfaces become visible. Multi-frame fusion via TSDF integration naturally handles occlusion: voxels occluded in one frame receive depth-not-available (no update), while unoccluded surfaces accumulate evidence across frames, progressively narrowing the confidence interval on surface position. Conservative occupancy marking (only marking voxels as occupied when multiple sensors agree) mitigates spurious occlusion claims.

**View Planning** generates active sensing trajectories that minimize occlusion. The robot computes a set of candidate viewpoints around an object, predicts which surfaces remain occluded from each viewpoint, and selects the viewpoint subset minimizing total occluded area subject to trajectory cost constraints. This greedy or global-optimization approach ensures that high-uncertainty regions receive additional measurements.

**Semantic Prior Integration** leverages object category knowledge to infer occluded geometry. If the system recognizes a coffee mug in partial occlusion, it can predict the mug's likely hidden shape based on learned category priors, filling gaps in direct measurements. This requires careful probabilistic treatment: inferred geometry has lower confidence than measured geometry, and predictions may fail for unusual object instances. Bayesian belief networks or probabilistic graphical models integrate semantic priors with measurement likelihood.

### 2.5 Semantic Segmentation: From Geometry to Understanding

Reconstructing geometry alone is insufficient for robotic task execution. A robot grasping objects from a table must distinguish between the table surface, grasping targets, and obstacles. Semantic segmentation—assigning a categorical label to each spatial voxel or pixel—bridges geometry and semantics.

Modern semantic segmentation in robotics relies on convolutional neural networks (CNNs) trained on labeled datasets. For a robotic bin-picking system, a typical approach uses a fully convolutional network (FCN) or U-Net architecture: the encoder downsamples input images via convolution and pooling, extracting hierarchical features; the decoder upsamples feature maps and fuses them with skip connections from earlier layers, restoring spatial resolution. The output is a dense per-pixel classification map assigning each pixel to a category (e.g., "part type A", "part type B", "background clutter").

Training such networks requires labeled datasets. For custom robotic systems, domain adaptation techniques reduce annotation burden. Synthetic rendering generates thousands of labeled images of objects in randomized poses and lighting; transfer learning from large-scale datasets (COCO, ImageNet) initializes network weights, and fine-tuning on a small corpus of real robotic data adapts the model to the specific camera, lighting, and object distribution encountered in deployment.

The geometry-semantics fusion pipeline integrates segmentation with spatial reconstruction:

1. **RGB Image Capture**: Acquire color image from robot camera.
2. **Depth Measurement**: Simultaneously capture depth via stereo, structured light, or lidar.
3. **CNN Inference**: Feed RGB image to trained segmentation network, obtaining per-pixel class probabilities.
4. **Back-projection**: Convert depth map to 3D point cloud, preserving pixel correspondences.
5. **Label Propagation**: Assign each 3D point the semantic label from its corresponding pixel.
6. **Semantic Point Cloud**: Output voxelized or raw point cloud with geometry and categorical labels.

This pipeline runs at 10–30 Hz on robots equipped with GPUs (NVIDIA Jetson platforms). For edge cases where GPU capacity is insufficient, model compression techniques (quantization, pruning, knowledge distillation) reduce inference latency without sacrificing accuracy.

### 2.6 Object Recognition and Pose Estimation

Semantic segmentation identifies *what* objects are present; object pose estimation determines *where* and *how* they are oriented. For manipulation, precise pose estimates are essential: a gripper approaching a cylindrical part must align with the part's axis and position the gripper fingertips at the friction-optimal grasp locations.

**6D Pose Estimation** recovers both position (3D translation) and orientation (3D rotation) relative to the world frame or robot base. Given a segmented point cloud belonging to an object of known 3D CAD model, the problem reduces to rigid alignment: find the pose (rotation **R** and translation **t**) that best aligns the model to the observed point cloud. This is formulated as:

$$
\min_{R, t} \sum_{i=1}^{N} \| R \mathbf{m}_i + \mathbf{t} - \mathbf{o}_i \|^2
$$

where **m_i** are model points and **o_i** are observed points. Optimization proceeds via:

1. **Correspondence Initialization**: Nearest-neighbor or learned descriptor matching establishes tentative point-to-point associations.
2. **Outlier Rejection**: RANSAC or robust M-estimators downweight misaligned points, focusing on inliers.
3. **Pose Refinement**: Singular Value Decomposition or nonlinear optimization (Levenberg-Marquardt) solves for optimal **R** and **t**.

For objects with ambiguous symmetries (cylinders, spheres), multiple poses may be geometrically equivalent; recognition systems must evaluate all symmetrically-equivalent candidates and select the pose consistent with gripper workspace or task constraints.

**Learned 6D Pose Estimation** trains neural networks to predict pose directly from RGB-D input. Networks like DenseFusion extract dense feature descriptors from each pixel via FCNs, aggregate features via iterative refinement, and regress 6D pose parameters. These approaches circumvent explicit CAD models, enabling rapid deployment to new object categories with modest retraining.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Computational Pipeline Optimization

Robotic spatial computing operates under strict real-time constraints: autonomous systems must perceive, plan, and act at deterministic frequencies (10–30 Hz for navigation, 100+ Hz for manipulation). Latency budgets for spatial computing are typically 30–100 milliseconds; a single slow algorithm can violate hard deadlines.

**Memory Hierarchy and Cache Efficiency** dominate performance. Point cloud processing via nested loops over 300K points easily cache-misses at every iteration. Optimized implementations tile point clouds into cache-aligned blocks, process points in sequential memory order, and minimize pointer indirection. For depth map processing, row-major layout matches memory access patterns; column-major access patterns incur page faults on large images.

**GPU Acceleration** is essential for inference-heavy pipelines. Semantic segmentation networks require GPU execution; CPU-only inference on dense depth maps yields 1–2 fps, inadequate for real-time robotics. Multi-GPU systems pipeline stages: while GPU0 processes segmentation on frame *n*, GPU1 handles pose estimation for frame *n-1*, and GPU2 updates the voxel grid. Careful synchronization via event-based signaling prevents pipeline stalls.

**Hierarchical Data Structures** enable coarse-to-fine algorithms that trade accuracy for latency. Octrees allow rapid rejection of distant voxels; spatial queries against a 1000×1000×1000 voxel grid complete in O(log N) time. Downsampled representations (voxel grids at 10 cm resolution) enable rapid planning and collision checking, while fine detail (1 cm voxels) is computed only for high-precision manipulation tasks.

**Asynchronous Processing** decouples sensor polling from computation. Sensor callbacks enqueue measurements; a background thread processes the queue, updating maps incrementally. If processing falls behind sensor acquisition, older frames are dropped; recent measurements always receive processing priority.

### 3.2 Failure Modes and Robustness Strategies

**Textureless Region Failures in Stereo**: Poorly-textured surfaces (white walls, glass) yield no reliable stereo correspondence. Solution: augment stereo with active sensing (structured light or lidar) in such regions. Hybrid systems switch modality based on texture confidence metrics estimated from image gradients.

**Multipath Interference in ToF Lidar**: Reflective or transparent materials cause multiple reflections, yielding errant depth values. Characterization shows systematic errors at material boundaries. Mitigation: apply learned correction models trained on calibration data; flag pixels exhibiting multipath signatures for reliability weighting.

**Loop Closure Failures**: Revisit detection based on visual similarity (bag-of-words, place recognition networks) occasionally produces false positives, introducing contradictory loop constraints that corrupt the global map. Solution: apply geometric consistency checks before accepting loop constraints; verify that the proposed loop closure is consistent with odometry and existing constraints within a probabilistic bound.

**Semantic Segmentation Hallucination**: Deep networks occasionally misclassify scenes due to distribution shift (objects or lighting not present in training data). A robot relying blindly on segmentation labels may grasp incorrectly. Mitigation: integrate segmentation with geometric reasoning; if segmentation assigns "metal part" to a region but geometric analysis reveals it's reflective glass (high specularity), flag the classification as uncertain and apply alternative strategies (e.g., request human intervention or default to safe fallback behaviors).

**Drift in
