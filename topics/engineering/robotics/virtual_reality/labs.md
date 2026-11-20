# Operational Verification Labs: Virtual Reality

## Objective & Operational Lab Setup

Virtual reality systems in robotics serve as critical validation environments where manipulator kinematics, sensor fusion algorithms, and human-robot interaction protocols undergo empirical testing before physical deployment. This laboratory guide establishes rigorous verification procedures for VR-integrated robotic systems, focusing on pose accuracy, latency budgets, and spatial calibration techniques that directly translate to real-world operational reliability.

The operational context for these exercises centers on a simulated industrial robotics cell where a six-degree-of-freedom manipulator operates within a virtual environment tracked by optical or electromagnetic pose estimation systems. You will validate end-effector positioning accuracy against ground-truth coordinate frames, characterize system latency through timestamp injection and capture, and stress-test collision avoidance algorithms under boundary conditions that would be unsafe or cost-prohibitive to execute on physical hardware.

Your analytical research environment requires a workstation running Ubuntu 22.04 LTS with ROS 2 Humble installed, paired with either Unity 3D (version 2022.3 LTS) or Unreal Engine 5.3 for the VR rendering pipeline. The ROS-Unity bridge or the UnrealROSIntegration plugin will serve as the middleware layer, translating joint state messages and transform trees between the robotics stack and the graphics engine. For head-mounted display (HMD) integration, the OpenXR runtime provides vendor-agnostic access to devices such as the Meta Quest 3, HTC Vive Pro 2, or Valve Index, though monitor-based development remains viable for kinematic and sensor fusion validation.

Begin by cloning the operational verification repository and installing dependencies. Open a terminal and execute the following sequence without modification:

```bash
mkdir -p ~/vr_robotics_lab/src
cd ~/vr_robotics_lab/src
git clone https://github.com/Unity-Technologies/ROS-TCP-Connector.git
git clone https://github.com/ros-planning/moveit2.git -b humble
cd ~/vr_robotics_lab
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

The ROS 2 workspace now contains the MoveIt 2 motion planning framework and the TCP connector that Unity will use to subscribe to `/joint_states` and publish `/tf` transformations. Next, configure the Unity project by launching Unity Hub, creating a new 3D Core project named `VRRoboticsVerification`, and importing the ROS-TCP-Connector package via the Unity Package Manager by adding the Git URL `https://github.com/Unity-Technologies/ROS-TCP-Connector.git?path=/com.unity.robotics.ros-tcp-connector`. Once imported, navigate to **Robotics → ROS Settings** and set the ROS IP address to `127.0.0.1` with port `10000`, then enable the **Protocol** dropdown to `ROS 2`.

For the robotic manipulator model, download the Universal Robots UR5e URDF from the official MoveIt 2 tutorials repository. Place the URDF in `~/vr_robotics_lab/src/ur5e_description/urdf/ur5e.urdf` and create a minimal ROS 2 launch file at `~/vr_robotics_lab/src/ur5e_description/launch/display.launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    urdf_path = PathJoinSubstitution([
        FindPackageShare('ur5e_description'),
        'urdf',
        'ur5e.urdf'
    ])
    
    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': open(urdf_path.perform(None)).read(),
                'publish_frequency': 100.0
            }]
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen'
        )
    ])
```

Build and source the workspace again, then launch the robot state publisher to verify that joint states propagate correctly:

```bash
cd ~/vr_robotics_lab
colcon build --packages-select ur5e_description
source install/setup.bash
ros2 launch ur5e_description display.launch.py
```

You should observe the joint state publisher GUI window with six sliders corresponding to the UR5e's shoulder pan, shoulder lift, elbow, wrist 1, wrist 2, and wrist 3 joints. Confirm that moving these sliders publishes messages on the `/joint_states` topic by opening a second terminal and running `ros2 topic echo /joint_states`. The output will display real-time joint position, velocity, and effort arrays.

Now establish the Unity-ROS 2 communication bridge by launching the ROS TCP endpoint server. In the ROS 2 terminal, execute:

```bash
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0 -p ROS_TCP_PORT:=10000
```

The server will listen on TCP port 10000 for incoming connections from Unity. Return to the Unity editor and import the UR5e robot model by converting the URDF to a Unity-compatible format using the URDF Importer package. Install the package via the Package Manager by adding `https://github.com/Unity-Technologies/URDF-Importer.git?path=/com.unity.robotics.urdf-importer`, then in the Unity menu bar select **Assets → Import Robot from URDF** and browse to the `ur5e.urdf` file. Set the axis conversion to **Y-up** and import with default articulation body settings.

The UR5e model will appear in the scene hierarchy as a nested GameObject structure with articulation bodies representing each joint. To synchronize these joints with ROS 2, attach a custom `JointStateSubscriber` script to the robot root object. Create a new C# script in `Assets/Scripts/JointStateSubscriber.cs`:

```csharp
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class JointStateSubscriber : MonoBehaviour
{
    private ROSConnection ros;
    private ArticulationBody[] articulationChain;
    private string[] jointNames = new string[] {
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint"
    };

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<JointStateMsg>("joint_states", UpdateJointStates);
        
        articulationChain = GetComponentsInChildren<ArticulationBody>();
    }

    void UpdateJointStates(JointStateMsg jointStateMsg)
    {
        for (int i = 0; i < jointStateMsg.name.Length; i++)
        {
            string jointName = jointStateMsg.name[i];
            int jointIndex = System.Array.IndexOf(jointNames, jointName);
            
            if (jointIndex >= 0 && jointIndex < articulationChain.Length)
            {
                ArticulationBody joint = articulationChain[jointIndex + 1];
                ArticulationDrive drive = joint.xDrive;
                drive.target = (float)(jointStateMsg.position[i] * Mathf.Rad2Deg);
                joint.xDrive = drive;
            }
        }
    }
}
```

