# symbols.py
# Minimal symbolic wrapper around geometric shapes

from dataclasses import dataclass
from typing import Tuple

Point2D = Tuple[float, float]
Segment2D = Tuple[Point2D, Point2D]


@dataclass(frozen=True)
class Shape:
    segments: tuple[Segment2D, ...]


@dataclass(frozen=True)
class Symbol:
    name: str
    shape: Shape

    def with_shape(self, shape: Shape):
        return Symbol(self.name, shape)


def make_square(size: float = 10.0, name: str = "A") -> Symbol:
    s = float(size)
    pts = [(0.0, 0.0), (s, 0.0), (s, s), (0.0, s)]
    segs = tuple(zip(pts, pts[1:] + pts[:1]))
    return Symbol(name=name, shape=Shape(segs))