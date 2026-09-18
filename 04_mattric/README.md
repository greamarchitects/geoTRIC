# Mattric

Mattric is a 3D wall-generation framework built around a **3D Point Matrix
Dictionary** — the same `(col, row)`-keyed dictionary idea as
[pattric](../03_pattric), extended with a z axis. Columns of points become
NURBS profile curves; those curves are lofted (or swept) into a single
wall surface. Where pattric stopped at 2D linework, mattric builds it up
into surface geometry.

------------------------------------------------------------------------

## Where this sits in the series

Fourth step, after [grammatric](../01_grammatric), [skeletric](../02_skeletric),
and [pattric](../03_pattric):

- **grammatric** — a single symbol, evolved through named *rules* applied
  in discrete *derivation* steps (one lineage, staged over time).
- **skeletric** — a *bone* (sampled curve points), with derived linework
  weighted by distance to an attractor (one structure, varied continuously
  over space).
- **pattric** — many cells at once, addressed by grid coordinate in a
  *dictionary*, each free to vary independently under shared rules (a
  field, varied over both space and state) — 2D linework only.
- **mattric** — pattric's dictionary-indexed matrix, one dimension up:
  each column of 3D points becomes a NURBS profile curve, and the set of
  profile curves is lofted/swept into a wall *surface*.

The per-cell attractor-falloff idea from pattric/skeletric carries over
directly: a rule reads a cell's grid position, measures its distance to
one or more attractor points, and displaces the cell (here, along the
wall's depth axis) by an eased amount — the only real change is that the
displaced points get strung into curves and lofted, instead of being
drawn as squares.

------------------------------------------------------------------------

## Assignment Requirements

(From the geoTRIC-level roadmap's mattric entry — see the [top-level
README](../README.md).)

- Generate a **3D point matrix**, dictionary-indexed (`{(col, row): cell}`),
  same mechanic as pattric's matrix but with a z (height) component.
- **Modify the matrix via attractor points** — conditional, per-cell
  displacement based on distance to one or more field points.
- **Loop through the matrix to build curves** — one NURBS curve per
  column (or row).
- **Loft or sweep those curves into a surface** — the wall itself.
- Produce **structured 3D geometry** (a surface, not just linework) as the
  deliverable.

------------------------------------------------------------------------

## Core Representation

```python
matrix = {
    (col, row): {
        "origin": (x, y, z),        # fixed base grid position -
                                     #   col along wall width (x),
                                     #   row climbing wall height (z)
        "offset": (0.0, 0.0, 0.0),  # rule-driven displacement from origin
                                     #   (bulge direction is y, the wall's
                                     #   depth/thickness axis)
        "seed": 0.1234,             # per-cell randomization source
    }
    for col in range(cols)
    for row in range(rows)
}
```

A **column** (`matrix.column_keys(matrix, col)`, sorted bottom to top) is
one vertical profile curve. A **row** (`row_keys`, sorted left to right)
is one horizontal course — an alternative pair of rail curves for a
two-rail sweep instead of a straight loft across every column.

**Implemented so far** (v0.1 first draft, `src/mattric/`):
- `matrix.py` — `build_matrix` (flat 3D grid of points), `column_keys` /
  `row_keys` (ordered per-column / per-row key lists, for building
  curves), `bounds`, `center_key`.
- `pattern.py` — `apply_rule` + rules: `radial_bulge_rule` (single
  attractor, same smoothstep falloff as skeletric/pattric),
  `three_point_bulge_rule` (the same falloff blended across three
  attractor points into one continuous depth field — the current
  default), and `constrain_bulge_rule` (wraps any rule so a cell's
  y-offset never exceeds a fixed `max_bulge`, regardless of what the
  wrapped rule computes).
- `rhino_backend.py` — `cell_point` (pure geometry: origin + offset),
  `draw_profile_curves_live` / `draw_course_curves_live` (one
  `rs.AddInterpCurve` per column / row), `loft_wall_live`
  (`rs.AddLoft` across the profile curves), and `draw_markers_live`
  (small circles marking attractor positions).
- `scripts/run_in_rhino.py` — the working entrypoint: builds an 8×10 flat
  base matrix and a second copy with `three_point_bulge_rule` (wrapped in
  `constrain_bulge_rule`) applied, draws both sets of profile curves
  (`mattric::base` gray, `mattric::transformed` blue), the three attractor
  markers (`mattric::attractors` red), and lofts the transformed profiles
  into the actual wall surface (`mattric::wall`).

