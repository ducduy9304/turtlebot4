# ArUco-based Localization & Initialization Workflow

## Current Status: Completed ✅
The TurtleBot4 delivery script (`mail_delivery.py`) has been successfully migrated from the physical IR docking system to a visual ArUco-based initialization system for simulation.

### Execution Workflow
Ensure the environment is sourced before running (`source ~/turtlebot4_ws/setup_env.sh`).

1. Launch simulation environment & Nav2:
   ```bash
   ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py nav2:=true slam:=false localization:=true rviz:=true
   ```
2. Run delivery script:
   ```bash
   ros2 run turtlebot4_python_tutorials mail_delivery
   ```

### Key Modifications Made
1. **Removed Hardware Dependencies:** Disabled `navigator.dock()` and `navigator.undock()` (which caused the node to hang since they don't exist in this simulation).
2. **ArUco Visual Trigger:** Created the `ArucoVerifier` node subscribing to `/oakd/rgb/preview/image_raw`. The script will block until the camera successfully detects the ArUco marker (DICT_4X4_50) for 5 consecutive frames.
3. **Hardcoded Initial Pose:** After visual confirmation, automatically inject the `SPAWN_POSE` coordinates for AMCL so Nav2 completes its initialization.
4. **Marker Texture Fix:** Updated the `aruco_marker_0.png` texture in the Gazebo world to include a "quiet zone" (white border), helping the OpenCV library detect it accurately.

---

## Proposed Optimizations (Future Work)

### 1. Dynamic Pose Estimation
- **Problem:** Currently, the initialization coordinates are hardcoded (`SPAWN_POSE`). The robot must be spawned at one specific exact point.
- **Idea:** Use `cv2.aruco.estimatePoseSingleMarkers()` to get the actual distance and rotation angle from the robot to the marker (rvec, tvec). By combining this with the static coordinates of the marker on the map, we can use the coordinate system (TF2) to calculate the robot's exact map position backwards.
- **Benefit:** The robot can accurately localize itself anywhere as long as it sees the marker, regardless of a fixed spawn point.

### 2. Auto-Search Behavior (Spin to find marker)
- **Problem:** The current code waits passively. If the robot is spawned with its back to the marker, it will wait forever.
- **Idea:** Add a timeout (e.g., 10 seconds). If the marker is not seen, automatically publish a small angular velocity to `/cmd_vel` so the robot "scans" (spins) around until it locks onto the target.

### 3. Multi-Marker System (Multi-point localization)
- **Problem:** Coordinates are only fetched once upon boot. Over a long travel distance, AMCL might drift.
- **Idea:** Attach multiple "signpost" markers along the hallway/delivery areas. Have `ArucoVerifier` run in the background. Whenever the robot drives past and sees any marker, it will use that marker to correct the current position error in AMCL.

### 4. Optimize Camera Topic
- **Problem:** Currently analyzing the `.../preview/image_raw` topic (RGB color image, large bandwidth).
- **Idea:** The OAK-D often has mono (grayscale) cameras on the sides providing much higher framerates and using less CPU. Switching to a grayscale topic will be more suitable for the ArUco algorithm (which inherently has to convert bgr2gray anyway).
