"""
Hiritric - Rhino entrypoint (v0.1 first draft)

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File").

Builds a series of modular towers. Each is a NURBS envelope - a loft through
floor plans that taper, bulge and twist - capped top and bottom into a
closed polysurface. The envelope is sampled in its (U, V) parameter space
into a dictionary keyed (col, row) - the surface matrix - where every cell
holds the surface's own point, normal and tangents. Attractor points tilt
each cell's normal, and a designed module - a perforated frustum frame,
itself a closed polysurface built from lofts - is built along the tilted
normal, sized, opened and colored by how strongly the attractors act on that
cell. The wall itself is defined floor by floor by perforated units - closed
polysurfaces reused from mattric - cut off by the tower body. The parameters are interpolated from START to END over several states,
giving a series of towers laid out in a row.

Same pipeline shape as pattric/mattric - build a matrix, apply one rule,
draw - with the logic in src/hiritric/ (vec, tower, matrix, pattern, module,
color, states, and rhino_backend, the only module that touches Rhino). This
file holds the configuration and the top-level pipeline. For the one-file
version the assignment upload needs, run scripts/bundle_single_file.py.

Note on editing + re-running: Rhino's Python engine keeps sys.modules alive
across repeated "Run" calls within the same session, so a plain
`import hiritric...` would keep reusing whatever was first imported and
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
for _mod_name in [m for m in list(sys.modules) if m == "hiritric" or m.startswith("hiritric.")]:
    del sys.modules[_mod_name]

from hiritric.color import GRADIENTS, gradient
from hiritric.matrix import build_matrix
from hiritric.pattern import apply_rule, attractor_tower_rule
from hiritric.rhino_backend import (delete_object, draw_attractors, draw_module, draw_tower,
                                    draw_wall_unit, progress, redraw_off, redraw_on,
                                    set_layer_visible, set_view, surface_sampler)
from hiritric.states import build_states
from hiritric.tower import tower_floor_points
from hiritric.vec import add
from hiritric.wall import wall_unit_corners


# ----------------------------------------------------------------------
#  1. CONFIG
# ----------------------------------------------------------------------
import time
import traceback
from collections import Counter

# QUALITY sets how big a run is. "draft" builds a lighter version of the whole
# series (fewer states, coarser grids, meshes for the louvers) so a first run
# finishes quickly and shows the shape; switch to "final" for the full one.
QUALITY = "draft"
PRESETS = {
    "draft": {"N_STATES": 3, "COLS": 12, "ROWS": 16, "WALL_COLS": 8, "AS_POLYSURFACE": False},
    "final": {"N_STATES": 5, "COLS": 18, "ROWS": 24, "WALL_COLS": 12, "AS_POLYSURFACE": True},
}
N_STATES = PRESETS[QUALITY]["N_STATES"]
COLS, ROWS = PRESETS[QUALITY]["COLS"], PRESETS[QUALITY]["ROWS"]   # louver modules around x up the tower
WALL_COLS = PRESETS[QUALITY]["WALL_COLS"]                          # wall units around the tower
AS_POLYSURFACE = PRESETS[QUALITY]["AS_POLYSURFACE"]   # louvers as closed lofted polysurfaces; False = meshes, ~10x faster
STATE_SPACING = 90.0        # world units between towers in the row
SEED = 0
GRADIENT = "ember"          # louver modules' color: key into GRADIENTS (color.py)

# The wall: one perforated unit per cell, WALL_COLS units around the tower x
# one ring per floor-to-floor band. The ring count is NOT a free setting - it
# is derived from params["floors"] in build_state (int(floors) - 1), so a row
# of wall units always sits in the surface *between two floors*, centered at
# the midpoint of that band (tower_floor_points places control floor f at
# v = f/(floors-1), evenly spaced, so band b of floors-1 sits at
# v = (b+0.5)/(floors-1) - exactly halfway between floor b and floor b+1).
# Each unit is a frame with an opening (mattric's perforated unit) cut off by
# the tower body, so it is a closed polysurface whose outer face is a piece of
# the tower surface, and it is built on the cell's own local tangent/normal
# frame (not world axes), so it follows the tower's curvature and twist at
# that point - it stays correct on a round tower, corner cases included: the
# grid wraps at the seam (build_matrix's neighbor lookup is `(col+1) % cols`),
# so the last column measures back to column 0 with no gap or overlap.
# Openings widen near attractors (the rule's inset_ratio).
BUILD_WALL_UNITS = True
WALL_FILL = 0.96            # unit size / its cell; < 1 leaves a thin seam between units
WALL_GRADIENT = "slate"     # wall units' color, by attractor influence
SHOW_TOWER_BODY = False     # the body is the units' cutter; shown, it would sit flush with them.
                            #   Kept visible anyway if any wall unit fails, so the shape never has holes.
VIEW_MODE = "Shaded"        # Shaded, Rendered, Ghosted, Arctic, Pen, Artistic, ...
ATTRACTOR_RADIUS = 2.0
ATTRACTOR_COLOR = (255, 255, 255)
TOWER_LAYER_COLOR = (150, 150, 150)

# One state = one dictionary. Numbers and lists of numbers are interpolated
# from START to END; attractors are relative to each tower's own origin.
START = {
    # tower envelope
    "height": 120.0, "floors": 8, "plan_points": 24,
    "radius_x": 20.0, "radius_y": 20.0,
    "squareness": 2.4,          # 2 = ellipse, ~4 = rounded square
    "taper": 1.0, "bulge": 0.0, "twist": 0.0,
    # attractors (x, y, z) relative to the tower origin - just off the facade
    "attractors": [(26.0, 0.0, 25.0), (-8.0, 26.0, 60.0), (0.0, -26.0, 95.0)],
    # field rule - falloff is a world-unit radius of influence around each
    # attractor; 55 gives a real spread of influence across the tower (median
    # ~0.5, not saturated) for a ~126-unit circumference, 120-unit-tall tower
    # with only 3 attractors - much smaller (e.g. 34) leaves 3/4 of the tower
    # at influence < 0.3, reading as "the rule does nothing" even though the
    # math is correct - see the "If the field looks flat" note below.
    "falloff": 55.0, "max_tilt": 25.0, "max_depth": 4.0, "void_chance": 0.0,
    # wall units: how far in from the tower surface they reach
    "wall_thickness": 1.2,
}
END = {
    "height": 150.0, "floors": 8, "plan_points": 24,
    "radius_x": 20.0, "radius_y": 20.0,
    "squareness": 4.5,
    "taper": 0.55, "bulge": 0.12, "twist": 100.0,
    "attractors": [(26.0, 0.0, 120.0), (-8.0, 26.0, 70.0), (0.0, -26.0, 30.0)],
    "falloff": 65.0, "max_tilt": 65.0, "max_depth": 9.0, "void_chance": 0.35,
    "wall_thickness": 2.4,
}


# ----------------------------------------------------------------------
# 10. PIPELINE  - the whole run, top to bottom
# ----------------------------------------------------------------------
def attempt(errors, label, function, *args):
    """
    Run one drawing call; if it raises, count the error under `label`, print
    the first one of each kind, and return None - so a single bad unit or
    module never stops the rest of the run.
    """
    try:
        return function(*args)
    except Exception as exc:
        errors[label] += 1
        if errors[label] == 1:
            print("Hiritric: first %s error - %s: %s" % (label, type(exc).__name__, exc))
        return None


def build_state(index, params, origin, errors):
    """Build and draw one tower state at `origin`. Returns (wall units, modules, voids)."""
    layer = "hiritric::state_%02d" % (index + 1)
    tag = "Hiritric: state %d/%d" % (index + 1, N_STATES)

    # 1. tower: lofted through the floor plans, capped top and bottom into a
    #    closed polysurface; the bare loft surface is kept only to sample from
    progress(tag + " - lofting the tower...", echo=False)
    body, skin, closed = draw_tower(
        tower_floor_points(params, origin), layer + "::tower", TOWER_LAYER_COLOR)
    if skin is None:
        print(tag + " - loft failed with every method, skipped.")
        return 0, 0, 0
    if not closed:
        print(tag + " - tower body is not closed (cap failed); no wall units can be cut.")

    # 2. surface -> two matrix dictionaries, sampled in (U, V): one cell per
    #    wall unit, one per louver module. wall_floors is the number of
    #    floor-to-floor bands (floors - 1), NOT an independent setting - so
    #    each row of wall units sits in the surface between two floors,
    #    centered on that band's midpoint (see the CONFIG comment above).
    progress(tag + " - sampling the surface...", echo=False)
    sampler = surface_sampler(skin, (origin[0], origin[1]))
    wall_floors = max(2, int(params["floors"]) - 1)  # build_matrix needs >= 2 rows
    wall_matrix = build_matrix(WALL_COLS, wall_floors, sampler, seed=SEED)
    matrix = build_matrix(COLS, ROWS, sampler, seed=SEED)
    delete_object(skin)

    # 3. attractor rule on both: the wall matrix takes its opening size
    #    (inset_ratio) and color position from it, the module matrix everything
    attractors = [add(a, origin) for a in params["attractors"]]
    rule = attractor_tower_rule(
        attractors, falloff_dist=params["falloff"], max_tilt=params["max_tilt"],
        max_depth=params["max_depth"], void_chance=params["void_chance"])
    apply_rule(wall_matrix, rule)
    apply_rule(matrix, rule)

    # 4. wall: one closed perforated unit per cell, floor by floor
    walls = 0
    if BUILD_WALL_UNITS and closed:
        wall_stops = GRADIENTS[WALL_GRADIENT]
        for n, key in enumerate(sorted(wall_matrix, key=lambda k: (k[1], k[0])), 1):
            progress("%s - wall unit %d/%d" % (tag, n, len(wall_matrix)), echo=False)
            cell = wall_matrix[key]
            outer, inner = wall_unit_corners(cell, params["wall_thickness"], WALL_FILL)
            unit = attempt(errors, "wall unit", draw_wall_unit, outer, inner, body,
                           layer + "::wall", gradient(cell["color_t"], wall_stops))
            walls += unit is not None
        if walls < len(wall_matrix):
            print("%s - %d of %d wall units failed; leaving the tower body visible instead."
                  % (tag, len(wall_matrix) - walls, len(wall_matrix)))
        elif not SHOW_TOWER_BODY:
            set_layer_visible(layer + "::tower", False)

    # 5. one louver module per active cell, colored along the gradient
    stops = GRADIENTS[GRADIENT]
    active_count = drawn = voids = 0
    for n, key in enumerate(sorted(matrix), 1):
        progress("%s - louver module %d/%d" % (tag, n, len(matrix)), echo=False)
        cell = matrix[key]
        if not cell["active"]:
            voids += 1
            continue
        active_count += 1
        module = attempt(errors, "louver module", draw_module, cell, layer + "::modules",
                         gradient(cell["color_t"], stops), AS_POLYSURFACE)
        drawn += module is not None
    if drawn < active_count:
        print("%s - %d of %d louver modules failed to build (silently, not an exception - "
              "draw_module/module_polysurface returned None)."
              % (tag, active_count - drawn, active_count))

    attempt(errors, "attractor marker", draw_attractors, attractors, ATTRACTOR_RADIUS,
            layer + "::attractors", ATTRACTOR_COLOR)
    return walls, drawn, voids


def main():
    started = time.time()
    errors = Counter()
    states = build_states(START, END, N_STATES)
    built = 0
    wall_floors_0 = max(2, int(states[0]["floors"]) - 1)
    print("Hiritric: %d states, quality '%s' (%d wall units and %d louver cells per state, "
          "%d floor-to-floor wall rings)."
          % (len(states), QUALITY, WALL_COLS * wall_floors_0, COLS * ROWS, wall_floors_0))

    redraw_off()        # no viewport redraw per object - the difference between seconds and minutes
    try:
        for index, params in enumerate(states):
            origin = (index * STATE_SPACING, 0.0, 0.0)
            try:
                walls, drawn, voids = build_state(index, params, origin, errors)
            except Exception:
                errors["state"] += 1
                print("Hiritric: state %d/%d failed - carrying on with the next one.\n%s"
                      % (index + 1, N_STATES, traceback.format_exc()))
                continue
            built += 1
            print("Hiritric: state %d/%d - %d wall units, %d modules, %d voids "
                  "(twist %.0f deg, taper %.2f)."
                  % (index + 1, N_STATES, walls, drawn, voids, params["twist"], params["taper"]))
    finally:
        redraw_on()     # always hand Rhino its viewports back, even after an error
    set_view(VIEW_MODE)

    summary = ", ".join("%d %s errors" % (count, label) for label, count in sorted(errors.items()))
    print("Hiritric: built %d of %d states in %.0f s%s."
          % (built, N_STATES, time.time() - started, " (" + summary + ")" if summary else ""))


if __name__ == "__main__":
    main()
