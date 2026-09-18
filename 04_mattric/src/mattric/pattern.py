# pattern.py
# Rules that mutate a mattric matrix's cell offsets in place - the same
# apply_rule/rule shape as pattric's pattern.py, but displacing a 3D
# point's depth (y) instead of a 2D cell's scale/rotation/position.
#
# Rules only ever touch the numeric state in each cell dict (offset) -
# never geometry or Rhino - so they can be written and checked with plain
# Python, independent of rhino_backend.py.

import math
from typing import Callable, Optional, Sequence

from .matrix import Matrix, CellKey, Cell, center_key

Rule = Callable[[Matrix, CellKey, Cell], None]


def apply_rule(matrix: Matrix, rule: Rule) -> Matrix:
    """Apply `rule` to every cell, in (col, row) sorted order for determinism."""
    for key in sorted(matrix.keys()):
        rule(matrix, key, matrix[key])
    return matrix


def _falloff(d: float, falloff_cells: float) -> float:
    """Smoothstep falloff shared by every rule below - 1 at d=0, 0 at/after
    falloff_cells, same shape as skeletric's attractor_radius and
    pattric's radial_grow_rule."""
    t = min(max(d / falloff_cells, 0.0), 1.0)
    ease = t * t * (3.0 - 2.0 * t)
    return 1.0 - ease


def radial_bulge_rule(center: Optional[CellKey] = None, max_bulge: float = 5.0,
                       falloff_cells: float = 4.0) -> Rule:
    """
    Single-attractor variant: cells near `center` (defaults to the matrix's
    own center) push outward along y (the wall's depth direction) up to
    `max_bulge`, easing back to 0 by falloff_cells away - a flat wall of
    points bulging into a dome around one point.
    """
    def rule(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        c = center if center is not None else center_key(matrix)
        d = math.dist(key, c)
        bulge = _falloff(d, falloff_cells) * max_bulge
        cell["offset"] = (0.0, bulge, 0.0)
    return rule


def three_point_bulge_rule(attractors: Sequence[CellKey], max_bulge: float = 5.0,
                            falloff_cells: float = 3.0) -> Rule:
    """
    Field driven by three attractor points at once (grid-space cell keys),
    same blending idea as pattric's three_point_attractor_rule: every
    cell's bulge is the combined (capped at 1) influence of all three,
    closer attractors contributing more - one continuous undulating
    surface instead of three separate domes.
    """
    def rule(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        total = 0.0
        for a in attractors:
            d = math.dist(key, a)
            total += _falloff(d, falloff_cells)
        bulge = min(total, 1.0) * max_bulge
        cell["offset"] = (0.0, bulge, 0.0)
    return rule


def constrain_bulge_rule(rule: Rule, max_bulge: float) -> Rule:
    """
    Wraps another rule so a cell's y-offset (bulge) never exceeds
    `max_bulge` in either direction, regardless of what the wrapped rule
    computes - same "guarantee it, don't just hope for it" shape as
    pattric's constrain_to_cell_rule.
    """
    def wrapped(matrix: Matrix, key: CellKey, cell: Cell) -> None:
        rule(matrix, key, cell)
        dx, dy, dz = cell.get("offset", (0.0, 0.0, 0.0))
        cell["offset"] = (dx, max(-max_bulge, min(max_bulge, dy)), dz)
    return wrapped
