# src/python/skeletric/derive.py
"""
derive.py
Generate complex 2D geometry from bone structures (lists of points).

This is the "complex form" layer:
- takes sampled point lists as input
- outputs linework via rs.AddLine(), rs.AddCurve(), rs.AddCircle()
- uses list operations: append, pop, len, sort/reverse (via bones.py)

Keep everything as 2D linework by forcing Z=0.
"""

import Rhinoscriptsyntax as rs


def force_z0(points):
    """Ensure 2D output: set z=0 for all points."""
    return [(p[0], p[1], 0.0) for p in points]


def polyline(points, closed=False):
    """
    Create a curve through a list of points using rs.AddCurve().
    If closed, repeats first point at the end.
    """
    pts = force_z0(points)
    if closed and pts:
        pts = pts + [pts[0]]
    return rs.AddCurve(pts)


def ribs_along_spine(spine_points, rib_len=2.0, every=2):
    """
    Create perpendicular 'ribs' along a spine polyline.
    Uses rs.AddLine() repeatedly (definite iteration).

    For each chosen point i, estimate a tangent direction using neighbors,
    then create a perpendicular vector in XY.
    """
    pts = force_z0(spine_points)
    lines = []

    n = len(pts)
    if n < 3:
        return lines

    for i in range(1, n - 1, every):
        prev_p = pts[i - 1]
        p = pts[i]
        next_p = pts[i + 1]

        # tangent approx
        tx = next_p[0] - prev_p[0]
        ty = next_p[1] - prev_p[1]

        # perpendicular in XY: (-ty, tx)
        px, py = -ty, tx

        # normalize
        mag = (px * px + py * py) ** 0.5
        if mag < 1e-9:
            continue
        px /= mag
        py /= mag

        a = (p[0] - px * rib_len * 0.5, p[1] - py * rib_len * 0.5, 0.0)
        b = (p[0] + px * rib_len * 0.5, p[1] + py * rib_len * 0.5, 0.0)

        lines.append(rs.AddLine(a, b))

    return lines


def connect_point_lists(a_points, b_points, mode="ladder"):
    """
    Connect two point lists to generate complex linework.

    mode="ladder": connect matching indices (a[i] -> b[i])
    mode="weave": connect alternating cross-links (a[i] -> b[i+1], b[i] -> a[i+1])
    """
    A = force_z0(a_points)
    B = force_z0(b_points)

    lines = []
    n = min(len(A), len(B))
    if n < 2:
        return lines

    if mode == "ladder":
        for i in range(n):
            lines.append(rs.AddLine(A[i], B[i]))

    elif mode == "weave":
        for i in range(n - 1):
            if i % 2 == 0:
                lines.append(rs.AddLine(A[i], B[i + 1]))
            else:
                lines.append(rs.AddLine(B[i], A[i + 1]))

    return lines


def circles_on_points(points, radius=0.5, every=3):
    """
    Add circles at points (2D).
    Uses rs.AddCircle().
    """
    pts = force_z0(points)
    circles = []
    for i in range(0, len(pts), every):
        circles.append(rs.AddCircle(pts[i], radius))
    return circles


def pop_tail(points, k=1):
    """
    Demonstrate .pop() safely: removes last k points from a copy.
    """
    pts = list(points)
    for _ in range(k):
        if len(pts) == 0:
            break
        pts.pop()  # .pop()
    return pts


def transform_group(obj_ids, move=(0, 0, 0), rotate_deg=0.0, scale=1.0, center=(0, 0, 0)):
    """
    Optional transforms to compose multiple states (for your PDF sequences).
    Uses MoveObjects / CopyObjects as well.
    """
    if not obj_ids:
        return []

    ids = list(obj_ids)

    if move != (0, 0, 0):
        rs.MoveObjects(ids, move)

    if rotate_deg != 0.0:
        rs.RotateObjects(ids, center, rotate_deg)

    if scale != 1.0:
        rs.ScaleObjects(ids, center, (scale, scale, 1.0))

    return ids