Attach this script to the UR5e root GameObject in Unity, then press Play in the editor. Return to the ROS 2 terminal running the joint state publisher GUI and manipulate the sliders. You will observe the Unity robot model mirroring the joint angles in real time, validating that the ROS-Unity bridge is functioning correctly. This establishes the baseline communication infrastructure required for all subsequent verification exercises.

For VR integration, install the XR Plugin Management package in Unity via **Edit → Project Settings → XR Plug-in Management** and enable the OpenXR provider. Add the XR Interaction Toolkit package from the Package Manager (version 2.5.0 or later), then create a new XR Origin GameObject by right-clicking in the hierarchy and selecting **XR → XR Origin (VR)**. This spawns a tracked camera rig with left and right hand controllers. Position the XR Origin at coordinates (0, 1.6, -2) to place the operator's viewpoint two meters in front of the robot at typical standing eye height.

The operational verification environment is now complete. The remainder of this guide will validate pose accuracy, temporal latency, and collision boundary behaviors through three progressively rigorous exercises.

## Exercise 1: Foundational Practical Implementation

This first exercise establishes ground-truth pose accuracy by comparing the robot's end-effector position in the VR environment against analytically computed forward kinematics. You will inject known joint angle configurations, compute the expected Cartesian coordinates using the Denavit-Hartenberg parameter method, and measure the spatial deviation in Unity's world frame using virtual measurement probes.

The UR5e manipulator's Denavit-Hartenberg parameters define the geometric relationship between consecutive joint frames. For the UR5e, the DH table is:

| Joint | α (rad) | a (m)   | d (m)    | θ (rad)  |
|-------|---------|---------|----------|----------|
| 1     | π/2     | 0       | 0.08916  | θ₁       |
| 2     | 0       | -0.425  | 0        | θ₂       |
| 3     | 0       | -0.39225| 0        | θ₃       |
| 4     | π/2     | 0       | 0.10915  | θ₄       |
| 5     | -π/2    | 0       | 0.09465  | θ₅       |
| 6     | 0       | 0       | 0.0823   | θ₆       |

The homogeneous transformation matrix from joint *i-1* to joint *i* follows the standard DH convention:

$$
T_i = \begin{bmatrix}
\cos\theta_i & -\sin\theta_i \cos\alpha_i & \sin\theta_i \sin\alpha_i & a_i \cos\theta_i \\
\sin\theta_i & \cos\theta_i \cos\alpha_i & -\cos\theta_i \sin\alpha_i & a_i \sin\theta_i \\
0 & \sin\alpha_i & \cos\alpha_i & d_i \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

Create a Python script at `~/vr_robotics_lab/src/ur5e_description/scripts/compute_fk.py` to calculate the end-effector pose for a given joint configuration:

```python
import numpy as np
import sys

def dh_transform(alpha, a, d, theta):
    """Compute DH transformation matrix."""
    return np.array([
        [np.cos(theta), -np.sin(theta)*np.cos(alpha), np.sin(theta)*np.sin(alpha), a*np.cos(theta)],
        [np.sin(theta), np.cos(theta)*np.cos(alpha), -np.cos(theta)*np.sin(alpha), a*np.sin(theta)],
        [0, np.sin(alpha), np.cos(alpha), d],
        [0, 0, 0, 1]
    ])

def ur5e_forward_kinematics(joint_angles):
    """
    Compute UR5e end-effector pose given joint angles in radians.
    Returns 4x4 homogeneous transformation matrix.
    """
    # DH parameters: [alpha, a, d]
    dh_params = [
        [np.pi/2, 0, 0.08916],
        [0, -0.425, 0],
        [0, -0.39225, 0],
        [np.pi/2, 0, 0.10915],
        [-np.pi/2, 0, 0.09465],
        [0, 0, 0.0823]
    ]
    
    T = np.eye(4)
    for i, (alpha, a, d) in enumerate(dh_params):
        T = T @ dh_transform(alpha, a, d, joint_angles[i])
    
    return T

if __name__ == "__main__":
    # Test configuration: all joints at 0 degrees
    joint_config = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    if len(sys.argv) == 7:
        joint_config = [float(x) for x in sys.argv[1:7]]
    
    T_end = ur5e_forward_kinematics(joint_config)
    
    print("Joint Configuration (rad):", joint_config)
    print("\nEnd-Effector Transformation Matrix:")
    print(T_end)
    print("\nEnd-Effector Position (m):")
    print(f"X: {T_end[0, 3]:.6f}")
    print(f"Y: {T_end[1, 3]:.6f}")
    print(f"Z: {T_end[2, 3]:.6f}")
```

Make the script executable and test it with the zero-configuration pose:

```bash
chmod +x ~/vr_robotics_lab/src/ur5e_description/scripts/compute_fk.py
python3 ~/vr_robotics_lab/src/ur5e_description/scripts/compute_fk.py 0 0 0 0 0 0
```

The output should indicate an end-effector position of approximately X = -0.81725 m, Y = 0.19145 m, Z = -0.00599 m in the base frame. This represents the fully extended horizontal reach configuration.

Now configure Unity to measure the actual end-effector position in the VR scene. Create a new empty GameObject named `EndEffectorProbe` and attach the following C# script as `Assets/Scripts/EndEffectorPoseLogger.cs`:

