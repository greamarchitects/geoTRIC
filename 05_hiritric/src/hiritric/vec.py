# vec.py
# Tiny 3D vector helpers on plain (x, y, z) tuples - no Rhino, no numpy - so
# matrix/pattern/module logic stays testable outside Rhino and IronPython-
# friendly, same reasoning as the rest of the series.

import math


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def distance(a, b):
    return length(sub(a, b))


def normalize(a):
    """Unit vector, or (0, 0, 0) if `a` has no length - callers check length()."""
    n = length(a)
    return (0.0, 0.0, 0.0) if n < 1e-12 else mul(a, 1.0 / n)


def lerp(a, b, t):
    return a + (b - a) * t


def rotate_toward(n, target, angle):
    """
    Tilt unit vector `n` by `angle` radians toward `target`, in the plane the
    two span. The result is exactly `angle` away from `n` however `target` is
    scaled - so a tilt limit holds by construction. `n` is returned unchanged
    if `target` is parallel to it.
    """
    tangential = sub(target, mul(n, dot(target, n)))
    if length(tangential) < 1e-9:
        return n
    t = normalize(tangential)
    return normalize(add(mul(n, math.cos(angle)), mul(t, math.sin(angle))))
