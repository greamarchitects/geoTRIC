# Pattric

Pattric is a 2D patterning framework built around a **Point Matrix
Dictionary** — a grid of cells keyed by `(col, row)`, each holding its own
state (position, rotation, scale, seed). It is designed for Rhino.Python
workflows: iterating and conditionally mutating that dictionary to produce
a progressively variable field pattern, then output as 2D linework.

This is a redo of assignment 02.2 (patterning), now required to be built
on the dictionary-keyed matrix structure rather than ad hoc per-object
logic.

------------------------------------------------------------------------

## Where this sits in the series

Third step after [grammatric](../01_grammatric) and [skeletric](../02_skeletric),
followed by [mattric](../04_mattric):

- **grammatric** — a single symbol, evolved through named *rules* applied
  in discrete *derivation* steps (one lineage, staged over time).
- **skeletric** — a *bone* (sampled curve points), with derived linework
  (ribs, circles) *weighted by distance to an attractor* (one structure,
  varied continuously over space).
- **pattric** — many cells at once, addressed by grid coordinate in a
  *dictionary* rather than one symbol or one curve, each free to vary
  independently under shared rules (a field, varied over both space and
  state).
- **mattric** — pattric's dictionary-indexed matrix pushed into a third
  dimension: columns/rows of 3D points become NURBS profile curves, which
  are lofted or swept into a wall surface (a field, built up into surface
  geometry instead of stopping at 2D linework).

The attractor-weighting idea from skeletric (`derive.attractor_radius`)
and the rule/step idea from grammatric (`rules.py` / `derivation.py`) are
both reusable here per-cell: a rule can read a cell's grid position, look
up its neighbors in the dictionary, and conditionally move/scale/rotate/
randomize it — including attractor-style falloff against one or more
field points. mattric reuses the same per-cell attractor-falloff idea
again, one dimension up.

------------------------------------------------------------------------

## Assignment Requirements

- Build the field on a **2D Point Matrix Dictionary**: `{(col, row): cell}`,
  each `cell` itself a dict of per-point state.
- Demonstrate **dictionaries, lists, iteration, and conditional execution**
  as the mechanics generating and mutating the matrix.
- Produce a **progressively variable pattern** — emergent field effects
  (moving, scaling, rotating, randomization, ...) across the matrix.
- Demonstrate variation as **sequential states**: a series of matrix
  snapshots, each rendered and printed to its own PDF, then compiled into
  one submission PDF showing the range the system can produce.
- **2D line work only.**
- Output via Rhino's own **File > Print** to PDF (not a script-side PDF
  library) — **Letter, Landscape**.
- Tune **line weight** away from the default so linework reads clearly
  once printed/rendered.
- **Deliverables**: the compiled PDF, and the code saved as `.rtf`,
  uploaded to the Gallery Site.

Reference: *Python for Rhinoceros 5* — Dictionaries (p.25); *PY4E* —
Dictionaries (pp.107-116); the course's Python.Rhinoscript Resources doc.

------------------------------------------------------------------------

## Core Representation

```python
matrix = {
    (col, row): {
        "origin": (x, y, z),  # fixed base grid position
        "offset": (0.0, 0.0), # rule-driven translation from origin (the
                               #   "moving" effect, kept separate from
                               #   origin so rules stay idempotent)
        "rotation": 0.0,
        "scale": 1.0,
        "seed": 0.1234,       # per-cell randomization source
        # + whatever a given pattern rule reads/writes
    }
    for col in range(cols)
    for row in range(rows)
}
```

Cells are addressed by `(col, row)` key, not by list index — so rules can
do neighbor lookups (`matrix.get((col-1, row))`), conditionally skip/branch
per cell, and stay independent of iteration order. A **state** is one
fully-evaluated matrix (a dict snapshot); a **sequence** is a list of
states over some varying parameter (step index, time, an attractor
position), which is what actually gets rendered into the multi-page/
multi-PDF deliverable.

**Implemented so far** (v0.1 first draft, `src/pattric/`):
- `matrix.py` — `build_matrix` (grid of cells), `spacing_for_gap` (turns a
  desired edge-to-edge gap between base squares into the center-to-center
  `spacing` `build_matrix` needs — `gap=0` tiles the base grid with no
  gaps), `neighbors`, `bounds`, `center_key`.
