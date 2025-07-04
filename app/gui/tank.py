# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
#

import taichi as ti

# Initialize Taichi environment
ti.init(arch=ti.gpu)

# 8 vertices of the tank
vertices = ti.Vector.field(3, dtype=ti.f32, shape=8)
vertices[0] = ti.Vector([0.0, 0.0, 0.0])
vertices[1] = ti.Vector([1.0, 0.0, 0.0])  # x = 1 meter
vertices[2] = ti.Vector([1.0, 1.0, 0.0])  # y = 1 meter
vertices[3] = ti.Vector([0.0, 1.0, 0.0])  # z = 0 meter
vertices[4] = ti.Vector([0.0, 0.0, 1.0])  # z = 1 meter
vertices[5] = ti.Vector([1.0, 0.0, 1.0])  # x = 1 meter, z = 1 meter
vertices[6] = ti.Vector([1.0, 1.0, 1.0])  # x = 1 meter, y = 1 meter, z = 1 meter
vertices[7] = ti.Vector([0.0, 1.0, 1.0])  # y = 1 meter, z = 1 meter

# Define the indices for the lines (each pair represents a line between two vertices)
indices = ti.field(int, shape=(24,))  

# Bottom face
indices[0], indices[1] = 0, 1  # Line 0: 0 -> 1
indices[2], indices[3] = 1, 2  # Line 1: 1 -> 2
indices[4], indices[5] = 2, 3  # Line 2: 2 -> 3
indices[6], indices[7] = 3, 0  # Line 3: 3 -> 0

# Top face
indices[8], indices[9] = 4, 5  # Line 4: 4 -> 5
indices[10], indices[11] = 5, 6  # Line 5: 5 -> 6
indices[12], indices[13] = 6, 7  # Line 6: 6 -> 7
indices[14], indices[15] = 7, 4  # Line 7: 7 -> 4

# Vertical edges
indices[16], indices[17] = 0, 4  # Line 8: 0 -> 4
indices[18], indices[19] = 1, 5  # Line 9: 1 -> 5
indices[20], indices[21] = 2, 6  # Line 10: 2 -> 6
indices[22], indices[23] = 3, 7  # Line 11: 3 -> 7

# Create a window and canvas
window = ti.ui.Window("Tank", res=(800, 800))
canvas = window.get_canvas()

# Create a scene and set up the camera
scene = window.get_scene()
camera = ti.ui.Camera()

# Set the initial camera position, look-at point, and up direction
camera.position(1, 2, 3)
camera.lookat(0.5, 0.5, 0.5)
camera.up(0, 1, 0)

# Lighting
scene.ambient_light((0.6, 0.6, 0.6))
scene.point_light(pos=(3, 3, 3), color=(1, 1, 1))

# Variables to track rotation angles
rotation_angle_z = 0.0  # Z-axis rotation

# Main loop
while window.running:
    # Check for 'a'&'d' key presses to rotate left around the Z-axis
    if window.is_pressed("a"):  # Clockwise 
        rotation_angle_z -= 0.01  # Rotate counterclockwise around Z-axis (left arrow)

    if window.is_pressed("d"):  # Right Arrow Key (as a string)
        rotation_angle_z += 0.01  # Rotate clockwise around Z-axis (right arrow)

    # Apply the rotation to the camera position, keeping the camera at a fixed radius (3 meters)
    radius = 3  # Fixed radius from the origin
    camera.position(radius * ti.cos(rotation_angle_z), radius * ti.sin(rotation_angle_z), radius)

    # Update the look-at point and up vector
    camera.lookat(0.5, 0.5, 0.5)
    camera.up(0, 1, 0)

    # Set the camera for this frame
    scene.set_camera(camera)

    # Draw the 3D box (tank) using lines
    scene.lines(vertices, indices=indices, color=(1.0, 0.0, 0.0), width=2.0)

    # Show the scene
    canvas.scene(scene)
    window.show()
