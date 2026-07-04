from dataclasses import dataclass

@dataclass
class DrawStyle:
    color: str

@dataclass
class LineStyle:
    color: str   = "black"
    alpha: float = 1.0
    width: float = 1

@dataclass
class TextStyle:
    hover: bool

@dataclass
class PointStyle:
    color: str   = "black"
    scale: float = 1.0
    shape: str   = "block"

NodeStyle = PointStyle


@dataclass
class MeshStyle:
    color: str   = "gray"
    alpha: float = 1.0
    edges: LineStyle = None