- `pattern.py` — `apply_rule` + rules: `checker_spin_rule` (checkerboard
  rotation, seeded scale, seeded position jitter — the v0.1 default),
  `radial_grow_rule` (attractor-style falloff against grid distance, reusing
  skeletric's smoothstep shape), `three_point_attractor_rule` (the same
  falloff blended across three attractor points into one continuous field
  — the current default), and `constrain_to_cell_rule` (wraps any rule so
  its scale/rotation/offset never push a cell's drawn square past its own
  `cell_size × cell_size` base rectangle — the square it would draw at
  scale=1/rotation=0/offset=(0,0) — regardless of the grid's spacing).
- `rhino_backend.py` — `cell_corners` (pure geometry: rotated/scaled/offset
  square corners), `draw_matrix_live` (draws + layers + colors a whole
  matrix), and `draw_markers_live` (small circles for marking points, e.g.
  attractors, on their own layer — 2D linework, not `rs.AddPoint` dots).
- `scripts/run_in_rhino.py` — the working entrypoint: builds a 6×6 base
  matrix (squares tiled edge-to-edge, `GAP = 0.0`) and a second copy with
  `three_point_attractor_rule` (wrapped in `constrain_to_cell_rule`, tuned
  for a strong, clearly visible effect) applied, drawing both superimposed
  at the same origin under `pattric::base` (gray) and `pattric::transformed`
  (blue), plus the three attractor positions as red circles under
  `pattric::attractors`. See **Pipeline** below for the exact step order.

Not yet built: `states.py` (sequential states) and `export.py` (Letter/
Landscape page setup + line-weight + the compiled multi-PDF workflow) — the
actual assignment deliverable still needs those; this first draft only
proves the matrix → rule → single Rhino drawing path end to end.

------------------------------------------------------------------------

## Pipeline

What `scripts/run_in_rhino.py` actually does, step by step:

```
INPUT   cols, rows, cell_size, gap, attractors[3], scale/falloff/pull params

spacing  = cell_size + gap                      # spacing_for_gap

base        = build_matrix(cols, rows, spacing) # untouched grid, scale=1
transformed = build_matrix(cols, rows, spacing) # identical second copy

rule = constrain_to_cell_rule(
           three_point_attractor_rule(attractors, max_scale, min_scale,
                                       falloff_cells, pull),
           cell_size)

FOR EACH (col, row) -> cell IN transformed, sorted by key:        # apply_rule
    influence_total = 0
    pull_vector     = (0, 0)
    FOR EACH attractor IN attractors:
        d = grid_distance((col, row), attractor)
        w = smoothstep_falloff(d, falloff_cells)   # 1 at attractor, 0 past falloff_cells
        influence_total += w
        pull_vector     += w * unit_direction_to(attractor)

    cell.scale    = lerp(min_scale, max_scale, min(influence_total, 1))
    cell.rotation = angle_of(pull_vector)                 # 0 if no influence
    cell.offset   = normalize(pull_vector) * pull * min(influence_total, 1)

    # constrain_to_cell_rule, applied right after the block above:
    reach = (cell_size * cell.scale / 2) * reach_factor(cell.rotation)
    IF reach > cell_size / 2 * margin:
        cell.scale = shrink so reach == cell_size / 2 * margin
    cell.offset = clamp(cell.offset, to +/- remaining room per axis)

DRAW base        -> layer "pattric::base"        (gray,  cell_size squares)
DRAW transformed -> layer "pattric::transformed" (blue,  cell_size squares)
DRAW attractors  -> layer "pattric::attractors"  (red circles, radius r)

OUTPUT  one Rhino document, three layers, base and transformed superimposed
```

The containment check is deliberately run as a *wrapper* around the field
rule rather than folded into it — any future rule (checkerboard, radial,
whatever comes next) can be dropped in and still gets the same "never
exceed your own base square" guarantee for free.

------------------------------------------------------------------------

## Project Structure (Draft)

    src/
    └── pattric/
        ├── matrix.py          # build/query the 2D point matrix dictionary
        ├── pattern.py         # rules: per-cell move/scale/rotate/randomize,
        │                      #   conditional on grid position/neighbors
        ├── states.py          # capture a matrix into a state; run a sequence
        ├── rhino_backend.py   # Rhino rendering adapter (draws one state)
        ├── export.py          # page setup (Letter/Landscape) + line weight
        │                      #   helpers, sequence -> compiled PDF notes
        └── cli.py             # optional batch execution

    scripts/                   # Rhino entrypoints
    recipes/                   # deterministic matrix configurations (JSON)
    outputs/                   # generated PDFs / gallery artifacts
    docs/                      # documentation / gallery

------------------------------------------------------------------------

## Design Direction

Same separation of concerns as grammatric:

Computational layer:

    matrix → pattern → states

Rendering / IO layer:

    rhino_backend → export

The matrix/pattern/states logic stays independent of Rhino and of PDF
page setup, exactly like grammatric keeps its grammar engine independent
of visualization - only `rhino_backend.py` should ever import
`rhinoscriptsyntax`.

------------------------------------------------------------------------

## Status

v0.2 in progress: `matrix.py`, `pattern.py`, and `rhino_backend.py` are
implemented and working end to end via `scripts/run_in_rhino.py` (see
**Implemented so far** and **Pipeline** above). `recipes/` and `docs/`
(beyond this README) are still empty; `states.py`/`export.py` (v0.3) are
not started.

## Roadmap

**v0.1**
Point matrix dictionary · one pattern rule (move/scale/rotate) · single-state
Rhino draw

**v0.2**
Conditional/neighbor-aware rules · randomization · attractor-style falloff
reused from skeletric

**v0.3**
Sequential states · Letter/Landscape page setup + line-weight helpers ·
multi-state export workflow feeding the compiled submission PDF
