#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
from .canvas import Canvas, NodeStyle, MeshStyle, LineStyle
import numpy as np

class PlotlyCanvas(Canvas):
    vertical = 3

    def __init__(self, config=None):
        self.data = []
        self.config = config
        self.annotations = []

    def plot_nodes(self, vertices, label = None, style=None, data=None, rotations=None):
        name = label or "nodes"
        x,y,z = vertices.T

        trace = {
                "name": name,
                "x": x, "y": y, "z": z,
                "type": "scatter3d","mode": "markers",
#               "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
#               "customdata": data,
                "marker": {
                    "symbol": "square",
                    "size": 3*style.scale,
                    "color": style.color
                    #**self.config["objects"]["nodes"]["default"]
                },
                "showlegend": False
        }
        self.data.append(trace)

    def plot_lines(self, vertices, indices=None, label=None, style=None):
        if indices is not None:
            for idx in indices:
                self.plot_lines(vertices[idx], label=label, style=style)
            return

        if style is None:
            style = LineStyle(color="#808080")


        x,y,z = vertices.T
        data = {
            "name": label if label is not None else "",
            "type": "scatter3d",
            "mode": "lines",
            "projection": dict(
                z=dict(show=True),
            ),
            "x": x, "y": y, "z": z,
            "line": {"color": style.color, "width": style.width},
            "hoverinfo":"skip"
        }
        self.data.append(data)


    def plot_hover(self, vertices, data=None, keys=None, text=None, html=None, style=None, label=None):
            if isinstance(data, dict):
                keys  = list(map(str, data.keys()))
                data  = [list(map(str, data.values())) for _ in range(len(vertices))]

            elif isinstance(data, list):
                assert keys is not None

            x, y, z = vertices.T

            self.data.append({
                "name": label,
                "x": x, "y": y, "z": z,
                "type": "scatter3d", "mode": "markers", # "lines", #
                "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
                "customdata": data,
                "opacity": 0
            })

    def annotate(self, text, coords, **kwds):
        self.annotations.append({
            "text": text,
            "showarrow": False,
            "xanchor": "left",
            "yshift": -10,
           #"yshift":  10, # For hockling
            "xshift":   5,
            "font": {"color": "black", "size": 48},
            "x": coords[0], "y": coords[1], "z": coords[2],
            **kwds
        })

    def plot_vectors(self, locs, vecs, **kwds):

        ne = vecs.shape[0]
        for j in range(3):
            X = np.zeros((ne*3, 3))*np.nan
            for i in range(j,ne,3):
                X[i*3,:] = locs[i]
                X[i*3+1,:] = locs[i] + vecs[i]

            color = kwds.get("color", ("red", "blue", "green")[j])

            # _label = label if label is not None else ""
            label = kwds.get("label", "")
            if isinstance(label, list):
                label = label[j]
            self.data.append({
                "name": label,
                "type": "scatter3d",
                "mode": "lines",
                "x": X.T[0], "y": X.T[1], "z": X.T[2],
                "line": {"color": color, "width": 4},
                "hoverinfo":"skip",
                "showlegend": False
            })

    def plot_mesh(self, vertices, triangles, style=None, local_coords=None):
        if style is None:
            style = MeshStyle()

        x,y,z = zip(*vertices)
        i,j,k = zip(*triangles)
        self.data.append({
            #"name": label if label is not None else "",
            "type": "mesh3d",
            "x": x, "y": y, "z": z,
            "i": i, "j": j, "k": k,
            "hoverinfo":"skip",
#           "lighting": dict(ambient=0.9, roughness=0.5, specular=2),
#           "lighting": dict(ambient=0.4, diffuse=0.5, roughness = 0.9, specular=0.6, fresnel=0.2),
            "opacity": style.alpha,
            "color":   style.color,
        })

    def build(self):
        opts = self.config
        show_objects = set()
#       show_axis = "axis" in opts["show_objects"]
        show_grid = False #"grid" in opts["show_objects"]
        import plotly.graph_objects as go
        fig = go.Figure(dict(
                data=self.data,
                rendermode='webgl',
                layout=go.Layout(
#                 paper_bgcolor='white',
                  scene=dict(aspectmode="data",
                         xaxis = {"showspikes": "tick" in show_objects, "nticks": 0,
                              "showbackground": show_grid, "backgroundcolor": "white",
                              "showticklabels": "tick" in show_objects,
                              "gridcolor": "gray" if show_grid else None
                         },
                         yaxis = {"showspikes": "tick" in show_objects, "nticks": 0,
                              "showbackground": show_grid, "backgroundcolor": "white",
                              "showticklabels": "tick" in show_objects,
                              "gridcolor": "gray" if show_grid else None
                         },
                         zaxis = {"showspikes": "tick" in show_objects, "nticks": 0,
                              "showbackground": show_grid, "backgroundcolor": "white",
                              "showticklabels": "tick" in show_objects,
                              "gridcolor": "gray" if show_grid else None
                         },
                     # LaTeX is not currently rendered in 3D, see:
                     # https://github.com/plotly/plotly.js/issues/608
#                    xaxis_title = r"$\mathbf{E}_1$",
                     xaxis_title = "", yaxis_title="", zaxis_title="",
                     xaxis_visible =  "x" in show_objects,#show_axis,
                     yaxis_visible =  "y" in show_objects,#show_axis,
                     zaxis_visible =  "z" in show_objects,#show_axis,
                     camera=dict(
                         projection={"type": opts["camera"]["projection"]}
                     ),
                     annotations=self.annotations,
                  ),
                  margin=dict(l=0,r=0,b=0,t=25),
#                 showlegend=("legend" in show_objects)
                )
            ))
        fig.update(layout_coloraxis_showscale=False)

        fig.update_traces(selector=dict(type='scatter3d', mode='lines'),
                          projection=dict(
                              z=dict(show=True),
                          )
        )
        self.fig = fig
        return self

    def to_html(self):
        import plotly
        #import plotly.offline
        #plotly.offline.plot(data, include_plotlyjs=False, output_type='div')
        options = {
          "include_plotlyjs": True,
          "include_mathjax" : "cdn",
          "full_html"       : True
        }
        return plotly.io.to_html(self.fig,
                                 div_id=str(id(self)),
                                 **options)

    def write(self, filename, format=None, **options):
        if "html" in filename:
            with open(filename,"w+") as f:
                f.write(self.to_html())

        elif "png" in filename:
            self.fig.write_image(filename, width=1920, height=1080)

        elif "json" in filename:
            with open(filename,"w+") as f:
                self.fig.write_json(f)

    def make_hover_data(self, data, ln=None):
        if ln is None:
            items = np.array([d.values for d in data])
            keys = data[0].keys()
        else:
            items = np.array([list(data.values())]*ln)
            keys = data.keys()
        return {
            "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
            "customdata": list(items),
        }

