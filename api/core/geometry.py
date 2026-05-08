from dataclasses import dataclass
from typing import List, Tuple

Point = Tuple[float, float, float]

@dataclass
class Polyline:
    points: List[Point]

@dataclass
class Column:
    x: float
    y: float
    height: float
    radius: float = 0.06

@dataclass
class Frame:
    name: str
    geometry: list
