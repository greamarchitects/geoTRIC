"""
Pattric - Rhino entrypoint (v0.1 first draft)

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File").

Builds a point matrix dictionary, applies one conditional pattern rule
across every cell, and draws the result as 2D linework - the first
concrete output for the pattric assignment (see README's v0.1 roadmap:
"point matrix dictionary - one pattern rule - single-state Rhino draw").

checker_spin_rule (the default below) alternates rotation direction in a
checkerboard (col+row parity - conditional execution), scales each cell
from its own deterministic seed (randomization), and nudges its position
with a seeded (x, y) jitter (moving) - covering move/scale/rotate/
randomize from the assignment brief in one rule. Swap in
pattern.radial_grow_rule for an attractor-style variant instead (reuses
skeletric's falloff shape against grid distance).

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

from pattric.matrix import build_matrix
from pattric.pattern import apply_rule, checker_spin_rule
from pattric import rhino_backend as rb


# -----------------------------
# CONFIG
# -----------------------------
COLS, ROWS = 8, 6
SPACING = 10.0
CELL_SIZE = 8.0

ROT_STEP = 20.0      # degrees, checkerboard rotation
SCALE_STEP = 0.35    # +/- fraction of scale driven by each cell's seed
JITTER = 1.5         # +/- units of seeded (x, y) position nudge

BASE_LAYER = "pattric"


def main():
    matrix = build_matrix(COLS, ROWS, spacing=SPACING)
    apply_rule(matrix, checker_spin_rule(rot_step=ROT_STEP, scale_step=SCALE_STEP, jitter=JITTER))

    ids = rb.draw_matrix_live(matrix, cell_size=CELL_SIZE, layer=BASE_LAYER)
    print(f"Pattric: drew {len(ids)} cells ({COLS}x{ROWS}) under '{BASE_LAYER}'.")


if __name__ == "__main__":
    main()
