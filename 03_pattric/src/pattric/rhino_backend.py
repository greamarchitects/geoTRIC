# rhino_backend.py
# Rhino rendering adapter for pattric.
#
# Turns a matrix (a dict of numeric per-cell state: origin/offset/rotation/
# scale) into 2D linework - this is the only module in the package that
# knows what a cell actually looks like as geometry, and the only one that
# imports rhinoscriptsyntax. matrix.py / pattern.py stay pure data + rules.
#
# Live-only for this first draft (draws directly into the active Rhino
# document). A headless rhino3dm path, if needed later, can follow the
# same shape as grammatric's rhino_backend.

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .matrix import Cell, Matrix

try:
    import rhinoscriptsyntax as rs  # only importable from inside Rhino
except ImportError:
    rs = None


def is_live() -> bool:
    """True if running inside Rhino's own Python engine (rhinoscriptsyntax available)."""
    return rs is not None


def _require_live() -> None:
    if not is_live():
        raise RuntimeError(
            "pattric.rhino_backend needs to run inside Rhino (rhinoscriptsyntax not found)."
        )


def cell_corners(cell: Cell, cell_size: float) -> List[Tuple[float, float, float]]:
    """
    Local unit-square corners (side = cell_size * cell['scale']), rotated by
    cell['rotation'] degrees about the cell's own center, then translated to
    cell['origin'] + cell['offset']. Pure function - no Rhino - so it's
    directly testable on its own.
    """
    ox, oy, oz = cell["origin"]
    dx, dy = cell.get("offset", (0.0, 0.0))
    cx, cy = ox + dx, oy + dy

    half = (cell_size * cell.get("scale", 1.0)) / 2.0
    ang = math.radians(cell.get("rotation", 0.0))
    c, s = math.cos(ang), math.sin(ang)

    local = [(-half, -half), (half, -half), (half, half), (-half, half)]
    corners = []
    for lx, ly in local:
        rx = lx * c - ly * s
        ry = lx * s + ly * c
        corners.append((cx + rx, cy + ry, oz))
    corners.append(corners[0])  # close the polyline
    return corners


def ensure_layer(path: str, color: Optional[Tuple[int, int, int]] = None) -> str:
    """
    Create a (possibly nested, 'A::B::C') layer path if missing, and set its
    color if given (every call, so re-running the script after a color
    tweak still picks it up - distinct colors are how overlapping base/
    transformed layers stay tellable apart). Live only.
    """
    _require_live()
    if not rs.IsLayer(path):
        parts = path.split("::")
        current = parts[0]
        if not rs.IsLayer(current):
            rs.AddLayer(current)
        for part in parts[1:]:
            nxt = f"{current}::{part}"
            if not rs.IsLayer(nxt):
                rs.AddLayer(part, parent=current)
            current = nxt
    if color is not None:
        rs.LayerColor(path, color)
    return path


def draw_matrix_live(matrix: Matrix, cell_size: float = 8.0, layer: str = "pattric",
                      zoom: bool = True, color: Optional[Tuple[int, int, int]] = None) -> List:
    """
    Draw every cell in `matrix` as a closed square outline (straight
    segments via rs.AddPolyline, not a smooth AddCurve) into Rhino.
    Returns the created object ids.
    """
    _require_live()
    ensure_layer(layer, color)
    ids = []
    for key in sorted(matrix.keys()):
        pts = cell_corners(matrix[key], cell_size)
        guid = rs.AddPolyline(pts)
        if guid:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    if zoom:
        rs.ZoomExtents()
    return ids


def draw_markers_live(points: List[Tuple[float, float, float]], radius: float = 1.5,
                       layer: str = "pattric::attractors", zoom: bool = False,
                       color: Optional[Tuple[int, int, int]] = None) -> List:
    """
    Draw each point as a small circle (2D linework, not an rs.AddPoint dot -
    so it survives the same Letter/Landscape line-weight print path as the
    matrix cells) into Rhino. Used to mark attractor positions on their own
    layer. Returns the created object ids.
    """
    _require_live()
    ensure_layer(layer, color)
    ids = []
    for pt in points:
        guid = rs.AddCircle(pt, radius)
        if guid:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    if zoom:
        rs.ZoomExtents()
    return ids
