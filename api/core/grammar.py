import math
from .geometry import Polyline

def square(cx=0, cy=0, size=1, angle=0):
    pts = []
    for a in [45, 135, 225, 315, 45]:
        r = math.radians(a + angle)
        pts.append((cx + size * math.cos(r), cy + size * math.sin(r), 0))
    return Polyline(pts)

def grammatric_state(t=0.0):
    return [
        square(-2.4, 1.6, 0.8, 0),
        square(2.4, 1.6, 0.8, 20 + t * 40),
        square(-2.4, -1.6, 0.8, 0),
        square(2.4, -1.6, 0.8, 35 + t * 50),
        square(2.9, -1.3, 0.45, -20 - t * 40),
    ]
