import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Polygon as MplPolygon

from matplotlib.patches import FancyArrowPatch

class PlaneArtist:
    def __init__(self, 
                 model, 
                 ax=None, 
                 title=None, 
                 cbar_layout=None,
                 shape=None, 
                 section=None,
                 **kwds):
        self._draw_done = False

        self.model = model
        self._shape = shape
        self._section = section


        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        if ax is None:
            _,ax = plt.subplots()
        self.ax = ax

        if title is not None:
            ax.set_title(title)

        ax.set_aspect("equal")#, adjustable="datalim")
        ax.axis("off")
        # ax.figure.patch.set_alpha(0.0)
        # ax.patch.set_alpha(0.0)

        divider = make_axes_locatable(ax)

        self._cbar_layout = cbar_layout
        if cbar_layout == "bottom":
            self._cax = divider.append_axes("bottom", size="10%", pad="10%")
        else:
            self._cax = divider.append_axes("right", size="5%", pad=0.1)
        self._cax.axis("off")


    def __repr__(self):
        return ""

    def _draw_nodes(self, nodes):
        self.ax.scatter(*zip(*nodes.values()))
        for k,v in nodes.items():
            self.ax.annotate(k, v)

    def draw_exterior(self):
        exterior = self._shape.exterior()
        self.ax.plot(*zip(*exterior, exterior[0]), color="black", lw=0.5)


    def draw_outlines(self, **kwds):
        ax = self.ax
        # TODO:
        nodes = self.model.nodes
        # nodes = np.array([Ra@x for x in model.node_position(state=state)])

        xy = []
        for element in self.model.cell_exterior():
            xy.extend([nodes[i] for i in element])
            xy.append([np.nan, np.nan])
            continue 
        
            # x = [nodes[element[i]][0] for i in range(len(element))]
            # y = [nodes[element[i]][1] for i in range(len(element))]
            # ax.fill(x, y, edgecolor='black', ls="-", lw=0.5, fill=False)
        ax.plot(*np.array(xy).T, color="black", ls="-", lw=0.5)


    def draw_fibers(self, color="steelblue"):
        shape = self._shape
        model = shape.model

        if self._section is not None:
            section = self._section
            if hasattr(section, "_fibers") and section._fibers is not None:
                self.ax.scatter(*section._fibers[:,:2].T, color=color, s=10)
                return

        fibers = np.array([fiber.coord for fiber in model.fibers]).T
        self.ax.scatter(fibers[0], fibers[1], color=color, s=10, zorder=5)


    def draw_groups(self, color_cycle=None, legend=True, alpha=None, legend_font=None):
        # June 2026

        import uuid
        from itertools import cycle

        shape = self._shape

        def _is_uuid(s):
            try:
                uuid.UUID(s)
                return True
            except ValueError:
                return False

        if color_cycle is None:
            color_cycle = cycle(["lightgray", 
                                 "lightblue", 
                                 "#CD7D5B", # "#9c502D",
                                 "lightcoral", 
                                 "lightgreen",
                                 "lightpink"])

        if isinstance(color_cycle, list):
            color_cycle = cycle(color_cycle)
            group_color = lambda group: next(color_cycle)
        elif isinstance(color_cycle, dict):
            group_color = lambda group: color_cycle.get(group, "lightgray")
        else:
            group_color = lambda group: next(color_cycle)

        labels = set()
        colors = {}
        for group in shape.groups:
            for patch in shape._find_group_patches(group):
                label = None
                if group is None or _is_uuid(group):
                    pass
                else:
                    if group not in labels:
                        label = group
                        labels.add(group)

                if group in colors:
                    color = colors[group]
                else:
                    # color = next(color_cycle)
                    color = group_color(group)
                    colors[group] = color
                
                    
                self.draw_shape(shape._patches[patch], color=color, label=label, alpha=alpha)

        if legend and labels:
            if legend_font is None:
                legend_font = {}
            self.ax.figure.legend(loc="upper left", frameon=False, **legend_font)

    def draw_surfaces(self, 
                      field=None, 
                      style=None,
                      group=None,
                      color="lightgray",
                      cbar_label=None,
                      fontsize=None,
                      levels=100,
                      show_scale=True):
        ax = self.ax
        try:
            import colorcet
            cmap = colorcet.cm['rainbow4']
        except ImportError:
            cmap = "twilight"

        #
        # Plot solution contours
        #

        triangulation = self._triangulation(group=group)
        # create an unstructured triangular grid instance
        if field is not None:
            model = self.model
            if isinstance(field, dict):
                field = np.array([field[node] for node in model.iter_node_tags()])
            elif callable(field):
                field = np.array([field(tag) for tag in model.iter_node_tags()])
            contours = \
                ax.tricontourf(triangulation, field, 
                            cmap=cmap,#"twilight", 
                            levels=levels,
                            #    alpha=0.5
                            )

            if show_scale:
                # plt.colorbar(contours, ax=self._cax, label=cbar_label)
                cbar = ax.figure.colorbar(contours, 
                                   ax=self._cax, 
                                   orientation="horizontal" if self._cbar_layout == "bottom" else None,
                )

                cbar.set_label(cbar_label, fontsize=fontsize)
                cbar.ax.tick_params(labelsize=fontsize)
                if self._cbar_layout == "bottom":
                    vmin, vmax = field.min(), field.max()
                    cbar.set_ticks([vmin, vmax])
                    cbar.set_ticklabels([f"{vmin:.2f}", f"{vmax:.2f}"])
            return contours
        else:
            # If no field is provided, just show the mesh with a light color
            # patch = self._mpl_polygon(group=group, color=color)
            # ax.add_patch(patch)

            # from matplotlib.collections import TriMesh
            ax.tripcolor(triangulation,
                        facecolors=np.ones(len(triangulation.triangles)),
                        cmap=plt.matplotlib.colors.ListedColormap([color]),
                        edgecolors='none')
            # ax.triplot(triangulation, color='black', linewidth=0.5)
            ax.autoscale_view()


    def _triangulation(self, group=None):
        import matplotlib.tri as tri
        nodes_x,  nodes_y, _ = self.model.node_position().T
        triangles = self.model.cell_triangles(group=group)
        return tri.Triangulation(nodes_x, nodes_y, triangles)
        
    def _mpl_polygon(self, group=None, color="lightgray"):
        triang = self._triangulation(group=group)

        # Get boundary edges (edges that belong to only one triangle)
        edges = set()
        for t in triang.triangles:
            for i in range(3):
                edge = tuple(sorted((t[i], t[(i+1) % 3])))
                if edge in edges:
                    edges.remove(edge)
                else:
                    edges.add(edge)

        # Order boundary edges into a closed polygon
        edge_list = list(edges)
        ordered = [edge_list.pop(0)]
        while edge_list:
            last = ordered[-1][1]
            for i, e in enumerate(edge_list):
                if e[0] == last:
                    ordered.append(edge_list.pop(i))
                    break
                elif e[1] == last:
                    ordered.append((e[1], e[0]))
                    edge_list.pop(i)
                    break

        boundary_indices = [e[0] for e in ordered]
        boundary_pts = np.column_stack([triang.x[boundary_indices], triang.y[boundary_indices]])

        return MplPolygon(boundary_pts, closed=True, facecolor=color, edgecolor='black', linewidth=1.5)
    
    def draw_shape(self, shape, color="lightgray", **kwds):
        self.ax.add_patch(_shape_to_path(shape,facecolor=color, **kwds))
        self.ax.autoscale_view()

    def draw_dimensions(self,
                        dimensions:dict=None, 
                        gap=None, 
                        fontsize=8, 
                        color="0.3",
                        head_length=6, 
                        head_width=3):

        ax = self.ax
        if gap is None and self._shape is not None:
            # ext = self.model.exterior()
            # print(ext)
            ext = np.array(self._shape.exterior())
            span = np.ptp(ext, axis=0).max()
            gap = span * 0.08

        if dimensions is None and self._shape is not None:
            shape = self._shape
            parameters = self._shape._annotate_parameters()
            dimensions = {key: shape._annotate_parameter(key) for key in parameters}

        for key, ((p1, p2), offset_dir, dim_type) in dimensions.items():
            p1 = np.asarray(p1, dtype=float)
            p2 = np.asarray(p2, dtype=float)
            offset_dir = np.asarray(offset_dir, dtype=float)

            delta = p2 - p1
            length = np.linalg.norm(delta)
            if length < 1e-12:
                continue

            tangent = delta / length
            normal  = np.array([-tangent[1], tangent[0]])
            if np.dot(normal, offset_dir) < 0:
                normal = np.dot(normal, offset_dir/np.linalg.norm(offset_dir)) * normal

            # Separate magnitude (controls offset distance) from direction (controls side)
            offset_mag = np.linalg.norm(offset_dir)
            shift_dist = offset_mag * gap
            if offset_mag > 1e-12:
                direction = offset_dir / offset_mag
            else:
                direction = np.zeros(2)

            shift = offset_dir * gap
            p1 = p1 + shift
            p2 = p2 + shift

            kw = dict(head_length=head_length, head_width=head_width,
                    direction=direction, shift_dist=shift_dist)

            if dim_type == "inside":
                _draw_inside(ax, p1, p2, key, normal, fontsize, color,
                            gap=gap, **kw)
            elif dim_type in ("+outside", "-outside"):
                _draw_sided_outside(ax, p1, p2, key, tangent, normal,
                                    fontsize, color, gap,
                                    side=dim_type, **kw)
            else:
                _draw_outside(ax, p1, p2, key, tangent, normal, length,
                            fontsize, color, gap, **kw)

    def draw_origin(self, length=None, color="k", lw=0.8, 
                    head_width=0.02, head_length=0.03,
                    label=None,
                    fontsize=None):
        ax = self.ax
        if length is None:
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            span = max(xlim[1] - xlim[0], ylim[1] - ylim[0])
            length = span * 0.12
            head_width = span * head_width
            head_length = span * head_length

        if isinstance(color, str):
            color = color, color

        arrow_style = "-|>, head_width=0.2, head_length=0.4"
        kw = dict(arrowstyle=arrow_style, lw=lw, shrinkA=0, shrinkB=0)

        ax.annotate("", xy=(length, 0), xytext=(0, 0), arrowprops={**kw, "color": color[0]})
        ax.annotate("", xy=(0, length), xytext=(0, 0), arrowprops={**kw, "color": color[1]})

        # if fontsize is not None:
        #     ax.annotate("$y$", xy=(length, 0), xytext=(length*1, length/3), 
        #                 color=color[0],
        #                 fontsize=fontsize,
        #                 ha="left", va="center")
        #     ax.annotate("$z$", xy=(0, length), xytext=(-length/2, length*1.), 
        #                 color=color[1],
        #                 fontsize=fontsize,
        #                 ha="center", va="bottom")
        
        if isinstance(label, tuple):
            x_label, y_label = label
            ax.annotate(x_label, xy=(length*1.1, 0), xytext=(length*1.1, 0), fontsize=fontsize, color=color[0])
            ax.annotate(y_label, xy=(0, length*1.1), xytext=(0, length*1.1), fontsize=fontsize, color=color[1])
        
        if isinstance(label, str):
            ax.annotate(label, xy=(0, 0), xytext=(-length/2, -length/2), 
                        color="k",
                        fontsize=fontsize,
                        ha="center", va="center")


    def draw_vector(self, vector, origin=(0, 0), color="steelblue", lw=1.5, label=None, fontsize=9):
        ax = self.ax
        ox, oy = origin
        vx, vy = vector
        ax.annotate("",
                    xy=(ox + vx, oy + vy),
                    xytext=(ox, oy),
                    arrowprops=dict(arrowstyle="-|>, head_width=0.3, head_length=0.4",
                                    color=color, lw=lw, shrinkA=0, shrinkB=0))
        if label is not None:
            ax.annotate(label,
                        xy=(ox + vx/2, oy + vy/2),
                        fontsize=fontsize, color=color,
                        ha="center", va="bottom")
            
    def draw_offset(self):
        if not hasattr(self._shape, "_offset"):
            return 
        try:
            y, z = self._shape._offset
        except:
            return

        ax = self.ax
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        zmin = min(ylim)
        ymax = max(xlim)
        dimensions = {}
        if y:
            dimensions[f"{abs(y)}"] = (((0, zmin), (y, zmin)), (0, -1), "inside")
        if z:
            dimensions[f"{abs(z)}"] = (((ymax, 0), (ymax, z)), (1,  0), "inside")
        print(dimensions)
        self.draw_dimensions(dimensions, color="k", fontsize=12)
        self.ax.autoscale_view()

    def draw(self):
        # self.ax.axis('equal')
        
        # self.ax.set_aspect("equal")#, adjustable="datalim")
        pass

    def show(self):
        import matplotlib.pyplot as plt
        self.draw()
        plt.show()

    def save(self, filename, bbox_inches="tight", pad_inches=0, **kwds):
        self.draw()
        self._set_section_limits()
        self.ax.figure.savefig(filename, 
                               bbox_inches=bbox_inches, 
                               pad_inches=pad_inches, **kwds)

    def _set_section_limits(self, margin=0.05):

        xy = np.asarray(self._shape.exterior(), dtype=float)
        lo = xy.min(axis=0)
        hi = xy.max(axis=0)

        span = hi - lo
        pad = margin * span

        self.ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0])
        self.ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
        self.ax.set_aspect("equal", adjustable="box")