Not yet built: `export.py` (Letter/Landscape or 3D-view page setup,
line-weight/render-style helpers) and any sequencing of multiple wall
states — this first draft proves the matrix → rule → curves → loft path
end to end for one state.

------------------------------------------------------------------------

## Pipeline

What `scripts/run_in_rhino.py` actually does, step by step:

```
INPUT   cols, rows, col_spacing, row_height, attractors[3], max_bulge, falloff_cells

base        = build_matrix(cols, rows, col_spacing, row_height)  # flat grid, offset=(0,0,0)
transformed = build_matrix(cols, rows, col_spacing, row_height)  # identical second copy

rule = constrain_bulge_rule(
           three_point_bulge_rule(attractors, max_bulge, falloff_cells),
           max_bulge)

FOR EACH (col, row) -> cell IN transformed, sorted by key:        # apply_rule
    influence_total = 0
    FOR EACH attractor IN attractors:
        d = grid_distance((col, row), attractor)
        influence_total += smoothstep_falloff(d, falloff_cells)   # 1 at attractor, 0 past falloff_cells

    cell.offset.y = min(influence_total, 1) * max_bulge   # push out along wall depth

    # constrain_bulge_rule, applied right after the block above:
    cell.offset.y = clamp(cell.offset.y, -max_bulge, +max_bulge)

FOR EACH col IN 0..cols-1:
    base_curve        = AddInterpCurve(points in base column col)
    transformed_curve = AddInterpCurve(points in transformed column col)

DRAW base curves        -> layer "mattric::base"        (gray)
DRAW transformed curves -> layer "mattric::transformed" (blue)
DRAW attractors         -> layer "mattric::attractors"  (red circles)

wall = AddLoft(transformed_curves)     # or AddSweep2(rails, transformed_curves)
DRAW wall -> layer "mattric::wall"

OUTPUT  one Rhino document: flat reference profiles, bulged profiles, the
        three attractor markers, and the lofted wall surface
```

Same design as pattric: the containment step (`constrain_bulge_rule`) is
a wrapper around the field rule, not folded into it, so any future bulge
rule keeps the same "never exceed the envelope" guarantee for free.

------------------------------------------------------------------------

## Project Structure (Draft)

    src/
    └── mattric/
        ├── matrix.py          # build/query the 3D point matrix dictionary
        ├── pattern.py         # rules: per-cell depth displacement,
        │                      #   conditional on grid position/attractors
        ├── rhino_backend.py   # Rhino rendering adapter (curves + loft/sweep)
        └── export.py          # (not yet built) page/view setup, sequencing

    scripts/                   # Rhino entrypoints
    recipes/                   # deterministic matrix configurations (JSON)
    outputs/                   # generated files / gallery artifacts
    docs/                      # documentation / gallery

------------------------------------------------------------------------

## Design Direction

Same separation of concerns as pattric/grammatric:

Computational layer:

    matrix → pattern

Rendering / IO layer:

    rhino_backend → export

The matrix/pattern logic stays independent of Rhino and of any output
setup, exactly like pattric keeps its rule logic independent of drawing —
only `rhino_backend.py` should ever import `rhinoscriptsyntax`.

------------------------------------------------------------------------

## Status

v0.1 first draft: `matrix.py`, `pattern.py`, and `rhino_backend.py` are
implemented and wired together via `scripts/run_in_rhino.py` (see
**Implemented so far** and **Pipeline** above), but unverified inside an
actual Rhino session — `rhinoscriptsyntax` isn't available outside Rhino,
so only the pure-Python matrix/pattern logic has been checked directly.
`recipes/`, `docs/`, and `export.py` are still empty/not started.

## Roadmap

**v0.1**
3D point matrix dictionary · one attractor-driven bulge rule · profile
curves per column · single loft into one wall surface

**v0.2**
Sweep (two-rail) as an alternative to loft · row-based courses as rails ·
additional bulge rules (e.g. checkerboard/seeded variants, reusing
pattric's `checker_spin_rule` idea in 3D)

**v0.3**
Sequenced wall states · export/page setup · compiled multi-state
deliverable (mirroring pattric's own v0.3 roadmap)