```csharp
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Geometry;

public class EndEffectorPoseLogger : MonoBehaviour
{
    public Transform endEffectorTransform;
    private ROSConnection ros;
    private float logInterval = 1.0f;
    private float lastLogTime = 0f;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<PoseStampedMsg>("end_effector_pose");
        
        if (endEffectorTransform == null)
        {
            Debug.LogError("End effector transform not assigned!");
        }
    }

    void Update()
    {
        if (Time.time - lastLogTime >= logInterval && endEffectorTransform != null)
        {
            Vector3 pos = endEffectorTransform.position;
            Quaternion rot = endEffectorTransform.rotation;
            
            PoseStampedMsg poseMsg = new PoseStampedMsg
            {
                header = new RosMessageTypes.Std.HeaderMsg
                {
                    stamp = new RosMessageTypes.BuiltinInterfaces.TimeMsg
                    {
                        sec = (int)Time.time,
                        nanosec = (uint)((Time.time % 1) * 1e9)
                    },
                    frame_id = "base_link"
                },
                pose = new PoseMsg
                {
                    position = new PointMsg(pos.x, pos.y, pos.z),
                    orientation = new QuaternionMsg(rot.x, rot.y, rot.z, rot.w)
                }
            };
            
            ros.Publish("end_effector_pose", poseMsg);
            
            Debug.Log($"End-Effector Position: X={pos.x:F6}, Y={pos.y:F6}, Z={pos.z:F6}");
            lastLogTime = Time.time;
        }
    }
}
```

In the Unity hierarchy, locate the UR5e robot model and drill down to find the `wrist_3_link` GameObject, which represents the tool flange mounting point. Drag this transform into the `endEffectorTransform` field of the `EndEffectorPoseLogger` script attached to the `EndEffectorProbe` GameObject.

Launch the full verification stack. In terminal 1, start the ROS 2 robot state publisher:

```bash
cd ~/vr_robotics_lab
source install/setup.bash
ros2 launch ur5e_description display.launch.py
```

In terminal 2, launch the ROS TCP endpoint:

```bash
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0 -p ROS_TCP_PORT:=10000
```

In terminal 3, echo the end-effector pose topic to monitor Unity's position reports:

```bash
ros2 topic echo /end_effector_pose
```

Press Play in the Unity editor. The VR scene will activate, and you will observe real-time pose messages streaming in terminal 3. With all joints at zero degrees, compare the Unity-reported position against the analytical forward kinematics result. Due to Unity's left-handed Y-up coordinate system versus ROS's right-handed Z-up convention, you must apply the transformation:

$$
\begin{bmatrix} x_{Unity} \\ y_{Unity} \\ z_{Unity} \end{bmatrix} = \begin{bmatrix} -z_{ROS} \\ y_{ROS} \\ x_{ROS} \end{bmatrix}
$$

Apply this transformation mentally or via a Python helper script. For the zero-configuration case, you should find Unity reporting approximately X = 0.006 m, Y = 0.191 m, Z = 0.817 m after coordinate frame conversion. The discrepancy should remain below 1 millimeter if the URDF import preserved link lengths and joint offsets correctly.

Now inject three additional test configurations to validate pose accuracy across the workspace. In the joint state publisher GUI, set the following configurations sequentially and record both the analytical FK result and the Unity measurement:

**Configuration A (Elbow Up):**
- shoulder_pan: 0.0 rad
- shoulder_lift: -1.57 rad
- elbow: 1.57 rad
- wrist_1: -1.57 rad
- wrist_2: 0.0 rad
- wrist_3: 0.0 rad

**Configuration B (Reach Forward):**
- shoulder_pan: 0.0 rad
- shoulder_lift: -0.785 rad
- elbow: 0.785 rad
- wrist_1: -0.785 rad
- wrist_2: 0.0 rad
- wrist_3: 0.0 rad

**Configuration C (Rotated Base):**
- shoulder_pan: 1.57 rad
- shoulder_lift: -1.57 rad
- elbow: 1.57 rad
- wrist_1: -1.57 rad
- wrist_2: 0.0 rad
- wrist_3: 0.0 rad

For each configuration, run the Python FK script with the corresponding joint angles and compare the output to the Unity log. Create a verification spreadsheet with columns for Configuration ID, Joint Angles, Analytical X/Y/Z, Unity X/Y/Z, and Euclidean Error. The Euclidean error is computed as:

$$
\epsilon = \sqrt{(x_{analytical} - x_{Unity})^2 + (y_{analytical} - y_{Unity})^2 + (z_{analytical} - z_{Unity})^2}
$$

For a correctly calibrated system, all errors should remain below 2 millimeters. If errors exceed this threshold, verify that the URDF link lengths match the official UR5e specification and that Unity's articulation body hierarchy preserves the correct parent-child joint relationships. Common failure modes include incorrect axis assignments (X vs Z rotation axes) or inverted joint angle signs due to coordinate frame mismatches.

This foundational exercise validates that the kinematic chain in VR accurately represents the physical robot's geometry. All subsequent exercises depend on this spatial ground truth.

## Exercise 2: Parameter Variation & Empirical Analysis

The second exercise quantifies end-to-end system latency by measuring the time delay between a joint state command issued in ROS 2 and the corresponding visual update in the VR environment. This latency budget directly impacts teleoperation control stability and must remain below 50 milliseconds to avoid oscillatory behavior or operator nausea during head-tracked manipulation.

Latency arises from four cascaded stages: ROS 2 message serialization and network transmission, Unity's main thread message queue processing, physics engine articulation body integration, and GPU rendering pipeline with VSync synchronization. You will instrument each stage with high-resolution timestamps to isolate bottlenecks and characterize the empirical latency distribution.

Begin by modifying the joint state publisher to inject timestamps at the moment of command generation. Create a custom ROS 2 node at `~/vr_robotics_lab/src/ur5e_description/scripts/latency_test_publisher.py`:

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Time
import time
import math

class LatencyTestPublisher(Node):
    def __init__(self):
        super().__init__('latency_test_publisher')
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.1, self.publish_joint_state)
        
        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        self.phase = 0.0
        self.get_logger().info('Latency test publisher initialized')
    
    def publish_joint_state(self):
        msg = JointState()
        
        # Get high-resolution timestamp
        current_time = self.get_clock().now().to_msg()
        msg.header.stamp = current_time
        msg.header.frame_id = 'base_link'
        
        msg.name = self.joint_names
        
        # Sinusoidal trajectory for smooth motion
        self.phase += 0.1
        base_angle = 0.5 * math.sin(self.phase)
        
        msg.position = [
            base_angle,
            -1.57 + 0.3 * math.sin(self.phase),
            1.57 + 0.3 * math.cos(self.phase),
            -1.57,
            0.0,
            0.0
        ]
        
        msg.velocity = [0.0] * 6
        msg.effort = [0.0] * 6
        
        self.publisher.publish(msg)
        
        # Log timestamp for latency correlation
        timestamp_ns = current_time.sec * 1e9 + current_time.nanosec
        self.get_logger().info(f'Published at: {timestamp_ns}')

