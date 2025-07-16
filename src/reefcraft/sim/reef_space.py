# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from reefcraft.sim.compute_lbm import ComputeLBM

"""
ReefSpace holds the space (i.e. tank) and coral that is acted upon by meshes and water physics (ComputeLBM)
"""

class ReefSpace:
    def __init__(self) -> None:
        # Simulation parameters
        self.grid_shape = (32, 32, 32)  # Grid size
        self.num_steps = 1000              # Total number of simulation steps
        self.current_step = 0
        self.water_speed = 0.02           # Fluid speed (m/s)
        stl_filename = 'coral.stl'  # Path to the coral mesh (for boundary conditions)
        post_process_interval = 100  # Interval for post-processing (e.g., saving VTK or images)

        # Create an instance of LatticeBoltzmannMethod
        self.sim = ComputeLBM(
            grid_shape=self.grid_shape,
            num_steps=self.num_steps,
            fluid_speed=self.water_speed,
            stl_filename=stl_filename,
            post_process_interval=post_process_interval
        )

    def step(self) -> None:
        """Execute simulation step"""
        self.sim.run_step(self.current_step)
        self.current_step+=1

    def get_fields_numpy(self) -> dict:
        """Returns dictionary of fields (includes coral as field)"""
        return self.sim.get_field_numpy()