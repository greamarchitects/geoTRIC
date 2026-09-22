# pattern.py
# Rules that mutate a surface matrix's rule-driven fields in place - the same
# apply_rule/rule shape as pattric and mattric, but where pattric moved/
# scaled/rotated a 2D square and mattric pushed a point's depth, this rotates
# the surface *normal* toward attractors and sizes a 3D module along it.
# Rules only touch numeric/flag state in each cell dict - never geometry or
# Rhino - so they can be written and checked with plain Python.

import math

from .vec import add, distance, length, lerp, mul, normalize, rotate_toward, sub


def apply_rule(matrix, rule):
    """Apply `rule` to every cell, in (col, row) sorted order for determinism."""
    for key in sorted(matrix.keys()):
        rule(matrix, key, matrix[key])
    return matrix


def falloff(d, falloff_dist):
    """Smoothstep falloff - 1 at d=0, 0 at/after falloff_dist. Same shape as
    skeletric's attractor_radius and pattric/mattric's rules, here against a
    world-space distance instead of a grid distance."""
    t = min(max(d / falloff_dist, 0.0), 1.0)
    return 1.0 - t * t * (3.0 - 2.0 * t)


def attractor_tower_rule(attractors, falloff_dist=35.0, max_tilt=55.0, min_depth=1.0,
                          max_depth=6.0, fill=0.85, inset_far=0.30, inset_near=0.12,
                          taper_far=0.85, taper_near=0.45, void_chance=0.0,
                          void_below=0.25, color_by="influence"):
    """
    The tower's field rule. Every cell blends the pull of all attractors
    (world-space points; nearer ones weigh more via `falloff`) into one
    influence in 0..1 and one pull direction, then sets:

      normal_mod   the surface normal tilted toward the pull by
                   influence * max_tilt degrees - never more than max_tilt,
                   by construction (rotate_toward)
      depth        min_depth -> max_depth with influence
      size         `fill` x the cell's own smaller side, so a module never
                   reaches its neighbours (bounded by construction, like
                   pattric's constrain_to_cell_rule)
      inset_ratio  frame thickness and top narrowing (taper), easing from
      taper        the *_far to the *_near value with influence
      active       a cell far from every attractor (influence < void_below)
                   becomes a void with probability void_chance, drawn from its
                   own seed - a conditional that punches irregular gaps into
                   the calm parts of the facade
      color_t      position along the color gradient: the influence
                   ("influence") or the height up the tower ("height")
    """
    def rule(matrix, key, cell):
        point, normal = cell["point"], cell["normal"]

        total, pull = 0.0, (0.0, 0.0, 0.0)
        for attractor in attractors:
            d = distance(point, attractor)
            w = falloff(d, falloff_dist)
            total += w
            if d > 1e-9:
                pull = add(pull, mul(normalize(sub(attractor, point)), w))
        influence = min(total, 1.0)

        cell["influence"] = influence
        if length(pull) > 1e-9:
            cell["normal_mod"] = rotate_toward(
                normal, normalize(pull), math.radians(max_tilt) * influence)
        else:
            cell["normal_mod"] = normal
        cell["depth"] = lerp(min_depth, max_depth, influence)
        cell["size"] = min(cell["cell_w"], cell["cell_h"]) * fill
        cell["inset_ratio"] = lerp(inset_far, inset_near, influence)
        cell["taper"] = lerp(taper_far, taper_near, influence)
        cell["active"] = not (influence < void_below and cell["seed"] < void_chance)
        cell["color_t"] = cell["uv"][1] if color_by == "height" else influence
    return rule