def main(args=None):
    rclpy.init(args=args)
    node = LatencyTestPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

Make the script executable and launch it in place of the GUI publisher:

```bash
chmod +x ~/vr_robotics_lab/src/ur5e_description/scripts/latency_test_publisher.py
cd ~/vr_robotics_lab
source install/setup.bash
ros2 run ur5e_description latency_test_publisher.py
```

The robot will now execute a sinusoidal motion pattern, and each joint state message will carry a precise ROS 2 timestamp in its header.

Next, instrument the Unity side to capture the receipt timestamp and compute the delta. Modify the `JointStateSubscriber.cs` script to log latency measurements:

```csharp
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;
using System.Collections.Generic;
using System.IO;

public class JointStateSubscriber : MonoBehaviour
{
    private ROSConnection ros;
    private ArticulationBody[] articulationChain;
    private string[] jointNames = new string[] {
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint"
    };
    
    private List<float> latencySamples = new List<float>();
    private StreamWriter logFile;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<JointStateMsg>("joint_states", UpdateJointStates);
        
        articulationChain = GetComponentsInChildren<ArticulationBody>();
        
        // Open latency log file
        string logPath = Path.Combine(Application.dataPath, "..", "latency_log.csv");
        logFile = new StreamWriter(logPath, false);
        logFile.WriteLine("ROS_Timestamp_NS,Unity_Timestamp_NS,Latency_MS");
        
        Debug.Log($"Latency log file created at: {logPath}");
    }

    void UpdateJointStates(JointStateMsg jointStateMsg)
    {
        // Capture Unity receive timestamp immediately
        long unityTimestampNS = System.DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() * 1000000;
        
        // Extract ROS timestamp from message header
        long rosTimestampNS = (long)jointStateMsg.header.stamp.sec * 1000000000L + 
                              (long)jointStateMsg.header.stamp.nanosec;
        
        // Compute latency in milliseconds
        float latencyMS = (unityTimestampNS - rosTimestampNS) / 1000000.0f;
        
        latencySamples.Add(latencyMS);
        logFile.WriteLine($"{rosTimestampNS},{unityTimestampNS},{latencyMS:F3}");
        
        // Update joint positions
        for (int i = 0; i < jointStateMsg.name.Length; i++)
        {
            string jointName = jointStateMsg.name[i];
            int jointIndex = System.Array.IndexOf(jointNames, jointName);
            
            if (jointIndex >= 0 && jointIndex < articulationChain.Length)
            {
                ArticulationBody joint = articulationChain[jointIndex + 1];
                ArticulationDrive drive = joint.xDrive;
                drive.target = (float)(jointStateMsg.position[i] * Mathf.Rad2Deg);
                joint.xDrive = drive;
            }
        }
        
        // Log statistics every 100 samples
        if (latencySamples.Count % 100 == 0)
        {
            float avgLatency = 0f;
            foreach (float sample in latencySamples)
                avgLatency += sample;
            avgLatency /= latencySamples.Count;
            
            Debug.Log($"Average Latency: {avgLatency:F2} ms (n={latencySamples.Count})");
        }
    }

    void OnApplicationQuit()
    {
        if (logFile != null)
        {
            logFile.Close();
            
            // Compute final statistics
            if (latencySamples.Count > 0)
            {
                latencySamples.Sort();
                float median = latencySamples[latencySamples.Count / 2];
                float p95 = latencySamples[(int)(latencySamples.Count * 0.95)];
                float p99 = latencySamples[(int)(latencySamples.Count * 0.99)];
                
                Debug.Log($"Latency Statistics (n={latencySamples.Count}):");
                Debug.Log($"  Median: {median:F2} ms");
                Debug.Log($"  95th percentile: {p95:F2} ms");
                Debug.Log($"  99th percentile: {p99:F2} ms");
            }
        }
    }
}
```

Launch the full stack with the latency test publisher running. Press Play in Unity and allow the robot to execute the sinusoidal trajectory for at least 60 seconds to accumulate sufficient statistical samples. Monitor the Unity console for the periodic average latency reports.

After stopping the Unity playback, examine the `latency_log.csv` file in the project root directory. Load this CSV into a Python environment for empirical analysis. Create a new script at `~/vr_robotics_lab/analyze_latency.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Load latency data
df = pd.read_csv('latency_log.csv')

latency_ms = df['Latency_MS'].values

# Remove outliers beyond 3 standard deviations
mean_latency = np.mean(latency_ms)
std_latency = np.std(latency_ms)
filtered_latency = latency_ms[np.abs(latency_ms - mean_latency) < 3 * std_latency]

# Compute statistics
median = np.median(filtered_latency)
p95 = np.percentile(filtered_latency, 95)
p99 = np.percentile(filtered_latency, 99)
mean = np.mean(filtered_latency)
std = np.std(filtered_latency)

print("Latency Analysis Results")
print("=" * 40)
print(f"Sample count: {len(filtered_latency)}")
print(f"Mean:         {mean:.2f} ms")
print(f"Std Dev:      {std:.2f} ms")
print(f"Median:       {median:.2f} ms")
print(f"95th %ile:    {p95:.2f} ms")
print(f"99th %ile:    {p99:.2f} ms")

# Plot histogram
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(filtered_latency, bins=50, edgecolor='black', alpha=0.7)
plt.axvline(median, color='r', linestyle='--', label=f'Median: {median:.2f} ms')
plt.axvline(p95, color='orange', linestyle='--', label=f'P95: {p95:.2f} ms')
plt.xlabel('Latency (ms)')
plt.ylabel('Frequency')
plt.title('Latency Distribution')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot time series
plt.subplot(1, 2, 2)
plt.plot(filtered_latency, linewidth=0.5, alpha=0.7)
plt.axhline(median, color='r', linestyle='--', label=f'Median: {median:.2f} ms')
plt.axhline(p95, color='orange', linestyle='--', label=f'P95: {p95:.2f} ms')
plt.xlabel('Sample Index')
plt.ylabel('Latency (ms)')
plt.title('Latency Time Series')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('latency_analysis.png', dpi=150)
print("\nPlot saved to latency_analysis.png")

# Test for normality
shapiro_stat, shapiro_p = stats.shapiro(filtered_latency[:5000])  # Shapiro-Wilk on first 5000 samples
print(f"\nShapiro-Wilk normality test: W={shapiro_stat:.4f}, p={shapiro_p:.4f}")
if shapiro_p < 0.05:
    print("Latency distribution is NOT normal (reject H0)")
else:
    print("Latency distribution is approximately normal")
```

