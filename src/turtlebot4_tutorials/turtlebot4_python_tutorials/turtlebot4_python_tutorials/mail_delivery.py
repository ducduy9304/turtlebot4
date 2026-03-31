#!/usr/bin/env python3

# Copyright 2023 Clearpath Robotics, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @author Hilary Luo (hluo@clearpathrobotics.com)
# Modified: ArUco-based initialization replacing dock-based flow

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image

from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Directions, TurtleBot4Navigator

import cv2
from cv_bridge import CvBridge

import threading
import time

# ============================================================
# CONFIGURATION - Hardcoded spawn pose (matches launch defaults)
# Robot spawns at x=1.0, y=0.0, yaw=3.14159 (SOUTH = facing -X)
# ============================================================
SPAWN_POSE = [1.0, 0.0]
SPAWN_HEADING = TurtleBot4Directions.SOUTH

# ArUco detection settings
ARUCO_DICT_TYPE = cv2.aruco.DICT_4X4_50      # Dictionary matching marker texture
REQUIRED_DETECTIONS = 5                       # Number of consecutive frames needed
CAMERA_TOPIC = '/oakd/rgb/preview/image_raw'  # OAK-D camera topic in simulation


class ArucoVerifier(Node):
    """
    Lightweight ROS 2 node that subscribes to the OAK-D camera feed,
    runs ArUco marker detection, and counts successful detections.
    """

    def __init__(self):
        super().__init__('aruco_verifier')
        self.bridge = CvBridge()
        self.detection_count = 0
        self.verified = False
        self.lock = threading.Lock()

        # ArUco detector setup
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT_TYPE)
        self.aruco_params = cv2.aruco.DetectorParameters_create()

        # Subscribe to camera
        self.subscription = self.create_subscription(
            Image,
            CAMERA_TOPIC,
            self._image_callback,
            qos_profile_sensor_data
        )
        self.get_logger().info(
            f'[ArUco] Subscribing to camera: {CAMERA_TOPIC}')
        self.get_logger().info(
            f'[ArUco] Waiting for {REQUIRED_DETECTIONS} valid detection frames...')

    def _image_callback(self, msg: Image):
        """Process each camera frame for ArUco markers."""
        with self.lock:
            if self.verified:
                return  # Already done, skip processing

        try:
            # Convert ROS Image → OpenCV BGR
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'[ArUco] cv_bridge error: {e}')
            return

        # Convert to grayscale for detection
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers
        corners, ids, _ = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.aruco_params)

        with self.lock:
            if ids is not None and len(ids) > 0:
                self.detection_count += 1
                detected_ids = [int(i) for i in ids.flatten()]
                self.get_logger().info(
                    f'[ArUco] ✓ Frame {self.detection_count}/{REQUIRED_DETECTIONS}'
                    f' — Detected marker IDs: {detected_ids}')

                if self.detection_count >= REQUIRED_DETECTIONS:
                    self.verified = True
                    self.get_logger().info(
                        '═══════════════════════════════════════════')
                    self.get_logger().info(
                        '[ArUco] VERIFICATION COMPLETE — '
                        f'{REQUIRED_DETECTIONS}/{REQUIRED_DETECTIONS} frames OK!')
                    self.get_logger().info(
                        '═══════════════════════════════════════════')
            else:
                self.get_logger().info(
                    f'[ArUco] ✗ No marker detected (still need '
                    f'{REQUIRED_DETECTIONS - self.detection_count} more frames)')

    def is_verified(self) -> bool:
        with self.lock:
            return self.verified


def run_aruco_verification(navigator: TurtleBot4Navigator) -> bool:
    """
    Spin an ArucoVerifier node until 5 valid frames are confirmed.
    Blocks the main flow until verification succeeds.
    Returns True on success.
    """
    verifier = ArucoVerifier()

    navigator.info('══════════════════════════════════════════════')
    navigator.info('[Phase 1] ArUco Marker Detection — Starting...')
    navigator.info('══════════════════════════════════════════════')

    try:
        while rclpy.ok() and not verifier.is_verified():
            rclpy.spin_once(verifier, timeout_sec=0.1)
            # Also spin navigator to keep it alive
            rclpy.spin_once(navigator, timeout_sec=0.05)
    except KeyboardInterrupt:
        verifier.get_logger().info('[ArUco] Interrupted by user.')
        verifier.destroy_node()
        return False

    verifier.destroy_node()
    return True


