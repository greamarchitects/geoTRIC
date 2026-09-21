# matrix.py
# The 3D Point Matrix Dictionary - mattric's core structure. Same idea as
# pattric's (col, row)-keyed dictionary, extended with a z axis: each cell
# is a control point for a NURBS profile curve, not a drawn square.
#
#     matrix[(col, row)] = {
#         "origin":   (x, y, z),          # fixed base grid position
#         "offset":   (0.0, 0.0, 0.0),    # rule-driven displacement from
#                                         #   origin (kept separate so rules
#                                         #   stay idempotent, same reasoning
#                                         #   as pattric's cell["offset"])
#         "seed":     0.0..1.0,           # deterministic per-cell pseudo-random source
#     }
#
# `col` runs along the wall (its width), `row` climbs the wall (its
# height) - rhino_backend.py reads one column at a time to build a
# vertical NURBS profile curve, then lofts/sweeps across all columns to
# build the wall surface.
#
# No Rhino/geometry here on purpose - just the dictionary and plain
# iteration/lookup helpers over it, so it's directly testable without
# rhinoscriptsyntax, exactly like pattric's matrix.py.

from typing import Dict, List, Tuple

Point3D = Tuple[float, float, float]
CellKey = Tuple[int, int]
Cell = Dict[str, object]
Matrix = Dict[CellKey, Cell]


def _cell_seed(col: int, row: int, seed: int = 0) -> float:
    """Deterministic pseudo-random value in [0, 1) for a cell - stable across
    runs for the same (col, row, seed), no random.seed()/global state."""
    h = hash((col, row, seed))
    return (h & 0xFFFFFFFF) / 0xFFFFFFFF


def build_matrix(cols: int, rows: int, col_spacing: float = 10.0, row_height: float = 10.0,
                  origin: Point3D = (0.0, 0.0, 0.0), seed: int = 0) -> Matrix:
    """
    Build a cols x rows 3D point matrix: columns spread along x
    (`col_spacing` apart), rows climb along z (`row_height` apart) - a flat
    vertical wall of control points, y left at the origin's value until a
    rule displaces it (the wall's depth/bulge direction).
    """
    ox, oy, oz = origin
    matrix: Matrix = {}
    for row in range(rows):
        for col in range(cols):
            matrix[(col, row)] = {
                "origin": (ox + col * col_spacing, oy, oz + row * row_height),
                "offset": (0.0, 0.0, 0.0),
                "seed": _cell_seed(col, row, seed),
            }
    return matrix


UnitGrid = Dict[CellKey, Dict[str, object]]


def wall_extents(matrix: Matrix) -> Tuple[float, float, float, float]:
    """(x_min, z_min, x_max, z_max) of the matrix's base origins - the
    wall's footprint in its own x/z plane (y is the depth direction)."""
    xs = [cell["origin"][0] for cell in matrix.values()]
    zs = [cell["origin"][2] for cell in matrix.values()]
    return (min(xs), min(zs), max(xs), max(zs))


def build_unit_grid(extents: Tuple[float, float, float, float], unit_size: float,
                     inset: float) -> UnitGrid:
    """
    Square grid of perforated wall units filling `extents` (x_min, z_min,
    x_max, z_max) edge to edge, centered so any leftover width/height is
    split evenly into margins. Each unit is a dictionary, keyed (i, j) like
    the point matrix:

        units[(i, j)] = {
            "center": (x, z),   # unit center in the wall's x/z plane
            "size":   unit_size,  # outer square side
            "inset":  inset,      # inner square sits `inset` inside the outer one
        }

    so the frame is `inset` thick all round and the hole is
    (size - 2*inset) square. `inset` lives on each unit (not just a global)
    so a later rule can vary the perforation per unit. Pure function - no Rhino.
    """
    if not 0.0 < inset < unit_size / 2.0:
        raise ValueError(f"inset must be between 0 and unit_size/2 ({unit_size / 2.0}); got {inset}")
    x0, z0, x1, z1 = extents
    n_cols = int(((x1 - x0) + 1e-9) // unit_size)
    n_rows = int(((z1 - z0) + 1e-9) // unit_size)
    if n_cols < 1 or n_rows < 1:
        raise ValueError(f"unit_size {unit_size} doesn't fit inside the wall extents {extents}")
    margin_x = ((x1 - x0) - n_cols * unit_size) / 2.0
    margin_z = ((z1 - z0) - n_rows * unit_size) / 2.0

    units: UnitGrid = {}
    for j in range(n_rows):
        for i in range(n_cols):
            units[(i, j)] = {
                "center": (x0 + margin_x + (i + 0.5) * unit_size,
                           z0 + margin_z + (j + 0.5) * unit_size),
                "size": unit_size,
                "inset": inset,
            }
    return units


def column_keys(matrix: Matrix, col: int) -> List[CellKey]:
    """(col, row) keys for one column, sorted bottom to top - one vertical
    wall profile."""
    return sorted(key for key in matrix if key[0] == col)


def row_keys(matrix: Matrix, row: int) -> List[CellKey]:
    """(col, row) keys for one row, sorted left to right - one horizontal
    course (an alternative sweep-rail direction)."""
    return sorted(key for key in matrix if key[1] == row)


def bounds(matrix: Matrix) -> Tuple[int, int, int, int]:
    """(min_col, min_row, max_col, max_row) over all keys."""
    cols = [c for c, _ in matrix]
    rows = [r for _, r in matrix]
    return (min(cols), min(rows), max(cols), max(rows))


def center_key(matrix: Matrix) -> CellKey:
    """Grid key nearest the matrix's center (for attractor-style rules)."""
    min_c, min_r, max_c, max_r = bounds(matrix)
    return (round((min_c + max_c) / 2), round((min_r + max_r) / 2))
