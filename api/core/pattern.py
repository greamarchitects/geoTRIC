import math
from .geometry import Polyline

def cross(x, y, s, angle):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def rot(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca, 0)

    return [
        Polyline([rot(-s, 0), rot(s, 0)]),
        Polyline([rot(0, -s), rot(0, s)]),
    ]

def pattric_state(t=0.0, n=18):
    geometry = []
    for i in range(n):
        for j in range(n):
            x = (i - n / 2) * 0.45
            y = (j - n / 2) * 0.45
            d = math.sqrt((x - 1)**2 + (y - 1)**2)
            s = max(0.05, 0.28 - d * 0.025)
            geometry.extend(cross(x, y, s, d * 20 + t * 180))
    return geometry
