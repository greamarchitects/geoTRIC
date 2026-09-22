# Hiritric

Hiritric is a modular high-rise tower generator built around a **Surface
Matrix Dictionary**: a NURBS tower envelope sampled in its (U, V)
parameter space into a `(col, row)`-keyed dictionary, where every cell
carries the surface's own point, normal and tangents. Attractor points tilt
those normals, and a designed **module** — a perforated frustum frame — is
built along each tilted normal, sized, opened and colored by how strongly
the attractors act on it. The wall itself is defined floor by floor by
**perforated wall units** — closed polysurfaces reused from mattric.
Interpolating the whole parameter set across a sequence of states gives a
*series* of towers.

It is the final assignment of the series: modular towers built on the 3D
surface-matrix logic, with the module geometry designed by hand first and
then coded.

------------------------------------------------------------------------

## Where this sits in the series

Fifth and last step, after [grammatric](../01_grammatric),
[skeletric](../02_skeletric), [pattric](../03_pattric) and
[mattric](../04_mattric):

- **grammatric** — a single symbol evolved through named *rules* in
  discrete *derivation* steps.
- **skeletric** — a *bone* (sampled curve points) with linework weighted by
  distance to an attractor.
- **pattric** — many cells addressed by grid coordinate in a *dictionary*,
  each varied independently under shared rules (2D).
- **mattric** — pattric's dictionary in 3D: columns of points become NURBS
  profile curves, lofted into a wall, then divided into perforated frame
  units cut off by the wall surface.
- **hiritric** — mattric's wall wrapped into a tower and read the other way
  round: the surface is no longer built *from* the matrix, it is *sampled
  into* it. The cells hold surface normals, the attractor rule rotates them,
  and mattric's perforated frame returns as a 3D module standing along the
  tilted normal instead of straight off a flat plane.

What carries over, by name: the `(col, row)` dictionary and `apply_rule`;
the smoothstep attractor falloff (now against world distance); the bounded
rule ("a cell never exceeds its own footprint"); the inset-square frame
from mattric's units; base/state layering with `ensure_layer`. What is new:
surface evaluation (`SurfaceFrame`), vector math on normals, color
gradients, and the sequence of states.

------------------------------------------------------------------------

## Assignment Requirements

- Design a **series of modular towers** using the demonstrated 3D surface
  matrix code; the **module geometry is your own**, modelled manually first
  and then coded.
- The series should **demonstrate the geometric variability** the coding
  system allows.
- Written as **functions**, using **dictionaries, lists, iteration and
  conditional execution**.
- Experiment with the **design potential of color**.
- Show variation as **sequential states**: images compiled into one PDF.
- View type that **represents surfaces** (shaded, rendered, ghosted,
  artistic, …); output with Rhino's own **File > Print** to PDF, **Letter,
  Landscape**, PDFs compiled into one for submission.
- **Deliverables**: the PDF and the code saved as `.rtf`, uploaded to the
  Gallery Site. Optional: a 20-second MP4/GIF animation.

Reference: *Python for Rhinoceros 5* — Functions (pp. 19-23), Surfaces
(pp. 99-107), Planes (pp. 58-59); *PY4E* — Functions (pp. 43-56); the
course's Python.Rhinoscript Resources doc.

------------------------------------------------------------------------

## The module

The module is a **louver frame**: a square frame with a square opening,
built on the facade's tangent plane and extruded along the attractor-tilted
normal, narrowing toward its tip.

    front view              side view (section through the frame)

    ┌───────────┐                    top ring (tapered)
    │ ┌───────┐ │                  ╱‾‾‾‾‾╲
    │ │       │ │   ← opening      │       │   ← inner wall faces the opening
    │ │       │ │                  │       │
    │ └───────┘ │              ────┴───────┴────  facade (tangent plane)
    └───────────┘             base ring sits on the facade

Design logic — what the module varies, and why:

| Control             | Far from an attractor      | Near an attractor        |
|---------------------|----------------------------|--------------------------|
| direction           | along the facade normal    | tilted up to `max_tilt`  |
| depth               | shallow (`min_depth`)      | deep (`max_depth`)       |
| frame thickness     | thick (`inset_far`)        | thin, open (`inset_near`)|
| top narrowing       | mild (`taper_far`)         | sharp (`taper_near`)     |
| color               | cool end of the gradient   | warm end                 |

