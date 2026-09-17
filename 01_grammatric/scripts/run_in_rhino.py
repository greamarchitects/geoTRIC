"""
Grammatric - Rhino entrypoint

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File"). It builds a small shape-grammar derivation
with the grammatric package and draws it via grammatric.rhino_backend -
no drawing logic lives in this script anymore, it only wires seed + rule
+ derivation together and calls the backend.

Two views are drawn side by side so you can see the same derivation two
ways (matches the README's "staged layers" + "grid layout" goals):

  grammatric::spiral   - every stage overlaid at the same center, so the
                          derivation reads as a single nested spiral of
                          rotated, shrinking squares (a true spiral - the
                          seed's centroid never moves, only rotate+scale
                          are applied, so nothing drifts off-center).
  grammatric::grid      - the same stages laid out one-per-cell in a grid,
                          offset clear of the spiral, for screenshots/print
                          where you want to compare stages individually.

See recipes/spiral_square.json for the parameters used here.

Note on editing + re-running: Rhino's Python engine keeps sys.modules alive
across repeated "Run" calls within the same session, so a plain `import
grammatric...` would keep reusing whatever was first imported and silently
ignore later edits to the package's .py files (this is what an
AttributeError for something that's clearly in the file usually means).
The reload block below forces a fresh import every run so edits always
take effect without needing to restart Rhino.
"""

import sys
from pathlib import Path

# Ensure src is importable when run inside Rhino
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force a fresh import of the package every run (see note above).
for _mod_name in [m for m in list(sys.modules) if m == "grammatric" or m.startswith("grammatric.")]:
    del sys.modules[_mod_name]

import rhinoscriptsyntax as rs

from grammatric.symbols import make_square
from grammatric.transforms import rotate_shape, scale_shape
from grammatric.rules import Rule
from grammatric.derivation import Derivation
from grammatric import rhino_backend as rb


# -----------------------------
# CONFIG (mirrors recipes/spiral_square.json)
# -----------------------------
SEED_SIZE = 24.0
STEPS = 10
ROT_STEP_DEG = 15.0
SCALE_FACTOR = 0.88

BASE_LAYER = "grammatric"
GRID_COLS = 4
GRID_CELL_W = 80.0
GRID_CELL_H = 60.0
GRID_OFFSET_X = 300.0  # keep the grid view clear of the spiral view


# -----------------------------
# RULE
# -----------------------------
def spiral_rule(symbol, step_i):
    """
    Rotate then scale the symbol's *current* shape in place (both pivot on
    the shape's own centroid, which this rule never translates), so
    repeated application nests successively smaller, rotated copies around
    one fixed center - a spiral of squares. Exactly one symbol out, so the
    derivation stays single-branch (no exponential growth across steps).
    """
    shape = rotate_shape(symbol.shape, ROT_STEP_DEG)
    shape = scale_shape(shape, SCALE_FACTOR)
    return [symbol.with_shape(shape)]


# -----------------------------
# MAIN
# -----------------------------
def main():
    seed = [make_square(size=SEED_SIZE, name="A")]
    rules = [Rule(target="A", replacement=spiral_rule)]
    history = Derivation(seed=seed, rules=rules).run(STEPS)

    # Spiral view: every stage overlaid at the same center (cols=1, no cell
    # size -> grid_offset() always returns (0, 0)).
    rb.draw_derivation_live(
        history,
        layer_prefix=f"{BASE_LAYER}::spiral",
        cols=1, cell_w=0.0, cell_h=0.0,
        zoom=False,
    )

    # Grid view: one stage per cell, moved clear of the spiral view.
    grid_ids = rb.draw_derivation_live(
        history,
        layer_prefix=f"{BASE_LAYER}::grid",
        cols=GRID_COLS, cell_w=GRID_CELL_W, cell_h=GRID_CELL_H,
        zoom=False,
    )
    if grid_ids:
        rs.MoveObjects(grid_ids, (GRID_OFFSET_X, 0.0, 0.0))

    rs.ZoomExtents()
    print(f"Grammatric: drew {STEPS + 1} stages "
          f"under '{BASE_LAYER}::spiral' and '{BASE_LAYER}::grid'.")


if __name__ == "__main__":
    main()
