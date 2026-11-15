# Operational Verification Labs: Augmented Reality

## Objective & Operational Lab Setup

Augmented Reality (AR) integration into robotic systems demands rigorous verification protocols that span sensor fusion accuracy, spatial registration stability, real-time rendering latency, and environmental robustness. This laboratory sequence trains practitioners to validate AR subsystems through quantitative measurement, stress testing under degraded conditions, and recovery protocol development. Unlike consumer AR applications optimized for visual appeal, robotic AR must maintain sub-centimeter spatial accuracy, deterministic frame rates, and graceful degradation under sensor occlusion, lighting extremes, and computational load spikes.

The operational context for these exercises centers on a robotic manipulator equipped with an RGB-D camera (Intel RealSense D435i or equivalent depth sensor providing 1280×720 resolution at 30 Hz with IMU fusion), a head-mounted display or tablet interface running ARCore/ARKit frameworks, and a computational platform delivering at least 4.0 GFLOPS sustained performance for simultaneous localization and mapping (SLAM) processing. The target manipulator operates within a structured workspace containing fiducial markers (AprilTags from the 36h11 family, printed at 150 mm square with 12.7 mm white borders on matte card stock to minimize specular reflections), calibration boards with checkerboard patterns (9×6 internal corners, 25 mm square size), and task-relevant objects whose CAD models are pre-loaded into the AR rendering pipeline.

Your analytical research environment requires MATLAB R2023b or Python 3.10 with NumPy 1.24, SciPy 1.10, OpenCV 4.8 (with contrib modules for ArUco/AprilTag detection), and Open3D 0.17 for point cloud manipulation. Install ROS 2 Humble on Ubuntu 22.04 to interface with the camera driver and manipulator controller, ensuring message timestamps synchronize across tf2 transform trees with sub-millisecond precision. For AR framework interaction, deploy Unity 2022.3 LTS with AR Foundation 5.0, configured to export telemetry logs capturing frame-to-frame pose deltas, feature point counts, and rendering pipeline stage timings. Statistical analysis demands R 4.3 with ggplot2, lme4 for mixed-effects modeling, and psych packages for reliability coefficients.

Hardware calibration precedes all exercises. Mount the RGB-D camera to the manipulator end-effector via a rigid aluminum bracket, ensuring the optical axis remains perpendicular to the mounting plane within 0.5 degrees (verify with a digital inclinometer). Perform intrinsic calibration using the checkerboard pattern: capture 30 images across the full field of view, varying distance from 0.3 to 1.2 meters and orientation from −30 to +30 degrees in roll, pitch, and yaw. Execute Zhang's method to extract the 3×3 camera matrix K and five-parameter radial-tangential distortion vector, achieving reprojection error below 0.3 pixels RMS. Record the extrinsic transform from camera frame to end-effector flange using hand-eye calibration: move the manipulator through 20 distinct poses while observing a fixed AprilTag, then solve the AX = XB equation via Tsai-Lenz dual quaternion optimization to obtain the 4×4 homogeneous transformation matrix with translation accuracy within 2 mm and rotation within 1 degree.

Workspace preparation establishes ground truth. Affix six AprilTags to the workspace perimeter at known 3D coordinates measured with a laser distance meter (±1 mm accuracy), forming a reference frame spanning at least 1.5 × 1.5 × 0.8 meters. Use photogrammetry or a coordinate measuring machine (CMM) to validate tag center positions, then encode these ground truth poses into a YAML configuration file mapping tag IDs to SE(3) transformations. This reference frame enables absolute pose error quantification throughout the verification protocol.

Diagnostic instrumentation centers on empirical audit rubrics tracking six key performance indicators: absolute pose error (APE) measuring the Euclidean distance between estimated and ground truth camera positions, relative pose error (RPE) quantifying frame-to-frame drift accumulation, tracking robustness expressed as the percentage of frames maintaining valid SLAM state, rendering latency from sensor capture to display photon emission, feature density reporting the number of SLAM map points per cubic meter, and computational headroom defined as the ratio of available to consumed CPU cycles per frame. Each exercise specifies target thresholds derived from robotic manipulation requirements: AR overlays guiding pick-and-place operations demand APE < 5 mm, while teleoperation interfaces tolerate APE < 20 mm but require latency < 50 ms to prevent operator disorientation.

## Exercise 1: Foundational Practical Implementation

### Baseline SLAM Initialization and Pose Estimation Accuracy

This foundational exercise establishes the nominal operating regime for your AR system by quantifying pose estimation accuracy under controlled laboratory conditions. You will initialize the SLAM pipeline, verify spatial registration against ground truth fiducials, and characterize the statistical distribution of pose errors across a representative motion trajectory.

Begin by launching the RGB-D camera driver and verifying data stream integrity. Execute `ros2 launch realsense2_camera rs_launch.py enable_gyro:=true enable_accel:=true unite_imu_method:=1` to activate the D435i with IMU fusion, then confirm publication of `/camera/color/image_raw` (sensor_msgs/Image), `/camera/aligned_depth_to_color/image_raw` (sensor_msgs/Image), and `/camera/imu` (sensor_msgs/Imu) topics at 30, 30, and 200 Hz respectively using `ros2 topic hz`. Inspect a depth frame with `ros2 run image_view image_view image:=/camera/aligned_depth_to_color/image_raw` to verify absence of dead pixels, excessive noise (depth standard deviation should remain below 15 mm at 1 m distance), or systematic bias (measure a calibrated target at known distances from 0.5 to 2.0 m, confirming error < 2% across the range).

Initialize the ORB-SLAM3 pipeline configured for RGB-D input with IMU fusion. Clone the repository and compile with `cd ORB_SLAM3 && ./build.sh`, then create a camera configuration YAML specifying the intrinsic matrix, distortion coefficients, depth scale factor (0.001 for RealSense outputting depth in millimeters), and IMU noise parameters (gyroscope random walk 1.7e-4 rad/s/√Hz, accelerometer random walk 2.0e-3 m/s²/√Hz for D435i). Launch SLAM with `./Examples/RGB-D-Inertial/rgbd_inertial_realsense_D435i ./Vocabulary/ORBvoc.txt ./Examples/RGB-D-Inertial/RealSense_D435i.yaml`, observing the initialization sequence in the visualization window. Successful initialization requires the camera to observe sufficient visual texture: move the camera slowly in a circular arc with 0.3 m radius while maintaining the workspace center in view, ensuring the feature point count exceeds 100 tracked points (displayed in the map panel). Initialization typically completes within 3 seconds as the system triangulates the initial map and estimates the IMU biases.

Once SLAM achieves tracking state (indicated by green trajectory visualization), execute a standardized motion sequence designed to exercise the full six degrees of freedom while maintaining visual overlap for robust tracking. Command the manipulator to follow a cubic Hermite spline trajectory visiting eight waypoints arranged in a rectangular prism pattern: four corners at Z = 0.4 m and four corners at Z = 0.7 m, with XY corners at (±0.3, ±0.3) meters relative to workspace center. Program the motion with velocity limits of 0.15 m/s linear and 0.3 rad/s angular to prevent motion blur degradation, and configure the manipulator controller to log joint angles and end-effector poses at 100 Hz synchronized with the camera trigger signal.

During trajectory execution, capture SLAM output poses and ground truth fiducial measurements concurrently. Modify the ORB-SLAM3 source to publish camera poses as `geometry_msgs/PoseStamped` messages on `/slam/camera_pose` by inserting the following into `System.cc` within the tracking thread loop:

