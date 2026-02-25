# transforms.py
# Basic affine transforms for 2D shapes

import math
from typing import Tuple
from .symbols import Shape

Point2D = Tuple[float, float]
Segment2D = Tuple[Point2D, Point2D]


def _centroid(shape: Shape) -> Point2D:
    pts = [p for seg in shape.segments for p in seg]
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    return (x, y)


def translate_shape(shape: Shape, dx: float, dy: float) -> Shape:
    segs = []
    for a, b in shape.segments:
        segs.append(((a[0] + dx, a[1] + dy),
                     (b[0] + dx, b[1] + dy)))
    return Shape(tuple(segs))


def rotate_shape(shape: Shape, angle_deg: float) -> Shape:
    cx, cy = _centroid(shape)
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)

    segs = []
    for p1, p2 in shape.segments:
        def rot(p):
            x, y = p
            x -= cx
            y -= cy
            xr = x * c - y * s
            yr = x * s + y * c
            return (xr + cx, yr + cy)

        segs.append((rot(p1), rot(p2)))

    return Shape(tuple(segs))


def scale_shape(shape: Shape, factor: float) -> Shape:
    cx, cy = _centroid(shape)
    segs = []
    for p1, p2 in shape.segments:
        def scl(p):
            x, y = p
            return (cx + (x - cx) * factor,
                    cy + (y - cy) * factor)

        segs.append((scl(p1), scl(p2)))

    return Shape(tuple(segs))