def render(mesh, field=None, ax=None,
         # mesh options
         show_edges=True,
         # contour options
         show_scale=True
    ):

    artist = PlaneArtist(_PlaneModel(mesh))

    #
    # plot the finite element mesh
    #
    if show_edges:
        artist.draw_outlines()

    if field is not None:
        artist.draw_surfaces(field=field, show_scale=show_scale)

    artist.draw() 
    return artist



_ARROW_COMMON = dict(
    linewidth=0.8,
    shrinkA=0,
    shrinkB=0,
)

def _arrow_style(style, head_length=6, head_width=3):
    """Return a filled-triangle arrow style string."""
    hl, hw = head_length, head_width
    if style == "both":
        return f"<|-|>,head_length={hl},head_width={hw}"
    elif style == "right":
        return f"-|>,head_length={hl},head_width={hw}"
    elif style == "left":
        return f"<|-,head_length={hl},head_width={hw}"


def _draw_witness_lines(ax, p1, p2, direction, shift_dist, gap, color):
    """Draw witness lines from shape surface through dimension line."""
    if shift_dist < 1e-12:
        return
    overshoot = gap * 0.3
    for p in (p1, p2):
        shape_end = p - direction * shift_dist       # back to the shape
        outer_end = p + direction * overshoot         # just past the arrowhead
        ax.plot([shape_end[0], outer_end[0]],
                [shape_end[1], outer_end[1]],
                color=color, linewidth=0.5)


