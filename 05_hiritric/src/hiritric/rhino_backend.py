# rhino_backend.py
# Rhino adapter for hiritric - the only module that imports
# rhinoscriptsyntax. It lofts the tower, exposes the loft as a plain
# `sampler(u, v)` callable for matrix.py, and draws modules, attractor
# markers and the view. Live-only for this first draft.

import math

from .module import module_mesh
from .vec import dot

try:
    import rhinoscriptsyntax as rs  # only importable from inside Rhino
except ImportError:
    rs = None


def require_rhino():
    if rs is None:
        raise RuntimeError("This function needs to run inside Rhino (rhinoscriptsyntax not found).")


def delete_object(guid):
    """Delete one object from the document."""
    require_rhino()
    rs.DeleteObject(guid)


def ensure_layer(path, color=None):
    """Create a (possibly nested, 'A::B::C') layer path if missing, and set its
    color if given. Same as pattric/mattric's ensure_layer."""
    require_rhino()
    if not rs.IsLayer(path):
        parts = path.split("::")
        current = parts[0]
        if not rs.IsLayer(current):
            rs.AddLayer(current)
        for part in parts[1:]:
            nxt = current + "::" + part
            if not rs.IsLayer(nxt):
                rs.AddLayer(part, parent=current)
            current = nxt
    if color is not None:
        rs.LayerColor(path, color)
    return path


def redraw_off():
    """Stop Rhino redrawing after every object added. Without this each of
    the thousands of objects a run creates forces a viewport redraw, which is
    what makes a big script crawl (or look frozen). Pair with redraw_on()."""
    require_rhino()
    rs.EnableRedraw(False)


def redraw_on():
    """Turn redrawing back on and refresh the viewports once."""
    require_rhino()
    rs.EnableRedraw(True)
    rs.Redraw()


def progress(message, echo=True):
    """Show `message` at Rhino's command prompt (so a long run visibly moves)
    and, if `echo`, print it too."""
    if echo:
        print(message)
    if rs is not None:
        try:
            rs.Prompt(message)
        except Exception:
            pass


def make_floor_curve(points, smooth=True):
    """
    One closed curve through a floor plan's points. With `smooth`, tries the
    smoothest construction first and falls back so a floor never comes back
    empty:
      1. periodic interpolated curve (knotstyle 3) - smooth, no seam kink
      2. interpolated curve through the points plus the first repeated
      3. closed polyline (always works; faceted)
    With smooth=False it goes straight to the polyline. Returns the curve id.
    """
    if smooth:
        for attempt in (lambda: rs.AddInterpCurve(points, 3, 3),
                        lambda: rs.AddInterpCurve(list(points) + [points[0]], 3, 0)):
            curve = attempt()
            if curve and rs.IsCurveClosed(curve):
                return curve
            if curve:
                rs.DeleteObject(curve)
    return rs.AddPolyline(list(points) + [points[0]])


def loft_floors(curves):
    """Loft the floor curves, trying Normal, then Loose, then Straight lofts
    (rs loft_type 0, 1, 2). Returns the list of new surface ids, empty if
    every type fails."""
    for loft_type in (0, 1, 2):
        lofts = rs.AddLoft(curves, loft_type=loft_type)
        if lofts:
            return lofts
    return []


def close_body(body, bottom_curve, top_curve):
    """
    Make the lofted `body` a closed polysurface. Tries Rhino's own
    CapPlanarHoles first; if that leaves it open, caps the planar bottom and
    top floor curves itself and joins them on. Returns the (possibly new) id
    and whether it ended up closed.
    """
    rs.CapPlanarHoles(body)
    if rs.IsPolysurfaceClosed(body):
        return body, True
    caps = (rs.AddPlanarSrf([bottom_curve]) or []) + (rs.AddPlanarSrf([top_curve]) or [])
    joined = rs.JoinSurfaces([body] + caps, delete_input=True) if caps else None
    if joined:
        return joined[0], bool(rs.IsPolysurfaceClosed(joined[0]))
    return body, False


