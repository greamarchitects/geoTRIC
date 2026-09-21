"""
Mattric - Rhino entrypoint (v0.1 first draft)

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File").

Builds a 3D point matrix (a flat vertical wall of control points), draws
its columns as untouched "base" profile curves, then applies a
three-attractor bulge rule to a copy of the matrix and draws that
"transformed" set of profile curves alongside it - and lofts the
transformed profiles into the actual wall surface (the assignment's NURBS
wall). Same base/transformed-plus-attractors structure as pattric's
scripts/run_in_rhino.py, one dimension up: pattric grows/rotates/moves a
2D square per cell, mattric bulges a 3D point's depth per cell, then
strings each column of points into a curve and lofts across all of them.

three_point_bulge_rule blends the pull of three attractor points into one
continuous depth field, wrapped in constrain_bulge_rule so no point ever
bulges out past max_bulge world units - the equivalent of pattric's
constrain_to_cell_rule, guaranteeing the effect stays inside a fixed
envelope instead of just hoping the parameters keep it there. Swap in
pattern.radial_bulge_rule for a single-attractor variant instead.

Note on editing + re-running: Rhino's Python engine keeps sys.modules
alive across repeated "Run" calls within the same session, so a plain
`import mattric...` would keep reusing whatever was first imported and
silently ignore later edits to the package's .py files. The reload block
below forces a fresh import every run so edits always take effect without
needing to restart Rhino.
"""

import sys
from pathlib import Path

# Ensure src is importable when run inside Rhino
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force a fresh import of the package every run (see note above).
for _mod_name in [m for m in list(sys.modules) if m == "mattric" or m.startswith("mattric.")]:
    del sys.modules[_mod_name]

from mattric.matrix import build_matrix
from mattric.pattern import apply_rule, three_point_bulge_rule, constrain_bulge_rule
from mattric import rhino_backend as rb


# -----------------------------
# CONFIG
# -----------------------------
COLS, ROWS = 8, 10          # 8 profile curves, each sampled at 10 points up the wall
COL_SPACING = 6.0           # world units between columns (the wall's width direction)
ROW_HEIGHT = 6.0            # world units between rows (the wall's height direction)

# Three attractor points, in (col, row) grid space - spread across the
# 8x10 grid so the resulting bulge field is shaped by all three at once.
ATTRACTORS = [(1, 2), (6, 3), (3, 8)]
ATTRACTOR_MARKER_RADIUS = 1.2

MAX_BULGE = 8.0       # world-unit depth (y) push at/near an attractor
FALLOFF_CELLS = 3.0   # grid-cell radius of each attractor's influence

LOFT_TYPE = "Tight"   # any Rhino.Geometry.LoftType member: Normal, Loose, Straight, Tight, ...

# Optional second wall: a NURBS surface built straight from the matrix's
# control-point net (port of the C++ CreateSurfacesExample) instead of
# lofted through the profile curves. It is pulled toward the points rather
# than passing through them, so it overlaps the lofted wall - leave off
# unless comparing the two.
DRAW_CV_SURFACE = False
U_DEGREE, V_DEGREE = 2, 3

BASE_PROFILE_LAYER = "mattric::base"
TRANSFORMED_PROFILE_LAYER = "mattric::transformed"
ATTRACTOR_LAYER = "mattric::attractors"
WALL_LAYER = "mattric::wall"
CV_WALL_LAYER = "mattric::cv_wall"

BASE_COLOR = (180, 180, 180)         # light gray - the flat, unmodified profiles
TRANSFORMED_COLOR = (20, 90, 220)    # blue - the bulged profiles actually lofted
ATTRACTOR_COLOR = (220, 30, 30)      # red - the points driving the field
WALL_COLOR = (140, 170, 220)         # pale blue - the lofted surface itself


def main():
    # Base and transformed matrices share the same origin - the base
    # profiles stay flat (y=0) as a visual reference for how far the
    # transformed wall has bulged.
    base = build_matrix(COLS, ROWS, col_spacing=COL_SPACING, row_height=ROW_HEIGHT)
    transformed = build_matrix(COLS, ROWS, col_spacing=COL_SPACING, row_height=ROW_HEIGHT)
    rule = constrain_bulge_rule(
        three_point_bulge_rule(ATTRACTORS, max_bulge=MAX_BULGE, falloff_cells=FALLOFF_CELLS),
        max_bulge=MAX_BULGE,
    )
    apply_rule(transformed, rule)

    rb.draw_profile_curves_live(base, COLS, layer=BASE_PROFILE_LAYER,
                                 zoom=False, color=BASE_COLOR)
    transformed_curve_ids = rb.draw_profile_curves_live(
        transformed, COLS, layer=TRANSFORMED_PROFILE_LAYER, zoom=False, color=TRANSFORMED_COLOR)

    attractor_points = [(ax * COL_SPACING, 0.0, ay * ROW_HEIGHT) for ax, ay in ATTRACTORS]
    attractor_ids = rb.draw_markers_live(attractor_points, radius=ATTRACTOR_MARKER_RADIUS,
                                          layer=ATTRACTOR_LAYER, zoom=False, color=ATTRACTOR_COLOR)

    wall_ids = rb.loft_wall_live(transformed_curve_ids, layer=WALL_LAYER, color=WALL_COLOR,
                                  loft_type=LOFT_TYPE)

    cv_wall_id = None
    if DRAW_CV_SURFACE:
        grid = rb.matrix_point_grid(transformed, COLS, ROWS)
        cv_wall_id = rb.nurbs_surface_live(grid, u_degree=U_DEGREE, v_degree=V_DEGREE,
                                            layer=CV_WALL_LAYER, color=WALL_COLOR)

    print(f"Mattric: drew {len(transformed_curve_ids)} base+transformed profile curves "
          f"({COLS} columns x {ROWS} rows each), {len(attractor_ids)} attractor markers "
          f"under '{ATTRACTOR_LAYER}', and lofted {len(wall_ids)} wall surface(s) "
          f"under '{WALL_LAYER}'"
          + (f"; control-point surface {'added' if cv_wall_id else 'FAILED (invalid)'} "
             f"under '{CV_WALL_LAYER}'." if DRAW_CV_SURFACE else "."))


if __name__ == "__main__":
    main()
