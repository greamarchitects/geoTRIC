"""
Skeletric - Rhino entrypoint

Run this from inside Rhino (Tools > EditPythonScript / the ScriptEditor in
Rhino 7 SR14+/8, "Run File").

- If you pre-select curve(s) before running, or pick them when prompted,
  the first selected curve is used as the spine.
- If nothing is selected/picked, a demo rectangle bone is created so the
  script still produces results with no manual input.
- You'll then be prompted to pick an attractor point (Enter/Esc skips it
  and falls back to the spine's centroid). Circles near the attractor grow
  up to CIRCLE_MAX_RADIUS and ease back down to CIRCLE_RADIUS by
  CIRCLE_FALLOFF_DIST away from it.

Output is filed into layers under BASE_LAYER (skeletric::spine,
skeletric::ribs, skeletric::circles, skeletric::attractor) via
skeletric.rhino_backend, so a run is easy to find and toggle in the Layers
panel instead of landing unlabeled on whatever layer was current.

Note on editing + re-running: Rhino's Python engine keeps sys.modules alive
across repeated "Run" calls within the same session, so a plain `import
skeletric...` would keep reusing whatever was first imported and silently
ignore later edits to bones.py/derive.py/rhino_backend.py (this is what an
AttributeError for a function that's clearly in the file usually means).
The reload block below forces a fresh import every run so edits always
take effect without needing to restart Rhino.
"""

import sys
from pathlib import Path

# Ensure src/python is importable when run inside Rhino
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "python"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force a fresh import of the package every run (see note above).
for _mod_name in [m for m in list(sys.modules) if m == "skeletric" or m.startswith("skeletric.")]:
    del sys.modules[_mod_name]

import rhinoscriptsyntax as rs

from skeletric import bones
from skeletric import derive
from skeletric import rhino_backend as rb


# -----------------------------
# CONFIG
# -----------------------------
BASE_LAYER = "skeletric"
SAMPLE_N = 25       # points to sample along the spine
RIB_LEN = 5.0
RIB_EVERY = 2
CIRCLE_RADIUS = 0.1        # normal ("resting") radius, far from the attractor
CIRCLE_MAX_RADIUS = 2.50    # radius right at the attractor
CIRCLE_FALLOFF_DIST = 8.0   # distance beyond which radius is back to CIRCLE_RADIUS
CIRCLE_EVERY = 4

DEMO_WIDTH = 12.0
DEMO_HEIGHT = 6.0


def _points_centroid(pts):
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    return (x, y, 0.0)


def _pick_attractor(spine, pts):
    """User-picked point, falling back to the spine's centroid (matching
    the same prompt-or-fallback pattern as bones.get_bones())."""
    picked = rs.GetPoint("Pick attractor point (Enter/Esc for spine center)")
    if picked:
        return picked
    centroid = bones.curve_centroid(spine)  # None for an open curve
    return centroid if centroid else _points_centroid(pts)


def main():
    crvs = bones.get_bones()
    if not crvs:
        rect = bones.make_rectangle_bone(DEMO_WIDTH, DEMO_HEIGHT)
        rb.file_objects([rect], f"{BASE_LAYER}::bone")
        crvs = [rect]

    spine = crvs[0]
    pts = bones.sample_curve(spine, n=SAMPLE_N)

    spine_line = derive.polyline(pts)
    rb.file_objects([spine_line], f"{BASE_LAYER}::spine")

    ribs = derive.ribs_along_spine(pts, rib_len=RIB_LEN, every=RIB_EVERY)
    rb.file_objects(ribs, f"{BASE_LAYER}::ribs")

    attractor = _pick_attractor(spine, pts)
    attractor_pt = rs.AddPoint(attractor)
    rb.file_objects([attractor_pt], f"{BASE_LAYER}::attractor")

    circles = derive.circles_on_points_attractor(
        pts, attractor,
        base_radius=CIRCLE_RADIUS, max_radius=CIRCLE_MAX_RADIUS,
        falloff_dist=CIRCLE_FALLOFF_DIST, every=CIRCLE_EVERY,
    )
    rb.file_objects(circles, f"{BASE_LAYER}::circles")

    rs.ZoomExtents()
    print(
        f"Skeletric: spine ({len(pts)} pts), "
        f"{len(ribs)} ribs, {len(circles)} circles "
        f"(radius {CIRCLE_RADIUS}-{CIRCLE_MAX_RADIUS} around attractor {attractor}) "
        f"under '{BASE_LAYER}::*'."
    )


if __name__ == "__main__":
    main()