def draw_tower(floor_points, layer, color=None):
    """
    Loft the floor-plan curves (tower_floor_points) into the tower and return
    (body, skin, closed):
      skin    the bare lofted NURBS surface - what the matrix is sampled from
              (a surface, so SurfaceFrame works on it); delete it afterwards
      body    a copy of the skin with its planar top and bottom capped: the
              tower itself, a closed polysurface, on `layer`
      closed  whether the body came out closed (a real solid)
    Falls back rather than giving up: smooth floor curves first, then plain
    polylines; Normal, Loose and Straight loft types (loft_floors); Rhino's
    CapPlanarHoles, then manual planar caps (close_body). Returns
    (None, None, False) only if every loft attempt fails.
    """
    require_rhino()
    ensure_layer(layer, color)
    curves, lofts = [], []
    for smooth in (True, False):
        curves = [make_floor_curve(points, smooth) for points in floor_points]
        lofts = loft_floors(curves) if all(curves) else []
        if lofts:
            break
        rs.DeleteObjects([c for c in curves if c])
    if not lofts:
        return None, None, False
    skin = lofts[0]
    rs.DeleteObjects(lofts[1:])

    body, closed = close_body(rs.CopyObject(skin), curves[0], curves[-1])
    rs.DeleteObjects(curves)
    rs.ObjectLayer(body, layer)
    return body, skin, closed


def surface_sampler(surface_id, center_xy):
    """
    Wrap a Rhino surface as the `sampler(u, v)` build_matrix expects: u, v in
    0..1 are mapped onto the surface's own parameter domains, and the surface
    frame there gives the point, the normal and the U/V tangents. The normal
    is flipped if needed to point away from the tower's axis (`center_xy`),
    since a loft's normal direction depends on curve order.
    """
    require_rhino()
    (u0, u1) = rs.SurfaceDomain(surface_id, 0)
    (v0, v1) = rs.SurfaceDomain(surface_id, 1)

    def sampler(u, v):
        frame = rs.SurfaceFrame(surface_id, (u0 + u * (u1 - u0), v0 + v * (v1 - v0)))
        point = (frame.Origin.X, frame.Origin.Y, frame.Origin.Z)
        normal = (frame.ZAxis.X, frame.ZAxis.Y, frame.ZAxis.Z)
        outward = (point[0] - center_xy[0], point[1] - center_xy[1], 0.0)
        if dot(normal, outward) < 0.0:
            normal = (-normal[0], -normal[1], -normal[2])
        return {
            "point": point,
            "normal": normal,
            "u_axis": (frame.XAxis.X, frame.XAxis.Y, frame.XAxis.Z),
            "v_axis": (frame.YAxis.X, frame.YAxis.Y, frame.YAxis.Z),
        }

    return sampler


def module_polysurface(vertices):
    """
    The module as a closed polysurface, built from lofts: the outer and the
    inner wall are each a straight loft between a base ring and a tip ring
    (four faces apiece), the top and base rings are planar surfaces with the
    opening cut out, and the four are joined. `vertices` is module_mesh's
    (base outer, base inner, top outer, top inner). Returns the id or None.
    """
    rings = [vertices[0:4], vertices[4:8], vertices[8:12], vertices[12:16]]
    base_outer, base_inner, top_outer, top_inner = [
        rs.AddPolyline(list(ring) + [ring[0]]) for ring in rings]

    outer_wall = rs.AddLoft([base_outer, top_outer], loft_type=2) or []
    inner_wall = rs.AddLoft([base_inner, top_inner], loft_type=2) or []
    top_ring = rs.AddPlanarSrf([top_outer, top_inner]) or []
    base_ring = rs.AddPlanarSrf([base_outer, base_inner]) or []
    rs.DeleteObjects([base_outer, base_inner, top_outer, top_inner])

    pieces = [outer_wall, inner_wall, top_ring, base_ring]
    parts = [guid for piece in pieces for guid in piece]
    if not all(pieces):
        rs.DeleteObjects(parts)
        return None
    joined = rs.JoinSurfaces(parts, delete_input=True)
    return joined[0] if joined else None


