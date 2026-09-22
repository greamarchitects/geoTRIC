# tower.py
# The tower's envelope, as data: one closed floor-plan polygon per control
# floor, which rhino_backend lofts into the NURBS surface the matrix then
# samples. Pure functions - no Rhino.

import math


def floor_plan_points(n_points, radius_x, radius_y, squareness, scale, rotation, z, origin):
    """
    Points of one closed floor plan, a superellipse |x/rx|^n + |y/ry|^n = 1:
    squareness 2 is an ellipse, ~4 a rounded square, larger a squarer one.
    `rotation` in degrees; the first point is not repeated at the end.
    """
    exponent = 2.0 / squareness
    cos_r, sin_r = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
    points = []
    for k in range(n_points):
        t = 2.0 * math.pi * k / n_points
        c, s = math.cos(t), math.sin(t)
        x = radius_x * scale * math.copysign(abs(c) ** exponent, c)
        y = radius_y * scale * math.copysign(abs(s) ** exponent, s)
        points.append((origin[0] + x * cos_r - y * sin_r,
                       origin[1] + x * sin_r + y * cos_r,
                       origin[2] + z))
    return points


def tower_floor_points(params, origin):
    """
    One plan polygon per control floor, bottom to top. Up the tower the plan
    is scaled (taper toward the top scale, plus a `bulge` fraction at
    mid-height) and rotated (`twist` degrees in total).
    """
    floors = int(params["floors"])
    result = []
    for f in range(floors):
        v = f / (floors - 1)
        scale = 1.0 + (params["taper"] - 1.0) * v + params["bulge"] * math.sin(math.pi * v)
        result.append(floor_plan_points(
            int(params["plan_points"]), params["radius_x"], params["radius_y"],
            params["squareness"], scale, params["twist"] * v, params["height"] * v, origin))
    return result
