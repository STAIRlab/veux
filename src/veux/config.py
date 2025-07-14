from dataclasses import dataclass
from collections import defaultdict

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
class NodeStyle:
    color: str   = "black"
    scale: float = 1.0
    shape: str   = "block"


@dataclass
class MeshStyle:
    color: str   = "gray"
    alpha: float = 1.0
    edges: LineStyle = None


def SketchConfig(kwds=None):
    if kwds is None:
        kwds = {}

    return apply_config(kwds, {
      "origin": {
          "axes":        {"show": True, "scale": 1.0, "label": [r"$\mathbf{E}_1$", r"$\mathbf{E}_2$", r"$\mathbf{E}_3$"], "style": LineStyle(color="black")},
      },
      "frame": {
          "outline":     {"show": True,  "style": LineStyle(color="black"), "basis": None},
          "surface":     {"show": False, "style": MeshStyle(),             "basis": None, "scale": 1.0, "outline": "long", "line_style": LineStyle(color="black", width=4)},
          "axes":        {"show": False},
          "contour":     None,
          "marker":      None,
          "info":        None,
          "hover":       {"show": False} #, "style": TextStyle(hover=True)},
      },
      "plane": {
          "outline":     {"show": True,  "style": LineStyle(), "basis": None},
          "surface":     {"show": True,  "style": MeshStyle()},
          "axes":        {"show": False, "style": LineStyle(), "scale": 1.0},
          "contour":     {"show": False, "style": MeshStyle(), "scale": 1.0}
      },
      "solid": {
          "edges":       {"show": True,  "style": LineStyle()},
          "outline":     {"show": True,  "style": LineStyle(), "basis": None},
          "surface":     {"show": True,  "style": MeshStyle(), "scale": 1.0},
          "axes":        {"show": True,  "style": LineStyle(), "scale": 1.0}
      },
      "node":  {
          "marker":  {"show": False, "style": NodeStyle(color="black") },
          "hover":   {"show": True, "style": NodeStyle(color="black") },
      }
    })

# @dataclass
# class ArtistConfig:
#     type: str = None
#     vert: int = 2
# 
#     scene: dict = {
#           "origin": {"show": False, "line_style": LineStyle(color="black")}
#     }
# 
#     def show(self, key):
#         pass
# 
#     def create(self, model_data):
#         pass

@dataclass
class ModelConfig:
    vert: int = 2


Config = lambda : {
  "model":         None,
  "res_file":      None,
  "write_file":    None,
  "displ":         defaultdict(list),
  "scale":         1.0,

  "viewer_config": {},
  "server_config": {},

  "model_config":  {},
  "state_config":  {},
  "canvas_config": {
      # Canvas
      "type":       "gltf",
      "view":       "iso",
      "camera": {
          "view": "iso",               # iso | plan| elev[ation] | sect[ion]
          "projection": "orthographic" # perspective | orthographic
      },
  },
  "artist_config": {
      "type": None,
      "vertical": 2,
      "sketches": {
          "default":   SketchConfig(),
#         "reference": SketchConfig({
#             "plane": {
#                 "outline":     {"show": False, "style": LineStyle(color="gray"), "basis": None},
#                 "surface":     {"show": False, "style": MeshStyle()},
#                 "axes":        {"show": False, "style": LineStyle(), "scale": 1.0},
#                 "contour":     {"show": False, "style": MeshStyle(), "scale": 1.0}
#             },
#         }),
          "displaced": SketchConfig({
              "frame": {
                  "outline":     {"show": True,   "style": LineStyle(color="red"), "basis": "Hermite"},
                  "surface":     {"show": False,  "style": MeshStyle(), "basis": "Lagrange", "scale": 1.0, "outline": "long", "line_style": LineStyle(color="black", width=4)},
                  "axes":        {"show": False},
         #        "contour":     None,
         #        "marker":      None,
         #        "info":        None,
              },
         #    "plane": {
         #        "outline":     {"show": True,  "style": LineStyle(), "basis": None},
         #        "surface":     {"show": True,  "style": MeshStyle()},
         #        "axes":        {"show": False, "style": LineStyle(), "scale": 1.0},
         #        "contour":     {"show": True,  "style": MeshStyle(), "scale": 1.0}
         #    },
         #    "solid": {
         #        "edges":   {"style": LineStyle()},
         #        "surface": {"style": MeshStyle(), "scale": 1.0},
         #        "axes":    {"style": LineStyle(), "scale": 1.0}
         #    },
         #    "node":  {
         #        "marker":  {"show": True, "style": NodeStyle(color="black") },
         #    }
         })
    }
  },

  # Artist
  "show_objects":  ["frames.displ", "nodes", "legend", "elastica", "reference"],
  "mode_num"    :  None,
  "displacements": {"scale": 1.0, "color": "#660505"},

  "objects": {
      "origin": {"color": "black", "scale": 1.0},
      "triads": {},
      "edges" : {
          "displaced": {"color": "red", "npoints": 20}
      },
      "nodes": {
          "scale": 1.0,
          "default": {"size": 3, "color": "#000000"},
      },
      "sections": {"scale": 1.0}
  },

}

def apply_config(conf, opts):
    for k,v in conf.items():
        if isinstance(v,dict) and k in opts:
            apply_config(v, opts[k])
        else:
            opts[k] = v
    return opts

