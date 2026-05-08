from .geometry import Polyline

POINTS = [
    (-3, -2, 0), (-2, -0.5, 0), (-2.5, 1, 0), (-1, 2.5, 0),
    (0.8, -1.7, 0), (1.6, 0, 0), (1.2, 1.8, 0), (3, 2.5, 0),
    (2.6, -2.3, 0)
]

EDGES = [(0,1), (1,2), (2,3), (1,4), (4,5), (5,6), (6,7), (5,8)]

def skeletric_state(t=1.0):
    count = max(1, int(len(EDGES) * t))
    return [Polyline([POINTS[a], POINTS[b]]) for a, b in EDGES[:count]]
