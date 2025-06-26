#simulation.py

from reefcraft import seed, sim_value

class SimulationEngine:
    """Starting point for Reefcraft simulation engine"""

    def __init__(self):
        self._time = 0.0            #curr sim time
        self._running = False       #is sim ticking?
        self._timestep = 1/60.0     #~60 FPS
        self._seed = 12345          #fixed seed
        self._last_val = 0.0        #most recent sim_value output

        seed(self._seed)            #initialize rng

    def start(self):
        self._running = True
        print("[Engine] Started")

    def pause(self):
        self._running = False

    def reset(self):
        self._time = 0.0
        seed(self._seed)
        self._last_val = sim_value(self._time)

    def update(self):
        if self._running:
            self._time += self._timestep
            self._last_val = sim_value(self._time)
        #     print(f"[Sim] t={self._time:.2f}, v={self._last_val:.3f}")  # TEMP DEBUG
        # else:
        #     print("[Sim] Not running")

    def get_last_value(self):
        return self._last_val
