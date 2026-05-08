# geoTRIC

Procedural computational design toolkit for geometric systems, skeletal structures, spatial matrices, and attractor-driven architectural generation.
---

# Modules

```text
01 grammatric  → Shape Grammars
02 skeletric   → Skeletal Graphs
03 pattric     → Pattern Fields
04 mattric     → 3D Matrices
05 hiritric    → Surface Tower Systems
```

Each module extends the previous one through:
* dimensional complexity
* iteration systems
* attractor logic
* vector fields
* procedural control

---

# Structure

```text
geoTRIC/
│
├── 01_grammatric/
├── 02_skeletric/
├── 03_pattric/
├── 04_mattric/
├── 05_hiritric/
│
├── api/
│   ├── core/
│   ├── rhino/
│   ├── blender/
│   ├── freecad/
│   ├── revit/
│   └── autocad/
│
├── render/
└── examples/
```

---

# API Logic

```text
Core Geometry
↓
Abstract Geometry
↓
Platform Adapter
↓
Rhino / Blender Objects
↓
Rendering / GIF Export
```

## Visual Sequence

```text
                ┌─────────────────────┐
                │ grammatric.py       │
                │ skeleton.py         │
                │ pattern.py          │
                │ matrix.py           │
                │ surface.py          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ ABSTRACT GEOMETRY   │
                │                     │
                │ Polyline            │
                │ Column              │
                │ Matrix              │
                │ Graph               │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Rhino API    │  │ Blender API  │  │ Future APIs  │
│ Adapter      │  │ Adapter      │  │ Revit/FCAD   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
 Rhino Objects     Blender Objects    BIM Objects
       │                 │
       ▼                 ▼
 Rendering         Rendering
       │
       ▼
 GIF / PNG / MP4
```

Core geometry is software-independent.

Adapters convert geometry into platform-specific objects.

Current implemented adapters:

* Rhino
* Blender

---

# Current Systems

## grammatric

Rule-based shape transformations.

## skeletric

Node-edge skeletal graph systems.

## pattric

Pattern repetition and field variation.

## mattric

3D matrix and column systems.

## hiritric

Surface-normal tower generation.

---

# Rendering

```text
Geometry
→ Frame Sequence
→ GIF / MP4
```

Used for:

* procedural animations
* geometric studies
* system visualizations
* architectural motion graphics

---

# Technologies

* Python
* RhinoScriptSyntax
* RhinoCommon
* Blender bpy
* NumPy

---

# Status

Currently focused on:
* Rhino + Blender workflows
* API abstraction layer
* multi-platform procedural geometry