```cpp
geometry_msgs::msg::PoseStamped pose_msg;
pose_msg.header.stamp = this->get_clock()->now();
pose_msg.header.frame_id = "world";
cv::Mat Tcw = mpTracker->mCurrentFrame.mTcw;
if (!Tcw.empty()) {
    cv::Mat Rwc = Tcw.rowRange(0,3).colRange(0,3).t();
    cv::Mat twc = -Rwc * Tcw.rowRange(0,3).col(3);
    Eigen::Matrix3d R_eigen;
    cv::cv2eigen(Rwc, R_eigen);
    Eigen::Quaterniond q(R_eigen);
    pose_msg.pose.position.x = twc.at<float>(0);
    pose_msg.pose.position.y = twc.at<float>(1);
    pose_msg.pose.position.z = twc.at<float>(2);
    pose_msg.pose.orientation.x = q.x();
    pose_msg.pose.orientation.y = q.y();
    pose_msg.pose.orientation.z = q.z();
    pose_msg.pose.orientation.w = q.w();
    pose_publisher_->publish(pose_msg);
}
```

Simultaneously, run the AprilTag detector to extract ground truth poses from the workspace perimeter markers. Deploy `ros2 run apriltag_ros apriltag_node --ros-args -p camera_frame:=camera_color_optical_frame -p family:=tag36h11 -p size:=0.150`, which publishes detections as `apriltag_msgs/AprilTagDetectionArray` containing tag IDs and SE(3) poses in the camera frame. Record both SLAM poses and AprilTag detections using `ros2 bag record /slam/camera_pose /tf /tf_static /apriltag/detections` throughout the 45-second trajectory.

Post-processing computes absolute pose error by comparing SLAM estimates to ground truth fiducial measurements. Extract the ROS bag data into CSV files using a Python script that reads the bag, synchronizes timestamps within ±10 ms, and transforms all poses into the world reference frame defined by the workspace AprilTag layout. For each timestep where at least three AprilTags are visible (ensuring overdetermined pose estimation), compute the ground truth camera pose by solving the Perspective-n-Point (PnP) problem with RANSAC outlier rejection (inlier threshold 3 pixels, confidence 0.999, minimum 100 iterations). Use OpenCV's `solvePnPRansac` with the ITERATIVE method, providing the 3D tag corner coordinates in world frame and their 2D projections in the image. This yields the ground truth transformation T_world_camera.

Compare SLAM poses to ground truth by computing the relative transformation error. For each synchronized pair of poses T_slam and T_ground_truth, calculate the absolute pose error in translation as APE_trans = ||t_slam - t_ground_truth||₂ and in rotation as APE_rot = arccos((trace(R_slam^T R_ground_truth) - 1) / 2), where t and R denote the translation vector and rotation matrix components. Aggregate statistics across the trajectory: compute mean, median, standard deviation, and 95th percentile for both translation and rotation errors. Target performance for this baseline exercise requires APE_trans_mean < 8 mm, APE_trans_95th < 15 mm, APE_rot_mean < 1.5 degrees, and APE_rot_95th < 3.0 degrees.

Generate diagnostic visualizations using MATLAB or Python matplotlib. Plot the 3D trajectory comparing SLAM estimates (blue line) to ground truth (red line), with error magnitude color-coded along the path. Create time series plots showing APE_trans and APE_rot versus time, overlaying vertical lines indicating manipulator direction reversals to correlate error spikes with motion events. Construct cumulative distribution functions (CDFs) for both error metrics to visualize the full statistical distribution beyond simple mean values.

Compute the relative pose error to quantify drift accumulation independently of global alignment errors. For consecutive pose pairs separated by Δt = 1.0 second (30 frames at 30 Hz), calculate the relative transformation between SLAM poses T_rel_slam = T_slam(t)^(-1) · T_slam(t+Δt) and ground truth T_rel_gt = T_gt(t)^(-1) · T_gt(t+Δt), then determine RPE_trans and RPE_rot using the same formulas as APE but applied to the relative transformations. Aggregate RPE statistics across all consecutive pairs, targeting RPE_trans_mean < 3 mm and RPE_rot_mean < 0.5 degrees to demonstrate minimal drift over short intervals.

Analyze tracking robustness by computing the percentage of frames in which SLAM maintains valid state (indicated by successful pose publication). Examine periods of tracking loss, correlating them with image properties: extract the per-frame feature point count from SLAM logs and depth image fill ratio (percentage of valid depth pixels). Tracking failures typically occur when feature count drops below 50 points or depth fill ratio falls below 40%, often caused by textureless surfaces or excessive distance from the workspace.

Characterize computational performance by logging CPU usage and frame processing times. Instrument the SLAM tracking thread to record the time elapsed from image receipt to pose output using `std::chrono::high_resolution_clock`, targeting mean frame time < 25 ms (40 Hz) to maintain temporal headroom beyond the 30 Hz camera rate. Monitor CPU utilization with `top -H -p $(pgrep -f ORB_SLAM3)` during trajectory execution, confirming that total CPU across all SLAM threads remains below 300% on a quad-core processor (leaving one core for system operations and manipulator control).

### AR Overlay Registration and Rendering Latency

Extend the baseline SLAM system with an AR rendering layer that projects virtual geometry onto the live camera feed, then quantify spatial registration accuracy and motion-to-photon latency. This exercise validates the complete perception-to-display pipeline required for robotic AR applications.

Deploy a Unity-based AR application that subscribes to the `/slam/camera_pose` topic and renders virtual overlay content in real time. Create a Unity project with AR Foundation, configure the AR Session Origin to receive external pose input via a ROS bridge (use ROS-TCP-Connector package with `ROSConnection.cs` configured to the ROS 2 bridge IP address), and implement a custom script `ExternalPoseDriver.cs` that updates the AR Camera transform based on incoming pose messages:

```csharp
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Geometry;

public class ExternalPoseDriver : MonoBehaviour
{
    private ROSConnection ros;
    private string poseTopic = "/slam/camera_pose";
    
    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<PoseStampedMsg>(poseTopic, UpdatePose);
    }
    
    void UpdatePose(PoseStampedMsg poseMsg)
    {
        Vector3 position = new Vector3(
            (float)poseMsg.pose.position.x,
            (float)poseMsg.pose.position.y,
            (float)poseMsg.pose.position.z
        );
        Quaternion rotation = new Quaternion(
            (float)poseMsg.pose.orientation.x,
            (float)poseMsg.pose.orientation.y,
            (float)poseMsg.pose.orientation.z,
            (float)poseMsg.pose.orientation.w
        );
        transform.SetPositionAndRotation(position, rotation);
    }
}
```

Design virtual overlay content consisting of coordinate frame axes (RGB for XYZ, 0.1 m length) positioned at each workspace AprilTag location and a virtual bounding box (wireframe cube, 0.2 m sides) centered at workspace origin. Import the ground truth tag poses from the YAML configuration and instantiate Unity GameObjects at the corresponding world positions. Configure the AR camera with intrinsic parameters matching the physical RGB-D camera: set the Unity Camera component's field of view to match the horizontal FOV computed from the intrinsic matrix as FOV = 2 · arctan(width / (2 · fx)), where fx is the focal length in pixels and width is the sensor width.