16 vertices in four rings (base outer / base inner / top outer / top inner)
and 16 quad faces make a closed solid with one hole through it. The modules
are built from a single definition (`module_mesh`) and drawn as
either a closed polysurface built from lofts (default) or, for quick
previews, a mesh.

------------------------------------------------------------------------

## The wall

The tower's wall is not the bare surface: it is a set of **perforated wall
units**, one per cell, `WALL_FLOORS` rings of `WALL_COLS` units (a row of the
matrix is one floor). They are mattric's units, rebuilt on a curved tower:

    mattric (flat wall, world axes)         hiritric (tower, each cell's own frame)
    outer box - inner box (inset)           outer box - inner box (inset), in the
    = frame with an opening                 cell's (tangent, up, normal) frame
    frame  intersect  wall surface          frame  intersect  closed tower body
    = closed unit ending on the surface     = closed unit ending on the tower surface

- **Outer box**: fills the cell's patch (`WALL_FILL`; 0.96 leaves a thin
  seam), reaching `wall_thickness` in from the surface and a little way out
  past it.
- **Inner box**: the opening, inset by the cell's `inset_ratio` all round and
  overshooting the outer box at both ends so the subtraction cuts cleanly
  through. The attractor rule sets `inset_ratio`, so **openings widen near an
  attractor** — the same field that tilts and deepens the louver modules.
- **Boolean intersection with the tower body**: the tower is lofted and capped
  into a closed polysurface, so the frame can be intersected with it. What is
  left is the part of the frame inside the tower, and its outer face is a
  piece of the tower surface — a closed polysurface that stops exactly where
  the surface is, with no separate capping step.
- The units use the untilted surface normal (the wall stays flush with the
  facade); the tilting belongs to the louver modules that stand on it. The
  body is hidden by default (`SHOW_TOWER_BODY = False`) because its surface
  would sit flush with the units'.

------------------------------------------------------------------------

## Core Representation

```python
matrix = {
    (col, row): {
        # read off the surface, never changed by rules
        "uv": (u, v), "point": (x, y, z), "normal": (x, y, z),
        "u_axis": (x, y, z), "v_axis": (x, y, z),
        "cell_w": 5.2, "cell_h": 4.0,     # distance to the next cell around / up
        "seed": 0.1234,                    # per-cell randomization source
        # written by the rule
        "normal_mod": (x, y, z),           # normal after attractor tilt
        "influence": 0.0,                  # combined attractor influence, 0..1
        "depth": 1.0, "size": 3.4, "inset_ratio": 0.25, "taper": 1.0,
        "active": True,                    # False = void, no module here
        "color_t": 0.0,                    # position on the color gradient
    }
    for col in range(cols)                 # around the tower (wraps at the seam)
    for row in range(rows)                 # up the tower
}
```

The surface never enters `build_matrix` itself: it is reached through a
`sampler(u, v)` callable, which `surface_sampler` builds from a Rhino
surface and a test can replace with an analytic stand-in.

A **state** is one parameter dictionary (tower shape + rule settings +
attractor positions); a **sequence** is that dictionary interpolated from
START to END over n steps (`build_states`).

**Implemented so far** (v0.1 first draft, `src/hiritric/`):
- `vec.py` — tuple vector helpers, including `rotate_toward` (tilt a unit
  vector by an exact angle toward a target, so a tilt limit holds by
  construction).
- `tower.py` — `floor_plan_points`, `tower_floor_points`: superellipse floor
  plans that taper, bulge and twist up the tower.
- `matrix.py` — `build_matrix(cols, rows, sampler)`: the surface matrix
  dictionary, sampled at patch centres, closed around U.
- `pattern.py` — `apply_rule`, `falloff`, `attractor_tower_rule`: blends all
  attractors into one influence and pull direction, then sets each cell's
  tilted normal, depth, size, frame thickness, taper, void flag and
  gradient position.
- `module.py` — `module_frame`, `module_mesh`: the designed module as pure
  geometry (16 vertices, 16 quads).
