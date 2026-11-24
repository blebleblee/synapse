# Studio Practice Labs: Autodesk Maya Production Pipelines and Rigging

## Objective & Studio Setup

This guide walks you through three progressive studio exercises that build production-ready rigging and pipeline skills in Autodesk Maya. You will construct a functional character rig from scratch, organize it within a studio-grade hierarchy, apply industry-standard constraint and deformation systems, and implement repeatable naming and organization conventions that hold up under collaborative, multi-artist pipelines.

Throughout these labs, you will work directly in Maya's interface, manipulate the scene graph, write Python scripts to automate pipeline tasks, and critique your own work against real-world production standards. The goal is not to follow a checklist but to develop the intuition that separates amateur rig files from production assets: clean hierarchies, predictable naming, robust constraint stacks, and deformation systems that survive animation without popping, stretching, or breaking symmetry.

### Environment & File Setup

You will need Autodesk Maya 2024 or later (the principles hold for 2022 and 2023, but attribute names and UI locations shift slightly). Install the **MASH Deformer**, **Advanced Skeleton**, and **Bifrost** plugin sets if available in your build; these are included with most commercial licenses but may require activation in the Plug-in Manager (Windows > Settings/Preferences > Plug-in Manager). You do not need external rigging plugins like AdvancedSkeleton or AutoDesk Rapidrig for these exercises—native Maya constraints, IK solvers, and deformers are sufficient and more instructive.

Create a project directory structure that mirrors professional studios:

```text
ProjectName/
├── scenes/
│   ├── 01_model_base.mb
│   ├── 02_rig_skeleton.mb
│   ├── 03_rig_controls.mb
│   ├── 04_rig_deformers.mb
│   └── 05_rig_final.mb
├── sourceimages/
│   └── reference_turntable.jpg
├── scripts/
│   ├── pipeline_utils.py
│   └── rig_tools.py
├── images/
└── data/
```

In Maya, set your project root via File > Set Project, then navigate to the ProjectName directory. This ensures all file references, texture paths, and scene dependencies resolve correctly when files are shared or archived.

---

## Exercise 1: Observation & Fundamentals Drill — Scene Graph Hierarchy and Node Architecture

### Understanding the Scene Through the Outliner

Begin by opening a reference character model. If you do not have a model, download the free **Karina** or **Mery** character rigs from the TurboSquid free resources or use a simple humanoid object you model yourself (a cylinder torso, sphere head, and arm/leg cylinders are sufficient for learning). Import the character mesh into a new Maya scene using File > Import.

The first discipline is understanding how Maya's scene graph is organized. Open the Outliner (Windows > Outliner) and examine the hierarchy. In a poorly organized file, you will see a flat list of objects: `pCylinder1`, `pSphere2`, `group3`, `transform4`. In a production rig, the Outliner becomes a legible blueprint: each object occupies a logical layer, naming follows a convention, and you can navigate to any part of the character without hunting.