Implement latency measurement infrastructure by embedding fiducial timestamps into the rendered overlay. Add a TextMeshPro component displaying the current system timestamp in milliseconds, positioned in the top-left corner of the AR view. Simultaneously, configure a high-speed camera (minimum 120 Hz, ideally 240 Hz) to record the AR display output, capturing both the live video feed and the timestamp overlay. This setup enables motion-to-photon latency calculation by comparing the displayed timestamp to the camera frame timestamp extracted from video metadata.

Execute the standardized trajectory from the baseline exercise while recording AR display output with the high-speed camera. Ensure the recording captures the entire trajectory duration with sufficient exposure to read the timestamp text clearly (manual verification of at least 95% OCR accuracy using Tesseract on extracted frames). Simultaneously log the SLAM pose timestamps and manipulator encoder timestamps to enable multi-stream synchronization.

Analyze spatial registration accuracy by measuring the alignment between virtual overlays and physical fiducials. Extract frames from the high-speed recording at 10 Hz, then use image processing to detect both the physical AprilTags and the rendered virtual coordinate frames. Apply adaptive thresholding to isolate the physical tags, compute their corner locations with sub-pixel refinement using `cv2.cornerSubPix` with a 5×5 search window, then calculate tag centers in image coordinates. For the virtual overlays, apply color-based segmentation to isolate the RGB axes (HSV thresholds: red H ∈ [0,10]∪[170,180], green H ∈ [40,80], blue H ∈ [100,140], all with S > 100 and V > 100), extract the axis endpoints via connected component analysis, and compute the rendered tag center as the intersection of the three axes in 2D.

Quantify registration error as the Euclidean distance in pixels between physical and virtual tag centers, normalized by tag distance from the camera to obtain angular error in milliradians. Aggregate statistics across all visible tags and all analyzed frames, targeting mean registration error < 3 mrad (approximately 3 mm at 1 m distance) and 95th percentile < 6 mrad. Construct a spatial error map showing registration error magnitude as a function of 3D position within the workspace to identify systematic biases or regions of degraded performance.

Compute motion-to-photon latency by correlating manipulator motion events with displayed pose updates. Identify timestamps of sharp manipulator accelerations (acceleration magnitude > 0.5 m/s²) from the encoder logs, then locate the corresponding display timestamp when the AR overlay begins moving. Extract display timestamps from each recorded frame using OCR, apply temporal filtering to remove misreads (reject outliers beyond 3 standard deviations from local median), then linearly interpolate to estimate the display timestamp at each high-speed camera frame. Calculate latency as the time difference between manipulator motion onset and observable display motion onset, using optical flow magnitude on the virtual overlay regions as the motion indicator (threshold: flow magnitude > 2 pixels/frame).

Aggregate latency measurements across multiple acceleration events (minimum 20 samples), reporting mean, standard deviation, and maximum latency. Target specifications require mean latency < 60 ms and maximum latency < 100 ms to maintain acceptable operator performance in teleoperation scenarios. Decompose total latency into component stages by instrumenting the pipeline: measure SLAM processing time (image receipt to pose output), network transmission time (pose output to Unity receipt, measured via ROS 2 QoS statistics), rendering time (Unity Update() to frame buffer swap, logged via `Time.deltaTime`), and display refresh delay (fixed at 16.7 ms for 60 Hz displays or 8.3 ms for 120 Hz).

### Feature Density and Map Quality Assessment

Evaluate the density and distribution of SLAM map points to assess the information content available for robust tracking and accurate pose estimation. Sparse or unevenly distributed maps indicate inadequate visual texture or suboptimal camera motion, degrading AR overlay stability.

Export the ORB-SLAM3 map points by modifying the `System::SaveTrajectoryTUM()` function to additionally output the map point cloud. Extract the map from the `mpAtlas` object, iterate through all active map points with `vpMPs = mpAtlas->GetAllMapPoints()`, then write point coordinates to a PCD file:

```cpp
pcl::PointCloud<pcl::PointXYZ>::Ptr map_cloud(new pcl::PointCloud<pcl::PointXYZ>);
for(size_t i=0; i<vpMPs.size(); i++) {
    if(vpMPs[i]->isBad()) continue;
    cv::Mat pos = vpMPs[i]->GetWorldPos();
    pcl::PointXYZ point;
    point.x = pos.at<float>(0);
    point.y = pos.at<float>(1);
    point.z = pos.at<float>(2);
    map_cloud->points.push_back(point);
}
map_cloud->width = map_cloud->points.size();
map_cloud->height = 1;
map_cloud->is_dense = false;
pcl::io::savePCDFileBinary("slam_map.pcd", *map_cloud);
```

Load the map point cloud into Open3D for quantitative analysis. Compute point density as the number of points per cubic meter by dividing the total point count by the workspace volume (measured from the axis-aligned bounding box of the ground truth tag positions). Target density exceeds 1000 points/m³ for robust tracking under partial occlusion or rapid motion. Visualize the point cloud with color-coding by height (Z-axis) to identify vertical coverage gaps, and overlay the ground truth tag positions as large red spheres to verify map alignment.

Assess map distribution uniformity by voxelizing the workspace into a 10×10×10 grid and counting map points per voxel. Compute the coefficient of variation (standard deviation divided by mean) of the per-voxel point counts, targeting CV < 0.5 to indicate uniform coverage. High CV values suggest concentrated features in textured regions with voids in textureless areas, increasing vulnerability to tracking loss when the camera views the sparse regions.

Analyze map point observation counts to quantify geometric redundancy. Each map point records the number of keyframes from which it was observed, providing a measure of triangulation robustness. Extract observation counts from the SLAM data structure, plot the histogram, and compute the median observation count. Target median > 3 observations per point, ensuring sufficient parallax for accurate depth estimation and resilience to outlier matches.

Correlate map quality metrics with trajectory APE statistics using multivariate regression. Construct a dataset where each trajectory segment (5-second window, sliding by 1 second) has associated mean APE and map quality features (point density in the currently visible volume, mean observation count of visible points, percentage of visible voxels containing at least one point). Fit a linear mixed-effects model in R using `lmer(APE ~ density + observations + coverage + (1|segment), data=df)` to quantify the relationship between map quality and pose accuracy, confirming that improved map metrics predict reduced APE with statistically significant coefficients (p < 0.05).

## Exercise 2: Parameter Variation & Empirical Analysis

### Illumination Robustness and Adaptive Exposure Control

Robotic AR systems must maintain pose estimation accuracy and overlay registration across a wide range of lighting conditions, from dimly lit industrial environments (50 lux) to outdoor bright sunlight (100,000 lux). This exercise quantifies performance degradation under illumination extremes and validates adaptive exposure control strategies.

Establish a controlled lighting environment using a combination of LED panels and neutral density filters. Mount four dimmable LED panels (5000K color temperature, CRI > 90) in a square arrangement 1.5 m above the workspace, each capable of 0 to 5000 lumens output. Measure illuminance at the workspace center using a calibrated lux meter (accuracy ±3%), positioning the sensor horizontally to capture the combined irradiance from all panels. Calibrate the relationship between LED controller PWM duty cycle and measured illuminance by sweeping from 0% to 100% in 10% increments, fitting a second-order polynomial to account for LED thermal droop at high currents.

Design an illumination sweep protocol covering four operating regimes: dim (100 lux, simulating emergency lighting), normal (500 lux, typical indoor office), bright (2000 lux, sunlit room near windows), and saturated (5000 lux, direct overhead industrial lighting). For each regime, execute the standardized trajectory from Exercise 1 while maintaining constant illuminance (feedback control: measure lux at 1 Hz, adjust LED PWM to maintain setpoint within ±5%). Record SLAM pose estimates, ground truth fiducial measurements, and camera auto-exposure parameters (shutter time, ISO gain, extracted from the RealSense metadata via `rs2_get_frame_metadata`).

