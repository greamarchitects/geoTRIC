# Grammatric

Grammatric is a lightweight 2D shape grammar framework for
computational geometry and rule-based geometric derivation.\
It is designed for Rhino.Python workflows with deterministic, staged
pattern generation.

------------------------------------------------------------------------

## Current Scope

-   2D geometric primitives\
-   Affine transformations (translate, rotate, scale)\
-   Symbolic shape abstraction\
-   Rule-based replacement logic\
-   Iterative derivation process

All geometry is line-based and 2D.

------------------------------------------------------------------------

## Project Structure (Draft)

    src/
    └── grammatric/
        ├── geometry.py        # 2D primitives + utilities
        ├── symbols.py         # symbolic shape definitions
        ├── transforms.py      # affine transforms
        ├── rules.py           # grammar rule definitions
        ├── derivation.py      # staged rule application
        ├── rhino_backend.py   # Rhino rendering adapter
        ├── export.py          # recipe + PDF/PNG export
        └── cli.py             # optional batch execution

    scripts/                   # Rhino entrypoints
    recipes/                   # deterministic grammar configurations (JSON)
    outputs/                   # generated artifacts
    docs/                      # documentation / gallery

------------------------------------------------------------------------

## Design Direction

Separation of concerns.

Computational layer:

    geometry → symbols → transforms → rules → derivation

Rendering / IO layer:

    rhino_backend → export

The grammar engine remains independent from visualization.
