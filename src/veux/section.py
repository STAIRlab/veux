#!/bin/env python
#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
import numpy as np
import matplotlib.pyplot  as plt
import matplotlib.patches as mplp
import matplotlib.lines   as lines
import matplotlib.collections
from math import sqrt

def show():
    plt.show()

def render(s, ax=None, show=None, **kwds):

    if isinstance(show, str):
        show = [show]

    elif show is None:
        show = ["fiber", "patch", "layer"]

    if isinstance(s, list):
        pass

    return MatplotlibSectionCanvas(ax=ax).plot_section(s, show=show, **kwds)


class MatplotlibSectionCanvas:
    def __init__(self, ax=None, **kwds):
        self.ax = ax
        self.kwds = kwds

    def get_section_layers(self, section, **kwds):
        for layer in section.layers:
            if hasattr(layer, "plot_opts"):
                options = layer.plot_opts
            else:
                options = dict(linestyle="--", color="k", linewidth=1.0, **kwds)

            if hasattr(layer, "vertices"):
                yield lines.Line2D(*np.asarray(layer.vertices).T, **options)

    def _get_patches(self, section, facecolor="grey", edgecolor="grey", **kwds):
        """
        Currently a circ must be represented by either an annulus or circle. this
        might be a solution:
        https://docs.bokeh.org/en/latest/docs/reference/models/glyphs/arc.html
        """
        collection = []
        for patch in section.patches:
            name = patch.__class__.__name__.lower()

            if "circ" in name:
                if patch.intRad:
                    width = patch.extRad - patch.intRad
                    collection.append(mplp.Annulus(patch.center, patch.extRad, width))
                else:
                    collection.append(mplp.Circle(patch.center, patch.extRad))
            elif "rect" in name:
                vertices = np.asarray(patch.vertices)
                collection.append(mplp.Rectangle(
                    vertices[0], *(vertices[2]-vertices[0])
                ))
            else:
                collection.append(mplp.Polygon(np.asarray(patch.vertices)))

        return matplotlib.collections.PatchCollection(
            collection,
            facecolor=facecolor,
            edgecolor=edgecolor,
            alpha=0.3
        )

    def plot_section(self,
        section,
        show_properties=False,
        plain=True,
        true_fibers=False,
        set_limits=False,
        show = None,
        show_dims=True,
        annotate=True,
        ax = None,
        fig = None,
        fix_axes=True,
        **kwds
    ):
        """Plot a composite cross section."""

        if plain:
            show_properties = show_dims = False

        if show_properties:
            fig = plt.figure(constrained_layout=True)
            gs = fig.add_gridspec(1,5)
            axp = fig.add_subplot(gs[0,3:-1])
            label = "\n".join([
                "${}$:\t\t{:0.4}".format(k,v) for k,v in self.properties().items()
            ])
            axp.annotate(label, (0.1, 0.5), xycoords='axes fraction', va='center')
            axp.axis("off")

            ax = fig.add_subplot(gs[0,:3])

        elif self.ax is not None:
            ax = self.ax
            fig = ax.figure
        else:
            fig, ax = plt.subplots()

        if fix_axes:
            ax.set_autoscale_on(True)
            ax.set_aspect(1)
            #ax.axis("equal")
            ax.axis("off")
            for i in 'top','right','bottom','left':
                ax.spines[i].set_visible(False)

        if set_limits:
            x_max = 1.01 * max(v[0]
                    for p in section.patches for v in p.vertices
                    if hasattr(p,"vertices"))
            y_max = 1.05 * max(v[1]
                    for p in section.patches for v in p.vertices
                        if hasattr(p,"vertices"))
            y_min = 1.05 * min(v[1]
                    for p in section.patches for v in p.vertices
                        if hasattr(p,"vertices"))

            ax.set_xlim(-x_max, x_max)
            ax.set_ylim( y_min, y_max)

        # add shapes
        if "patch" in show:
            ax.add_collection(self._get_patches(section, **kwds))

        if "layer" in show:
            for l in self.get_section_layers(section, **kwds):
                ax.add_line(l)

        if "fiber" in show:
            if true_fibers:
                circles = [
                    plt.Circle(f.coord, radius=sqrt(f.area/np.pi), linewidth=0)
                        for layer in section.layers for f in layer.fibers
                ] + [
                    plt.Circle(f.coord, radius=sqrt(f.area/np.pi), linewidth=0)
                        for patch in section.patches for f in patch.fibers
                ]
                c = matplotlib.collections.PatchCollection(circles)
                ax.add_collection(c)
            else:
                # TODO: clean this up
#               try:
#                   ax.scatter(*zip(*(f.coord for patch in section.patches for f in patch.fibers)), s=0.1)
#               except Exception as e:
#                   print(e)
#                   pass

                try:
                    ax.scatter(*zip(*(f.coord for f in section.fibers)), s=0.1)
                except Exception as e:
                    print(e)
                    pass


#               try:
#                   coords, areas = zip(*((f.coord, 20*f.area) for layer in section.layers for f in layer.fibers))
#                   ax.scatter(*zip(*coords), s=areas, color="k")
#               except Exception as e:
#                   # print(e)
#                   pass

        # show centroid
        #ax.scatter(*section.centroid)
        # show origin
        # ax.scatter(0, 0)
        ax.axis("equal")
        #plt.show()

        return ax



