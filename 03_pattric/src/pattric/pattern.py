# pattern.py
# Rules that mutate a matrix's cell states in place - move/scale/rotate/
# randomize - iterating the dictionary and branching conditionally on grid
# position or distance to a field point.
#
# Rules only ever touch the numeric state in each cell dict (offset,
# rotation, scale) - never geometry or Rhino - so they can be written and
# checked with plain Python, independent of rhino_backend.py.

import math
from typing import Callable, Optional, Sequence

from .matrix import Matrix, CellKey, Cell, center_key

Rule = Callable[[Matrix, CellKey, Cell], None]


def apply_rule(matrix: Matrix, rule: Rule) -> Matrix:
    """Apply `rule` to every cell, in (col, row) sorted order for determinism."""
    for key in sorted(matrix.keys()):
        rule(matrix, key, matrix[key])
    return matrix


def _hash01(*parts) -> float:
    """Same idea as matrix._cell_seed, but for a second independent random
    axis (e.g. y-jitter) without needing extra fields on the cell dict."""
    h = hash(parts)
    return (h & 0xFFFFFFFF) / 0xFFFFFFFF


def checker_spin_rule(rot_step: float = 20.0, scale_step: float = 0.35, jitter: float = 1.5) -> Rule:
    """
    v0.1 default rule - conditional + iteration + randomization in one pass:
      - rotation alternates direction in a checkerboard (col+row parity)
      - scale is seeded per cell (deterministic "randomization")
      - origin gets a small seeded (x, y) jitter via `offset` ("moving")
    """
    def rule(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        col, row = key
        direction = 1 if (col + row) % 2 == 0 else -1
        cell["rotation"] = direction * rot_step
        cell["scale"] = 1.0 + (cell["seed"] - 0.5) * 2 * scale_step
        jx = (_hash01(col, row, "jx") - 0.5) * 2 * jitter
        jy = (_hash01(col, row, "jy") - 0.5) * 2 * jitter
        cell["offset"] = (jx, jy)
    return rule


def radial_grow_rule(center: Optional[CellKey] = None, max_scale: float = 1.8,
                      min_scale: float = 0.5, falloff_cells: float = 4.0) -> Rule:
    """
    Attractor-style rule - same falloff shape as skeletric's
    attractor_radius (smoothstep, not linear), reused here against grid
    distance instead of world distance: cells near `center` (defaults to
    the matrix's own center) scale up toward max_scale and ease back down
    to min_scale by falloff_cells away. A v0.2-style option to swap in
    once a single conditional rule (checker_spin_rule) has been reviewed.
    """
    def rule(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        c = center if center is not None else center_key(matrix)
        d = math.dist(key, c)
        t = min(max(d / falloff_cells, 0.0), 1.0)
        ease = t * t * (3.0 - 2.0 * t)  # 0 at center, 1 at/after falloff_cells
        cell["scale"] = max_scale + (min_scale - max_scale) * ease
        cell["rotation"] = (1.0 - ease) * 45.0
    return rule


def three_point_attractor_rule(attractors: Sequence[CellKey], max_scale: float = 1.5,
                                min_scale: float = 0.7, falloff_cells: float = 3.0,
                                pull: float = 3.0) -> Rule:
    """
    Field driven by three attractor points (grid-space cell keys) at once,
    rather than radial_grow_rule's single center: every cell blends the
    pull of all three, closer attractors contributing more via the same
    smoothstep falloff, so scale grows, rotation turns to face the combined
    pull direction, and offset nudges toward it - one continuous field
    shaped by three points instead of three separate regions.

    `pull` is a world-unit offset distance (same units as `offset`); pair
    this rule with constrain_to_cell_rule so scale/offset never push a
    cell's drawn square outside its own grid footprint.
    """
    def influence(d: float) -> float:
        t = min(max(d / falloff_cells, 0.0), 1.0)
        ease = t * t * (3.0 - 2.0 * t)
        return 1.0 - ease  # 1 at the attractor, 0 at/after falloff_cells

    def rule(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        col, row = key
        vx = vy = 0.0
        total = 0.0
        for ax, ay in attractors:
            d = math.dist(key, (ax, ay))
            w = influence(d)
            total += w
            if d > 1e-9:
                vx += w * (ax - col) / d
                vy += w * (ay - row) / d
        combined = min(total, 1.0)
        cell["scale"] = min_scale + (max_scale - min_scale) * combined

        mag = math.hypot(vx, vy)
        if mag > 1e-9:
            ux, uy = vx / mag, vy / mag
            cell["rotation"] = math.degrees(math.atan2(uy, ux))
            cell["offset"] = (ux * pull * combined, uy * pull * combined)
        else:
            cell["rotation"] = 0.0
            cell["offset"] = (0.0, 0.0)
    return rule


def constrain_to_cell_rule(rule: Rule, cell_size: float, margin: float = 0.98) -> Rule:
    """
    Wraps another rule so a cell's drawn square - after that rule sets its
    scale/rotation/offset - never exceeds the cell's own *base rectangle*:
    the cell_size x cell_size square it would draw at scale=1, rotation=0,
    offset=(0, 0). That's the cell's own footprint as actually drawn, not
    the (usually larger) grid spacing between neighboring origins - using
    spacing here would let a scaled-up cell balloon past its own drawn
    square while still technically not touching a neighbor's origin.

    Both the drawn square (rotated by `cell['rotation']`) and the base
    rectangle are squares, so the correct per-axis reach of a half-side `h`
    square rotated by angle theta is h * (|cos theta| + |sin theta|) - 1x at
    0/90 degrees, up to sqrt(2)x at 45 degrees - not the (larger, overly
    conservative) circumradius. `margin` leaves a small safety buffer short
    of the true half-cell_size limit.
    """
    half_limit = (cell_size / 2.0) * margin

    def wrapped(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        rule(matrix, key, cell)

        rad = math.radians(cell.get("rotation", 0.0))
        reach_factor = abs(math.cos(rad)) + abs(math.sin(rad))  # 1..sqrt(2)

        scale = cell.get("scale", 1.0)
        half_side = cell_size * scale / 2.0
        reach = half_side * reach_factor
        if reach > half_limit:
            half_side = half_limit / reach_factor
            cell["scale"] = (half_side * 2.0) / cell_size
            reach = half_limit

        remaining = max(half_limit - reach, 0.0)
        ox, oy = cell.get("offset", (0.0, 0.0))
        cell["offset"] = (max(-remaining, min(remaining, ox)),
                           max(-remaining, min(remaining, oy)))
    return wrapped