def draw_module(cell, layer, color=None, as_polysurface=True):
    """
    Draw one module (module_mesh) at `cell`, colored `color`. As a closed
    polysurface built from lofts (module_polysurface) by default; or, with
    `as_polysurface=False`, a single 16-quad mesh - much faster, for quick
    previews with many modules. Returns the new object id, or None.
    """
    require_rhino()
    ensure_layer(layer)   # color is per-object below, not the layer's own color
    vertices, faces = module_mesh(cell)
    if as_polysurface:
        guid = module_polysurface(vertices)
    else:
        guid = rs.AddMesh(vertices, faces)
    if guid:
        rs.ObjectLayer(guid, layer)
        if color is not None:
            rs.ObjectColor(guid, color)
    return guid


def bbox_diagonal(guid):
    """Length of the diagonal of `guid`'s world axis-aligned bounding box, or
    0.0 if it has none (a degenerate/empty result)."""
    require_rhino()
    corners = rs.BoundingBox(guid)
    if not corners:
        return 0.0
    lo, hi = corners[0], corners[6]
    return math.sqrt((hi.X - lo.X) ** 2 + (hi.Y - lo.Y) ** 2 + (hi.Z - lo.Z) ** 2)


def draw_wall_unit(outer_corners, inner_corners, body_id, layer, color=None,
                    min_diag_ratio=0.2):
    """
    One closed wall unit, the way mattric builds them: a box (`outer_corners`)
    minus a smaller box (`inner_corners`) leaves a frame with an opening, and
    intersecting that frame with the closed tower body keeps only the part
    inside the tower - its outer face becomes a piece of the tower surface,
    so the unit ends exactly where the surface is and comes out a closed
    polysurface. `body_id` is left untouched, ready for the next unit.

    A boolean can return more than one fragment (e.g. a stray sliver
    alongside the real piece); the largest by bounding-box diagonal is kept,
    the rest deleted - picking index 0 blindly risks keeping a sliver and
    losing the actual unit. The kept piece is also checked against the outer
    box's own diagonal: if it is smaller than `min_diag_ratio` of that (a
    near-degenerate result - the boolean "succeeded" but produced almost
    nothing), it is rejected as a failure instead of left invisible on
    screen while still counting as built.

    Returns the new object id, or None if a boolean fails or its result is
    rejected as degenerate.
    """
    require_rhino()
    ensure_layer(layer)   # color is per-object below, not the layer's own color
    outer = rs.AddBox(outer_corners)
    inner = rs.AddBox(inner_corners)
    if not (outer and inner):
        rs.DeleteObjects([g for g in (outer, inner) if g])
        return None
    outer_diag = bbox_diagonal(outer)
    frame = rs.BooleanDifference([outer], [inner], delete_input=True)
    if not frame:
        rs.DeleteObjects([outer, inner])
        return None
    units = rs.BooleanIntersection(frame, [body_id], delete_input=False)
    rs.DeleteObjects(frame)
    if not units:
        return None
    guid = max(units, key=bbox_diagonal)
    rs.DeleteObjects([u for u in units if u != guid])
    if outer_diag > 0 and bbox_diagonal(guid) < min_diag_ratio * outer_diag:
        rs.DeleteObject(guid)
        return None
    rs.ObjectLayer(guid, layer)
    if color is not None:
        rs.ObjectColor(guid, color)
    return guid


def set_layer_visible(layer, visible):
    """Show or hide a layer - used to keep the tower body as the wall units'
    cutter without displaying it (its surface would sit flush with theirs)."""
    require_rhino()
    rs.LayerVisible(layer, visible)


def draw_attractors(points, radius, layer, color=None):
    """Mark each attractor as a small sphere on its own layer."""
    require_rhino()
    ensure_layer(layer, color)
    ids = []
    for point in points:
        guid = rs.AddSphere(point, radius)
        if guid:
            rs.ObjectLayer(guid, layer)
            ids.append(guid)
    return ids


def set_view(mode="Shaded", zoom=True):
    """Switch the active viewport to a surface display mode (Shaded, Rendered,
    Ghosted, Arctic, Pen, Artistic, ...) - the assignment asks for a view that
    shows surfaces, not wireframe - and optionally zoom to fit."""
    require_rhino()
    try:
        rs.ViewDisplayMode(None, mode)
    except Exception as exc:
        print("Hiritric: could not switch the view to %s (%s) - set it by hand." % (mode, exc))
    if zoom:
        rs.ZoomExtents()
