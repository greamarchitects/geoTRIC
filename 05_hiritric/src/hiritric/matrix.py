# matrix.py
# The Surface Matrix Dictionary - hiritric's core structure. Same idea as
# mattric's (col, row)-keyed dictionary, but the cells are no longer
# hand-placed grid points: each one is a sample of a NURBS surface in its
# (U, V) parameter space, carrying the surface's own point, normal and
# tangent directions there. The surface is reached only through a
# `sampler(u, v)` callable, so this module stays free of Rhino and directly
# testable with an analytic stand-in.

from .vec import distance


#  matrix[(col, row)] = {
#      # read off the surface, never changed by the rule
#      "uv", "point", "normal", "u_axis", "v_axis", "cell_w", "cell_h", "seed",
#      # written by the rule
#      "normal_mod", "influence", "depth", "size", "inset_ratio", "taper",
#      "active", "color_t",
#  }
#  `col` runs around the tower (wraps at the seam), `row` climbs it.
def cell_seed(col, row, seed=0):
    """Deterministic pseudo-random value in [0, 1) for a cell - stable across
    runs for the same (col, row, seed), no random.seed()/global state."""
    h = hash((col, row, seed))
    return (h & 0xFFFFFFFF) / 0xFFFFFFFF


def build_matrix(cols, rows, sampler, seed=0):
    """
    Sample a surface into a cols x rows matrix at patch centres
    (u = (col + 0.5) / cols, v = (row + 0.5) / rows), so no sample sits on the
    seam or the top/bottom edge. `sampler(u, v)` returns {"point", "normal",
    "u_axis", "v_axis"} for u, v in 0..1 (section 9's surface_sampler builds
    one from a Rhino surface). U is closed: the last column's neighbour is
    column 0.
    """
    if cols < 2 or rows < 2:
        raise ValueError("need at least 2 columns and 2 rows to measure cell size")

    samples = {}
    for row in range(rows):
        for col in range(cols):
            u, v = (col + 0.5) / cols, (row + 0.5) / rows
            samples[(col, row)] = (u, v, sampler(u, v))

    matrix = {}
    for (col, row), (u, v, s) in samples.items():
        point = s["point"]
        east = samples[((col + 1) % cols, row)][2]["point"]
        north_row = row + 1 if row + 1 < rows else row - 1
        north = samples[(col, north_row)][2]["point"]
        cell_w, cell_h = distance(point, east), distance(point, north)
        matrix[(col, row)] = {
            "uv": (u, v),
            "point": point,
            "normal": s["normal"],
            "u_axis": s["u_axis"],
            "v_axis": s["v_axis"],
            "cell_w": cell_w,
            "cell_h": cell_h,
            "seed": cell_seed(col, row, seed),
            "normal_mod": s["normal"],
            "influence": 0.0,
            "depth": 0.0,
            "size": min(cell_w, cell_h),
            "inset_ratio": 0.25,
            "taper": 1.0,
            "active": True,
            "color_t": 0.0,
        }
    return matrix