Analyze pose accuracy degradation as a function of illuminance. For each lighting condition, compute the APE statistics following the Exercise 1 methodology, then plot mean APE_trans and APE_trans_95th versus illuminance on a semi-log x-axis. Fit a piecewise linear model identifying critical thresholds where accuracy begins deteriorating: typically, performance remains stable across 200–2000 lux, degrades below 200 lux due to insufficient SNR and above 2000 lux due to saturation and reduced dynamic range.

Examine the relationship between camera exposure settings and pose accuracy. Extract the per-frame shutter time and ISO gain from the metadata, then compute the exposure value EV = log₂(gain · time) as a single metric representing total light integration. Plot APE versus EV, color-coding points by illuminance to separate the effects of scene brightness from camera response. Optimal EV typically lies between 8 and 11 (corresponding to 1/125 s at ISO 400), with accuracy degrading outside this range due to motion blur at slow shutters or photon noise at high gain.

Implement and validate an adaptive exposure control algorithm that maintains near-optimal EV across varying illuminance. Develop a ROS 2 node that subscribes to `/camera/color/image_raw`, computes the mean pixel intensity of the central 50% region (avoiding vignetting and high-contrast edges), then adjusts exposure via the RealSense API to target mean intensity of 115 (on a 0–255 scale, placing the midpoint at 45% to preserve headroom for bright features). Use a PI controller with K_p = 0.02, K_i = 0.005, and anti-windup limits to prevent oscillation:

```python
import pyrealsense2 as rs
import numpy as np

class AdaptiveExposureController:
    def __init__(self, target_intensity=115):
        self.target = target_intensity
        self.K_p = 0.02
        self.K_i = 0.005
        self.integral = 0.0
        self.integral_limit = 100.0
        
    def update(self, image, current_exposure):
        roi = image[image.shape[0]//4:3*image.shape[0]//4,
                    image.shape[1]//4:3*image.shape[1]//4]
        mean_intensity = np.mean(roi)
        error = self.target - mean_intensity
        
        self.integral += error
        self.integral = np.clip(self.integral, -self.integral_limit, self.integral_limit)
        
        adjustment = self.K_p * error + self.K_i * self.integral
        new_exposure = np.clip(current_exposure + adjustment, 1, 10000)
        return int(new_exposure)
```

Re-execute the illumination sweep with adaptive exposure control enabled, measuring APE statistics at each lighting level. Compare controlled versus uncontrolled conditions by computing the percentage improvement in mean APE and the reduction in APE standard deviation. Target improvements exceed 30% in the dim and saturated regimes while maintaining baseline performance in the normal range.

Quantify tracking robustness under illumination transients by introducing step changes during trajectory execution. At t = 15 s, instantly switch illuminance from 500 to 2000 lux, then at t = 30 s return to 500 lux. Analyze the temporal response: plot APE versus time with vertical lines indicating transient events, measure the recovery time (duration for APE to return within 20% of baseline after perturbation), and count any tracking loss events. Adaptive exposure should achieve recovery within 1.5 seconds without tracking loss, compared to 4+ seconds or outright failure under fixed exposure.

### Occlusion Handling and Partial Observability

Real-world robotic tasks frequently introduce partial occlusions of the workspace, whether from the manipulator itself, grasped objects, or environmental clutter. This exercise stress-tests AR pose estimation under controlled occlusion scenarios, quantifying the minimum visible feature density required to maintain tracking.

Fabricate occlusion masks from 300 mm × 300 mm black foam board panels mounted on adjustable stands, allowing precise positioning within the workspace. Design four occlusion scenarios with increasing severity: Level 1 occludes 25% of the workspace (one panel positioned 0.3 m from workspace center), Level 2 occludes 40% (two panels in an L configuration), Level 3 occludes 55% (three panels forming a U), and Level 4 occludes 70% (four panels leaving only a narrow viewing corridor). For each level, measure the visible workspace volume by taking a panoramic depth scan from the camera's starting position, applying connected component analysis to identify the largest depth-contiguous region, then computing its volume via voxel summation at 10 mm resolution.

Execute the standardized trajectory under each occlusion level, recording SLAM poses and ground truth measurements. Analyze tracking robustness by computing the percentage of frames maintaining valid SLAM state and the mean duration of tracking loss episodes. Plot these metrics versus visible workspace percentage, identifying the critical threshold below which tracking becomes unreliable (typically 35–40% remaining visibility for ORB-SLAM3 with default parameters).

Examine the spatial distribution of tracking failures by constructing a 3D tracking quality map. Voxelize the workspace into 50 mm cubes, then for each voxel, compute the percentage of frames where the camera occupied that voxel and maintained valid tracking. Visualize using a heatmap overlay on the point cloud, identifying regions where occlusion prevents stable tracking. Correlate failure regions with map point density: extract the map point count within 0.2 m radius of each failure voxel, confirming that failures cluster in areas with density below 500 points/m³.

Implement and evaluate an occlusion-aware pose recovery strategy based on AprilTag detection. Modify the SLAM system to fuse direct fiducial pose estimates when feature tracking degrades: monitor the feature point count, and when it drops below 60 points, trigger a PnP pose estimation using all visible AprilTags as an alternative pose source. Use a Kalman filter to blend SLAM and fiducial estimates with weights proportional to their respective covariance matrices:

```python
def fused_pose_estimate(slam_pose, slam_cov, fiducial_pose, fiducial_cov):
    # Kalman update: K = P_slam * (P_slam + P_fid)^-1
    K = slam_cov @ np.linalg.inv(slam_cov + fiducial_cov)
    
    # SE(3) manifold addition for poses
    pose_error = se3_log(se3_inverse(slam_pose) @ fiducial_pose)
    fused_pose = slam_pose @ se3_exp(K @ pose_error)
    fused_cov = (np.eye(6) - K) @ slam_cov
    
    return fused_pose, fused_cov
```

Re-run the occlusion scenarios with fiducial-assisted recovery, measuring the improvement in tracking robustness. Compute the percentage reduction in tracking loss episodes and the decrease in mean APE during low-feature-count periods. Target improvements achieve at least 50% reduction in loss episodes for Level 3 occlusion while maintaining APE < 12 mm during fiducial-assisted intervals.

### Motion Dynamics and Velocity-Dependent Drift

High-speed manipulator motions induce motion blur, rolling shutter distortion, and increased IMU integration errors, all degrading pose estimation accuracy. This exercise characterizes performance across a range of motion velocities and accelerations, establishing safe operating envelopes for AR-guided tasks.

Design a velocity sweep experiment using the manipulator controller to execute straight-line motions at five speeds: 0.05, 0.10, 0.20, 0.40, and 0.80 m/s along the workspace X-axis over a 0.6 m distance. Maintain constant velocity during the central 0.4 m segment using a trapezoidal velocity profile with 0.1 m acceleration zones. For each speed, execute 10 repetitions alternating direction, recording SLAM poses and manipulator encoder data.

Compute velocity-dependent pose error by segmenting each trajectory into constant-velocity and acceleration phases. During constant-velocity segments, calculate the instantaneous APE at 30 Hz and aggregate statistics per velocity level. Plot mean APE_trans versus velocity, fitting an exponential model APE(v) = APE₀ · exp(α · v) to quantify the error growth rate. Typical results show APE doubling between 0.10 and 0.40 m/s due to motion blur exceeding the camera's 33 ms integration time.

