#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
import numpy as np
import warnings
from .canvas import Canvas, NodeStyle, MeshStyle, LineStyle

VIEWS = { # pre-defined plot views
    "plan":    dict(azim=  0, elev= 90),
    "sect":    dict(azim=  0, elev=  0),
    "elev":    dict(azim=-90, elev=  0),
    "iso":     dict(azim= 45, elev= 35)
}

class MatplotlibCanvas(Canvas):
    # vertical direction is the third coordinate
    vertical = 3

    def __init__(self, config=None, ndm=3, ax=None):

        self.ndm = ndm
        self.config = config

        import matplotlib.pyplot as plt
        self.plt = plt
        if ax is None:
            _, ax = plt.subplots(1, 1, subplot_kw={"projection": "3d"})
            ax.set_autoscale_on(True)
            ax.set_axis_off()

        self.ax = ax

    def popup(self):
        self.plt.show()

    def build(self):
        ax = self.ax
        opts = self.config
        aspect = [ub - lb for lb, ub in (getattr(ax, f'get_{a}lim')() for a in 'xyz'[:self.ndm])]
        aspect = [max(a,max(aspect)/8) for a in aspect]
        if self.ndm == 3:
            ax.set_box_aspect(aspect)#, zoom=3)
            ax.view_init(**VIEWS[opts["view"]])
        else:
            ax.set_aspect("equal") #set_box_aspect(1)#, zoom=3)
        return ax

    def write(self, filename):
        self.ax.figure.savefig(filename)

    def plot_lines(self, vertices, label=None, style=None, indices=None):
        if indices is not None:
            warnings.warn("matplotlib canvas does not support indices in plot_lines")
            return
        if style is None:
            style = LineStyle(width=0.5, color="gray", alpha=0.6)

        # Map the LineStyle attributes to Matplotlib's kwds
        props = {"color":     style.color,
                 "alpha":     style.alpha,
                 "linewidth": style.width}
        self.ax.plot(*vertices.T, **props)

    def plot_nodes(self, vertices, label=None, style=None, rotations=None, data=None):
        if style is None:
            style = NodeStyle(color="black")

        props = {"color":  style.color,
                 "marker": "s",
                 "s":      0.1*style.scale,
                 "zorder": 2
        }
        self.ax.scatter(*vertices.T, **props)

    def plot_mesh(self, vertices, indices, local_coords=None, style=None):
        if style is None:
            style = MeshStyle()
        self.ax.plot_trisurf(*np.array(vertices).T, triangles=indices, color=style.color)


    def plot_vectors(self, locs, vecs, alr=0.1, **kwds):
        self.ax.quiver(*locs.T, *vecs.T, arrow_length_ratio=alr, color="black")


