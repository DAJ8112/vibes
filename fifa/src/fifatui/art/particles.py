"""Firework particles for the goal celebration.

Simple physics: each particle gets a velocity on a jittered ring, falls under
gravity, and fades from a bright spark to a dim ember over its lifetime. All
randomness comes from an injectable ``random.Random`` so tests are deterministic.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from . import theme
from .canvas import CharGrid

GRAVITY = 5.0            # rows / s²
ASPECT = 0.5             # terminal cells are ~2× taller than wide
CHAR_RAMP = "✶*▪·"       # bright → dim as a particle ages
CHAR_RAMP_ASCII = "*+.·" # swap-in if ✶/▪ misrender in a terminal font


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: str
    lifetime: float
    age: float = 0.0


class Fireworks:
    def __init__(
        self,
        width: int,
        height: int,
        colors: list[str],
        rng: random.Random | None = None,
    ):
        self.width = width
        self.height = height
        self.colors = colors
        self.rng = rng or random.Random()
        self.particles: list[Particle] = []

    def spawn_burst(
        self,
        x: float,
        y: float,
        n: int = 26,
        speed: tuple[float, float] = (6.0, 14.0),
    ) -> None:
        for i in range(n):
            angle = 2 * math.pi * i / n + self.rng.uniform(-0.15, 0.15)
            v = self.rng.uniform(*speed)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * v,
                    vy=math.sin(angle) * v * ASPECT,
                    color=self.rng.choice(self.colors),
                    lifetime=self.rng.uniform(0.9, 1.6),
                )
            )

    def step(self, dt: float) -> None:
        for p in self.particles:
            p.age += dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += GRAVITY * dt
        self.particles = [
            p for p in self.particles if p.age < p.lifetime and p.y < self.height + 1
        ]

    @property
    def alive(self) -> bool:
        return bool(self.particles)

    def paint(self, grid: CharGrid) -> None:
        for p in self.particles:
            t = p.age / p.lifetime
            char = CHAR_RAMP[min(len(CHAR_RAMP) - 1, int(t * len(CHAR_RAMP)))]
            grid.put(round(p.x), round(p.y), char, theme.fade(p.color, t * 0.85))
