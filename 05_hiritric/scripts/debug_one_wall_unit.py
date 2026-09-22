"""
Hiritric - one-wall-unit diagnostic

Run this from inside Rhino instead of run_in_rhino.py when the wall isn't
showing up: it builds ONE tower (state 1's START parameters) and then tries
to build exactly ONE wall unit near the tower's base, printing every step -
whether the tower closed, the outer/inner box sizes, whether each boolean
returned anything, how many fragments it returned and how big each one was,
and whether the kept piece was rejected as degenerate. Whatever step it
fails at tells you which of the fallbacks in rhino_backend.py to look at
next. Leaves the tower body and, if it built, the one wall unit, both
visible, on layer "hiritric::debug".

Usage: open it in Rhino's Script Editor and Run File, or from the command
line paste the reported CELL_KEY into WALL_KEY below to inspect a
different cell (e.g. one near the top, where twist/taper is strongest).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
for _mod_name in [m for m in list(sys.modules) if m == "hiritric" or m.startswith("hiritric.")]:
    del sys.modules[_mod_name]

import rhinoscriptsyntax as rs

from hiritric.matrix import build_matrix
from hiritric.pattern import apply_rule, attractor_tower_rule
from hiritric.rhino_backend import bbox_diagonal, draw_tower, ensure_layer, surface_sampler
from hiritric.wall import wall_unit_corners

# The same START parameters run_in_rhino.py's state 1 uses.
PARAMS = {
    "height": 120.0, "floors": 8, "plan_points": 24,
    "radius_x": 20.0, "radius_y": 20.0, "squareness": 2.4,
    "taper": 1.0, "bulge": 0.0, "twist": 0.0,
    "attractors": [(26.0, 0.0, 25.0), (-8.0, 26.0, 60.0), (0.0, -26.0, 95.0)],
    "falloff": 34.0, "max_tilt": 25.0, "max_depth": 4.0, "void_chance": 0.0,
    "wall_thickness": 1.2,
}
WALL_COLS, WALL_FLOORS = 8, 10
WALL_KEY = None   # e.g. (0, 0); None picks the middle of the grid


def main():
    from hiritric.tower import tower_floor_points

    layer = "hiritric::debug"
    ensure_layer(layer)
    origin = (0.0, 0.0, 0.0)

    print("1. lofting the tower...")
    body, skin, closed = draw_tower(tower_floor_points(PARAMS, origin), layer + "::tower",
                                    (150, 150, 150))
    if skin is None:
        print("   FAILED: every loft attempt (Normal/Loose/Straight, smooth/polyline floors) "
              "returned nothing. The floor curves themselves are the next thing to check.")
        return
    print("   tower body: %s, closed: %s" % (body, closed))
    if not closed:
        print("   STOP: the body is open, so a boolean intersection with it will not work. "
              "This is why no wall units can show - fix the cap first.")
        return

    print("2. sampling the surface into a %dx%d wall matrix..." % (WALL_COLS, WALL_FLOORS))
    sampler = surface_sampler(skin, (origin[0], origin[1]))
    wall_matrix = build_matrix(WALL_COLS, WALL_FLOORS, sampler, seed=0)
    apply_rule(wall_matrix, attractor_tower_rule(
        PARAMS["attractors"], falloff_dist=PARAMS["falloff"], max_tilt=PARAMS["max_tilt"],
        max_depth=PARAMS["max_depth"], void_chance=PARAMS["void_chance"]))
    rs.DeleteObject(skin)

    key = WALL_KEY or (WALL_COLS // 2, WALL_FLOORS // 2)
    if key not in wall_matrix:
        print("   WALL_KEY %r is not in the matrix (0..%d, 0..%d) - pick one from that range."
              % (key, WALL_COLS - 1, WALL_FLOORS - 1))
        return
    cell = wall_matrix[key]
    print("   using cell %r: point=%s cell_w=%.2f cell_h=%.2f inset_ratio=%.3f"
          % (key, tuple(round(c, 2) for c in cell["point"]), cell["cell_w"], cell["cell_h"],
             cell["inset_ratio"]))

    print("3. building the outer and inner boxes...")
    outer_c, inner_c = wall_unit_corners(cell, PARAMS["wall_thickness"], 0.96)
    outer = rs.AddBox(outer_c)
    inner = rs.AddBox(inner_c)
    print("   outer box: %s (diag %.3f)  inner box: %s (diag %.3f)"
          % (outer, bbox_diagonal(outer) if outer else 0.0,
             inner, bbox_diagonal(inner) if inner else 0.0))
    if not (outer and inner):
        print("   FAILED: AddBox returned nothing for one of the boxes - the 8 corners "
              "(see wall.py box_corners) are not forming a valid box. Print outer_c/inner_c "
              "below and check them by eye.")
        print("   outer_c =", outer_c)
        print("   inner_c =", inner_c)
        return
    outer_diag = bbox_diagonal(outer)

    print("4. BooleanDifference(outer, inner)...")
    frame = rs.BooleanDifference([outer], [inner], delete_input=True)
    print("   result:", frame)
    if not frame:
        print("   FAILED: the subtraction returned nothing - inner is probably not fully "
              "enclosed by outer, or the two overlap in a way Rhino's boolean engine rejects. "
              "Try File > Properties > Units > Absolute tolerance: a coarser tolerance than the "
              "geometry's own scale is a common cause.")
        return
    for guid in frame:
        rs.ObjectLayer(guid, layer + "::frame")
        print("   frame piece %s: diag %.3f" % (guid, bbox_diagonal(guid)))

    print("5. BooleanIntersection(frame, body)...")
    units = rs.BooleanIntersection(frame, [body], delete_input=False)
    print("   result:", units)
    if not units:
        print("   FAILED: the intersection returned nothing - the frame and the tower body "
              "may not actually overlap (check the outer box really reaches the surface: "
              "increase wall_thickness or the reach margin in wall.py), or this is a tolerance "
              "issue like step 4's.")
        rs.DeleteObjects(frame)
        return
    for guid in units:
        print("   fragment %s: diag %.3f" % (guid, bbox_diagonal(guid)))
    rs.DeleteObjects(frame)

    kept = max(units, key=bbox_diagonal)
    for guid in units:
        if guid != kept:
            rs.DeleteObject(guid)
    ratio = bbox_diagonal(kept) / outer_diag if outer_diag else 0.0
    print("6. kept the largest fragment %s (diag ratio to outer box: %.3f)" % (kept, ratio))
    if ratio < 0.2:
        print("   This would be REJECTED as degenerate by draw_wall_unit (ratio < 0.2) - "
              "the boolean 'succeeded' but produced almost nothing. That is very likely why "
              "the wall doesn't show even without a printed error.")
    else:
        print("   Looks like a real wall unit. If you still don't see it in the viewport, "
              "check layer '%s::wall' visibility and the camera position - ZoomExtents." % layer)
    rs.ObjectLayer(kept, layer + "::wall")
    rs.ObjectColor(kept, (220, 60, 60))
    rs.ZoomExtents()


if __name__ == "__main__":
    main()
