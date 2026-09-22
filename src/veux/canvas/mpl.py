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


def place_legend(ax, **kwargs):
    """Place legend flush to the right of ax, top-aligned, no overlap."""
    fig = ax.get_figure()

    kwargs.setdefault("fontsize", "small")
    kwargs.setdefault("handlelength", 1.5)
    kwargs.setdefault("handletextpad", 0.4)
    kwargs.setdefault("borderpad", 0.3)

    # let tight_layout position the axes using the full figure width
    fig.tight_layout()

    # place legend anchored to the axes top-right corner
    leg = ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
        **kwargs,
    )

    # measure the legend in figure-fraction coordinates
    renderer = fig.canvas.get_renderer()
    leg_width = (
        leg.get_window_extent(renderer)
        .transformed(fig.transFigure.inverted())
        .width
    )

    # shrink axes from the right to make room
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0, pos.width - leg_width, pos.height])

    return leg

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
        # Map the LineStyle attributes to Matplotlib's kwds
        props = {"color":     style.color,
                 "alpha":     style.alpha,
                 "linewidth": style.width}

        if style is None:
            style = LineStyle(width=0.5, color="gray", alpha=0.6)
    
        if indices is not None:
            warnings.warn("matplotlib canvas does not support indices in plot_lines")
            return

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

    def plot_mesh(self, vertices, indices, local_coords=None, style=None)->int:
        if style is None:
            style = MeshStyle()
    
        self.ax.plot_trisurf(*np.array(vertices).T, triangles=indices, color=style.color)

    def plot_mesh_field(self, mesh, field):
        pass


    def plot_vectors(self, locs, vecs, alr=0.1, **kwds):
        try:
            self.ax.quiver(*locs.T, *vecs.T, arrow_length_ratio=alr, color="black")
        except:
            pass


