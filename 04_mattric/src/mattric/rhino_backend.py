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
    import scriptcontext as sc
    import Rhino
    import System
except ImportError:
    rs = sc = Rhino = System = None


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
                    color: Optional[Tuple[int, int, int]] = None,
                    loft_type: str = "Tight", closed: bool = False) -> List:
    """
    Python (RhinoCommon) port of the C++ CArgsRhinoLoft / RhinoSdkLoftSurface
    sample: loft the given curves (in order - typically
    draw_profile_curves_live's output) into one wall.

    Mapping from the C++ sample:
      m_loft_type = ltTight             -> LoftType.Tight (`loft_type` names any LoftType member)
      m_bClosed                         -> `closed`
      m_bUseStartpoint/Endpoint = FALSE -> Point3d.Unset start/end
      m_simplify_method = lsNone        -> plain Brep.CreateFromLoft (no rebuild/refit)
      RemoveShortSegments(...)          -> Curve.RemoveShortSegments(tolerance) on a duplicate
      RhinoJoinBreps(...)               -> Brep.JoinBreps(...)
      doc.AddBrepObject / Redraw        -> sc.doc.Objects.AddBrep / Views.Redraw

    Like the C++ sample, this does no curve sorting or direction matching -
    curves must already be in loft order and point the same way, which
    draw_profile_curves_live's column-by-column, bottom-to-top output is.
    """
    _require_live()
    ensure_layer(layer, color)
    tolerance = sc.doc.ModelAbsoluteTolerance

    curves = []
    for curve_id in curve_ids:
        source = rs.coercecurve(curve_id)
        if source is None:
            continue
        curve = source.DuplicateCurve()
        curve.RemoveShortSegments(tolerance)
        curves.append(curve)
    if len(curves) < 2:
        return []

    unset = Rhino.Geometry.Point3d.Unset
    breps = Rhino.Geometry.Brep.CreateFromLoft(
        curves, unset, unset, getattr(Rhino.Geometry.LoftType, loft_type), closed)
    if not breps:
        return []

    if len(breps) > 1:
        joined = Rhino.Geometry.Brep.JoinBreps(breps, tolerance)
        if joined:
            breps = joined

    ids = []
    for brep in breps:
        guid = sc.doc.Objects.AddBrep(brep)
        if guid != System.Guid.Empty:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    sc.doc.Views.Redraw()
    return ids


def clamped_uniform_knots(cv_count: int, degree: int) -> List[float]:
    """
    Clamped uniform knot vector WITHOUT the 2 superfluous end knots
    (length cv_count + degree - 1) - the convention both ON_NurbsSurface in
    the C++ sample and RhinoCommon's NurbsSurface.KnotsU/KnotsV use. Pure
    function - no Rhino. e.g. (3 cvs, degree 2) -> [0, 0, 1, 1]; (5 cvs,
    degree 3) -> [0, 0, 0, 1, 2, 2, 2].
    """
    interior = cv_count - degree - 1
    return ([0.0] * degree
            + [float(i) for i in range(1, interior + 1)]
            + [float(interior + 1)] * degree)


def matrix_point_grid(matrix: Matrix, cols: int, rows: int) -> List[List[Tuple[float, float, float]]]:
    """Matrix -> grid[col][row] of drawn points (origin + offset) - the
    control-point net nurbs_surface_live takes. Pure function - no Rhino."""
    return [[cell_point(matrix[(col, row)]) for row in range(rows)] for col in range(cols)]


def nurbs_surface_live(point_grid: List[List[Tuple[float, float, float]]],
                        u_degree: int = 2, v_degree: int = 3,
                        layer: str = "mattric::cv_wall",
                        color: Optional[Tuple[int, int, int]] = None) -> Optional[object]:
    """
    Python (RhinoCommon) port of the C++ CreateSurfacesExample: build a
    non-rational NURBS surface directly from a control-point net
    (`point_grid[i][j]`, i along u, j along v), instead of lofting through
    curves - here the matrix's own points ARE the control net, so the
    surface is *pulled toward* them (like a control-point surface) rather
    than passing through them (like the loft).

    Mapping from the C++ sample:
      ON_NurbsSurface(dim, bIsRational, u_degree+1, v_degree+1, u_cv, v_cv)
                                       -> NurbsSurface.Create(3, False, u_degree+1, v_degree+1, u_cv, v_cv)
      SetKnot(0/1, i, ...)             -> surface.KnotsU[i] / KnotsV[j] = ... (clamped_uniform_knots)
      SetCV(i, j, point)               -> surface.Points.SetPoint(i, j, Point3d)
      IsValid() then AddSurfaceObject  -> surface.IsValid then sc.doc.Objects.AddSurface
    Degrees are reduced automatically if the net is too small for them
    (a degree needs at least degree+1 control points). Returns the new
    object id, or None if the surface wasn't valid.
    """
    _require_live()
    ensure_layer(layer, color)
    u_cv, v_cv = len(point_grid), len(point_grid[0])
    u_degree = min(u_degree, u_cv - 1)
    v_degree = min(v_degree, v_cv - 1)

    surface = Rhino.Geometry.NurbsSurface.Create(3, False, u_degree + 1, v_degree + 1, u_cv, v_cv)
    for i, knot in enumerate(clamped_uniform_knots(u_cv, u_degree)):
        surface.KnotsU[i] = knot
    for j, knot in enumerate(clamped_uniform_knots(v_cv, v_degree)):
        surface.KnotsV[j] = knot
    for i in range(u_cv):
        for j in range(v_cv):
            x, y, z = point_grid[i][j]
            surface.Points.SetPoint(i, j, Rhino.Geometry.Point3d(x, y, z))

    if not surface.IsValid:
        return None
    guid = sc.doc.Objects.AddSurface(surface)
    if guid == System.Guid.Empty:
        return None
    rs.ObjectLayer(guid, layer)
    sc.doc.Views.Redraw()
    return guid


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
