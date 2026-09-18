# Pattric — A Field of Squares, Pulled by Three Attractors

*Assignment 3 (a redo of 02.2, patterning) — built around a 2D Point Matrix
Dictionary in Rhino.Python.*

## The idea

Pattric starts from a grid of squares — six columns, six rows, 36 cells
tiled edge to edge with no gaps. Every cell is a small Python dictionary:
where it sits, how big it is, how it's rotated, and whether it's been
nudged off its resting spot. Nothing is drawn yet at this point — it's
just numbers in a dictionary, keyed by `(column, row)` instead of a list
index, so any cell can look up its neighbors or be addressed directly.

Three **attractor points** are placed across the grid. Every cell checks
its distance to all three and blends their pull into one response: cells
close to an attractor grow toward their maximum size and turn to face the
pull direction; cells far from all three shrink back down and settle flat.
Because all three attractors contribute everywhere (not just the nearest
one), the result reads as one continuous field rather than three separate
zones stitched together.

The one rule enforced everywhere: **no square is ever allowed to grow or
shift past the footprint of its own base cell.** Growth, rotation, and
movement all stay inside the square each cell started as — the field can
reshape a cell, but it can never spill into its neighbor's space.

## The pipeline

```
1. Build the base grid
   36 cells, 6x6, laid out edge-to-edge (no gap between squares)

2. Copy it
   A second, identical 36-cell grid — this one will be transformed

3. For every cell in the second grid:
     - measure its distance to each of the 3 attractors
     - blend those three influences into one combined pull
     - grow the cell toward the attractor(s) it's closest to
     - turn the cell to face the direction of that pull
     - nudge the cell's position slightly toward the pull

4. Safety pass, on every cell, right after step 3:
     - if the grown/rotated square would poke outside its own
       original square, shrink it back until it just fits
     - if the nudge would push it outside too, shorten the nudge

5. Draw all three layers into the same Rhino document:
     - the untouched base grid   -> gray
     - the transformed grid      -> blue, drawn directly on top of the base
     - the 3 attractor positions -> small red circles
```

## Why draw base and result on top of each other

Overlaying the two grids at the same origin — rather than side by side —
makes the *deformation itself* the thing you look at: every blue square
sits exactly on the gray square it came from, so growth, rotation, and
drift are all read as a displacement from a known reference, cell by
cell, instead of two separate pictures you have to compare by eye.

## Why the containment rule matters

Without it, a cell near an attractor could grow large enough to overlap
its neighbors, and the "grid" would stop reading as a grid — it would
just be a pile of overlapping shapes. The containment step is written as
a wrapper that runs *after* any field rule, checking the resulting
square's reach against its own cell size and scaling/clamping it back if
needed. That means the same guarantee — "stay inside your own square" —
applies automatically to whatever rule drives the field, now or later.

## What you'd see

- A tidy 6×6 gray grid of touching squares (the base state).
- The same grid in blue, superimposed: squares near each red attractor
  circle are visibly larger and rotated to face it; squares far from all
  three have shrunk down and sit flat, unrotated.
- Nowhere does a blue square cross the boundary of the gray square behind
  it — the field is strong, but always contained.

## What's next

This is the single-state draft. The assignment itself calls for a
*sequence* of states (e.g. the attractors moving, or the field's
intensity ramping up) — each one printed to its own Letter/Landscape PDF
page and compiled into one submission. That sequencing-and-export layer
is the next piece to build.