Analyze rolling shutter distortion by examining the SLAM keyframe images extracted during high-speed motion. The RealSense D435i uses a rolling shutter with 30 ms row readout time, causing geometric distortion when the camera translates during exposure. Detect straight workspace edges (AprilTag borders or calibration board edges) using the Hough line transform, measure their deviation from straightness via polynomial fitting, then quantify distortion as the maximum perpendicular distance from the ideal line. Plot distortion magnitude versus velocity, confirming approximately linear scaling (1 mm distortion per 0.1 m/s velocity for objects at 0.5 m distance).

Evaluate IMU fusion benefit under dynamic motion by comparing pose accuracy with and without IMU integration. Reconfigure ORB-SLAM3 to disable IMU input (switch from RGBD-Inertial to RGBD mode), then repeat the velocity sweep. Compute the percentage increase in APE for the IMU-disabled case, demonstrating that IMU fusion provides 40–60% accuracy improvement at velocities above 0.3 m/s by compensating for inter-frame motion blur.

Implement velocity-adaptive exposure control to mitigate motion blur at high speeds. Extend the adaptive exposure controller to receive manipulator velocity estimates from the encoder topic, then reduce shutter time as velocity increases according to the constraint: shutter ≤ max_blur / (velocity · depth), where max_blur = 1.5 pixels tolerable blur and depth is the average distance to map points. This typically requires reducing shutter from 15 ms at rest to 5 ms at 0.40 m/s, compensated by increasing ISO gain from 200 to 600:

```python
def compute_max_shutter(velocity, mean_depth, max_blur_pixels=1.5, focal_length=615):
    # max_blur_pixels = (velocity * shutter) / (depth / focal_length)
    max_shutter_ms = (max_blur_pixels * mean_depth) / (velocity * focal_length) * 1000
    return max(1, min(max_shutter_ms, 33))  # Clamp to 1-33 ms range
```

Re-run the velocity sweep with adaptive shutter control, measuring the reduction in velocity-dependent APE growth. Target improvements demonstrate APE remaining below 10 mm for velocities up to 0.40 m/s, compared to exceeding 18 mm under fixed exposure.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Environmental Degradation: Smoke, Fog, and Particulate Occlusion

Industrial and field robotic deployments often encounter airborne particulates, smoke, or fog that scatter light and degrade both RGB and depth sensing modalities. This exercise quantifies AR system failure modes under controlled atmospheric obscuration and validates recovery protocols.

Construct a fog chamber by enclosing the workspace within transparent acrylic panels (1.5 × 1.5 × 1.0 m) with access ports for the manipulator and camera. Install an ultrasonic fog generator (5 L/hour output, glycol-based fog fluid) at the chamber base with a circulation fan to maintain uniform fog density. Measure optical density using a laser transmissometer: project a 650 nm laser pointer across the chamber diagonal (2.1 m path length), detect transmitted intensity with a photodiode, then compute extinction coefficient β via Beer-Lambert law I = I₀ · exp(−β · L).

Calibrate fog density by adjusting generator output and circulation time to achieve five atmospheric conditions: clear (β = 0), light haze (β = 0.1 m⁻¹, equivalent to 5 km meteorological visibility), moderate fog (β = 0.5 m⁻¹, 1 km visibility), dense fog (β = 1.5 m⁻¹, 300 m visibility), and opaque fog (β = 3.0 m⁻¹, 150 m visibility). Allow 5 minutes for thermal equilibrium after each density change, confirming stability by monitoring transmissometer readings at 1 Hz with standard deviation < 0.02 m⁻¹ over a 60-second window.

Execute the standardized trajectory under each fog condition, recording SLAM tracking status, ground truth measurements, and RGB-D image quality metrics. For each frame, compute depth fill ratio (percentage of pixels with valid depth measurements) and RGB image contrast (standard deviation of pixel intensities divided by mean). Plot these metrics versus fog density, observing the rapid degradation beyond β = 0.5 m⁻¹ as depth sensing fails due to time-of-flight signal attenuation and RGB contrast collapses from scattering.

Quantify tracking robustness by measuring the time to tracking loss (TTL) under each fog condition. Start the trajectory with the system already tracking in clear conditions, then introduce fog at t = 10 s by activating the generator. Record the timestamp when SLAM loses tracking (feature count drops below 20 and fails to recover for 3 consecutive seconds). Plot TTL versus fog density, fitting a survival curve model to predict failure probability as a function of atmospheric opacity. Typical results show tracking collapse within 15 seconds at β = 1.0 m⁻¹ and immediate loss above β = 2.0 m⁻¹.

Validate a tag-based recovery protocol for operation in degraded visual conditions. Augment the workspace AprilTags with high-contrast retro-reflective borders and active LED illumination (940 nm IR, outside the visible spectrum but detectable by the RealSense IR imagers). Implement a recovery routine that, upon tracking loss, commands the manipulator to execute a systematic search pattern: spiral outward from the last known pose in 100 mm steps, pausing at each waypoint to scan for illuminated tags. When at least two tags are detected, reinitialize SLAM by feeding the PnP-derived pose as the starting estimate:

```python
def recovery_search_pattern(last_pose, workspace_bounds, step_size=0.1):
    # Archimedean spiral centered on last known position
    theta = 0
    radius = 0
    waypoints = [last_pose]
    
    while radius < workspace_bounds.max_radius:
        theta += np.pi / 4
        radius += step_size / (2 * np.pi)
        x = last_pose.x + radius * np.cos(theta)
        y = last_pose.y + radius * np.sin(theta)
        z = last_pose.z
        
        if workspace_bounds.contains(x, y, z):
            waypoints.append(Pose(x, y, z, last_pose.orientation))
    
    return waypoints
```

Test the recovery protocol under dense fog (β = 1.5 m⁻¹) by inducing tracking loss, initiating the search pattern, and measuring the time to recovery (TTR) and positional drift during the lost interval. Execute 15 trials with randomized initial loss positions, computing TTR statistics (mean, median, 95th percentile) and final positional error relative to the ground truth pose after recovery. Target performance achieves TTR_mean < 12 seconds and drift < 30 mm for 90% of trials.

### Computational Load and Real-Time Deadline Violations

AR systems must maintain deterministic frame rates despite computational load variations from SLAM complexity, rendering workload, and competing system processes. This exercise stress-tests the pipeline under extreme computational demands and validates load-shedding strategies to preserve real-time guarantees.

Establish baseline computational budgets by profiling each pipeline stage under nominal conditions. Use Linux `perf` to sample CPU cycles per function during the standardized trajectory: `perf record -F 999 -g -p $(pgrep ORB_SLAM3)` for SLAM, and Unity Profiler for AR rendering. Generate flame graphs with `perf script | stackcollapse-perf.pl | flamegraph.pl > slam_profile.svg`, identifying the dominant compute kernels: typically ORB feature extraction (35% CPU), descriptor matching (25%), bundle adjustment (20%), and rendering (15%).

Design a computational stress test by introducing artificial load spikes via CPU-intensive background processes. Use `stress-ng --cpu 3 --cpu-load 75 --timeout 10s` to saturate three cores at 75% utilization, triggering at t = 15, 30, and 45 seconds during the trajectory. Monitor SLAM and rendering frame times via instrumentation logs, detecting deadline violations when frame time exceeds 33 ms (causing frame drops below the target 30 Hz camera rate).

