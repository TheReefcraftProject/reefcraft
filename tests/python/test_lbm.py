from app.sim.water import LBM

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

if __name__ == "__main__":
    test_lbm_init()
