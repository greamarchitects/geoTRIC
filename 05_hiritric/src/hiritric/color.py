# color.py
# Color gradients as data: a list of RGB stops, sampled at t in 0..1 by
# linear interpolation between neighbouring stops. Pure - no Rhino.


GRADIENTS = {
    "ember": [(28, 36, 82), (40, 120, 176), (236, 196, 84), (226, 78, 52)],
    "moss":  [(24, 52, 44), (78, 130, 82), (196, 208, 120), (246, 236, 190)],
    "slate": [(30, 34, 44), (96, 108, 128), (190, 198, 210), (250, 250, 250)],
}


def gradient(t, stops):
    """Color at t (clamped to 0..1) along `stops`, evenly spaced, linearly blended."""
    t = min(max(t, 0.0), 1.0)
    if len(stops) == 1:
        return tuple(stops[0])
    scaled = t * (len(stops) - 1)
    i = min(int(scaled), len(stops) - 2)
    f = scaled - i
    lo, hi = stops[i], stops[i + 1]
    return tuple(int(round(lo[c] + (hi[c] - lo[c]) * f)) for c in range(3))