Quantify the impact of deadline violations on pose accuracy by correlating frame drops with APE spikes. Extract timestamps of all frames where processing exceeded 33 ms, then compute the APE increase in a ±2 second window surrounding each violation. Aggregate statistics across all violations, typically revealing 2–3× APE increase during and immediately following deadline misses due to degraded temporal resolution in motion integration.

Implement a multi-level load shedding strategy that degrades gracefully under computational stress. Configure SLAM to adjust feature extraction resolution based on available headroom: monitor the ratio of actual to target frame time, and when it exceeds 0.8, reduce the ORB pyramid levels from 8 to 6 (reducing feature count by approximately 40% while maintaining coverage). For rendering, implement adaptive mesh LOD selection based on GPU utilization: query the GPU load via `nvidia-smi` or equivalent, selecting lower-resolution meshes when load exceeds 85%.

Validate load shedding effectiveness by repeating the computational stress test with adaptive strategies enabled. Measure the reduction in deadline violation count, the preservation of mean APE below 12 mm despite load spikes, and the subjective AR overlay stability via user rating (five operators rate stability on a 1–5 Likert scale, targeting mean > 4.0). Confirm that load shedding activates within one frame after load spike detection and restores full quality within two frames after load subsides.

Analyze the tradeoff between computational headroom and pose accuracy by sweeping the number of background CPU-intensive threads from 0 to 6 (on a quad-core system, forcing CPU oversubscription). For each load level, execute a 30-second trajectory segment and compute mean APE, frame drop percentage, and load shedding activation frequency. Plot APE versus CPU load percentage, identifying the critical load threshold (typically 75–80% total CPU) beyond which accuracy degrades exponentially.

### Multi-Modal Sensor Fusion: Depth Sensor Failure and RGB-Only Degradation

Depth sensor failures occur from IR interference, overexposure to ambient IR sources, or hardware faults, requiring fallback to monocular RGB-based pose estimation. This exercise validates AR system resilience under depth modality loss and quantifies the accuracy degradation.

Simulate depth sensor failure by masking the depth stream in software: configure a ROS 2 bridge node that subscribes to `/camera/aligned_depth_to_color/image_raw`, detects a trigger signal (published on `/test/depth_failure_trigger`), then republishes only invalid depth (all pixels set to zero) for a specified duration. Design three failure scenarios: transient (5-second dropout), intermittent (alternating 2-second valid/invalid periods), and permanent (sustained failure after t = 20 s).

Reconfigure ORB-SLAM3 to accept RGB-D input but handle missing depth gracefully: modify the tracking thread to detect frames with >95% invalid depth pixels, then switch internally to monocular mode for those frames by disabling depth-based map point creation and relying solely on stereo triangulation from motion parallax. Instrument the code to log mode transitions and per-frame tracking quality indicators (number of matched features, parallax angle for triangulated points).

Execute the standardized trajectory under each failure scenario, recording SLAM tracking status and APE statistics. Compare RGB-D versus RGB-only performance by computing the APE increase during depth outages: for transient failures, expect 1.5–2× APE increase during the dropout and 1–2 second recovery period; for permanent failures, sustained 2–3× APE degradation but continued tracking if sufficient motion parallax is maintained (minimum 5-degree viewing angle change between keyframes).

Examine scale drift in monocular mode by analyzing the relative transformation between consecutive keyframes. In RGB-D mode, scale is directly observable from depth measurements, but monocular SLAM estimates scale up to an arbitrary factor. Compute the scale factor drift as the ratio of estimated to ground truth trajectory lengths over 5-second windows during depth outages. Implement scale correction via IMU integration: the accelerometer double integration provides absolute scale, constraining the monocular estimate. Validate correction effectiveness by demonstrating scale drift reduction from 15–20% uncorrected to <5% with IMU fusion.

Develop a sensor health monitoring and fallback protocol that detects degraded depth quality before complete failure. Compute per-frame depth metrics: fill ratio, mean depth of valid pixels, and temporal depth stability (correlation coefficient between consecutive aligned depth frames). Trigger preemptive fallback to monocular mode when fill ratio drops below 50% or temporal stability falls below 0.7, avoiding abrupt tracking loss:

```python
class DepthHealthMonitor:
    def __init__(self):
        self.fill_threshold = 0.50
        self.stability_threshold = 0.70
        self.previous_depth = None
        
    def check_health(self, depth_image):
        valid_pixels = np.count_nonzero(depth_image > 0)
        fill_ratio = valid_pixels / depth_image.size
        
        if self.previous_depth is not None:
            # Compute correlation between frames
            valid_mask = (depth_image > 0) & (self.previous_depth > 0)
            if np.sum(valid_mask) > 100:
                correlation = np.corrcoef(
                    depth_image[valid_mask].flatten(),
                    self.previous_depth[valid_mask].flatten()
                )[0,1]
            else:
                correlation = 0.0
        else:
            correlation = 1.0
        
        self.previous_depth = depth_image.copy()
        
        is_healthy = (fill_ratio > self.fill_threshold and 
                      correlation > self.stability_threshold)
        return is_healthy, fill_ratio, correlation
```

Test the health monitoring system by inducing gradual depth degradation: progressively increase ambient 850 nm IR illumination (using IR LED floods) to interfere with the RealSense's structured light pattern, causing fill ratio to decline from 95% to 30% over 20 seconds. Verify that the monitor triggers fallback before catastrophic tracking loss, maintaining APE below 15 mm throughout the degradation and recovery cycle.

### Failure Recovery and State Persistence

AR system robustness requires not only detection and mitigation of failures but also rapid recovery to pre-failure operational state. This exercise validates state persistence mechanisms and quantifies recovery latency after catastrophic tracking loss.

Implement a state checkpointing system that periodically saves the SLAM map, keyframe database, and covariance estimates to non-volatile storage. Configure ORB-SLAM3 to serialize the map every 5 seconds using the existing save/load trajectory methods, extended to include the full map point cloud and keyframe descriptors. Measure serialization overhead by timing the save operation and confirming it completes within 200 ms without blocking the tracking thread (execute save in a separate thread with double-buffering to isolate from real-time pipeline).

Induce catastrophic tracking failures via complete visual occlusion: at t = 25 s, position an opaque barrier directly in front of the camera, blocking all visual and depth input for 10 seconds. Monitor SLAM tracking status, confirming loss within one frame and sustained failure throughout the occlusion. At t = 35 s, remove the barrier and observe the recovery process.

Without state persistence, recovery requires complete reinitialization: the system must re-detect the environment, rebuild the map from scratch, and relocalize relative to ground truth, typically consuming 5–10 seconds and exhibiting large transient pose errors (>100 mm) during convergence. With state persistence, recovery proceeds via map-based relocalization: the system loads the last checkpoint, extracts features from the current frame, matches them against the saved keyframe database using bag-of-words lookup, then recovers the pose via PnP and resumes tracking. Measure recovery latency as the time from occlusion removal to valid pose output, and transient error magnitude as the peak APE during the recovery period.

Compare checkpoint-based recovery performance across different checkpoint intervals: test 2, 5, 10, and 30-second intervals, executing 20 occlusion trials per configuration. Plot recovery latency versus checkpoint age (time elapsed since last checkpoint), revealing approximately linear scaling: recovery from a 2-second-old checkpoint requires 0.5–1.0 seconds, while a 30-second-old checkpoint requires 3–5 seconds due to accumulated environmental changes invalidating saved features. Optimal checkpoint interval balances latency (favoring frequent saves) against storage overhead and computational load (favoring infrequent saves), typically settling on 5–10 second intervals for robotic AR applications.

