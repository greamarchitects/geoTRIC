# wall.py
# The tower's wall, floor by floor: one perforated unit per cell, ported
# from mattric's perforated wall units. Same construction - an outer box, an
# inner box inset inside it, the second cut out of the first to leave a
# frame with an opening, then the frame's far end cut off by the wall
# surface so its face follows the surface - but oriented on each cell's own
# surface frame (tangent, up, normal) instead of the flat wall's x/y/z, so it
# works on a curved, twisting tower. Row = floor, so each row of cells is one
# floor's ring of units.
#
# This module is pure geometry - the eight corners of each box. Turning them
# into solids, and cutting them by the tower body, is rhino_backend's job.

from .module import module_frame
from .vec import add, mul

_SIGNS = ((-1, -1), (1, -1), (1, 1), (-1, 1))  # counter-clockwise seen from +normal


def box_corners(center, a, b, n, half_a, half_b, z0, z1):
    """
    The 8 corners of a box on frame (a, b, n) at `center`: extent +/-half_a
    along a, +/-half_b along b, from z0 to z1 along n. Bottom rectangle first
    (z0), counter-clockwise seen from +n, then the top one (z1) in the same
    order - the order rs.AddBox expects.
    """
    corners = []
    for z in (z0, z1):
        for sa, sb in _SIGNS:
            corners.append(add(center, add(add(mul(a, sa * half_a), mul(b, sb * half_b)),
                                            mul(n, z))))
    return corners


def wall_unit_corners(cell, thickness, fill=0.96):
    """
    (outer, inner) corner lists for the wall unit at `cell`.

    The unit fills the cell's own patch - `fill` of its width around and its
    height up (fill < 1 leaves a thin seam between neighbours) - so a floor's
    units tile its whole ring. It reaches `thickness` in from the surface
    point and out past the surface (by a third of the cell's smaller side,
    enough to clear the surface's curvature over one patch), where the tower
    body cuts it off. The inner box is inset by cell["inset_ratio"] x the
    smaller side all round - the opening - and overshoots the outer box at both
    ends so the subtraction cuts cleanly through.
    """
    a, b, n = module_frame(cell, "normal")
    p = cell["point"]
    half_a = cell["cell_w"] * fill / 2.0
    half_b = cell["cell_h"] * fill / 2.0
    inset = cell["inset_ratio"] * min(cell["cell_w"], cell["cell_h"]) * fill
    reach = min(cell["cell_w"], cell["cell_h"]) / 3.0

    outer = box_corners(p, a, b, n, half_a, half_b, -thickness, reach)
    inner = box_corners(p, a, b, n, half_a - inset, half_b - inset, -thickness - 1.0, reach + 1.0)
    return outer, inner
