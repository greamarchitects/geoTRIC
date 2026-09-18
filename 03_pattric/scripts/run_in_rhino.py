"""
Pattric - Rhino entrypoint (v0.1 first draft)

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File").

Builds a point matrix dictionary, draws it untouched as a "base" state,
then applies one conditional pattern rule to a copy and draws that
"transformed" state directly on top of it (same origin, different layer
color) - so base and result are visible superimposed in the same Rhino
document (see README's v0.1 roadmap: "point matrix dictionary - one
pattern rule - single-state Rhino draw").

three_point_attractor_rule (the default below) blends the pull of three
attractor points into one continuous field: cells near any of the three
grow and turn to face the combined pull direction, easing back to a
resting scale/rotation away from all three (attractor-driven move/scale/
rotate in one rule). It's wrapped in constrain_to_cell_rule so no cell's
drawn square ever grows or shifts past its own spacing x spacing
footprint - transformations stay inside the base grid rectangle, they
never spill into a neighboring cell's territory. Parameters below are
tuned for a visibly strong effect (wide scale range, short falloff, large
pull) rather than a subtle one. The three attractor positions are also
drawn as small circles on their own layer. Swap in
pattern.checker_spin_rule or pattern.radial_grow_rule for the earlier
single-center/checkerboard variants instead.

Note on editing + re-running: Rhino's Python engine keeps sys.modules
alive across repeated "Run" calls within the same session, so a plain
`import pattric...` would keep reusing whatever was first imported and
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
for _mod_name in [m for m in list(sys.modules) if m == "pattric" or m.startswith("pattric.")]:
    del sys.modules[_mod_name]

from pattric.matrix import build_matrix, spacing_for_gap
from pattric.pattern import apply_rule, three_point_attractor_rule, constrain_to_cell_rule
from pattric import rhino_backend as rb


# -----------------------------
# CONFIG
# -----------------------------
COLS, ROWS = 6, 6
CELL_SIZE = 8.0
GAP = 0.0            # world units (mm, assuming a millimeter Rhino doc) between
                     #   adjacent base squares' edges - 0 = squares touch, tiling
                     #   the base grid with no gaps
SPACING = spacing_for_gap(CELL_SIZE, GAP)  # center-to-center distance = CELL_SIZE + GAP
CELL_MARGIN = 0.98   # safety buffer short of the true half-cell_size containment limit

# Three attractor points, in (col, row) grid space - spread across the 6x6
# grid so the resulting field is shaped by all three at once, not one.
ATTRACTORS = [(1, 1), (4, 1), (2, 4)]
ATTRACTOR_MARKER_RADIUS = 1.6

# constrain_to_cell_rule caps the drawn square at CELL_SIZE (its own base
# rectangle) regardless of MAX_SCALE, so growth tops out around 1.0x there -
# the visible contrast instead comes from a low MIN_SCALE (cells shrink hard
# away from all three attractors), a short falloff (sharp near/far contrast),
# and a large rotation/offset swing while a cell still has room to move.
MAX_SCALE = 1.0      # scale at/near an attractor - already the max constrain_to_cell_rule allows
MIN_SCALE = 0.3      # resting scale, away from all three attractors
FALLOFF_CELLS = 2.4  # grid-cell radius of each attractor's influence
PULL = 3.0           # world-unit nudge toward the combined pull direction

BASE_LAYER = "pattric::base"
TRANSFORMED_LAYER = "pattric::transformed"
ATTRACTOR_LAYER = "pattric::attractors"

BASE_COLOR = (180, 180, 180)         # light gray - the unmodified grid, drawn underneath
TRANSFORMED_COLOR = (20, 90, 220)    # blue - the rule's output, drawn on top of it
ATTRACTOR_COLOR = (220, 30, 30)      # red - the points driving the field


def main():
    # Base and transformed matrices share the same origin - drawn directly
    # on top of each other, distinguished by layer color rather than position.
    base = build_matrix(COLS, ROWS, spacing=SPACING)
    transformed = build_matrix(COLS, ROWS, spacing=SPACING)
    rule = constrain_to_cell_rule(
        three_point_attractor_rule(ATTRACTORS, max_scale=MAX_SCALE, min_scale=MIN_SCALE,
                                    falloff_cells=FALLOFF_CELLS, pull=PULL),
        cell_size=CELL_SIZE, margin=CELL_MARGIN,
    )
    apply_rule(transformed, rule)

    base_ids = rb.draw_matrix_live(base, cell_size=CELL_SIZE, layer=BASE_LAYER,
                                    zoom=False, color=BASE_COLOR)
    transformed_ids = rb.draw_matrix_live(transformed, cell_size=CELL_SIZE, layer=TRANSFORMED_LAYER,
                                           zoom=False, color=TRANSFORMED_COLOR)

    attractor_points = [(ax * SPACING, ay * SPACING, 0.0) for ax, ay in ATTRACTORS]
    attractor_ids = rb.draw_markers_live(attractor_points, radius=ATTRACTOR_MARKER_RADIUS,
                                          layer=ATTRACTOR_LAYER, zoom=True, color=ATTRACTOR_COLOR)

    print(f"Pattric: drew {len(base_ids)} base cells under '{BASE_LAYER}', "
          f"{len(transformed_ids)} transformed cells under '{TRANSFORMED_LAYER}' "
          f"({COLS}x{ROWS} each, superimposed), and {len(attractor_ids)} attractor "
          f"markers under '{ATTRACTOR_LAYER}'.")


if __name__ == "__main__":
    main()
