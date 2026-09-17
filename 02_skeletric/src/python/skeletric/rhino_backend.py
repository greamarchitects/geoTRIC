# rhino_backend.py
# Rhino output adapter for skeletric.
#
# bones.py / derive.py already draw straight into the active Rhino document
# (they return Rhino object ids directly, not a backend-agnostic geometry
# type like grammatric's Shape) - so unlike grammatric this has no headless
# rhino3dm path yet. What it adds is layer bookkeeping: creating nested
# layers and filing generated objects into them, so a run's output is
# organized instead of dumped unlabeled onto the current layer.
#
# Live-only: everything here needs rhinoscriptsyntax, i.e. running inside
# Rhino (EditPythonScript / ScriptEditor, Rhino 7 SR14+/8).

from __future__ import annotations

from typing import Iterable, List, Optional

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
            "skeletric.rhino_backend needs to run inside Rhino "
            "(rhinoscriptsyntax not found)."
        )


def ensure_layer(path: str) -> str:
    """Create a (possibly nested, 'A::B::C') layer path if missing."""
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


def file_objects(obj_ids: Optional[Iterable], layer: str) -> List:
    """
    Move a batch of object ids (curve/line/circle ids returned by bones.py /
    derive.py - None entries from a failed rs.Add* call are skipped) onto
    `layer`, creating it if needed. Returns the surviving ids.
    """
    _require_live()
    ensure_layer(layer)
    ids = [oid for oid in (obj_ids or []) if oid]
    for oid in ids:
        rs.ObjectLayer(oid, layer)
    return ids
