# rhino_backend.py
# Rhino rendering adapter for grammatric.
#
# Two interchangeable backends, selected automatically by environment:
#
#   live      - running inside Rhino itself (EditPythonScript / ScriptEditor,
#               Rhino 7 SR14+ / Rhino 8), via `rhinoscriptsyntax`. Draws
#               directly into the active Rhino document.
#
#   headless  - running anywhere else (this repo, a CI job, a plain
#               terminal), via the `rhino3dm` package
#               (pip install rhino3dm). Builds geometry in memory and
#               writes a .3dm file - no Rhino install or license required
#               to *generate* the file, only to later open it.
#
# Both backends consume the same computational-layer objects (Symbol / Shape
# from .symbols, as produced by .derivation.Derivation.run()) so a
# derivation renders identically either way - only the destination differs.
# This keeps the grammar engine independent of Rhino, per the project's
# design direction (see README.md).
#
# ---------------------------------------------------------------------------
# Quick start
# ---------------------------------------------------------------------------
#
# Inside Rhino (EditPythonScript console, or a script under scripts/):
#
#     from grammatric.symbols import make_square
#     from grammatric.rules import Rule
#     from grammatric.derivation import Derivation
#     from grammatric.transforms import rotate_shape, scale_shape
#     from grammatric import rhino_backend as rb
#
#     def grow(symbol, step_i):
#         s = scale_shape(rotate_shape(symbol.shape, 15 * (step_i + 1)),
#                          0.9 ** (step_i + 1))
#         return [symbol, symbol.with_shape(s)]
#
#     history = Derivation([make_square(20, "A")], [Rule("A", grow)]).run(8)
#     rb.draw_derivation_live(history)   # staged, grid-laid-out output
#
# Outside Rhino (headless, e.g. from this repo / CI, no Rhino needed):
#
#     rb.export_derivation_3dm(history, "outputs/spiral_square.3dm")
#
# Or let one call site do either, depending on where it runs:
#
#     rb.render_derivation(history, path="outputs/spiral_square.3dm")

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from .symbols import Symbol, Shape
from .transforms import translate_shape

try:
    import rhinoscriptsyntax as rs  # only importable from inside Rhino
except ImportError:
    rs = None


def is_live() -> bool:
    """True if running inside Rhino's own Python engine (rhinoscriptsyntax available)."""
    return rs is not None


def _require_live() -> None:
    if not is_live():
        raise RuntimeError(
            "This function needs to run inside Rhino (rhinoscriptsyntax not found). "
            "Outside Rhino, use the headless equivalent (export_derivation_3dm / "
            "build_model_headless) or call render_derivation(..., path=...) instead."
        )


def _require_rhino3dm():
    try:
        import rhino3dm
    except ImportError as exc:
        raise RuntimeError(
            "The headless backend needs the `rhino3dm` package: pip install rhino3dm"
        ) from exc
    return rhino3dmnm


# ---------------------------------------------------------------------------
# shared layout helper (pure - no Rhino dependency, used by both backends)
# ---------------------------------------------------------------------------

def grid_offset(index: int, cols: int, cell_w: float, cell_h: float) -> Tuple[float, float]:
    """(dx, dy) to place stage `index` in a left-to-right, top-to-bottom grid."""
    col = index % cols
    row = index // cols
    return (col * cell_w, -row * cell_h)


# ---------------------------------------------------------------------------
# live backend - rhinoscriptsyntax
# ---------------------------------------------------------------------------

def ensure_layer(path: str) -> str:
    """Create a (possibly nested, 'A::B::C') layer path if missing. Live only."""
    _require_live()
    if rs.IsLayer(path):
        return path
    parts = path.split("::")
    current = parts[0]
    if not rs.IsLayer(current):
        rs.AddLayer(current)
    for part in parts[1:]:
        nxt = f"{current}::{part}"
        if not rs.IsLayer(nxt):
            rs.AddLayer(part, parent=current)
        current = nxt
    return path


def draw_shape_live(shape: Shape, layer: Optional[str] = None, z: float = 0.0) -> List:
    """Draw one Shape's segments as lines into the active document. Returns object guids."""
    _require_live()
    ids = []
    for (x1, y1), (x2, y2) in shape.segments:
        guid = rs.AddLine((x1, y1, z), (x2, y2, z))
        if guid and layer:
            rs.ObjectLayer(guid, layer)
        ids.append(guid)
    return ids


def draw_symbol_live(symbol: Symbol, layer: Optional[str] = None, z: float = 0.0) -> List:
    """Draw a single Symbol into the active document."""
    if layer:
        ensure_layer(layer)
    return draw_shape_live(symbol.shape, layer=layer, z=z)


