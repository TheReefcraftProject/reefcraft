import taichi as ti

@ti.data_oriented
class LlabresSurface:
    def __init__(self, grid_size: int) -> None:
        self.grid_size = grid_size
        self.pos = ti.Vector.field(3, dtype = ti.f32, shape = (grid_size, grid_size)) #3D coords of each point
        self.norms = ti.Vector.field(3, dtype = ti.f32, shape = (grid_size, grid_size)) #surface norms
        self.dspl = ti.field(dtype = ti.f32, shape = (grid_size, grid_size)) #accumulates total displacement of pt

    @ti.kernel
    def init_flat(self) -> None:
        for i, j in self.pos:
            self.pos[i, j] = ti.Vector([ #init flat surface with origin @ center
                (i - self.grid_size / 2) * 0.05,
                (j - self.grid_size / 2) * 0.05,
                0.0
            ])
            self.norms[i, j] = ti.Vector([0.0, 0.0, 1.0])   #normals point up
            self.dspl[i, j] = 0.0

    @ti.kernel
    def grow(self, threshold: float, amount: float) -> None: #grow a frame
        for i, j in self.pos:
            n = self.norms[i, j]
            nx, ny, nz = n[0], n[1], n[2]  # Explicit unpacking, taichi didn't like n.x**2
            sigma = nz/ti.sqrt(nx**2 + ny**2 + 1e-6)

            if sigma >= threshold:
                self.pos[i,j] += amount * n.normalized() #move pt along norm
                self.dspl[i, j] += amount
            else:
                self.dspl[i, j] += 0.0

    def step(self, threshold: float, amount: float) -> None: #next frame
        self.grow(threshold, amount) #currently only grow() but allows flexibility

    def reset(self) -> None: #reset surface
        self.init_flat()  #currently only init_flat() but allows flexibility