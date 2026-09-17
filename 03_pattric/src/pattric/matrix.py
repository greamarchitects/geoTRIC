# matrix.py
# The 2D Point Matrix Dictionary - the core structure this whole package
# builds, mutates (via pattern.py) and renders (via rhino_backend.py).
#
# A matrix is a plain dict keyed by (col, row) grid coordinates - not a
# list index - so rules can do neighbor lookups and stay independent of
# iteration order:
#
#     matrix[(col, row)] = {
#         "origin":   (x, y, z),   # fixed base grid position
#         "offset":   (0.0, 0.0),  # rule-driven translation from origin
#                                  #   (the "moving" effect - kept separate
#                                  #   from origin so rules stay idempotent)
#         "rotation": 0.0,         # degrees
#         "scale":    1.0,
#         "seed":     0.0..1.0,    # deterministic per-cell pseudo-random source
#     }
#
# No Rhino/geometry here on purpose - just the dictionary and plain
# iteration/lookup helpers over it, so it's directly testable without
# rhinoscriptsyntax.

from typing import Dict, Tuple

Point3D = Tuple[float, float, float]
CellKey = Tuple[int, int]
Cell = Dict[str, object]
Matrix = Dict[CellKey, Cell]


def _cell_seed(col: int, row: int, seed: int = 0) -> float:
    """
    Deterministic pseudo-random value in [0, 1) for a cell - stable across
    runs for the same (col, row, seed), no random.seed()/global state.
    """
    h = hash((col, row, seed))
    return (h & 0xFFFFFFFF) / 0xFFFFFFFF


def build_matrix(cols: int, rows: int, spacing: float = 10.0,
                  origin: Point3D = (0.0, 0.0, 0.0), seed: int = 0) -> Matrix:
    """Build a cols x rows point matrix dictionary on a regular grid."""
    ox, oy, oz = origin
    matrix: Matrix = {}
    for row in range(rows):
        for col in range(cols):
            matrix[(col, row)] = {
                "origin": (ox + col * spacing, oy + row * spacing, oz),
                "offset": (0.0, 0.0),
                "rotation": 0.0,
                "scale": 1.0,
                "seed": _cell_seed(col, row, seed),
            }
    return matrix


def neighbors(matrix: Matrix, col: int, row: int) -> Dict[str, Cell]:
    """4-neighborhood lookup; missing neighbors (grid edges) are simply absent."""
    candidates = {"N": (col, row + 1), "S": (col, row - 1),
                  "E": (col + 1, row), "W": (col - 1, row)}
    return {name: matrix[key] for name, key in candidates.items() if key in matrix}


def bounds(matrix: Matrix) -> Tuple[int, int, int, int]:
    """(min_col, min_row, max_col, max_row) over all keys."""
    cols = [c for c, _ in matrix]
    rows = [r for _, r in matrix]
    return (min(cols), min(rows), max(cols), max(rows))


def center_key(matrix: Matrix) -> CellKey:
    """Grid key nearest the matrix's center (for radial/attractor-style rules)."""
    min_c, min_r, max_c, max_r = bounds(matrix)
    return (round((min_c + max_c) / 2), round((min_r + max_r) / 2))