Execute the analysis script:

```bash
python3 ~/vr_robotics_lab/analyze_latency.py
```

For a typical workstation with a dedicated GPU and local ROS 2 communication, you should observe a median latency between 8 and 15 milliseconds, with the 95th percentile remaining below 25 milliseconds. The distribution often exhibits a right-skewed tail due to occasional garbage collection pauses in Unity's C# runtime or GPU driver stalls during frame rendering.

If the 95th percentile exceeds 50 milliseconds, investigate the following optimization pathways. First, verify that Unity's quality settings use the **Ultra** performance preset with VSync disabled. Navigate to **Edit → Project Settings → Quality** and set VSync Count to **Don't Sync**. This decouples the rendering loop from the monitor's refresh rate, reducing frame-time variance.

Second, confirm that the ROS TCP Connector is not buffering messages excessively. In the ROS Settings window, set the **Queue Size** to 1 to force immediate processing of the most recent joint state rather than draining a backlog of stale messages. Third, enable Unity's Job System and Burst compiler for the articulation body physics integration. Navigate to **Edit → Project Settings → Physics** and enable **Enhanced Determinism** with **Reuse Collision Callbacks** checked.

Fourth, profile the ROS 2 middleware layer to isolate serialization overhead. Switch from the default CycloneDDS to FastDDS by exporting the RMW implementation:

```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Rerun the latency test and compare results. FastDDS typically reduces median latency by 2-3 milliseconds due to optimized shared memory transport when both publisher and subscriber reside on the same host.

Finally, analyze the parameter sensitivity by varying the joint state publication rate. Modify the `latency_test_publisher.py` timer interval from 0.1 seconds (10 Hz) to 0.02 seconds (50 Hz) and 0.01 seconds (100 Hz). Record the latency statistics for each configuration. You will observe that higher publication rates increase the 99th percentile tail due to message queue contention, but median latency remains stable. For teleoperation tasks, a 50 Hz update rate provides the optimal balance between control bandwidth and latency stability.

Document your findings in a parameter variation table with columns for Publication Rate (Hz), Median Latency (ms), P95 Latency (ms), and P99 Latency (ms). This empirical characterization informs the operational tuning of deployed VR teleoperation systems.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The final exercise validates collision avoidance and workspace boundary enforcement under adversarial conditions where rapid trajectory commands drive the manipulator toward kinematic singularities, joint limits, or virtual obstacles. You will implement a real-time collision detection framework in Unity, inject pathological motion commands, and verify that the system gracefully halts or recovers without damage to the virtual or physical hardware.

Begin by defining the operational workspace as a cylindrical volume centered at the robot base with radius 0.85 meters and height 1.2 meters. Any commanded trajectory that would place the end-effector outside this volume must trigger an emergency stop. Create a new Unity script at `Assets/Scripts/WorkspaceBoundaryEnforcer.cs`:

```csharp
using UnityEngine;

public class WorkspaceBoundaryEnforcer : MonoBehaviour
{
    public Transform endEffectorTransform;
    public Transform baseTransform;
    public float workspaceRadius = 0.85f;
    public float workspaceHeight = 1.2f;
    public bool enforceBoundaries = true;
    
    private bool boundaryViolationActive = false;
    private Material endEffectorMaterial;
    private Color originalColor;

    void Start()
    {
        if (endEffectorTransform == null || baseTransform == null)
        {
            Debug.LogError("End effector or base transform not assigned!");
            return;
        }
        
        // Get material for visual feedback
        Renderer renderer = endEffectorTransform.GetComponent<Renderer>();
        if (renderer != null)
        {
            endEffectorMaterial = renderer.material;
            originalColor = endEffectorMaterial.color;
        }
    }

    void Update()
    {
        if (!enforceBoundaries || endEffectorTransform == null || baseTransform == null)
            return;
        
        Vector3 localPos = baseTransform.InverseTransformPoint(endEffectorTransform.position);
        
        // Check cylindrical boundary
        float radialDistance = Mathf.Sqrt(localPos.x * localPos.x + localPos.z * localPos.z);
        float height = localPos.y;
        
        bool violatesBoundary = radialDistance > workspaceRadius || 
                                height < 0f || 
                                height > workspaceHeight;
        
        if (violatesBoundary && !boundaryViolationActive)
        {
            OnBoundaryViolation(localPos, radialDistance, height);
            boundaryViolationActive = true;
        }
        else if (!violatesBoundary && boundaryViolationActive)
        {
            OnBoundaryRestored();
            boundaryViolationActive = false;
        }
    }

