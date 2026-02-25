# src/python/skeletric/bones.py
"""
bones.py
Utilities to acquire / build "bone structures" (curves, polylines) and
sample them into point lists.

This is the stable input layer:
- select curves/lines from Rhino
- create simple base bones (rectangle, polyline)
- divide curves into point lists (Tuples/Lists are central)
"""

import Rhinoscriptsyntax as rs


def get_bones(prompt="Select bone curves (lines/curves/polylines)", preselect=True):
    """
    Returns a list of Rhino object ids (curves/polylines).
    Uses rs.GetObjects() as requested.
    """
    ids = rs.GetObjects(prompt, filter=rs.filter.curve, preselect=preselect)
    return ids or []


def make_rectangle_bone(width=10.0, height=6.0, origin=(0.0, 0.0, 0.0), closed=True):
    """
    Creates a rectangle as a base 'bone' curve using rs.AddCurve().
    Output is a curve id.
    """
    ox, oy, oz = origin
    pts = [
        (ox, oy, oz),
        (ox, oy, oz),
        (ox + width, oy, oz),
        (ox + width, oy + height, oz),
        (ox, oy + height, oz),
    ]
    if closed:
        pts.append(pts[0])  # close polyline
    return rs.AddCurve(pts)


def curve_key_points(crv_id):
    """
    Returns (start, mid, end) tuples.
    Uses rs.CurveStartPoint(), rs.CurveMidPoint(), rs.CurveEndPoint().
    """
    return (
        rs.CurveStartPoint(crv_id),
        rs.CurveMidPoint(crv_id),
        rs.CurveEndPoint(crv_id),
    )


def curve_centroid(crv_id):
    """
    Returns centroid point tuple if available.
    Uses rs.CurveAreaCentroid().
    """
    result = rs.CurveAreaCentroid(crv_id)
    if not result:
        return None
    centroid, _area = result
    return centroid


def sample_curve(crv_id, n=20, include_ends=True):
    """
    Divides a curve into a list of points.
    - rs.DivideCurve() returns a LIST of point tuples.
    - include_ends keeps it robust for later curve creation.

    Returns: list[(x,y,z), ...]
    """
    pts = rs.DivideCurve(crv_id, n, create_points=False, return_points=True)
    pts = pts or []
    if include_ends:
        # Ensure start/end are present (sometimes DivideCurve gives them, sometimes not depending on params)
        s = rs.CurveStartPoint(crv_id)
        e = rs.CurveEndPoint(crv_id)
        if len(pts) == 0:
            return [s, e]
        if pts[0] != s:
            pts.insert(0, s)
        if pts[-1] != e:
            pts.append(e)
    return pts


def edit_points(crv_id):
    """
    Returns edit points if Rhino provides them.
    Uses rs.CurveEditPoints().
    """
    pts = rs.CurveEditPoints(crv_id)
    return pts or []


def sort_points_xy(points, reverse=False):
    """
    Demonstrates list sorting.
    Sorts points by (x,y). Returns new list.
    """
    pts = list(points)  # copy
    pts.sort(key=lambda p: (p[0], p[1]), reverse=reverse)  # .sort()
    return pts


def reverse_points(points):
    """
    Demonstrates list reverse().
    """
    pts = list(points)
    pts.reverse()
    return pts