- `wall.py` — `box_corners`, `wall_unit_corners`: the eight corners of each
  wall unit's outer and inner box on the cell's own frame (pure geometry,
  ported from mattric's perforated units).
- `color.py` — `gradient` over a list of RGB stops, plus three palettes
  (`ember`, `moss`, `slate`).
- `states.py` — `interpolate_params`, `build_states`.
- `rhino_backend.py` — the only module that calls `rhinoscriptsyntax`:
  `redraw_off` / `redraw_on` (no viewport redraw per object while building),
  `progress` (message at Rhino's command prompt), `make_floor_curve` (closed
  floor curve with fallbacks: periodic interpolated -> interpolated through a
  repeated first point -> closed polyline), `loft_floors` (Normal, then
  Loose, then Straight loft), `close_body` (`CapPlanarHoles`, else manual
  planar caps joined on), `draw_tower` (lofts the floor curves; returns the
  bare *skin* surface for sampling plus the *body*: a copy with top and
  bottom capped into a closed polysurface), `surface_sampler`, `module_polysurface` (the
  module as a closed polysurface built from lofts), `draw_module`,
  `draw_wall_unit` (box minus box, intersected with the tower body; if the
  boolean returns more than one fragment the largest by bounding-box
  diagonal is kept and the rest discarded, and a kept piece far smaller than
  the outer box is rejected as degenerate rather than silently accepted),
  `bbox_diagonal`, `set_layer_visible`, `draw_attractors`, `set_view`,
  `ensure_layer`, `delete_object`.
- `scripts/run_in_rhino.py` — the entrypoint: the configuration (`QUALITY`
  presets, `START` / `END` parameter dictionaries) and the pipeline
  (`attempt`, `build_state`, `main`): the states, START -> END, laid out in a
  row on
  `hiritric::state_NN::{tower, wall, modules, attractors}` layers, view set to
  Shaded.
- `scripts/bundle_single_file.py` — stitches the configuration, every
  module and the pipeline into one generated, self-contained file,
  `outputs/hiritric_single_file.py` (no package imports, every function in one file), for
  the assignment upload (code saved as RTF). Edit `src/`, re-run the
  bundler; don't edit the output.

Not yet built: the export step (Letter/Landscape page setup and the
per-state PDF workflow), the optional animation, and `recipes/`.

------------------------------------------------------------------------

## Pipeline

What `scripts/run_in_rhino.py` does, step by step:

```
INPUT   START, END parameter dictionaries; n_states; cols, rows; gradient

states = [ lerp(START, END, k / (n-1)) for k in 0..n-1 ]      # numbers and lists interpolate

FOR EACH state k, params, at origin (k * spacing, 0, 0):

    floors  = [ plan(f) for f in 0..floors-1 ]
        plan(f):   v = f / (floors-1)
                   scale    = 1 + (taper-1)*v + bulge*sin(pi*v)
                   rotation = twist * v
                   z        = height * v
                   superellipse(rx, ry, squareness) * scale, rotated, at z

    skin = Loft( closed curve through each floor )                   # NURBS envelope
    body = Cap( copy of skin, top and bottom )                       # the tower: a closed polysurface

    wall_matrix, matrix = {}, {}                                     # two grids off the same skin
    FOR EACH grid (wall_cols x wall_floors, cols x rows):
        FOR row, col:                                                # sample at patch centres
            u, v = (col+0.5)/cols, (row+0.5)/rows
            frame = SurfaceFrame(skin, u, v)
            grid[(col,row)] = { point, normal (flipped outward), u_axis, v_axis,
                                cell_w, cell_h, seed, ...defaults }

    FOR EACH cell IN matrix, sorted by key:                          # apply_rule
        total = 0 ; pull = (0,0,0)
        FOR EACH attractor:
            d = distance(cell.point, attractor)
            w = smoothstep_falloff(d, falloff)                       # 1 at attractor, 0 past falloff
            total += w ; pull += w * unit_direction_to(attractor)
        influence        = min(total, 1)
        cell.normal_mod  = rotate_toward(normal, pull, influence * max_tilt)   # never > max_tilt
        cell.depth       = lerp(min_depth, max_depth, influence)
        cell.size        = fill * min(cell_w, cell_h)                # stays inside its own patch
        cell.inset_ratio = lerp(inset_far, inset_near, influence)
        cell.taper       = lerp(taper_far, taper_near, influence)
        cell.active      = NOT (influence < void_below AND seed < void_chance)
        cell.color_t     = influence            (or height, v)

    Delete skin                                                      # only needed for sampling

    apply the attractor rule to wall_matrix AND matrix               # (the loop below is that rule)

    FOR EACH cell IN wall_matrix, floor by floor (row, then col):    # THE WALL
        outer = box on the cell's (tangent, up, normal) frame:
                cell_w*fill by cell_h*fill, from -wall_thickness to +cell/3
        inner = same box inset by inset_ratio * min(side) all round,
                overshooting both ends
        frame = outer - inner                                        # frame with an opening
        unit  = frame  INTERSECT  body                               # closed polysurface; outer face = tower surface
        color = gradient(cell.color_t, wall_stops)
    IF NOT show_tower_body: hide the tower layer

    FOR EACH cell IN matrix, sorted by key:                          # LOUVER MODULES
        IF cell.active:
            a, b, n = orthonormal frame (n = normal_mod, a = u_axis made perpendicular)
            rings   = base outer, base inner (at point), top outer, top inner (at point + n*depth, * taper)
            module  = Join( Loft(base outer, top outer),             # outer wall
                            Loft(base inner, top inner),             # inner wall
                            PlanarSrf(top outer, top inner),         # top ring, opening cut out
                            PlanarSrf(base outer, base inner) )      # base ring
                      (or a 16-quad mesh when AS_POLYSURFACE = False)
            color = gradient(cell.color_t, stops)

    DRAW attractor markers; layers hiritric::state_kk::{tower, wall, modules, attractors}

SET view = Shaded ; ZoomExtents
OUTPUT  n_states towers in a row, each on its own layers - print per state to PDF
```

------------------------------------------------------------------------

## Project Structure (Draft)

    src/
    └── hiritric/
        ├── vec.py             # vector helpers on (x, y, z) tuples
        ├── tower.py           # floor plans -> the tower's control curves
        ├── matrix.py          # surface -> (col, row) matrix dictionary
        ├── pattern.py         # attractor rule: normals, depth, size, color_t
        ├── module.py          # the designed louver module (pure geometry)
        ├── wall.py            # perforated wall units per floor (pure geometry)
        ├── color.py           # gradients
        ├── states.py          # parameter sequences START -> END
        ├── rhino_backend.py   # Rhino adapter (loft, cap, sampler, drawing)
        └── export.py          # (not yet built) page setup + PDF workflow

    scripts/
    ├── run_in_rhino.py        # entrypoint: config + pipeline
    └── bundle_single_file.py  # src/ + config + pipeline -> one file for upload
    recipes/                   # deterministic parameter sets (JSON)
    outputs/                   # generated PDFs, hiritric_single_file.py
    docs/                      # documentation / gallery

------------------------------------------------------------------------

## Design Direction

Same separation of concerns as pattric and mattric:

Computational layer:

    tower → (surface) → matrix → pattern → module + wall → color → states

Rendering / IO layer:

    rhino_backend → export

Only `rhino_backend.py` imports `rhinoscriptsyntax`. Everything else takes
and returns plain tuples, lists and dictionaries, so the whole
computational layer runs (and is tested) outside Rhino.

------------------------------------------------------------------------

## If the wall doesn't show

`draw_wall_unit`'s booleans can go wrong in Rhino in ways that don't raise an
error and don't get reported as a failure count either: `BooleanIntersection`
can return more than one fragment (a sliver alongside the real piece), or a
single fragment that is technically non-null but nearly zero-sized - the call
"succeeds" while producing nothing worth looking at. Both are now guarded
against (the largest fragment is kept, a too-small one is rejected and
counted as a failure), but if the wall still isn't appearing:

- Run `scripts/debug_one_wall_unit.py` instead of `run_in_rhino.py`. It
  builds one tower and tries exactly one wall unit, printing each step - box
  sizes, whether each boolean returned anything, how many fragments and how
  big each one was - so it names the exact step that fails or produces a
  degenerate result, on your machine and your Rhino version. Set `WALL_KEY`
  in it to check a cell elsewhere on the tower (e.g. near the top, where
  twist and taper are strongest) if the middle cell is fine.
- Check the run's own summary line - `built N of N states in ... (K wall
  unit errors)` - and the first `Hiritric: first wall unit error - ...` line
  above it, which names the exception.
- If every wall unit is reported as failed, `SHOW_TOWER_BODY` is overridden
  and the plain tower body is left visible instead of nothing - so "a plain
  closed tower shows up but no perforations" points at the boolean step,
  while "nothing shows up at all" points further back, at the loft/cap step
  (`draw_tower`, see `closed` in the printed output).

------------------------------------------------------------------------

## Running it

`QUALITY` at the top of `scripts/run_in_rhino.py` sets the size of a run:

| preset  | states | louver cells | wall units | louvers     |
|---------|--------|--------------|------------|-------------|
| `draft` | 3      | 12 x 16      | 8 x 10     | meshes      |
| `final` | 5      | 18 x 24      | 12 x 16    | polysurface |

Start with `draft` (the default): it builds the whole series lighter, so the
first run finishes quickly and shows the shape. Switch to `final` once it
looks right. While it runs the command prompt shows the current stage
(`state 2/3 - wall unit 41/80`), and the run is built to keep going:

- viewport redraw is switched off while building and always switched back on
  afterwards (thousands of objects each forcing a redraw is what makes a big
  script look frozen);
- the tower falls back through smooth -> polyline floor curves, Normal ->
  Loose -> Straight lofts, and `CapPlanarHoles` -> manual planar caps before
  a state is given up on;
- every wall unit and louver is drawn inside `attempt(...)`: a failure is
  counted, the first error of each kind is printed, and the run carries on;
- if any wall unit fails, the tower body is left visible so the shape has no
  holes; a state that raises is reported with its traceback and the next
  state still runs;
- the last line summarises: `built 3 of 3 states in 41 s (2 wall unit
  errors)`. If something is wrong, the message that names the failing call is
  the thing to look at.

------------------------------------------------------------------------

## Status

v0.1 first draft. The computational layer (everything but `rhino_backend.py`) has been checked outside Rhino
against an analytic cylinder standing in for the lofted surface: tilt never
exceeds `max_tilt`, sizes stay inside each cell, voids occur only where the
influence is low, every module's faces wind outward (signed volume matches
the analytic frustum-frame volume), the twist/taper sequence interpolates
as expected. `rhino_backend.py` and the script are **unverified inside an
actual Rhino session**: the Rhino calls (`AddInterpCurve` with periodic
knot style 3, `AddLoft`, `CapPlanarHoles`, `AddPlanarSrf`, `JoinSurfaces`, `AddBox`, `EnableRedraw`,
`SurfaceFrame`, `ViewDisplayMode`) still need a first run. The whole Rhino
path has been run against a mock of `rhinoscriptsyntax`, which checks the
control flow: two capped tower bodies, 192 wall units and hundreds of
module polysurfaces per state end up layered and colored, no temporary
curves/lofts/boxes leak, a failed floor curve falls back to a polyline, and
a failed loft, cap, box subtraction or intersection is reported instead of
silently drawing nothing. The wall-unit *geometry* is checked directly: each
box is right-handed, the outer box fills its patch, the opening sits inside
it and overshoots both ends. What only Rhino can confirm is the booleans
themselves (`BooleanDifference`, `BooleanIntersection` on the curved body) —
the most likely place to need tuning; wall units also cost one boolean each
(192 per state), so lower `WALL_COLS`/`WALL_FLOORS` while iterating. Expect to tune the defaults by eye once modules
are on screen.

## Roadmap

**v0.1**
Surface matrix dictionary · attractor-tilted normals · one designed module ·
color gradient · a sequence of states

**v0.2**
Letter/Landscape page setup and per-state PDF printing (`export.py`) ·
`recipes/` for named towers · more rules (e.g. checkerboard/seeded
variation reused from pattric) · modules as polysurfaces by default

**v0.3**
Second module type chosen by a conditional · material/render setup ·
20-second animation of the state sequence
