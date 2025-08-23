# school.py
# -----------------------------------------------------------------------------
#  
# -----------------------------------------------------------------------------
"""School of fish that face into the current and drift in place."""
from __future__ import annotations

import numpy as np
import pygfx as gfx
import warp as wp

from reefcraft.render.fish_shader import FishPointsMaterial  # custom Points material that loads fish.wgsl


class FishSchool:
    """Self-contained fish school actor."""

    def __init__(self, num_fish: int = 100, grid_shape: tuple[int, int, int] = (100, 100, 100)) -> None:
        """Initialize school of fish."""
        # --- configuration (tweak freely) -------------------------------------
        self.num_fish = num_fish
        self.grid_shape = np.array(grid_shape, dtype=np.float32)
        self.turn_rate = 6.0           # how quickly yaw turns toward upstream (rad/s)
        self.spring_k = 2.0          # how strongly we pull back toward "home" (1/s)
        self.drift_amp = 10.0           # forward/back amplitude (world units)
        self.drift_hz = 0.05           # oscillation frequency (cycles/s)
        self.wrap_margin = 1.0         # keep them just inside the box when wrapping
        self.paused = False
        self.forward_ratio = 0.001      # 0<r<1  (portion of cycle spent lunging forward)
        self.spread_frac = 0.35        # 0..0.5  (spawn half-width as fraction of W/Z)
        
        # --- initial placement -------------------------------------------------
        # world-space AABB is x in [-W/2, W/2], y in [0, H], z in [-D/2, D/2]
        W, H, D = self.grid_shape
        rng = np.random.default_rng(41)
        # scatter the school roughly in the middle-upper area
        sx = float(self.spread_frac) * float(W)
        sz = float(self.spread_frac) * float(D)

        init_pos = np.stack(
            [
                rng.uniform(-sx, sx, size=num_fish),
                rng.uniform(0.35 * H, 0.75 * H, size=num_fish),   # keep Y band for now
                rng.uniform(-sz, sz, size=num_fish),
            ],
            axis=1,
        ).astype(np.float32)

        # each fish has a "home" anchor near its spawn; keep them close to it
        home_pos = init_pos.copy().astype(np.float32)

        # initial yaw (radians) — point along +Z for now
        yaw0 = np.zeros((num_fish, 1), dtype=np.float32)

        # a deterministic per-fish phase so they don't all breathe in sync
        # phase = rng.uniform(0.0, 2.0 * np.pi, size=(num_fish, 1)).astype(np.float32)
        #sync phases so all fish "breathe" together
        phase = np.zeros((num_fish, 1), dtype=np.float32)

        # --- GPU buffers (Warp) -----------------------------------------------
        self.pos_wp = wp.array(init_pos, dtype=wp.vec3)
        self.home_wp = wp.array(home_pos, dtype=wp.vec3)
        self.yaw_wp = wp.array(yaw0.reshape(-1), dtype=float)     # 1 float per fish
        self.phase_wp = wp.array(phase.reshape(-1), dtype=float)

        # --- gfx geometry ------------------------------------------------------
        # positions -> gfx buffer; rotations -> per-vertex yaw (1 float)
        self.positions_buf = gfx.Buffer(init_pos)
        self.rotations_buf = gfx.Buffer(yaw0)  # Nx1 float32; shader reads yaw per fish

        self.geometry = gfx.Geometry(positions=self.positions_buf, rotations=self.rotations_buf)

        # --- per-fish colors ---------------------------------------------------
        palette = np.array([(0.17, 0.31, 0.35, 1.0),  
                            (0.76, 0.83, 0.74, 1.0), 
                            (0.11, 0.16, 0.23, 1.0), 
                            ],
                            dtype=np.float32,)
        color_idx = rng.integers(0, len(palette), size=num_fish)
        colors = palette[color_idx]
        self.colors_buf = gfx.Buffer(colors.astype(np.float32))
        
        self.geometry = gfx.Geometry(
            positions=self.positions_buf,
            rotations=self.rotations_buf,
            colors=self.colors_buf,
            )

        # Important: tell our custom shader to read rotations from the geometry
        self.material = FishPointsMaterial(
            color="#2C4F59",
            color_mode="vertex",
            size=60,
            rotation_mode="vertex",  # <-- enables binding s_rotations in FishPointsShader
            aa=True,
        )
        self.points = gfx.Points(self.geometry, self.material)

    def get_actor(self) -> gfx.Points:
        """The single actor you add to the scene."""
        return self.points

    def reset(self) -> None:
        """Reseed fish around the same region; keeps 'home' aligned with new positions."""
        W, H, D = self.grid_shape
        rng = np.random.default_rng(123)
        sx = float(self.spread_frac) * float(W)
        sz = float(self.spread_frac) * float(D)

        new_pos = np.stack(
            [
                rng.uniform(-sx, sx, size=self.num_fish),
                rng.uniform(0.35 * H, 0.75 * H, size=self.num_fish),
                rng.uniform(-sz, sz, size=self.num_fish),
            ],
            axis=1,
        ).astype(np.float32)
        self.pos_wp = wp.array(new_pos, dtype=wp.vec3)
        self.home_wp = wp.array(new_pos.copy(), dtype=wp.vec3)
        self.yaw_wp = wp.array(np.zeros((self.num_fish,), dtype=np.float32), dtype=float)

        self.positions_buf.set_data(new_pos)
        self.rotations_buf.set_data(np.zeros((self.num_fish, 1), dtype=np.float32))

    def step(self, velocity_field: np.ndarray, t: float, dt: float) -> None:
        """One call per frame.

        - sample flow at each fish
        - yaw turns upstream
        - small forward/back drift around home
        - wrap inside domain
        - sync GPU->CPU for gfx
        """
        if self.paused:
            return
        
        flat_vel = velocity_field.reshape(-1, 3).astype(np.float32)
        vel_wp = wp.array(flat_vel, dtype=wp.vec3)

        wp.launch(
            kernel=fish_school_step,
            dim=self.num_fish,
            inputs=[
                self.pos_wp,
                self.home_wp,
                self.yaw_wp,
                self.phase_wp,
                vel_wp,
                wp.vec3(*self.grid_shape),
                float(self.turn_rate),
                float(self.spring_k),
                float(self.drift_amp),
                float(self.drift_hz),
                float(self.wrap_margin),
                float(self.forward_ratio),
                float(t),
                float(dt),
            ],
        )

        # sync back to CPU for rendering (positions and per-fish yaw buffer)
        new_pos = self.pos_wp.numpy()
        new_yaw = self.yaw_wp.numpy().reshape(-1, 1).astype(np.float32)
        self.positions_buf.set_data(new_pos)
        self.rotations_buf.set_data(new_yaw)

    def pause(self) -> None:
        """Pause school movement."""
        self.paused = True

    def resume(self) -> None:
        """Resume school movement."""
        self.paused = False


