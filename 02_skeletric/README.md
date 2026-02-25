
# skeletric

**skeletric** is a modular framework for generating and studying skeletal
“bone structures” — graph-based geometric systems composed of nodes (points) and
edges (connections) — used as controllable base geometry for procedural design,
structural exploration, and computational form generation.

The project bridges rule-based derivation logic with structured graph representations
across Python and C++ environments

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
│   ├── core/        # Shared graph schema (language-agnostic)
│   ├── python/      # Grammar-style derivation toolkit + Rhino adapter
│   └── cpp/         # C++ procedural implementation + exporters
├── apps/            # 3D-based demo application
├── recipes/         # Deterministic generation configs
├── outputs/         # Exported artifacts
└── docs/            # Concept + roadmap + interoperability notes
```

## Roadmap

**v0.1**  
Graph model · Grid generator · Attractor weighting · JSON export

**v0.2**  
Branching + pruning rules · Deterministic seeds · PLY export

**v0.3**  
Extended Easy3D integration · Advanced structural patterns