Validate recovery accuracy by comparing the post-recovery pose estimate to ground truth. During the recovery transient, APE may spike to 50–100 mm before converging to baseline levels within 2–3 seconds as the system integrates new observations and refines the pose via bundle adjustment. Compute the recovery convergence time as the duration for APE to stabilize within 20% of pre-failure baseline, targeting convergence within 3 seconds for 90% of recovery events.

Implement and test a multi-hypothesis relocalization strategy that evaluates multiple candidate poses in parallel during recovery. When the checkpoint-based relocalization attempts to match current features against the saved map, it typically generates multiple candidate poses from different keyframe matches. Rather than selecting the single best match, maintain the top five candidates and propagate each forward via separate tracking threads for 1 second, then select the hypothesis with the highest accumulated tracking quality (total number of inlier feature matches across frames). This multi-hypothesis approach improves recovery reliability from 75% to >95% success rate in environments with repetitive visual features:

```python
class MultiHypothesisRecovery:
    def __init__(self, num_hypotheses=5):
        self.num_hypotheses = num_hypotheses
        
    def relocalize(self, current_frame, keyframe_database):
        # Generate candidate poses via bag-of-words matching
        candidates = keyframe_database.query(current_frame, self.num_hypotheses)
        
        # Initialize hypothesis trackers
        hypotheses = []
        for candidate in candidates:
            pose_estimate = pnp_ransac(current_frame, candidate.map_points)
            tracker = HypothesisTracker(pose_estimate)
            hypotheses.append((tracker, 0))  # (tracker, accumulated_score)
        
        # Track each hypothesis for N frames
        for frame in incoming_frames[:30]:  # 1 second at 30 Hz
            for i, (tracker, score) in enumerate(hypotheses):
                success, inliers = tracker.update(frame)
                if success:
                    hypotheses[i] = (tracker, score + len(inliers))
        
        # Select best hypothesis
        best_hypothesis = max(hypotheses, key=lambda x: x[1])
        return best_hypothesis[0].pose
```

Quantify the multi-hypothesis benefit by comparing single-hypothesis versus multi-hypothesis recovery success rates across 50 trials with varied environmental conditions (different object configurations, lighting changes). Compute the percentage of trials achieving successful recovery (APE converging below 20 mm within 5 seconds) for each method, demonstrating multi-hypothesis improvement from 76% to 94% success rate.

## Operational Reference Guide & Diagnostic Checklist

### Pre-Flight System Verification Protocol

Execute this checklist before each AR-enabled robotic operation to ensure system readiness and minimize in-operation failures.

**Camera System Health**
1. Power cycle the RGB-D camera and verify LED status indicates normal operation (solid green for RealSense D435i).
2. Confirm data stream publication at target rates: `ros2 topic hz /camera/color/image_raw` should report 29.5–30.5 Hz, `/camera/aligned_depth_to_color/image_raw` 29.5–30.5 Hz, `/camera/imu` 195–205 Hz.
3. Inspect a live color image: check for dead pixels (0.01% threshold), lens contamination (detect via high-frequency noise in flat regions), and correct white balance (gray card should render neutral RGB within ±5 digital levels).
4. Validate depth accuracy: place a flat calibration board at precisely 1.000 m distance (measured with laser rangefinder), capture 100 depth frames, compute mean depth of the board region, confirm 980–1020 mm (±2% tolerance).
5. Verify IMU calibration: with the camera stationary on a level surface, record 10 seconds of IMU data, compute accelerometer mean across axes, confirm Z-axis reads 9.80 ± 0.15 m/s² and X, Y axes read 0.00 ± 0.10 m/s².

**SLAM Subsystem Initialization**
6. Launch ORB-SLAM3 and confirm successful vocabulary load (ORBvoc.txt, expected load time 3–5 seconds).
7. Verify configuration file matches camera calibration: compare intrinsic parameters in the YAML to the latest calibration results, ensuring focal lengths agree within 1 pixel and principal point within 2 pixels.
8. Execute a minimal motion to trigger initialization: slowly translate camera 0.2 m while observing the GUI feature point overlay, confirm >100 green tracked features within 5 seconds and map panel shows >200 map points.
9. Check tf2 transform tree: `ros2 run tf2_tools view_frames.py`, verify transforms exist from world → map → camera_link with update rates matching the SLAM output frequency (30 Hz).

**Workspace Calibration and Ground Truth Reference**
10. Verify AprilTag positions: using a laser distance meter, re-measure the distances between pairs of workspace perimeter tags, compare to the ground truth YAML configuration, confirm agreement within ±3 mm.
11. Validate lighting uniformity: measure illuminance at five points (workspace center and four corners), compute coefficient of variation, confirm CV < 0.15 for uniform conditions.
12. Check manipulator calibration: command motion to three known Cartesian positions, measure actual end-effector location with external tracking (laser tracker or CMM if available), confirm positioning error <1 mm.

**AR Rendering Pipeline**
13. Launch Unity AR application and verify network connectivity to ROS 2: monitor the ROS-TCP-Connector console for successful connection message, ping latency should remain <5 ms on local network.
14. Confirm pose message reception: observe the AR camera transform updates in the Unity Hierarchy panel, should update at 30 Hz synchronized with SLAM output.
15. Validate virtual overlay alignment: with camera viewing a workspace AprilTag, verify the rendered coordinate frame overlays the physical tag with visible offset <5 mm (subjective visual assessment sufficient for pre-flight check, quantitative measurement performed during Exercise 1).
16. Test rendering performance: enable the Unity Profiler, confirm CPU frame time <20 ms and GPU frame time <12 ms under idle conditions (no active manipulation tasks).

**Computational Resources**
17. Monitor system load: `htop` or equivalent should show total CPU utilization <40% before SLAM initialization, confirming headroom for operational load.
18. Check available memory: confirm at least 4 GB free RAM to accommodate SLAM map growth and rendering buffers.
19. Verify disk write performance: test checkpoint save operation, confirm write completes in <200 ms (`time` the save function call).
20. Validate network bandwidth: `iperf3` between robot computer and AR rendering host should demonstrate >100 Mbps throughput with <1% packet loss.

### Real-Time Diagnostic Dashboard Metrics

Deploy a live monitoring dashboard displaying these key performance indicators during operation, flagging alerts when thresholds are exceeded.

**Pose Estimation Quality** (update 10 Hz)
- **APE Translation**: Current absolute pose error translation magnitude relative to last fiducial check, threshold warning >10 mm, critical >20 mm.
- **APE Rotation**: Current absolute pose error rotation magnitude, threshold warning >2°, critical >5°.
- **Feature Count**: Number of tracked ORB features in current frame, threshold warning <80, critical <50.
- **Map Point Density**: Number of map points visible in current frustum divided by visible volume, threshold warning <800/m³, critical <500/m³.
- **Tracking State**: Boolean indicator of valid SLAM state, alert on any tracking loss event.

**Rendering Performance** (update at frame rate)
- **Motion-to-Photon Latency**: Estimated total latency from manipulator motion to display update, threshold warning >70 ms, critical >100 ms.
- **Frame Time**: Combined SLAM processing + rendering time, threshold warning >30 ms (causing frame drops), critical >50 ms (severe degradation).
- **Registration Error**: Pixel-space distance between virtual overlay and physical fiducial when both visible, threshold warning >5 pixels, critical >10 pixels.

