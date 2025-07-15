from app.sim.water import LBM
import taichi as ti
import numpy as np

def test_lbm_init():
    grid_size = 32
    tau = 1
    lbm = LBM(grid_size=grid_size, tau=tau)

    # Check if the object's attributes are initialized correctly
    assert lbm.n == grid_size, f"Expected grid size {grid_size}, but got {lbm.n}"
    assert lbm.tau == tau, f"Expected tau {tau}, but got {lbm.tau}"

    # Check that the velocity field (u) has the correct shape (3D)
    assert lbm.u.shape == (grid_size, grid_size, grid_size, 3), \
        f"Expected shape {(grid_size, grid_size, grid_size, 3)} for velocity field, but got {lbm.u.shape}"
    
    # Check that the density field (rho) has the correct shape (3D)
    assert lbm.rho.shape == (grid_size, grid_size, grid_size), \
        f"Expected shape {(grid_size, grid_size, grid_size)} for density field, but got {lbm.rho.shape}"

    print("test_lbm_init passed.")

def test_equilibrium():
    grid_size = 4  # Small grid for testing
    tau = 1.0  # Relaxation time
    
    # Create LBM object
    lbm = LBM(grid_size, tau)
    
    # Set some simple test values for density and velocity
    lbm.rho.fill(1.0)  # Set uniform density
    lbm.u.fill(ti.Vector([1.0, 0.0, 0.0]))  # Set uniform velocity in the x-direction
    
    # Call the compute_feq method
    lbm.compute_feq()

    # Check the equilibrium distribution at (0, 0, 0)
    feq_at_0 = lbm.feq[0, 0, 0].to_numpy()

    # Expected equilibrium distribution values
    expected_feq = np.zeros(19)
    rho = 1.0
    cu = np.array([1.0, 0.0, 0.0])  # u = (1, 0, 0)
    
    # Calculate the expected equilibrium distribution for each direction
    for l in range(19):
        vx, vy, vz = lbm.velocities[l].to_numpy()
        cu_dot = np.dot(cu, [vx, vy, vz])
        expected_feq[l] = (1 / 3) * rho * (1 + 3 * cu_dot + 9 * cu_dot**2 / 2 - np.linalg.norm(cu)**2 / 2)

    # Check if computed equilibrium distribution matches expected values
    for i in range(19):
        assert np.isclose(feq_at_0[i], expected_feq[i]), f"Test failed for direction {i}: {feq_at_0[i]} != {expected_feq[i]}"

    print("Equilibrium function test passed.")

if __name__ == "__main__":
    test_lbm_init()
    test_equilibrium()