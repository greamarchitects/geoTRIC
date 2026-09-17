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

Third step after [grammatric](../01_grammatric) and [skeletric](../02_skeletric):

- **grammatric** — a single symbol, evolved through named *rules* applied
  in discrete *derivation* steps (one lineage, staged over time).
- **skeletric** — a *bone* (sampled curve points), with derived linework
  (ribs, circles) *weighted by distance to an attractor* (one structure,
  varied continuously over space).
- **pattric** — many cells at once, addressed by grid coordinate in a
  *dictionary* rather than one symbol or one curve, each free to vary
  independently under shared rules (a field, varied over both space and
  state).

The attractor-weighting idea from skeletric (`derive.attractor_radius`)
and the rule/step idea from grammatric (`rules.py` / `derivation.py`) are
both reusable here per-cell: a rule can read a cell's grid position, look
up its neighbors in the dictionary, and conditionally move/scale/rotate/
randomize it — including attractor-style falloff against one or more
field points.

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
- `matrix.py` — `build_matrix`, `neighbors`, `bounds`, `center_key`.
- `pattern.py` — `apply_rule` + two rules: `checker_spin_rule` (checkerboard
  rotation, seeded scale, seeded position jitter — the v0.1 default) and
  `radial_grow_rule` (attractor-style falloff against grid distance, reusing
  skeletric's smoothstep shape — a v0.2-style option).
- `rhino_backend.py` — `cell_corners` (pure geometry: rotated/scaled/offset
  square corners) and `draw_matrix_live` (draws + layers a whole matrix).
- `scripts/run_in_rhino.py` — the working entrypoint: builds an 8×6 matrix,
  applies `checker_spin_rule`, draws it under the `pattric` layer.

Not yet built: `states.py` (sequential states) and `export.py` (Letter/
Landscape page setup + line-weight + the compiled multi-PDF workflow) — the
actual assignment deliverable still needs those; this first draft only
proves the matrix → rule → single Rhino drawing path end to end.

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

Not yet implemented - this README is the scaffold/plan. Nothing under
`src/`, `scripts/`, `recipes/`, or `docs/` exists yet.

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
