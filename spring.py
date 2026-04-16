"""
Spring physics engine.

Implements damped spring dynamics for Apple-style animations.
Each SpringValue tracks position, velocity, and a target.
Calling update(dt) moves the value one timestep forward.

Usage:
    s = SpringValue(0, stiffness=280, damping=26)
    s.target = 300
    while not s.settled:
        s.update(0.016)
        apply(s.pos)
"""


class SpringValue:
    """
    Single 1-D spring-damper.

    stiffness : controls how fast it moves toward target (higher = faster)
    damping   : controls overshoot (lower = more bounce, higher = overdamped)

    Apple-feel  → stiffness ≈ 260–320, damping ≈ 24–30  (slight bounce)
    Snappy      → stiffness ≈ 400–500, damping ≈ 38–45  (no bounce)
    """

    SETTLE_POS = 0.4   # px
    SETTLE_VEL = 0.4   # px/s

    def __init__(self, initial: float, stiffness: float = 280, damping: float = 26):
        self.pos:       float = float(initial)
        self.vel:       float = 0.0
        self.target:    float = float(initial)
        self.stiffness: float = stiffness
        self.damping:   float = damping

    # ── Core ──────────────────────────────────────────────────────────────────

    def set_target(self, value: float, instant: bool = False):
        self.target = float(value)
        if instant:
            self.pos = self.target
            self.vel = 0.0

    def update(self, dt: float = 0.016) -> bool:
        """Advance one timestep. Returns True if still animating."""
        if self.settled:
            return False
        spring_f  = -self.stiffness * (self.pos - self.target)
        damping_f = -self.damping   * self.vel
        accel     = spring_f + damping_f
        self.vel += accel * dt
        self.pos += self.vel * dt
        return True

    @property
    def settled(self) -> bool:
        return (
            abs(self.pos - self.target) < self.SETTLE_POS
            and abs(self.vel) < self.SETTLE_VEL
        )

    def snap(self):
        """Immediately jump to target."""
        self.pos = self.target
        self.vel = 0.0

    @property
    def value(self) -> int:
        """Convenience: integer pixel value."""
        return int(round(self.pos))


class SpringGroup:
    """
    Manages multiple SpringValues and provides a single settled check.
    """
    def __init__(self):
        self._springs: list[SpringValue] = []

    def add(self, spring: SpringValue) -> SpringValue:
        self._springs.append(spring)
        return spring

    def update(self, dt: float = 0.016) -> bool:
        return any(s.update(dt) for s in self._springs)

    @property
    def settled(self) -> bool:
        return all(s.settled for s in self._springs)

    def snap_all(self):
        for s in self._springs:
            s.snap()
