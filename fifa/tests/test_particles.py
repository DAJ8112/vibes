import random

from fifatui.art.canvas import CharGrid
from fifatui.art.particles import GRAVITY, Fireworks


def make(seed=42, w=40, h=20):
    return Fireworks(w, h, colors=["#ff0000", "#00ff00"], rng=random.Random(seed))


def test_spawn_burst_creates_n_particles_deterministically():
    a, b = make(), make()
    a.spawn_burst(20, 10, n=12)
    b.spawn_burst(20, 10, n=12)
    assert len(a.particles) == 12
    assert [(p.x, p.y, p.vx, p.vy, p.color) for p in a.particles] == [
        (p.x, p.y, p.vx, p.vy, p.color) for p in b.particles
    ]


def test_step_applies_velocity_and_gravity():
    fw = make()
    fw.spawn_burst(20, 10, n=4)
    p = fw.particles[0]
    x0, y0, vy0 = p.x, p.y, p.vy
    fw.step(0.1)
    assert p.x == x0 + p.vx * 0.1
    assert p.y == y0 + vy0 * 0.1
    assert p.vy == vy0 + GRAVITY * 0.1


def test_particles_die_after_lifetime():
    fw = make()
    fw.spawn_burst(20, 10, n=10)
    for _ in range(40):  # 4 seconds >> max lifetime 1.6s
        fw.step(0.1)
    assert not fw.alive


def test_paint_stays_in_bounds():
    fw = make(w=10, h=6)
    fw.spawn_burst(5, 3, n=30, speed=(50.0, 80.0))  # deliberately fast
    grid = CharGrid(10, 6)
    for _ in range(5):
        fw.step(0.07)
        fw.paint(grid)  # bounds-checked put: must not raise
    assert grid.width == 10 and grid.height == 6


def test_chargrid_stamp_and_render():
    grid = CharGrid(10, 3)
    grid.stamp_text(2, 1, "HI", "bold red")
    group = grid.to_group()
    assert len(group.renderables) == 3
    assert group.renderables[1].plain == "  HI      "