def _draw_inside(ax, p1, p2, key, normal, fontsize, color,
                 gap,
                 direction, shift_dist,
                 head_length=6, head_width=3):
    arrow = FancyArrowPatch(
        posA=p1, posB=p2,
        arrowstyle=_arrow_style("both", head_length, head_width),
        mutation_scale=1,
        color=color,
        **_ARROW_COMMON,
    )
    ax.add_patch(arrow)

    _draw_witness_lines(ax, p1, p2, direction, shift_dist, gap, color)
    _draw_label(ax, (p1 + p2) / 2, normal, key, fontsize, color)


def _draw_outside(ax, p1, p2, key, tangent, normal, length,
                  fontsize, color, gap,
                  direction, shift_dist,
                  head_length=6, head_width=3):
    ext = gap * 0.1
    outer1 = p1 - tangent * ext
    outer2 = p2 + tangent * ext

    a1 = FancyArrowPatch(
        posA=outer1, posB=p1,
        arrowstyle=_arrow_style("right", head_length, head_width),
        mutation_scale=1,
        color=color,
        **_ARROW_COMMON,
    )
    ax.add_patch(a1)

    a2 = FancyArrowPatch(
        posA=outer2, posB=p2,
        arrowstyle=_arrow_style("right", head_length, head_width),
        mutation_scale=1,
        color=color,
        **_ARROW_COMMON,
    )
    ax.add_patch(a2)

    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color=color, linewidth=0.5, linestyle=":")

    _draw_witness_lines(ax, p1, p2, direction, shift_dist, gap, color)

    label_pos = (outer1 + outer2) / 2
    _draw_label(ax, label_pos, normal, key, fontsize, color)