    void OnBoundaryViolation(Vector3 localPos, float radialDist, float height)
    {
        Debug.LogWarning($"WORKSPACE BOUNDARY VIOLATION! " +
                        $"Position: ({localPos.x:F3}, {localPos.y:F3}, {localPos.z:F3}), " +
                        $"Radial: {radialDist:F3} m (limit: {workspaceRadius:F3} m), " +
                        $"Height: {height:F3} m (limit: 0 to {workspaceHeight:F3} m)");
        
        if (endEffectorMaterial != null)
        {
            endEffectorMaterial.color = Color.red;
        }
        
        // Trigger emergency stop
        BroadcastMessage("EmergencyStop", SendMessageOptions.DontRequireReceiver);
    }

    void OnBoundaryRestored()
    {
        Debug.Log("End effector returned to safe workspace");
        
        if (endEffectorMaterial != null)
        {
            endEffectorMaterial.color = originalColor;
        }
    }

    void OnDrawGizmos()
    {
        if (baseTransform == null) return;
        
        // Draw workspace cylinder
        Gizmos.color = boundaryViolationActive ? Color.red : Color.green;
        
        Vector3 basePos = baseTransform.position;
        
        // Draw cylinder outline
        int segments = 32;
        for (int i = 0; i < segments; i++)
        {
            float angle1 = (float)i / segments * 2f * Mathf.PI;
            float angle2 = (float)(i + 1) / segments * 2f * Mathf.PI;
            
            Vector3 p1_bottom = basePos + new Vector3(
                workspaceRadius * Mathf.Cos(angle1),
                0f,
                workspaceRadius * Mathf.Sin(angle1)
            );
            Vector3 p2_bottom = basePos + new Vector3(
                workspaceRadius * Mathf.Cos(angle2),
                0f,
                workspaceRadius * Mathf.Sin(angle2)
            );
            
            Vector3 p1_top = p1_bottom + Vector3.up * workspaceHeight;
            Vector3 p2_top = p2_bottom + Vector3.up * workspaceHeight;
            
            Gizmos.DrawLine(p1_bottom, p2_bottom);
            Gizmos.DrawLine(p1_top, p2_top);
            Gizmos.DrawLine(p1_bottom, p1_top);
        }
    }
}
```

Attach this script to an empty GameObject named `SafetySystem` in the Unity hierarchy. Assign the `wrist_3_link` transform to the `endEffectorTransform` field and the UR5e base link to the `baseTransform` field.

Next, implement collision detection against virtual obstacles using Unity's physics system. Create three box colliders representing a workbench, a safety fence, and a human operator's exclusion zone. In the Unity scene, add three cube GameObjects:

1. **Workbench**: Position (0, 0.4, 0.5), Scale (1.2, 0.8, 0.6), add Box Collider component, set Layer to "Obstacles"
2. **SafetyFence**: Position (-0.6, 0.6, 0), Scale (0.1, 1.2, 2.0), add Box Collider, Layer "Obstacles"
3. **OperatorZone**: Position (0.4, 0.8, -0.7), Scale (0.5, 1.6, 0.5), add Box Collider, Layer "Obstacles"

For each GameObject, set the Renderer material color to semi-transparent red (RGBA: 1, 0, 0, 0.3) to visualize the hazard zones.

Now instrument the robot's articulation bodies to detect collisions. Modify the `JointStateSubscriber` script to add collision event handlers:

```csharp
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;
using System.Collections.Generic;

public class JointStateSubscriber : MonoBehaviour
{
    private ROSConnection ros;
    private ArticulationBody[] articulationChain;
    private string[] jointNames = new string[] {
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint"
    };
    
    private bool emergencyStopActive = false;
    private List<Collision> activeCollisions = new List<Collision>();

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<JointStateMsg>("joint_states", UpdateJointStates);
        
        articulationChain = GetComponentsInChildren<ArticulationBody>();
        
        // Attach collision monitors to all articulation bodies
        foreach (ArticulationBody body in articulationChain)
        {
            CollisionMonitor monitor = body.gameObject.AddComponent<CollisionMonitor>();
            monitor.parentController = this;
        }
    }

    void UpdateJointStates(JointStateMsg jointStateMsg)
    {
        if (emergencyStopActive)
        {
            Debug.LogWarning("Emergency stop active - ignoring joint commands");
            return;
        }
        
        for (int i = 0; i < jointStateMsg.name.Length; i++)
        {
            string jointName = jointStateMsg.name[i];
            int jointIndex = System.Array.IndexOf(jointNames, jointName);
            
            if (jointIndex >= 0 && jointIndex < articulationChain.Length)
            {
                ArticulationBody joint = articulationChain[jointIndex + 1];
                ArticulationDrive drive = joint.xDrive;
                drive.target = (float)(jointStateMsg.position[i] * Mathf.Rad2Deg);
                joint.xDrive = drive;
            }
        }
    }

    public void EmergencyStop()
    {
        if (!emergencyStopActive)
        {
            emergencyStopActive = true;
            Debug.LogError("EMERGENCY STOP TRIGGERED");
            
            // Freeze all articulation bodies
            foreach (ArticulationBody body in articulationChain)
            {
                body.immovable = true;
            }
        }
    }

    public void ResetEmergencyStop()
    {
        emergencyStopActive = false;
        activeCollisions.Clear();
        
        foreach (ArticulationBody body in articulationChain)
        {
            body.immovable = false;
        }
        
        Debug.Log("Emergency stop reset - system operational");
    }

    public void OnCollisionDetected(Collision collision)
    {
        if (collision.gameObject.layer == LayerMask.NameToLayer("Obstacles"))
        {
            if (!activeCollisions.Contains(collision))
            {
                activeCollisions.Add(collision);
                Debug.LogWarning($"Collision detected with {collision.gameObject.name} at {collision.contacts[0].point}");
                EmergencyStop();
            }
        }
    }

    public void OnCollisionLost(Collision collision)
    {
        activeCollisions.Remove(collision);
        
        if (activeCollisions.Count == 0 && emergencyStopActive)
        {
            Debug.Log("All collisions cleared");
        }
    }
}

public class CollisionMonitor : MonoBehaviour
{
    public JointStateSubscriber parentController;