Create a new, organized hierarchy for your character. We will start by grouping mesh geometry into logical body regions. In the Outliner, select all geometry objects (the mesh nodes representing the character's body parts). Then execute this Python script in the Script Editor (Windows > General Editors > Script Editor):

```python
import maya.cmds as cmds

# Select all visible mesh objects
meshes = cmds.ls(type='mesh', visible=True)
transforms = cmds.listRelatives(meshes, parent=True, fullPath=True)
transforms = list(set(transforms))  # Remove duplicates

# Create a top-level group for all geometry
geo_group = cmds.group(transforms, name='Geo_Group')

# Parent geometry under logical body regions
head_meshes = ['Prim_Head_Mesh', 'Prim_Eyes_Mesh']  # Replace with actual names
torso_meshes = ['Prim_Torso_Mesh', 'Prim_Spine_Mesh']
arm_l_meshes = ['Prim_Arm_L_Mesh']
arm_r_meshes = ['Prim_Arm_R_Mesh']
leg_l_meshes = ['Prim_Leg_L_Mesh']
leg_r_meshes = ['Prim_Leg_R_Mesh']

# Group each body region
cmds.group(head_meshes, name='Head_Geo', parent=geo_group)
cmds.group(torso_meshes, name='Torso_Geo', parent=geo_group)
cmds.group(arm_l_meshes, name='Arm_L_Geo', parent=geo_group)
cmds.group(arm_r_meshes, name='Arm_R_Geo', parent=geo_group)
cmds.group(leg_l_meshes, name='Leg_L_Geo', parent=geo_group)
cmds.group(leg_r_meshes, name='Leg_R_Geo', parent=geo_group)

cmds.select(clear=True)
cmds.confirmDialog(title='Hierarchy Created', message='Geometry organized into body regions.')
```

If your mesh naming differs, modify the lists to match. The principle remains: group related geometry under semantically meaningful parents, and lock the Geo_Group and all its children after setup to prevent accidental transforms during rigging. Lock transforms and visibility by selecting the group and running:

```python
import maya.cmds as cmds

def lock_hierarchy(node):
    """Recursively lock transforms and visibility on a node and its children."""
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
    for attr in attrs:
        try:
            cmds.setAttr(f'{node}.{attr}', lock=True)
        except:
            pass
    
    children = cmds.listRelatives(node, children=True, fullPath=True) or []
    for child in children:
        lock_hierarchy(child)

lock_hierarchy('Geo_Group')
```

### Building the Skeleton (Joint Chain)

The skeleton is the digital armature upon which deformations hang. Begin by hiding the geometry group so you can see the joints you will create. Select Geo_Group in the Outliner, right-click, and choose "Hide". Alternatively, press H to hide selected objects.

Create a joint chain for the spine. In the main menu bar, go to Skeleton > Create Joints (or use the menu Skeleton > Create Joints). This enters joint-creation mode. Click once at the base of the torso to place the first joint, then click at the sternum, then the neck base. Press Enter to exit joint-creation mode. These three joints form a simple spine.

Maya names newly created joints as `joint1`, `joint2`, `joint3` by default. Immediately rename them to follow a naming convention. Select `joint1` and in the Attributes panel (press Ctrl+A or Windows > Attribute Editor), change the name to `Spine_1_Jnt`. Select `joint2` and rename to `Spine_2_Jnt`. Select `joint3` and rename to `Spine_3_Jnt` (or `Neck_Base_Jnt` if you prefer semantic clarity). The convention is `BodyRegion_Index_Jnt` or `BodyRegion_Description_Jnt`.

Now create an arm chain. Enter joint-creation mode again (Skeleton > Create Joints). Click at the shoulder, elbow, wrist, and hand tip. Exit joint creation. This creates a child joint hierarchy under joint4. Select joint4 (the shoulder) and rename it `Arm_L_1_Jnt`. Select its child and rename to `Arm_L_2_Jnt` (elbow). Select the next to `Arm_L_3_Jnt` (wrist). Create a mirrored chain on the right side by either repeating the process or using Skeleton > Mirror Joints: select the left arm root, then Skeleton > Mirror Joints, choose "YZ" plane (assuming your character faces +X), and Maya will duplicate and mirror the chain, automatically renaming to `Arm_R_*_Jnt`.

Repeat for legs: create a hip-to-knee-to-ankle-to-toe chain on the left, rename to `Leg_L_1_Jnt`, `Leg_L_2_Jnt`, `Leg_L_3_Jnt`, then mirror. Create a head chain if desired: `Neck_1_Jnt` and `Head_Jnt` as a simple two-joint chain.

Your skeleton should now look like this in the Outliner:

```text
Spine_1_Jnt
├── Spine_2_Jnt
│   └── Spine_3_Jnt (or Neck_Base_Jnt)
│       └── Neck_1_Jnt
│           └── Head_Jnt
├── Arm_L_1_Jnt
│   ├── Arm_L_2_Jnt
│   │   └── Arm_L_3_Jnt
├── Arm_R_1_Jnt
│   ├── Arm_R_2_Jnt
│   │   └── Arm_R_3_Jnt
├── Leg_L_1_Jnt
│   ├── Leg_L_2_Jnt
│   │   └── Leg_L_3_Jnt
└── Leg_R_1_Jnt
    ├── Leg_R_2_Jnt
    │   └── Leg_R_3_Jnt
```

Bind the skeleton to the geometry. Select all geometry objects, then Shift+click the root joint (`Spine_1_Jnt`). Go to Skin > Bind Skin. Maya opens the Bind Skin dialog. Leave settings at default (Bind To: "Joints", Bind Skin: "Linear", Max Influences: 5). Click Bind. The geometry now deforms when you move joints.

Test deformation by selecting `Spine_2_Jnt` and rotating it slightly (press E for rotate, then middle-mouse-drag in the viewport). The torso should bend. If the deformation looks wrong—skin tears, inverts, or doesn't follow the joint—you will fix this in Exercise 2 using weight painting. For now, the goal is to confirm the bind and understand the relationship between skeleton and geometry.

### Node Architecture and Attribute Editor Inspection

Open the Attribute Editor (Windows > Attribute Editor or press Ctrl+A). Select one of your joints. Notice the Attributes panel shows Transform attributes (Translate, Rotate, Scale), plus special joint attributes: `Orient`, `Preferred Angle`, and `Rotation Order`. These are native to joint nodes and are distinct from regular transform nodes.

Select a geometry mesh (e.g., `Prim_Torso_Mesh`). In the Attributes panel, scroll down to the History section. You will see a `SkinCluster` node listed. Click on it to expand the skin cluster's attributes. Notice attributes like `Deformation Weights` and solver parameters. This is where the bind skin operation stored its deformation data. The scene graph is not just the visual hierarchy in the Outliner—it is also the network of deformation nodes, constraints, and solvers that control behavior.

**Key insight:** Maya's node-based architecture means that transforms are connected to deformations through attribute links. When you rotate a joint, the rotation value flows through the rig network to the skin cluster, which uses that rotation to deform the mesh. Understanding this data flow is fundamental to building reliable rigs.

Create a simple diagnostic script that prints the scene graph structure and all associated deformation nodes:

```python
import maya.cmds as cmds
import maya.api.OpenMaya as om

def print_scene_tree(node, indent=0):
    """Print scene hierarchy with associated deformation nodes."""
    node_type = cmds.nodeType(node)
    print(' ' * indent + f'{node} ({node_type})')
    
    # Check for deformation clusters or constraints
    history = cmds.listHistory(node, pruneDagObjects=True) or []
    deformers = [h for h in history if cmds.nodeType(h) in ['skinCluster', 'blendShape', 'wire', 'cluster']]
    
    if deformers:
        for deformer in deformers:
            print(' ' * (indent + 2) + f'└─ {deformer} ({cmds.nodeType(deformer)})')
    
    # Recurse through children
    children = cmds.listRelatives(node, children=True, fullPath=True) or []
    for child in children:
        print_scene_tree(child, indent + 2)

# Run from Script Editor
root = 'Spine_1_Jnt'
print(f'\nScene Graph for {root}:')
print_scene_tree(root)
```

Execute this script from the Script Editor (highlight all, then press Ctrl+Enter). The output will show your skeleton hierarchy and any deformers attached to geometry. This is a diagnostic tool you will use throughout production to verify rig structure.

Save your work: File > Save As, navigate to `scenes/01_model_base.mb`, and save. At the end of this exercise, you should have a character with organized geometry, a properly named skeleton, and a bound skin cluster. The deformation may be imperfect—that is acceptable. The goal is to understand the structural foundation.

---

## Exercise 2: Technique Study, Step by Step — Rigging Controls, Constraints, and Deformation Refinement

### Building a Control Rig Layer

Professional animators do not keyframe joints directly. Instead, they manipulate control objects (usually NURBS curves or simple polygon shapes) that drive the skeleton through constraints. This decoupling allows riggers to build robust, non-linear rigs and animators to work with intuitive, artist-friendly controls.

Open your saved scene from Exercise 1 (File > Open, `01_model_base.mb`). Create a new layer for controls. In the Outliner, right-click and select "Create a New Layer". Rename it `Rig_Controls`. We will organize all control objects in this layer for visibility toggling.

Begin with a master control at the character's center of mass. This control translates and rotates the entire character. Create a NURBS circle: Create > NURBS Primitives > Circle. It appears at the origin. Scale it up to roughly the size of the character's torso (hold S, middle-mouse-drag to scale). Position it at the base of the spine using move tool (press W, then middle-mouse-drag). Rename this object `Master_Ctrl`.

Right-click `Master_Ctrl` in the Outliner and choose "Add to Layer", then select the `Rig_Controls` layer. Repeat this for all controls you will create in this exercise.

Create a spine control rig using a series of cubic control shapes. These controls will use **IK (Inverse Kinematics)** to drive the spine joints. First, create a simple spine IK chain. Select `Spine_1_Jnt`, then Shift+click `Spine_3_Jnt` (or the last spine joint). Go to Skeleton > Create IK Handle. In the dialog, choose IK Solver: "ikRPsolver" (Rotate Plane solver, suitable for 3-joint chains). Click Create. Maya creates an IK handle object named `ikHandle1`. Rename it to `Spine_IK_Handle`.

An IK handle is not user-friendly—animators cannot intuitively see it in the viewport. Create a visual control curve for it. Execute this Python script to generate a cubic control shape:

```python
import maya.cmds as cmds

def create_control_curve(name, shape='cube', scale=1.0):
    """Create a NURBS or polygon control shape."""
    if shape == 'cube':
        # Create a NURBS cube-like curve (8 corner points + center)
        curve = cmds.curve(
            d=1,
            p=[
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1), (-1, -1, 1)
            ],
            k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            name=name
        )
        # Connect additional edges to complete the cube visual
        cmds.curve(curve, append=True, d=1, p=[(1, -1, -1), (1, -1, 1)])
        cmds.curve(curve, append=True, d=1, p=[(1, 1, -1), (1, 1, 1)])
        cmds.curve(curve, append=True, d=1, p=[(-1, 1, -1), (-1, 1, 1)])
    elif shape == 'circle':
        curve = cmds.circle(normal=(0, 1, 0), radius=1, name=name, constructionHistory=False)[0]
    
    cmds.scale(scale, scale, scale, curve)
    return curve

# Create spine control
spine_ctrl = create_control_curve('Spine_Ctrl', shape='cube', scale=2.0)
cmds.select(clear=True)
```

This creates a cubic NURBS curve named `Spine_Ctrl`. Move it to the chest area (press W, position it over the middle spine joint). Now constrain the IK handle to follow this control. Select `Spine_Ctrl`, then Shift+click `Spine_IK_Handle`. Go to Constrain > Point Constraint. The IK handle will now follow the control. Optionally, add an Orient Constraint if you want the IK handle to rotate with the control: select `Spine_Ctrl`, Shift+click `Spine_IK_Handle`, Constrain > Orient Constraint.

### Creating Arm Controls and IK Rigs

For arms, you will use an **IK chain** from shoulder to wrist, driven by a control. Select `Arm_L_1_Jnt`, then Shift+click `Arm_L_3_Jnt` (wrist). Go to Skeleton > Create IK Handle. Choose "ikRPsolver". Click Create. Rename the handle to `Arm_L_IK_Handle`.

Create a wrist control for the left arm:

```python
import maya.cmds as cmds

# Create wrist control
wrist_ctrl = cmds.curve(
    d=1,
    p=[(0, 1, 0), (0.7, 0.7, 0), (1, 0, 0), (0.7, -0.7, 0), (0, -1, 0),
       (-0.7, -0.7, 0), (-1, 0, 0), (-0.7, 0.7, 0), (0, 1, 0)],
    k=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    name='Arm_L_Wrist_Ctrl'
)

# Scale to appropriate size
cmds.scale(1.5, 1.5, 1.5, wrist_ctrl)

# Position at wrist joint
cmds.move(5, 2, 0, wrist_ctrl)  # Adjust coordinates to match your wrist position
```

Constrain the IK handle to the wrist control: select `Arm_L_Wrist_Ctrl`, Shift+click `Arm_L_IK_Handle`, Constrain > Point Constraint.

For the shoulder, you want rotational control over the arm's root joint without IK interference. Create a shoulder control:

```python
shoulder_ctrl = cmds.circle(normal=(0, 1, 0), radius=1.5, name='Arm_L_Shoulder_Ctrl', constructionHistory=False)[0]
cmds.move(4, 2.5, 0, shoulder_ctrl)
```

Constrain the shoulder joint's rotation to this control: select `Arm_L_Shoulder_Ctrl`, Shift+click `Arm_L_1_Jnt` (shoulder joint), Constrain > Orient Constraint. This allows the shoulder to rotate freely while the IK chain handles elbow and wrist.

Repeat for the right arm, naming controls `Arm_R_Wrist_Ctrl` and `Arm_R_Shoulder_Ctrl`.

### Leg Rigs with Pole Vector Constraints

Leg IK requires careful handling of the knee direction. Without a pole vector constraint, the IK solver might flip the knee backward unexpectedly. Create IK handles for both legs: select `Leg_L_1_Jnt`, Shift+click `Leg_L_3_Jnt`, Skeleton > Create IK Handle, choose "ikRPsolver". Rename to `Leg_L_IK_Handle`. Repeat for the right leg.

Create foot controls and pole vector guides. For the left foot:

```python
import maya.cmds as cmds

# Create foot control (a simple square/rectangle)
foot_ctrl = cmds.curve(
    d=1,
    p=[(1, 0, 1), (1, 0, -1), (-1, 0, -1), (-1, 0, 1), (1, 0, 1)],
    k=[0, 1, 2, 3, 4],
    name='Leg_L_Foot_Ctrl'
)
cmds.scale(1.5, 1.5, 1.5, foot_ctrl)
cmds.move(0, 0, -5, foot_ctrl)  # Position at ankle

# Create pole vector locator (guides IK knee direction)
pv_locator = cmds.spaceLocator(name='Leg_L_PoleVector_Loc')[0]
cmds.scale(0.3, 0.3, 0.3, pv_locator)
# Position in front of the knee (adjust based on your character's knee position)
cmds.move(0, 1.5, 3, pv_locator)
```

Constrain the foot IK handle to the foot control: select `Leg_L_Foot_Ctrl`, Shift+click `Leg_L_IK_Handle`, Constrain > Point Constraint. Then apply a Pole Vector constraint: select `Leg_L_PoleVector_Loc`, Shift+click `Leg_L_IK_Handle`, Constrain > Pole Vector. The knee will now point toward the pole vector locator, giving animators predictable control.

### Weight Painting and Skin Refinement

Return to the Geo_Group (unhide it if hidden). Select a geometry mesh and go to Skin > Paint Skin Weights Tool. This opens a brush interface where you paint the influence of each joint on nearby geometry. The red areas indicate 100% influence, blue indicates 0% influence.

The goal is to ensure that only nearby joints influence a vertex. For example, the torso geometry should be influenced primarily by spine joints, with little to no influence from arm or leg joints. If you see the arm deforming when you rotate the spine, the skin weights are wrong.

Paint systematically: select a mesh, start with `Spine_1_Jnt` in the Paint Weights tool, and paint red over the lower torso. Switch to `Spine_2_Jnt` and paint red over the mid-torso. For the shoulder area, paint influence from both spine and arm joints, with spine fading to blue as you approach the shoulder joint. Use a soft brush (Brush Radius: 1.0) and low opacity (Opacity: 0.3) to create smooth transitions.

After painting, test deformation by rotating joints. Select `Arm_L_2_Jnt` (elbow) and rotate it. The arm should bend naturally; the torso should not deform. Adjust weights if needed.

A production-grade skin weight file is saved separately. Export weights using Skin > Export Skin Weights. This creates a JSON file that can be reapplied to new geometry or shared with other riggers. Store this in `data/skin_weights_v01.json` for backup.

Save your work as `scenes/02_rig_skeleton.mb`.

---

## Exercise 3: Finished Piece & Self-Critique — Complete Rig Assembly, Pipeline Organization, and Animation Testing

### Assembling the Full Control Hierarchy

You now have controls for spine, arms, and legs. Create a master organizational structure so animators interact with a single hierarchy. At the top, place your `Master_Ctrl`. All other controls should be driven by or grouped under it.

Create a group called `Rig_System` to hold all rig components:

```python
import maya.cmds as cmds

# Create top-level rig group
rig_group = cmds.group(empty=True, name='Rig_System')

# Parent all control objects under it (order matters for hierarchy)
master_ctrl = 'Master_Ctrl'
spine_ctrl = 'Spine_Ctrl'
arm_l_wrist_ctrl = 'Arm_L_Wrist_Ctrl'
arm_l_shoulder_ctrl = 'Arm_L_Shoulder_Ctrl'
arm_r_wrist_ctrl = 'Arm_R_Wrist_Ctrl'
arm_r_shoulder_ctrl = 'Arm_R_Shoulder_Ctrl'
leg_l_foot_ctrl = 'Leg_L_Foot_Ctrl'
leg_r_foot_ctrl = 'Leg_R_Foot_Ctrl'
leg_l_pv = 'Leg_L_PoleVector_Loc'
leg_r_pv = 'Leg_R_PoleVector_Loc'

controls = [master_ctrl, spine_ctrl, arm_l_wrist_ctrl, arm_l_shoulder_ctrl, 
            arm_r_wrist_ctrl, arm_r_shoulder_ctrl, leg_l_foot_ctrl, leg_r_foot_ctrl]
pole_vectors = [leg_l_pv, leg_r_pv]

for ctrl in controls:
    try:
        cmds.parent(ctrl, rig_group)
    except:
        pass

# Create a separate group for pole vectors (usually hidden from animators)
pv_group = cmds.group(pole_vectors, name='PoleVectors_GRP', parent=rig_group)
cmds.setAttr(f'{pv_group}.visibility', 0)  # Hide by default

cmds.select(clear=True)
```

### Setting Up Animation Layers and Non-Destructive Workflow

Animation in production is non-destructive. Rather than keyframing controls directly, animators use **Animation Layers** to separate base motion, overlapping action, and secondary motion. Create an animation layer: select `Rig_System`, then go to Animation > Create Layers > Create Empty Layer. Rename it `Base_Motion_Layer`. Add controls to it: in the Animation Layers window (Windows > Animation > Animation Layers), right-click on the layer and "Add selected objects".

Create additional layers for overlapping action and secondary motion. This allows multiple artists to work on different aspects without conflicts.

### Testing the Rig with Forward Kinematics and IK Blending

Animate a simple pose to test the rig. Select `Master_Ctrl` and move it slightly (press W for move tool, middle-mouse-drag). The entire character should translate. Select `Spine_Ctrl` and rotate it (press E for rotate, middle-mouse-drag). The spine should bend and the connected geometry should deform smoothly.

Select `Arm_L_Wrist_Ctrl` and move it. The arm should follow via IK. If the elbow bends incorrectly or the wrist doesn't reach, adjust the pole vector `Leg_L_PoleVector_Loc` position. Move it further away from or toward the joint chain until the knee points in the correct direction.

Test FK (Forward Kinematics) rotation on individual joints. Select `Arm_L_1_Jnt` (shoulder) and rotate it (press E). The arm should rotate from the shoulder. If rotation feels stiff or unintuitive, check that the Joint Orient is set correctly. For a production rig, you might add an FK/IK blend attribute that allows animators to switch between FK and IK control, but for now, test both independently.

### Dynamics Simulation for Secondary Motion

Add secondary motion (hair, cloth, or accessories) using dynamics. Create a simple hair strand rig. First, create a chain of joints for the hair: Skeleton > Create Joints, place joints in a line above the character's head. Rename them `Hair_1_Jnt` through `Hair_4_Jnt`. Create an IK handle from the base to the tip: select `Hair_1_Jnt`, Shift+click `Hair_4_Jnt`, Skeleton > Create IK Handle, choose "ikSplineSolver" (this creates a smooth spine-like IK). Name it `Hair_IK_Handle`.

Constrain the hair root to the head: select `Head_Jnt`, Shift+click `Hair_1_Jnt`, Constrain > Parent Constraint. The hair will now move with the head.

Apply a hair dynamic: select the hair IK handle, go to Dynamics > Hair > Create Hair System. Maya creates a hair system that simulates gravity and collisions. The hair will now swing realistically when the character moves. Adjust the hair dynamics in Dynamics > Hair > Modify Hair System if the hair behaves too rigidly or too fluidly.

### Creating a Rig Documentation Script

Professional studios document rig structure and control mappings in readable formats. Create a Python script that generates a rig control map:

```python
import maya.cmds as cmds

def document_rig_controls(rig_root='Rig_System'):
    """Generate a control map document."""
    
    controls = cmds.listRelatives(rig_root, allDescendents=True, type='transform')
    control_info = []
    
    for ctrl in controls:
        # Get control type (joint, curve, locator)
        node_type = cmds.nodeType(ctrl)
        
        # Get control position
        try:
            pos = cmds.xform(ctrl, query=True, worldSpace=True, translation=True)
            pos_str = f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})"
        except:
            pos_str = "N/A"
        
        # Get parent
        parent = cmds.listRelatives(ctrl, parent=True)
        parent_str = parent[0] if parent else "Root"
        
        control_info.append({
            'name': ctrl,
            'type': node_type,
            'parent': parent_str,
            'position': pos_str
        })
    
    # Write to file
    output_file = 'data/rig_control_map.txt'
    with open(output_file, 'w') as f:
        f.write("RIG CONTROL DOCUMENTATION\n")
        f.write("=" * 60 + "\n\n")
        
        for ctrl in control_info:
            f.write(f"Control: {ctrl['name']}\n")
            f.write(f"  Type: {ctrl['type']}\n")
            f.write(f"  Parent: {ctrl['parent']}\n")
            f.write(f"  World Position: {ctrl['position']}\n\n")
    
    cmds.confirmDialog(title='Documentation Created', 
                       message=f'Rig documentation saved to {output_file}')

# Run from Script Editor
document_rig_controls()
```

Execute this from the Script Editor. It outputs a human-readable control map to `data/rig_control_map.txt`, documenting every control's name, type, parent, and position. This is invaluable for animators and future riggers who inherit the file.

### Finalizing the Scene File Structure

Before saving, freeze all transforms on control objects to prevent animation artifacts. Select all controls in `Rig_System`, then go to Modify > Freeze Transformations. This resets their local transforms to zero while maintaining their world position, ensuring clean keyframing for animators.

Lock the skeleton and geometry layers to prevent accidental selection during animation. Right-click `Geo_Group` in the Outliner, choose "Lock" to lock the entire layer. Do the same for the skeleton.

Create multiple incremental saves as you work. Save as `scenes/03_rig_controls.mb` after adding controls, `scenes/04_rig_deformers.mb` after refining skin weights, and `scenes/05_rig_final.mb` as the production-ready version. This allows rollback if issues arise.

### Publishing the Rig as an Importable Asset

Studio pipelines often separate rig creation from animation by exporting the rig as a referenced or imported file. To prepare your rig for publishing, group all rig elements (controls, IK handles, joints) under a top-level node labeled `RIG`. Then export this node as a separate Maya file:

```python
import maya.cmds as cmds

# Select the Rig_System group
rig_root = 'Rig_System'

# Export as a reference file
export_path = 'scenes/Character_Rig_v01.mb'

cmds.select(rig_root)
cmds.file(export_path, force=True, type='mayaBinary', exportSelected=True)

cmds.confirmDialog(title='Rig Exported', message=f'Rig exported to {export_path}')
```

This creates a standalone rig file that animators can import into animation scenes. When imported, the rig maintains its control structure but is isolated from the base model, allowing multiple animators to reference the same rig without file conflicts.

Save your final rig as `scenes/05_rig_final.mb`.

---

## Critique Checklist & Common Fixes

Use this checklist to evaluate your finished rig against production standards. Each criterion has a quick diagnostic and corrective action.

### Hierarchy and Naming

**Criterion:** Scene graph is legible and follows a consistent naming convention.

**Diagnostic:** Open the Outliner. Can you identify the purpose of every node at a glance? Are all names spelled consistently (e.g., all left-side objects use `_L_`, not `_L` or `Left_`)? Are there orphaned or duplicate objects?

**Common Issues & Fixes:**
- **Issue:** Unnamed nodes like `transform1`, `group5`.
  - **Fix:** Rename systematically. Select the node, press F2, type the new name. Use a template: `BodyRegion_Description_Type` (e.g., `Arm_L_IK_Handle`).
- **Issue:** Mixed naming conventions (`ArmLeft` vs. `Arm_L` vs. `LeftArm`).
  - **Fix:** Choose one convention and apply it uniformly. Run this script to find inconsistencies:
    ```python
    import maya.cmds as cmds
    
    nodes = cmds.ls(dag=True)
    left_names = [n for n in nodes if 'left' in n.lower()]
    if left_names and any('_L_' in n for n in nodes):
        print("NAMING CONFLICT: Mixed left-side naming conventions detected.")
        print("Left-side nodes:", left_names)
    ```

### Deformation Quality

**Criterion:** Geometry deforms smoothly and predictably when joints rotate; no tears, inversions, or weight bleeding.

**Diagnostic:** Select each joint and rotate it 90 degrees. Watch the geometry. Does it fold naturally? Are there sharp creases or discontinuities? Does unrelated geometry deform?

**Common Issues & Fixes:**
- **Issue:** Shoulder geometry stretches or tears when arm rotates.
  - **Fix:** Open Skin > Paint Skin Weights Tool. Select the shoulder geometry and the shoulder joint. Paint red (100% influence) only on the shoulder geometry; paint blue (0%) on adjacent arm geometry. Use a soft brush (Radius: 1.5, Opacity: 0.4) to create smooth transitions.
- **Issue:** Torso deforms when moving the arm IK handle.
  - **Fix:** This indicates skin weight bleeding from arm joints to torso geometry. Select torso geometry, open Paint Skin Weights, switch to arm joints, and paint them blue (zero influence) over the torso.
- **Issue:** Geometry inverts or flips inside-out when rotating a joint.
  - **Fix:** This is a binding error or negative scale. First, check joint orientation: select the joint, Modify > Freeze Transformations, then re-bind the skin. If the issue persists, verify that no geometry has negative scale (select the mesh, check Attributes panel for negative `scaleX`, `scaleY`, or `scaleZ`).

### Control Usability

**Criterion:** Controls are visually distinct, spatially intuitive, and respond predictably to animation input.

**Diagnostic:** Select each control. Can you easily see it in the viewport? Does it highlight in white when selected? When you move or rotate it, does the rig respond immediately without lag or flipping?

**Common Issues & Fixes:**
- **Issue:** Controls are too small or blend into geometry.
  - **Fix:** Select a control curve, press S for scale, middle-mouse-drag to increase size. Aim for 1.5–2.0 times the size of the body part it controls. Optionally, change control color: select the control, Display > Wireframe (or toggle shading), then right-click and choose "Assign New Color".
- **Issue:** IK handles snap or flip when animated.
  - **Fix:** This indicates an IK solver singularity or pole vector misalignment. Move the pole vector (`Leg_L_PoleVector_Loc`) further away from the joint chain. If the problem persists, switch to a different IK solver: select the IK handle, Attributes panel, search for "ikSolver", and try "ikSplineSolver" or "ikSCsolver".
- **Issue:** FK rotation feels non-intuitive or rotations don't follow expected axes.
  - **Fix:** Check joint orientation. Select the joint, Attributes panel, examine `Rotate Axis` and `Joint Orient`. These may be misaligned. Reorient using Skeleton > Reorient Joints or manually adjust Joint Orient values so that X-axis rotation feels natural.

### Constraint Integrity

**Criterion:** All constraints (Point, Orient, Parent, Pole Vector) are correctly applied and do not conflict.

**Diagnostic:** Select a control and check its Attributes. Scroll to Constraints. Are there conflicting constraints (e.g., two Translate values constrained differently)? Do rotations behave oddly when multiple orientation constraints are active?

**Common Issues & Fixes:**
- **Issue:** Parent constraint causes unexpected rotation or offset.
  - **Fix:** When creating a constraint, check the "Maintain Offset" option. Select the control, Shift+click the target, Constrain > Parent Constraint, check "Maintain Offset", click Add. This preserves the control's local position/rotation relative to its target.
- **Issue:** Pole vector constraint causes the IK chain to twist unexpectedly.
  - **Fix:** Ensure the pole vector is perpendicular to the joint plane. For a leg with hip-knee-ankle, the pole vector should be directly in front of the knee (along the Z-axis if the leg extends along Y). Move the locator and test incrementally.

### File Organization and Pipeline Readiness

**Criterion:** Scene file is organized for collaborative use; all references and assets are properly linked.

**Diagnostic:** Reopen the saved scene file. Do all references load correctly? Are there any "Unresolved Reference" warnings? Can you open the file on a different computer without broken links?

**Common Issues & Fixes:**
- **Issue:** References break when file is moved or opened on another machine.
  - **Fix:** Use relative paths. File > Reference Editor, right-click each reference, "Edit reference ...", ensure the reference path is relative (e.g., `../sourceimages/character_base.mb`) rather than absolute (e.g., `/Users/artistname/Projects/Character/scenes/character_base.mb`).
- **Issue:** Scene file is too large (> 50 MB) and slow to open.
  - **Fix:** Split the scene into separate files: `01_model_base.mb`, `02_rig_skeleton.mb`, etc. Use File > Create Reference to link them. This allows multiple artists to work on different components without file conflicts. Ensure the reference is locked (Edit > Reference > Lock Reference) so animators cannot accidentally modify referenced geometry.

### Animation Layer Stability

**Criterion:** Animation layers stack correctly; keyframes do not conflict or override each other unexpectedly.

**Diagnostic:** In the Animation Layers window, create a simple rotation keyframe on the Base_Motion layer, then create an overlay animation on a secondary layer. Play the timeline. Do both layers animate, or does one override the other?

**Common Issues & Fixes:**
- **Issue:** Keyframes on different layers conflict; character jitters or behaves unpredictably.
  - **Fix:** Ensure each layer's weight is set correctly. In Animation Layers window, right-click the layer, "Edit Layer Attributes", check the "Weight" value (should be 1.0 for full influence). If two layers have overlapping rotations, reduce one layer's weight or remove conflicting keyframes.

### Performance and Optimization

**Criterion:** Rig evaluates in real-time; playback is smooth at 24 FPS without stuttering.

**Diagnostic:** Play the timeline (press Spacebar). Watch the playback speed indicator at the bottom of the viewport. If it drops below 24 FPS, the rig is too heavy.

**Common Issues & Fixes:**
- **Issue:** Playback stutters or drops to 10–15 FPS.
  - **Fix:** Identify the heaviest computation nodes. Go to Windows > General Editors > Script Editor, run:
    ```python
    import maya.cmds as cmds
    
    # List all deformer nodes and their evaluation time
    deformers = cmds.ls(type=['skinCluster', 'blendShape', 'wire', 'cluster'])
    for deformer in deformers:
        print(f'{deformer}: {cmds.getAttr(f"{deformer}.nodeState")}')
    ```
    Set heavy deformers to "Cached" mode (nodeState: 2) during playback. Disable unnecessary constraints or simplify hair dynamics.

---

## Final Submission Workflow

After completing all three exercises, perform a final review:

1. **Save and increment:** Save the final rig as `scenes/05_rig_final.mb`.
2. **Export documentation:** Run the control map script to generate `data/rig_control_map.txt`.
3. **Test in a new animation scene:** Create a new scene, import your rig (File > Import), and animate a simple 10-frame walk cycle to verify all controls work correctly.
4. **Archive:** Copy the entire project directory to a backup location or version control system (e.g., Git). Include all scripts, documentation, and scene files.

A production rig is never "finished"—it evolves as animators discover edge cases or new requirements. Document all changes in a text file: `data/rig_changelog.txt`. Each time you refine the rig, note the date, the change, and the revised file version:

```text
RIG CHANGELOG
=============

v01 - Initial skeleton bind, basic IK setup
  - Created spine, arm, leg skeleton chains
  - Applied skinCluster binding with default weights
  - Added basic IK handles and foot controls

v02 - Control rig and constraint setup
  - Added NURBS controls for spine, arms, legs
  - Applied point and orient constraints
  - Refined skin weights for shoulder and hip deformation

v03 - Final deformation pass
  - Painted weights for smooth arm/leg bending
  - Added pole vector constraints for knees
  - Tested FK/IK blending and secondary motion (hair dynamics)
```

This rig is now production-ready: organized, documented, and tested. The skills you have developed—scene graph architecture, constraint stacks, deformation management, and pipeline organization—form the foundation of professional rigging across all studios.
