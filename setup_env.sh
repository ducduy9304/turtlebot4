#!/bin/bash

# --- CONFIGURATION ---
# Get the absolute path of the current directory
WS_PATH=$(pwd)
# Set your venv folder name here (change if needed)
VENV_NAME=".venv" 

echo "-------------------------------------------------------"
echo "Initializing Turtlebot4 ROS2 Humble Workspace..."
echo "-------------------------------------------------------"

# 1. Source Global ROS2 Humble
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    echo "[1/4] Success: Global ROS2 Humble sourced."
else
    echo "[!] Error: ROS2 Humble not found at /opt/ros/humble/"
    return
fi

# 2. Activate Python Virtual Environment
if [ -d "$WS_PATH/$VENV_NAME" ]; then
    source "$WS_PATH/$VENV_NAME/bin/activate"
    echo "[2/4] Success: Virtual environment '$VENV_NAME' activated."
else
    echo "[!] Warning: '$VENV_NAME' not found. Creating a new one with system-site-packages..."
    python3 -m venv --system-site-packages "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
fi

# 3. Build the Workspace (Optional: Comment out to skip auto-build)
if [ -d "$WS_PATH/src" ]; then
    echo "[3/4] Status: Running colcon build... (this may take a moment)"
    colcon build --symlink-install
else
    echo "[!] Warning: 'src' directory not found. Skipping build."
fi

# 4. Source Workspace Overlay
if [ -f "$WS_PATH/install/setup.bash" ]; then
    source "$WS_PATH/install/setup.bash"
    echo "[4/4] Success: Workspace overlay sourced."
else
    echo "[!] Warning: 'install/setup.bash' not found. Please check build logs."
fi

echo "-------------------------------------------------------"
echo "Setup Complete!"
echo "-------------------------------------------------------"