    void OnCollisionEnter(Collision collision)
    {
        if (parentController != null)
        {
            parentController.OnCollisionDetected(collision);
        }
    }

    void OnCollisionExit(Collision collision)
    {
        if (parentController != null)
        {
            parentController.OnCollisionLost(collision);
        }
    }
}
```

Before testing, configure Unity's physics collision matrix to ensure the robot links detect collisions with obstacles but not with each other. Navigate to **Edit → Project Settings → Physics** and expand the **Layer Collision Matrix**. Create two new layers: "RobotLinks" and "Obstacles". Uncheck the box at the intersection of "RobotLinks" with itself to disable self-collision, but ensure "RobotLinks" collides with "Obstacles".

Assign all UR5e link GameObjects to the "RobotLinks" layer and all hazard zone GameObjects to the "Obstacles" layer.

Now create a stress test trajectory publisher that deliberately commands the robot into forbidden zones. Create `~/vr_robotics_lab/src/ur5e_description/scripts/stress_test_publisher.py`:

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Time
import math
import random

class StressTestPublisher(Node):
    def __init__(self):
        super().__init__('stress_test_publisher')
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.05, self.publish_joint_state)
        
        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        self.test_phase = 0
        self.phase_counter = 0
        self.get_logger().info('Stress test publisher initialized')
    
    def publish_joint_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.name = self.joint_names
        
        # Test phases: 0=workspace boundary, 1=collision zone, 2=singularity, 3=random
        self.phase_counter += 1
        
        if self.phase_counter > 100:
            self.phase_counter = 0
            self.test_phase = (self.test_phase + 1) % 4
            self.get_logger().info(f'Entering test phase {self.test_phase}')
        
        if self.test_phase == 0:
            # Drive toward workspace boundary
            msg.position = [
                0.0,
                -0.5,
                0.5,
                -1.57,
                0.0,
                0.0
            ]
        elif self.test_phase == 1:
            # Drive into collision zone (toward workbench)
            msg.position = [
                0.0,
                -1.2,
                0.8,
                -1.0,
                0.0,
                0.0
            ]
        elif self.test_phase == 2:
            # Approach kinematic singularity (all joints near 0)
            msg.position = [
                0.1 * math.sin(self.phase_counter * 0.1),
                0.05 * math.cos(self.phase_counter * 0.1),
                0.1 * math.sin(self.phase_counter * 0.15),
                0.0,
                0.0,
                0.0
            ]
        else:
            # Random exploration
            msg.position = [
                random.uniform(-3.14, 3.14),
                random.uniform(-3.14, 0),
                random.uniform(0, 3.14),
                random.uniform(-3.14, 3.14),
                random.uniform(-3.14, 3.14),
                random.uniform(-3.14, 3.14)
            ]
        
        msg.velocity = [0.0] * 6
        msg.effort = [0.0] * 6
        
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = StressTestPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

Make the script executable and launch the stress test:

```bash
chmod +x ~/vr_robotics_lab/src/ur5e_description/scripts/stress_test_publisher.py
cd ~/vr_robotics_lab
source install/setup.bash
ros2 run ur5e_description stress_test_publisher.py
```

With Unity running in Play mode, observe the robot executing the four test phases. During phase 0, the end-effector should approach the cylindrical workspace boundary, triggering the red visual alarm and emergency stop message in the console. During phase 1, the robot will collide with the virtual workbench, causing all articulation bodies to freeze via the `immovable` flag.

To validate the recovery protocol, implement a manual reset command. Create a new ROS 2 service definition at `~/vr_robotics_lab/src/ur5e_description/srv/ResetEstop.srv`:

```yaml
---
bool success
string message
```

Add a service server to the Unity side by modifying the `JointStateSubscriber` script:

```csharp
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;
using RosMessageTypes.Std;

void Start()
{
    ros = ROSConnection.GetOrCreateInstance();
    ros.Subscribe<JointStateMsg>("joint_states", UpdateJointStates);
    ros.ImplementService<EmptyRequest>("reset_estop", ResetEstopService);
    
    articulationChain = GetComponentsInChildren<ArticulationBody>();
}