**Sensor Health** (update 1 Hz)
- **Depth Fill Ratio**: Percentage of valid depth pixels, threshold warning <60%, critical <40%.
- **Depth Temporal Stability**: Frame-to-frame correlation coefficient, threshold warning <0.75, critical <0.60.
- **Image Brightness**: Mean pixel intensity in central ROI, threshold warning <40 or >200 (on 0–255 scale), critical <20 or >235.
- **IMU Acceleration Magnitude**: Norm of accelerometer reading, threshold critical if >50 m/s² (likely sensor fault or violent collision).

**Computational Load** (update 1 Hz)
- **CPU Utilization**: Percentage of total CPU consumed by SLAM and rendering processes, threshold warning >75%, critical >90%.
- **Memory Usage**: Resident set size of SLAM process, threshold warning >6 GB, critical >7 GB (approaching OOM risk).
- **GPU Utilization**: Percentage of GPU cycles consumed, threshold warning >85%, critical >95%.
- **Network Latency**: Round-trip time for pose messages from robot to AR host, threshold warning >10 ms, critical >25 ms.

### Common Failure Modes and Diagnostic Procedures

**Symptom: Tracking Loss Within 10 Seconds of Initialization**
- **Root Cause**: Insufficient visual texture or excessive motion blur during initialization.
- **Diagnostic**: Examine first keyframe image for feature density, compute ORB feature count with `cv2.ORB_create().detect()`, should exceed 500 features.
- **Mitigation**: Improve workspace lighting, add high-contrast fiducial markers, reduce initialization motion speed below 0.05 m/s.

**Symptom: Gradual Pose Drift (APE Increasing >1 mm/s)**
- **Root Cause**: Scale drift from insufficient loop closure or IMU bias accumulation.
- **Diagnostic**: Plot trajectory in 3D, check for closed loops (should return to starting position within 10 mm after 60-second circuit), verify loop closure events in SLAM log.
- **Mitigation**: Enable loop closure detection, reduce trajectory size to ensure frequent revisits to starting region, recalibrate IMU to minimize bias.

**Symptom: Sudden APE Spike to >50 mm Lasting <2 Seconds**
- **Root Cause**: Transient occlusion or rapid lighting change causing momentary feature loss.
- **Diagnostic**: Correlate APE spike timing with manipulator motion logs and lighting sensor data, check depth fill ratio during spike window.
- **Mitigation**: Implement feature prediction to bridge short occlusions, enable adaptive exposure control, add illuminated fiducials for recovery.

**Symptom: Rendering Latency Exceeding 100 ms**
- **Root Cause**: Network congestion, CPU overload, or GPU saturation.
- **Diagnostic**: Use `ros2 topic bw` to check message sizes and rates, `iftop` for network bandwidth monitoring, Unity Profiler to identify rendering bottleneck (CPU or GPU bound).
- **Mitigation**: Reduce message size via compression, offload rendering to dedicated GPU, lower mesh polygon count, decrease overlay scene complexity.

**Symptom: Depth Sensor Reports >50% Invalid Pixels**
- **Root Cause**: IR interference from ambient sources, surface material reflectivity issues, or hardware fault.
- **Diagnostic**: Capture raw IR image from RealSense, check for saturation (all pixels >240 indicate overexposure), measure ambient 850 nm illuminance with spectrometer.
- **Mitigation**: Shield workspace from ambient IR (sunlight through windows, halogen lamps), adjust IR emitter power, apply anti-reflective treatment to glossy surfaces, fallback to monocular mode if hardware fault.

**Symptom: Recovery from Occlusion Fails (>10 Second Relocalization)**
- **Root Cause**: Insufficient environmental features or excessive change since last checkpoint.
- **Diagnostic**: Load checkpoint map and compare feature distribution to current observations, compute percentage of saved features still detectable (should exceed 40% for reliable relocalization).
- **Mitigation**: Increase checkpoint frequency to reduce environmental drift, add static high-contrast features (checkerboard panels on walls), implement multi-hypothesis relocalization.

### Performance Tuning Parameter Reference

**ORB-SLAM3 Configuration Optimization**
- `ORBextractor.nFeatures`: Target number of ORB features per frame. Default 1000, increase to 1500 for feature-rich environments to improve robustness, decrease to 600 for computational constraints. Must maintain >500 for stable tracking.
- `ORBextractor.scaleFactor`: Pyramid scale factor between levels. Default 1.2, decrease to 1.15 for finer scale sampling at cost of 15% more computation, increase to 1.3 for faster extraction but reduced multi-scale coverage.
- `ORBextractor.nLevels`: Number of pyramid levels. Default 8, reduce to 6 for load shedding (40% compute reduction), increase to 10 for environments with extreme depth variation (0.2–5.0 m).
- `IMU.NoiseGyro`: Gyroscope white noise density (rad/s/√Hz). Calibrate via Allan variance analysis of static IMU recording, typical values 1.6e-4 to 2.0e-4 for RealSense D435i.
- `IMU.NoiseAcc`: Accelerometer white noise density (m/s²/√Hz). Typical values 1.8e-3 to 2.5e-3, verify via static recording with FFT analysis of acceleration spectrum.
- `IMU.GyroWalk`: Gyroscope random walk (rad/s²/√Hz). Typical 1.9e-5, increase if observing drift in rotational estimates during constant velocity motion.
- `IMU.AccWalk`: Accelerometer random walk (m/s³/√Hz). Typical 3.0e-3, increase if observing drift in positional estimates during constant velocity motion.

**Adaptive Exposure Control Tuning**
- `target_intensity`: Target mean pixel brightness (0–255 scale). Default 115 provides balanced headroom, increase to 130 for low-light bias (better feature detection in shadows), decrease to 95 for bright-light bias (preserve highlight detail).
- `K_p`: Proportional gain for exposure controller. Default 0.02, increase to 0.04 for faster response to lighting changes (risk of oscillation), decrease to 0.01 for smoother transitions.
- `K_i`: Integral gain for exposure controller. Default 0.005, increase to 0.01 to eliminate steady-state error faster, decrease to 0.002 if observing overshoot and ringing.
- `max_shutter`: Maximum allowable shutter time (milliseconds). Default 33 ms (matches frame period), reduce to 20 ms to limit motion blur during fast motion (requires compensatory ISO increase).
- `max_ISO`: Maximum allowable ISO gain. Default 800, increase to 1600 for very dark environments accepting noise penalty, decrease to 400 to prioritize image quality over low-light performance.

**Unity AR Rendering Optimization**
- `targetFrameRate`: Desired rendering frame rate. Default 60 fps, reduce to 30 fps to match camera rate and halve GPU load, increase to 90 fps for high-refresh displays if GPU permits.
- `shadowDistance`: Maximum distance for shadow rendering. Default 50 m, reduce to 5 m for workspace-scale operations (70% GPU savings), increase only if distant shadows provide visual cues.
- `meshLOD`: Level-of-detail bias. Default 1.0, reduce to 0.5 to favor higher polygon meshes (10% GPU cost), increase to 2.0 to favor lower polygon meshes (30% GPU savings).

This operational reference provides the empirical foundation for deploying AR systems in production robotic environments, ensuring quantitative verification, predictable failure modes, and rapid recovery protocols.
