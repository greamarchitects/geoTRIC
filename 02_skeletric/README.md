
# skeletric

**skeletric** is a modular framework for generating and studying skeletal
“bone structures” — graph-based geometric systems composed of nodes (points) and
edges (connections) — used as controllable base geometry for procedural design,
structural exploration, and computational form generation.

The project bridges rule-based derivation logic with structured graph representations
across Python and C++ environments

---

## Status

What actually runs today, vs. what's still aspirational in the sections below:

**Implemented** (`src/python/skeletric/`, Rhino-only via `rhinoscriptsyntax`):

- `bones.py` — acquire/build bone curves (`get_bones`, `make_rectangle_bone`),
  sample them into point lists (`sample_curve`), plus centroid/key-point/list
  helpers.
- `derive.py` — generate linework from those point lists: `polyline`,
  `ribs_along_spine`, `connect_point_lists` (ladder/weave), `circles_on_points`,
  and `circles_on_points_attractor` — radius grows near a single attractor
  point and eases (smoothstep, not linear) back down to a resting radius by a
  falloff distance.
- `rhino_backend.py` — nested layer creation + filing generated objects into
  layers, so a run's output is organized instead of landing unlabeled on the
  current layer.
- `scripts/run_in_rhino.py` — the working entrypoint tying the above together
  (see Quick Start below).

**Not yet implemented**: the formal Graph/Node/Edge core described under
*Core Representation* (`src/core/graph_schema.json`, `schema.md` are still
empty), the C++ side (`src/cpp/*.hpp`, `apps/Tutorial_604_ProceduralBoneStructure`),
and a recipe loader (`recipes/demo_grid_attractor.json` is a placeholder, not
yet read by any script). Today's attractor weighting lives directly in
`derive.py` against raw point lists, not against a graph/edge model yet.

---

## Quick Start (Rhino)

Run `scripts/run_in_rhino.py` from Rhino's Python editor (Tools >
EditPythonScript / the ScriptEditor in Rhino 7 SR14+/8, "Run File"):

1. Pre-select or pick a spine curve when prompted - otherwise a demo
   rectangle bone is created automatically.
2. Pick an attractor point (Enter/Esc falls back to the spine's centroid).
3. Output is filed into layers under `skeletric::` (`spine`, `ribs`,
   `circles`, `attractor`) - circles grow near the attractor and ease back
   to their resting radius with distance.

Tuning knobs are at the top of the script: `SAMPLE_N`, `RIB_LEN`,
`RIB_EVERY`, `CIRCLE_RADIUS`, `CIRCLE_MAX_RADIUS`, `CIRCLE_FALLOFF_DIST`,
`CIRCLE_EVERY`.

The script force-clears any cached `skeletric.*` modules from `sys.modules`
before importing, so edits to the package take effect on the next "Run"
without needing to restart Rhino.

---

## Research Context

In computational design, simplified base structures (“bone structures”) are often
used to drive the generation of more complex geometries.

skeletric formalizes this idea as a:

- **Graph-based model** (Node / Edge / Properties)
- **Deterministic procedural generators** (recipes + seeds)
- **Interoperable schema** for cross-tool workflows
- **Multi-language implementation** (Python + C++)

This supports controlled experimentation with:

- Attractor-based weighting
- Connectivity patterns and pruning/branching rules
- Reproducible geometry pipelines

---

## Core Representation

A bone structure is defined as:

- **Nodes** → 3D coordinates `(x, y, z)`
- **Edges** → index pairs referencing nodes
- Optional **edge properties** (e.g., attractor-based strength)

The representation is intentionally minimal and portable, supporting integration with:

- Rhino (2D line workflows through the Python toolkit)
- Easy3D (interactive visualization via the C++ tutorial app)
- Custom geometry systems and batch pipelines

---


## Architecture

```
skeletric/
├── src/
│   ├── core/        # Shared graph schema (language-agnostic)         - not yet implemented
│   ├── python/      # Bone/derive toolkit + Rhino adapter             - implemented, Rhino-only
│   └── cpp/         # C++ procedural implementation + exporters       - not yet implemented
├── apps/            # 3D-based demo application                      - not yet implemented
├── recipes/         # Deterministic generation configs                - schema drafted, not yet consumed
├── outputs/         # Exported artifacts
└── docs/            # Concept + roadmap + interoperability notes      - not yet written
```

## Roadmap

**v0.1**  
Graph model · Grid generator · Attractor weighting *(done for Rhino linework - see Status; not yet on a graph/edge model)* · JSON export

**v0.2**  
Branching + pruning rules · Deterministic seeds · PLY export

**v0.3**  
Extended Easy3D integration · Advanced structural patterns