EmptyResponse ResetEstopService(EmptyRequest request)
{
    ResetEmergencyStop();
    return new EmptyResponse();
}
```

Build the ROS 2 package with the new service definition:

```bash
cd ~/vr_robotics_lab
colcon build
source install/setup.bash
```

When the emergency stop triggers, call the reset service from the ROS 2 terminal:

```bash
ros2 service call /reset_estop std_srvs/srv/Empty
```

The Unity console should log "Emergency stop reset - system operational" and the robot will resume motion.

To quantify the stress test results, instrument the system to log all boundary violations and collisions to a CSV file. Modify the `WorkspaceBoundaryEnforcer` and `CollisionMonitor` scripts to append events with timestamps and positions. After running the stress test for 5 minutes, analyze the event log to compute:

1. **Mean Time to Failure (MTTF):** Average duration between emergency stop events
2. **False Positive Rate:** Percentage of emergency stops triggered without actual collision or boundary violation
3. **Recovery Time:** Duration from emergency stop trigger to successful reset and motion resumption

For a correctly tuned system, MTTF should exceed 30 seconds during random exploration, false positive rate should remain below 5%, and recovery time should stay under 2 seconds. If MTTF falls below 10 seconds, the workspace boundaries may be overly conservative or the collision geometry requires refinement.

This stress testing protocol validates that the VR system behaves predictably under adversarial conditions and provides deterministic recovery pathways, critical requirements for any robotics simulation environment used in safety-critical applications.

## Operational Reference Guide & Diagnostic Checklist

### System Architecture Summary

The VR robotics verification environment consists of four decoupled subsystems: the ROS 2 joint state source, the ROS TCP bridge middleware, the Unity physics and rendering pipeline, and the HMD interface. Each subsystem contributes to the end-to-end latency budget and introduces potential failure modes that must be isolated during troubleshooting.

The joint state source publishes `sensor_msgs/JointState` messages at 10-100 Hz, carrying joint positions in radians, optional velocities, and effort values. The ROS TCP bridge serializes these messages over a persistent TCP socket, with the default port 10000. Unity's main thread polls this socket at each frame update, deserializes incoming messages, and updates the articulation body target positions. The physics engine integrates these targets at the fixed timestep rate (default 50 Hz), and the GPU renders the resulting transforms at the display refresh rate (60-120 Hz depending on HMD or monitor configuration).

### Common Failure Modes and Remediation

**Symptom:** Robot model does not appear in Unity scene after URDF import.

**Diagnosis:** Verify that the URDF file paths are correct and all mesh files (.dae or .stl) exist in the specified locations. Check the Unity console for import errors related to missing collada_urdf Python dependencies.

**Remediation:** Install the URDF Importer package prerequisites by running `pip3 install --user numpy pyyaml lxml` in the system Python environment. Re-import the URDF and confirm that all link GameObjects appear in the hierarchy.

---

**Symptom:** Robot model is present but does not move when joint states are published.

**Diagnosis:** Confirm that the ROS TCP endpoint server is running and listening on the correct port. Check that Unity's ROS Settings specify the same IP and port. Verify that the `JointStateSubscriber` script is attached to the robot root GameObject and the joint name array matches the URDF joint names exactly.

**Remediation:** Enable Unity's console log filtering to display all ROS messages. You should observe periodic "Received message" logs when joint states arrive. If no messages appear, the TCP connection is not established. Restart the ROS TCP endpoint with verbose logging: `ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0 -p ROS_TCP_PORT:=10000 --log-level DEBUG`.

---

**Symptom:** Robot motion is jerky or exhibits high-frequency oscillations.

**Diagnosis:** The articulation body PD controller gains are likely too aggressive. Unity's default stiffness and damping values may not suit the robot's inertia distribution.

**Remediation:** Select each articulation body in the hierarchy and inspect the **ArticulationBody** component. Reduce the **Stiffness** value from 10000 to 1000 and increase the **Damping** value from 100 to 500. Re-tune iteratively while observing motion smoothness.

---

**Symptom:** High latency (>50 ms) reported by the latency logger.

**Diagnosis:** Multiple bottlenecks can contribute to excessive latency. Check the following in order:
1. ROS 2 message queue depth: Ensure the joint state subscriber queue size is 1, not 10.
2. Unity frame rate: Confirm VSync is disabled and the frame rate exceeds 60 FPS.
3. CPU/GPU load: Monitor system resource usage during playback. If CPU exceeds 80%, reduce the publication rate or simplify the Unity scene.

**Remediation:** Profile the Unity editor using the **Window → Analysis → Profiler** tool. Identify whether the bottleneck occurs in the scripting layer (C# message deserialization), physics layer (articulation body integration), or rendering layer (GPU draw calls). Apply targeted optimizations to the slowest subsystem.

---

**Symptom:** Workspace boundary enforcer triggers false alarms when the end-effector is within safe limits.

**Diagnosis:** Coordinate frame mismatches between ROS and Unity may cause incorrect position calculations. Verify that the base transform reference frame aligns with the robot's physical base.

**Remediation:** Use Unity's Gizmo visualization to draw the workspace boundary cylinder in the Scene view. Manually position the end-effector at the boundary edge and confirm that the radial distance calculation matches the physical measurement. If discrepancies persist, re-check the URDF link offsets and the Unity Transform hierarchy.

---

**Symptom:** Collision detection does not trigger emergency stop when the robot penetrates an obstacle.

**Diagnosis:** The collision layers may be misconfigured, or the collider geometry may have gaps.

**Remediation:** Open the Physics settings (**Edit → Project Settings → Physics**) and verify that "RobotLinks" and "Obstacles" layers are set to collide. Add a Box Collider to a test GameObject, set its layer to "Obstacles", and manually move it to intersect the robot. If no collision event fires, the articulation body colliders may be missing. Ensure each link GameObject has a Collider component (Box, Sphere, or Mesh).

---

### Verification Checklist for Production Deployment

Before deploying a VR robotics system to operational environments, complete the following validation steps:

**Kinematic Accuracy Validation:**
- [ ] Forward kinematics verification completed for at least 5 test configurations with error < 2 mm
- [ ] All joint limits enforced in both software (Unity) and ROS parameter files
- [ ] End-effector pose published to ROS at >10 Hz with valid transform tree

**Latency Performance Validation:**
- [ ] Median end-to-end latency < 20 ms measured over 1000+ samples
- [ ] 95th percentile latency < 50 ms
- [ ] No frame drops or stuttering observed during 5-minute continuous operation

**Safety System Validation:**
- [ ] Workspace boundary enforcement triggers within 100 ms of violation
- [ ] Collision detection activates before penetration depth exceeds 5 mm
- [ ] Emergency stop immobilizes all joints within 1 physics timestep
- [ ] Manual reset service restores nominal operation within 2 seconds
- [ ] Stress test executed with MTTF > 30 seconds and false positive rate < 5%

**VR Interface Validation (if using HMD):**
- [ ] Head tracking latency < 20 ms to prevent motion sickness
- [ ] Stereo rendering maintains 90+ FPS per eye
- [ ] IPD (interpupillary distance) calibrated for operator
- [ ] Controller input mapped to robot commands with tactile feedback

**Documentation and Training:**
- [ ] Operator manual includes emergency stop procedure and recovery protocol
- [ ] System limitations documented (workspace boundaries, joint limits, collision geometry accuracy)
- [ ] Training session completed with all operators, including boundary violation scenarios

This operational verification framework ensures that VR-integrated robotics systems meet the reliability and safety standards required for industrial deployment, teleoperation interfaces, and operator training applications. The methodologies presented here generalize to arbitrary manipulator kinematics, sensor modalities, and virtual environment complexities, providing a reusable template for robotics verification workflows.
