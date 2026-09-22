# module.py
# The tower's module - the one piece of geometry that is designed rather than
# derived: a perforated frustum frame ("louver frame"). Pure function on the
# cell dict, no Rhino: rhino_backend turns the same vertices/faces into
# either a polysurface or a mesh.

from .vec import add, cross, dot, mul, normalize, sub


#  Seen from the front: a square frame with a square opening (the same
#  outer-square / inset-square idea as mattric's perforated wall units).
#  It is built on the facade's tangent plane and extruded along the
#  attractor-tilted normal, narrowing toward its tip:
#
#            top outer  ____
#                      /_  _\      top ring   (tapered, faces outward)
#          top inner  |  \/  |     inner walls (face into the opening)
#                     |      |     outer walls (face out)
#         base outer  |______|     base ring  (sits on the facade)
#
#  16 vertices in four rings of four, 16 quad faces: a closed solid with one
#  hole through it.
SIGNS = ((-1, -1), (1, -1), (1, 1), (-1, 1))  # counter-clockwise seen from +normal


def module_frame(cell, normal_key="normal_mod"):
    """
    Orthonormal (a, b, n) at the cell: n the cell's normal (the attractor-
    tilted "normal_mod" by default; pass "normal" for the untilted surface
    normal, as the wall units do), a the surface's U tangent made
    perpendicular to n, b = n x a - so a x b = n. Falls back to any
    perpendicular if the tangent ends up parallel to n.
    """
    n = normalize(cell[normal_key])
    u = cell["u_axis"]
    a = normalize(sub(u, mul(n, dot(u, n))))
    if a == (0.0, 0.0, 0.0):
        helper = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
        a = normalize(cross(helper, n))
    return a, cross(n, a), n


def module_mesh(cell):
    """
    (vertices, faces) of the module at `cell`:
      base outer 0-3, base inner 4-7, top outer 8-11, top inner 12-15,
    faces wound so every normal points out of the solid (outer walls out,
    inner walls into the opening, top ring along the tilted normal, base ring
    back into the facade).
    """
    a, b, n = module_frame(cell)
    p = cell["point"]
    half_outer = cell["size"] / 2.0
    half_inner = half_outer - cell["size"] * cell["inset_ratio"]
    tip = add(p, mul(n, cell["depth"]))
    taper = cell["taper"]

    def ring(center, half):
        return [add(center, add(mul(a, sx * half), mul(b, sy * half))) for sx, sy in SIGNS]

    vertices = (ring(p, half_outer) + ring(p, half_inner)
                + ring(tip, half_outer * taper) + ring(tip, half_inner * taper))
    bo, bi, to, ti = 0, 4, 8, 12

    faces = []
    for k in range(4):
        k1 = (k + 1) % 4
        faces.append((bo + k, bo + k1, to + k1, to + k))    # outer wall
        faces.append((bi + k1, bi + k, ti + k, ti + k1))    # inner wall
        faces.append((to + k, to + k1, ti + k1, ti + k))    # top ring
        faces.append((bo + k1, bo + k, bi + k, bi + k1))    # base ring
    return vertices, faces