def _draw_sided_outside(ax, p1, p2, key, tangent, normal,
                        fontsize, color, gap,
                        direction, shift_dist,
                        side="+outside",
                        head_length=6, head_width=3):
    ext = gap #* 0.1
    outer1 = p1 - tangent * ext
    outer2 = p2 + tangent * ext

    a1 = FancyArrowPatch(
        posA=outer1, posB=p1,
        arrowstyle=_arrow_style("right", head_length, head_width),
        mutation_scale=1,
        color=color,
        **_ARROW_COMMON,
    )
    ax.add_patch(a1)

    a2 = FancyArrowPatch(
        posA=outer2, posB=p2,
        arrowstyle=_arrow_style("right", head_length, head_width),
        mutation_scale=1,
        color=color,
        **_ARROW_COMMON,
    )
    ax.add_patch(a2)

    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color=color, linewidth=0.5, linestyle=":")

    _draw_witness_lines(ax, p1, p2, direction, shift_dist, gap, color)

    label_margin = gap * 0.6
    if side == "+outside":
        label_pos = outer2 + tangent*label_margin
    else:
        label_pos = outer1 - tangent*label_margin

    ax.text(
        label_pos[0], label_pos[1],
        key,
        fontsize=fontsize,
        color=color,
        ha="center",
        va="center",
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            pad=1.0,
            alpha=0.85,
        ),
    )

def _draw_label(ax, pos, normal, key, fontsize, color):
    offset = normal * fontsize * 0.1
    ax.text(
        pos[0] + offset[0],
        pos[1] + offset[1],
        key,
        fontsize=fontsize,
        color=color,
        ha="center",
        va="center",
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            pad=1.0,
            alpha=0.85,
        ),
    )


def _shape_to_path(shape, **kwargs):
    """Convert a shape with .exterior() and .interior() to a PathPatch.
    """
    rings = [np.asarray(shape.exterior())]

    holes = shape.interior()
    if holes is not None:
        for hole in holes:
            rings.append(np.asarray(hole))

    vertices = []
    codes = []
    for ring in rings:
        n = len(ring)
        vertices.append(ring)
        vertices.append(ring[:1])  # close the sub-path
        codes.extend([Path.MOVETO] + [Path.LINETO] * (n - 1) + [Path.CLOSEPOLY])

    path = Path(np.concatenate(vertices, axis=0), codes)
    return PathPatch(path, **kwargs)