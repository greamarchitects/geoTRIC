# pattern.py
# Rules that mutate a matrix's cell states in place - move/scale/rotate/
# randomize - iterating the dictionary and branching conditionally on grid
# position or distance to a field point.
#
# Rules only ever touch the numeric state in each cell dict (offset,
# rotation, scale) - never geometry or Rhino - so they can be written and
# checked with plain Python, independent of rhino_backend.py.

import math
from typing import Callable, Optional

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
