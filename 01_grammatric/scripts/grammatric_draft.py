# Grammatric
# -----------------------------------------------------------------------------
# Intent:
# Input → Transform → Output
# Small rule-based geometric evolution
# Staged layers for assignment-style PDF export
# Grid layout for screenshots / print
#
# TODO (future):
# - Replace the single-symbol curve with Symbol/Rule objects from your package
# - Add recipe JSON loader (seed + rules + params)
# - Export PDF/PNGs automatically
# - Add rule selection strategies (random / conditional / weighted)
# -----------------------------------------------------------------------------

import rhinoscriptsyntax as rs
import math

# -----------------------------
# CONFIG (keep small + editable)
# -----------------------------
STEPS = 10                 # number of derivation stages
CELL_W = 70.0              # grid cell width
CELL_H = 55.0              # grid cell height
COLS = 5                   # grid columns for layout
BASE_LAYER = "grammatric_draft"

# rule parameters (simple + deterministic)
ROT_STEP_DEG = 12.0
SCALE_FACTOR = 0.92
MOVE_LOCAL = (14.0, 6.0, 0.0)   # local translation applied each step


# -----------------------------
# HELPERS
# -----------------------------
def ensure_layer(path):
    """Create nested layer path if missing. Example: 'A::B::C'."""
    if rs.IsLayer(path):
        return path
    parts = path.split("::")
    current = parts[0]
    if not rs.IsLayer(current):
        rs.AddLayer(current)
    for p in parts[1:]:
        nxt = current + "::" + p
        if not rs.IsLayer(nxt):
            rs.AddLayer(p, parent=current)
        current = nxt
    return path


def square(center=(0, 0, 0), size=20.0):
    """Create a 2D square polyline (closed). Returns curve id."""
    x, y, z = center
    h = size / 2.0
    pts = [
        (x - h, y - h, z),
        (x + h, y - h, z),
        (x + h, y + h, z),
        (x - h, y + h, z),
        (x - h, y - h, z),
    ]
    return rs.AddPolyline(pts)


def bbox_center(obj_id):
    """Center point of object bounding box (robust for 2D curve)."""
    bb = rs.BoundingBox(obj_id)
    if not bb:
        return (0, 0, 0)
    xs = [p[0] for p in bb]
    ys = [p[1] for p in bb]
    zs = [p[2] for p in bb]
    return (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs)))


# -----------------------------
# “RULES” (draft grammar logic)
# -----------------------------
def rule_rotate_scale_translate(obj_id, step_i):
    """
    Draft rule:
    - copy the curve
    - rotate around its bbox center (increasing angle)
    - scale around center (exponential decay)
    - translate by a fixed vector (per step)
    Returns: new curve id
    """
    c = bbox_center(obj_id)
    new_id = rs.CopyObject(obj_id)

    rs.RotateObject(new_id, c, ROT_STEP_DEG * (step_i + 1))
    s = SCALE_FACTOR ** (step_i + 1)
    rs.ScaleObject(new_id, c, (s, s, 1.0))
    rs.MoveObject(new_id, MOVE_LOCAL)

    return new_id


def rule_branch_copy(obj_id, step_i):
    """
    Draft “branch” rule:
    - produce two copies with mirrored rotation directions
    Returns: list of curve ids
    """
    c = bbox_center(obj_id)
    a = rs.CopyObject(obj_id)
    b = rs.CopyObject(obj_id)

    ang = ROT_STEP_DEG * (step_i + 1)
    rs.RotateObject(a, c, +ang)
    rs.RotateObject(b, c, -ang)

    rs.MoveObject(a, (MOVE_LOCAL[0], 0.0, 0.0))
    rs.MoveObject(b, (0.0, MOVE_LOCAL[1], 0.0))

    return [a, b]


# -----------------------------
# MAIN
# -----------------------------
def main():
    # Clean start (optional)
    ensure_layer(BASE_LAYER)

    # Seed (input)
    seed = square(center=(0, 0, 0), size=22.0)

    # Keep track of current “active” objects (grammar state)
    current = [seed]

    # Stage 0 output
    stage0_layer = ensure_layer(f"{BASE_LAYER}::stage_{0:02d}")
    for obj in current:
        rs.ObjectLayer(obj, stage0_layer)

    # Derivation loop (processing + staged output)
    for i in range(1, STEPS + 1):
        stage_layer = ensure_layer(f"{BASE_LAYER}::stage_{i:02d}")

        # Simple deterministic alternation between two rule types
        next_state = []
        for obj in current:
            if i % 2 == 0:
                next_state.append(rule_rotate_scale_translate(obj, i))
            else:
                next_state.extend(rule_branch_copy(obj, i))

        # Assign to layer
        for obj in next_state:
            rs.ObjectLayer(obj, stage_layer)

        # Replace state
        current = next_state

    # Layout stages into a grid for quick screenshots/printing
    # (Moves entire stage layers by an offset)
    for i in range(0, STEPS + 1):
        col = i % COLS
        row = i // COLS
        dx = col * CELL_W
        dy = -row * CELL_H
        layer = f"{BASE_LAYER}::stage_{i:02d}"
        objs = rs.ObjectsByLayer(layer) or []
        if objs:
            rs.MoveObjects(objs, (dx, dy, 0.0))

    rs.ZoomExtents()
    print("Done: created staged layers under", BASE_LAYER)


if __name__ == "__main__":
    main()