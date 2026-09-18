# rhino_backend.py
# Rhino rendering adapter for mattric.
#
# Turns a matrix (a dict of 3D control points: origin/offset) into NURBS
# curves and, from those, a lofted/swept wall surface - this is the only
# module in the package that knows what a matrix looks like as geometry,
# and the only one that imports rhinoscriptsyntax. matrix.py / pattern.py
# stay pure data + rules, same split as pattric.
#
# Live-only for this first draft (draws directly into the active Rhino
# document).

from __future__ import annotations

from typing import List, Optional, Tuple

from .matrix import Cell, Matrix, column_keys, row_keys

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
            "mattric.rhino_backend needs to run inside Rhino (rhinoscriptsyntax not found)."
        )


def cell_point(cell: Cell) -> Tuple[float, float, float]:
    """Cell's actual drawn point: origin + offset. Pure function - no Rhino."""
    ox, oy, oz = cell["origin"]
    dx, dy, dz = cell.get("offset", (0.0, 0.0, 0.0))
    return (ox + dx, oy + dy, oz + dz)


def ensure_layer(path: str, color: Optional[Tuple[int, int, int]] = None) -> str:
    """Create a (possibly nested, 'A::B::C') layer path if missing, and set its
    color if given. Live only. Identical to pattric.rhino_backend.ensure_layer."""
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


def draw_profile_curves_live(matrix: Matrix, cols: int, layer: str = "mattric::profiles",
                              zoom: bool = False, color: Optional[Tuple[int, int, int]] = None) -> List:
    """
    One interpolated NURBS curve per column (bottom to top) - the wall's
    vertical profiles, later fed to loft_wall_live. Returns the created
    curve ids, in column order (0..cols-1) so callers can loft/sweep them
    directly.
    """
    _require_live()
    ensure_layer(layer, color)
    ids = []
    for col in range(cols):
        pts = [cell_point(matrix[key]) for key in column_keys(matrix, col)]
        guid = rs.AddInterpCurve(pts)
        if guid:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    if zoom:
        rs.ZoomExtents()
    return ids


def draw_course_curves_live(matrix: Matrix, rows: int, layer: str = "mattric::courses",
                             zoom: bool = False, color: Optional[Tuple[int, int, int]] = None) -> List:
    """
    One interpolated NURBS curve per row (left to right) - horizontal
    courses, the alternative rail set for rs.AddSweep2 (bottom + top course
    as the two rails, profile curves as cross-sections) instead of a loft
    across every column.
    """
    _require_live()
    ensure_layer(layer, color)
    ids = []
    for row in range(rows):
        pts = [cell_point(matrix[key]) for key in row_keys(matrix, row)]
        guid = rs.AddInterpCurve(pts)
        if guid:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    if zoom:
        rs.ZoomExtents()
    return ids


def loft_wall_live(curve_ids: List, layer: str = "mattric::wall",
                    color: Optional[Tuple[int, int, int]] = None) -> List:
    """
    Loft the given curves (in order - typically draw_profile_curves_live's
    output) into one wall surface. Swap for rs.AddSweep2(rails, shapes) if
    a two-rail sweep (e.g. bottom/top course as rails, profiles as shapes)
    reads better for a given wall shape than a straight loft.
    """
    _require_live()
    ensure_layer(layer, color)
    surfaces = rs.AddLoft(curve_ids, loft_type=0) or []
    for guid in surfaces:
        rs.ObjectLayer(guid, layer)
    return surfaces


def draw_markers_live(points: List[Tuple[float, float, float]], radius: float = 1.5,
                       layer: str = "mattric::attractors", zoom: bool = False,
                       color: Optional[Tuple[int, int, int]] = None) -> List:
    """Draw each point as a small circle (2D linework, not an rs.AddPoint dot)
    into Rhino - used to mark attractor positions on their own layer.
    Identical in spirit to pattric.rhino_backend.draw_markers_live."""
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