def draw_stage_live(symbols: Iterable[Symbol], layer_prefix: str, index: int, z: float = 0.0) -> List:
    """Draw one derivation step (a list of symbols) onto '<layer_prefix>::stage_NN'."""
    layer = ensure_layer(f"{layer_prefix}::stage_{index:02d}")
    ids = []
    for sym in symbols:
        ids.extend(draw_shape_live(sym.shape, layer=layer, z=z))
    return ids


def draw_derivation_live(
    history: Sequence[Sequence[Symbol]],
    layer_prefix: str = "grammatric",
    cols: int = 4,
    cell_w: float = 80.0,
    cell_h: float = 60.0,
    z: float = 0.0,
    zoom: bool = True,
) -> List:
    """
    Draw an entire derivation history (Derivation.run() output) into Rhino:
    one sub-layer per step ('<layer_prefix>::stage_00', 'stage_01', ...),
    laid out in a grid so stages don't overlap and print/screenshot cleanly.
    """
    _require_live()
    ensure_layer(layer_prefix)
    all_ids = []
    for i, symbols in enumerate(history):
        ids = draw_stage_live(symbols, layer_prefix, i, z=z)
        dx, dy = grid_offset(i, cols, cell_w, cell_h)
        if ids and (dx or dy):
            rs.MoveObjects(ids, (dx, dy, 0.0))
        all_ids.extend(ids)
    if zoom:
        rs.ZoomExtents()
    return all_ids


# ---------------------------------------------------------------------------
# headless backend - rhino3dm (pip install rhino3dm)
# ---------------------------------------------------------------------------

def build_model_headless(
    history: Sequence[Sequence[Symbol]],
    layer_prefix: str = "grammatric",
    cols: int = 4,
    cell_w: float = 80.0,
    cell_h: float = 60.0,
    z: float = 0.0,
):
    """
    Build an in-memory rhino3dm.File3dm for a whole derivation history,
    mirroring draw_derivation_live(): one layer per step, grid-arranged.
    """
    rhino3dm = _require_rhino3dm()
    model = rhino3dm.File3dm()

    for i, symbols in enumerate(history):
        layer_name = f"{layer_prefix}::stage_{i:02d}"
        layer_index = model.Layers.AddLayer(layer_name, (0, 0, 0, 255))
        attrs = rhino3dm.ObjectAttributes()
        attrs.LayerIndex = layer_index

        dx, dy = grid_offset(i, cols, cell_w, cell_h)
        for sym in symbols:
            shape = translate_shape(sym.shape, dx, dy) if (dx or dy) else sym.shape
            for (x1, y1), (x2, y2) in shape.segments:
                model.Objects.AddLine(
                    rhino3dm.Point3d(x1, y1, z),
                    rhino3dm.Point3d(x2, y2, z),
                    attrs,
                )
    return model


def export_derivation_3dm(
    history: Sequence[Sequence[Symbol]],
    path: str,
    layer_prefix: str = "grammatric",
    cols: int = 4,
    cell_w: float = 80.0,
    cell_h: float = 60.0,
    z: float = 0.0,
    version: int = 6,
) -> str:
    """
    Write a whole derivation history to a .3dm file without needing Rhino
    open (uses rhino3dm). `version` is the file format to write (6 is
    readable by Rhino 6/7/8). Returns `path`.
    """
    model = build_model_headless(
        history, layer_prefix=layer_prefix, cols=cols, cell_w=cell_w, cell_h=cell_h, z=z
    )
    if not model.Write(path, version):
        raise RuntimeError(f"rhino3dm failed to write {path!r} (invalid model?)")
    return path


# ---------------------------------------------------------------------------
# unified entrypoint
# ---------------------------------------------------------------------------

def render_derivation(history: Sequence[Sequence[Symbol]], path: Optional[str] = None, **kwargs):
    """
    Convenience dispatcher that works from either environment:
      - path given             -> always writes a .3dm via the headless
                                   backend (works whether or not Rhino is
                                   running); kwargs forwarded to
                                   export_derivation_3dm.
      - no path, inside Rhino  -> draws live into the active document;
                                   kwargs forwarded to draw_derivation_live.
      - no path, outside Rhino -> raises (nothing to draw into).
    """
    if path is not None:
        return export_derivation_3dm(history, path, **kwargs)
    if is_live():
        return draw_derivation_live(history, **kwargs)
    raise RuntimeError(
        "Not running inside Rhino and no output `path` given - pass "
        "path='outputs/....3dm' to write a file via the headless backend."
    )