def main(args=None):
    rclpy.init(args=args)

    navigator = TurtleBot4Navigator()

    # ===================================================================
    # STEP 1: ArUco verification (replaces docking logic)
    # OLD (commented out — causes hang without real Create 3 hardware):
    #   if not navigator.getDockedStatus():
    #       navigator.info('Docking before intialising pose')
    #       navigator.dock()
    # ===================================================================

    navigator.info('Robot spawned. Starting ArUco verification sequence...')
    aruco_ok = run_aruco_verification(navigator)

    if not aruco_ok:
        navigator.error('ArUco verification failed or was interrupted. Exiting.')
        rclpy.shutdown()
        return

    # ===================================================================
    # STEP 2: Set hardcoded initial pose (spawn location)
    # ===================================================================
    navigator.info('══════════════════════════════════════════════')
    navigator.info('[Phase 2] Setting initial pose from spawn location...')
    navigator.info(f'  Pose: x={SPAWN_POSE[0]}, y={SPAWN_POSE[1]}, '
                   f'heading={SPAWN_HEADING.name}')
    navigator.info('══════════════════════════════════════════════')

    initial_pose = navigator.getPoseStamped(SPAWN_POSE, SPAWN_HEADING)
    navigator.setInitialPose(initial_pose)

    # ===================================================================
    # STEP 3: Wait for Nav2 (AMCL + localization) to be fully active
    # ===================================================================
    navigator.info('[Phase 3] Waiting for Nav2 stack (AMCL, planner, controller)...')
    navigator.waitUntilNav2Active()
    navigator.info('══════════════════════════════════════════════')
    navigator.info('Nav2 is ACTIVE — Robot is localized and ready!')
    navigator.info('══════════════════════════════════════════════')

    # ===================================================================
    # OLD undock (commented out — no dock in this simulation):
    #   navigator.undock()
    # ===================================================================

    # ===================================================================
    # STEP 4: Interactive waypoint delivery (PRESERVED — no changes)
    # ===================================================================

    # Prepare goal pose options
    goal_options = [
        {'name': 'Home',
         'pose': navigator.getPoseStamped([-1.0, 1.0], TurtleBot4Directions.EAST)},

        {'name': 'Position 1',
         'pose': navigator.getPoseStamped([10.0, 6.0], TurtleBot4Directions.EAST)},

        {'name': 'Position 2',
         'pose': navigator.getPoseStamped([-9.0, 9.0], TurtleBot4Directions.NORTH)},

        {'name': 'Position 3',
         'pose': navigator.getPoseStamped([-12.0, 2.0], TurtleBot4Directions.NORTH_WEST)},

        {'name': 'Position 4',
         'pose': navigator.getPoseStamped([3.0, -7.0], TurtleBot4Directions.WEST)},

        {'name': 'Exit',
         'pose': None}
    ]

    navigator.info('Welcome to the mail delivery service.')

    while True:
        # Create a list of the goals for display
        options_str = 'Please enter the number corresponding to the desired robot goal position:\n'
        for i in range(len(goal_options)):
            options_str += f'    {i}. {goal_options[i]["name"]}\n'

        # Prompt the user for the goal location
        raw_input = input(f'{options_str}Selection: ')

        selected_index = 0

        # Verify that the value input is a number
        try:
            selected_index = int(raw_input)
        except ValueError:
            navigator.error(f'Invalid goal selection: {raw_input}')
            continue

        # Verify that the user input is within a valid range
        if (selected_index < 0) or (selected_index >= len(goal_options)):
            navigator.error(f'Goal selection out of bounds: {selected_index}')

        # Check for exit
        elif goal_options[selected_index]['name'] == 'Exit':
            break

        else:
            # Navigate to requested position
            navigator.startToPose(goal_options[selected_index]['pose'])

    rclpy.shutdown()


if __name__ == '__main__':
    main()