@wp.func
def _fast_atan2(y: float, x: float) -> float:
    # fast atan2 approximation is fine for turning
    # (or use wp.atan2 when available)
    return wp.atan2(y, x)


@wp.func
def _angle_diff(a: float, b: float) -> float:
    # signed shortest difference a->b
    d = (b - a + wp.pi) % (2.0 * wp.pi) - wp.pi
    return d


@wp.func
def _lerp_angle(curr: float, target: float, max_delta: float) -> float:
    # clamp angular step by max_delta (per step)
    d = _angle_diff(curr, target)
    if d > max_delta:
        d = max_delta
    elif d < -max_delta:
        d = -max_delta
    return curr + d


@wp.kernel
def fish_school_step(
    pos: wp.array(dtype=wp.vec3),
    home: wp.array(dtype=wp.vec3),
    yaw: wp.array(dtype=float),
    phase: wp.array(dtype=float),
    vel_field: wp.array(dtype=wp.vec3),
    grid_shape: wp.vec3,
    turn_rate: float,
    spring_k: float,
    drift_amp: float,
    drift_hz: float,
    wrap_margin: float,
    forward_ratio: float,
    t: float,
    dt: float,
) -> None:
    """Step the fish school."""
    tid = wp.tid()

    P = pos[tid]
    H = home[tid]
    Y = yaw[tid]

    # --- sample flow at this fish (nearest) -----------------------------------
    half_x = grid_shape[0] * 0.5
    half_z = grid_shape[2] * 0.5
    gx = wp.clamp(wp.int(wp.round(P[0] + half_x)), 1, int(grid_shape[0]) - 2)
    gy = wp.clamp(wp.int(wp.round(P[1])), 1, int(grid_shape[1]) - 2)
    gz = wp.clamp(wp.int(wp.round(P[2] + half_z)), 1, int(grid_shape[2]) - 2)
    idx = (gx * int(grid_shape[1]) + gy) * int(grid_shape[2]) + gz
    V = vel_field[idx]

    # --- face into the current (XZ-plane) -------------------------------------
    # upstream = -normalize([V.x, V.z])
    vxz_len = wp.sqrt(V[0] * V[0] + V[2] * V[2]) + 1e-6
    fwd_x = -V[0] / vxz_len
    fwd_z = -V[2] / vxz_len
    target_yaw = _fast_atan2(fwd_x, fwd_z)  # yaw so +Z local points along (fwd_x, fwd_z)

    # step toward target yaw with limited turn rate (rad/s)
    Y = _lerp_angle(Y, target_yaw, turn_rate * dt)

    # --- asymmetric drift: quick forward lunge, slower back glide ------------
    # all in sync (ignores per-fish phase to keep the group together)
    s = drift_hz * t
    s = s - wp.floor(s)                       # fract in [0,1)
    A = drift_amp
    beta = wp.clamp(forward_ratio, 0.05, 0.95)
    drift = -A + 2.0 * A * (s / beta) if s < beta else A - 2.0 * A * ((s - beta) / (1.0 - beta))
    goal = H + wp.vec3(drift * fwd_x, 0.0, drift * fwd_z)

    # critically-damped-ish spring toward 'goal'
    P += (goal - P) * (spring_k * dt)

    # --- keep inside the domain with wrap -------------------------------------
    if P[0] < -half_x:
        P[0] = half_x - wrap_margin
    elif P[0] > half_x:
        P[0] = -half_x + wrap_margin

    if P[1] < 0.0:
        P[1] = 0.5
    elif P[1] > grid_shape[1]:
        P[1] = grid_shape[1] - 0.5

    if P[2] < -half_z:
        P[2] = half_z - wrap_margin
    elif P[2] > half_z:
        P[2] = -half_z + wrap_margin

    # write back
    pos[tid] = P
    yaw[tid] = Y
