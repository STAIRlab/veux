import numpy as np
from veux.model import Model
from veux.state import BasicState

def _plot_grid(x,y, ax=None, **kwargs):
    ax = ax or plt.gca()
    segs1 = np.stack((x,y), axis=2)
    segs2 = segs1.transpose(1,0,2)
    ax.add_collection(LineCollection(segs1, **kwargs))
    ax.add_collection(LineCollection(segs2, **kwargs))
    ax.autoscale()


def _make_state(res, model=None, time=None, scale=None, transform=None, recover=None, **opts):


    if isinstance(res, np.ndarray) or callable(res):
        return BasicState(res, model, transform=transform, scale=scale, time=time)


    # Dict of state dicts
    elif isinstance(next(iter(res.values())), dict):
        return {
            k: BasicState(v, model, transform=transform, scale=scale)
                for k,v in res.items()
        }

    # Dict from node tag to nodal values
    else:
        return BasicState(res, model, transform=transform, scale=scale)


class PlaneModel(Model):
    ndm = 2
    def __init__(self, mesh, ndf=2):
        self.recs = []
        self.tris = []
        self._tri6 = []

        self.ndf = ndf

        if isinstance(mesh, tuple):
            nodes, elems = mesh
            if isinstance(nodes, dict):
                self.nodes = nodes
            else:
                self.nodes = {i: list(coord) for i, coord in enumerate(nodes)}

            if isinstance(elems, dict):
                self.recs = [
                    tuple(elem[i]-1 for i in range(4)) for elem in elems.values() if len(elem) >= 4
                ]
                self.tris = [
                    tuple(i-1   for i in elem) for elem in elems.values() if len(elem) == 3
                ]
                self._tri6 = [
                    tuple(i-1 for i in elem) for elem in elems.values() if len(elem) == 6
                ]
            else:
                self.recs = [
        #            tuple(i-1 for i in elem) for elem in elems.values() if len(elem) == 4
                    tuple(elem[i]   for i in range(4)) for elem in elems if len(elem) >= 4
                ]
                self.tris = [
                    tuple(i for i in elem) for elem in elems if len(elem) == 3
                ]
                self._tri6 = [
                    tuple(i for i in elem) for elem in elems if len(elem) == 6
                ]

        else:
            # assume mesh is a meshio object
            self.nodes = {i: list(coord)[:2] for i, coord in enumerate(mesh.points)}
            for blk in mesh.cells:
                if blk.type == "triangle":
                    self.tris = self.tris + [
                        tuple(int(i) for i in elem) for elem in blk.data
                    ]
                elif blk.type == "quad":
                    self.recs = self.recs + [
                        tuple(int(i) for i in elem) for elem in blk.data
                    ]

    def wrap_state(self, state, scale=None, transform=None)->BasicState:
        """
        """
        if not isinstance(state, BasicState):
            return _make_state(state,
                            model=self,
                            scale=scale,
                            transform=transform)
        else:
            return state

    def frame_orientation(self, tag):
        return None


    def iter_node_tags(self):
        for tag in self.nodes:
            yield tag 

    def iter_cell_tags(self):
        for tag in range(len(self.tris)+len(self.recs)):
            yield tag

    def cell_matches(self, tag, type=None):
        if type == "plane":
            return True 
        else:
            return False

    def cell_exterior(self, tag=None):
        if tag is None:
            return [
                self.cell_exterior(tag) for tag in range(len(self.recs)+len(self.tris)+len(self._tri6))
            ]
        elif tag < len(self.tris):
            return self.tris[tag]
        elif tag < len(self.tris) + len(self._tri6):
            return self._tri6[tag-len(self.tris)][:3]
        else:
            return self.recs[tag]

    def node_position(self, tag=None, state=None):
        if tag is None:
            return np.array([self.node_position(tag, state=state) for tag in self.iter_node_tags()])

        xyz = np.zeros(3)
        xyz[:2] = self.nodes[tag]

        if state is not None:
            xyz = xyz + state.node_array(tag, dof=state.position)
        return xyz

    def cell_triangles(self, tag=None):
        if tag is None:
            return [
                    self.cell_triangles(tag) for tag in range(len(self.recs)+len(self.tris))
            ]
#           node_tag_to_index = {tag: i for i, tag in enumerate(self.nodes.keys())}
#           return [
#                   tuple(node_tag_to_index[tag] for tag in elem)
#                   for elem in self.tris + _quads_to_tris(self.recs)
#           ]
        elif tag < len(self.tris):
            return self.tris[tag]
        elif tag < len(self.tris) + len(self._tri6):
            return self._tri6[tag-len(self.tris)][:3]
        else:
            quad = self.recs[tag]
            return [
                [quad[0], quad[1], quad[2]],
                [quad[2], quad[3], quad[0]]
            ]


class PlaneArtist:
    def __init__(self, model, ax=None, **kwds):

        import matplotlib.pyplot as plt
        if ax is None:
            _,ax = plt.subplots()
        self.ax = ax

        self.model = model

    def _draw_nodes(self, nodes):
        self.ax.scatter(*zip(*nodes.values()))
        for k,v in nodes.items():
            self.ax.annotate(k, v)

    def draw_outlines(self, **kwds):
        ax = self.ax
        # TODO:
        nodes = self.model.nodes

        for element in self.model.cell_exterior():
            x = [nodes[element[i]][0] for i in range(len(element))]
            y = [nodes[element[i]][1] for i in range(len(element))]
            ax.fill(x, y, edgecolor='black', ls="-", lw=0.5, fill=False)


    def draw_surfaces(self, field=None, show_scale=False):
        ax = self.ax
        import matplotlib.tri as tri
        import matplotlib.pyplot as plt
        #
        # Plot solution contours
        #
        nodes_x, _, nodes_y = self.model.node_position().T

        triangles = self.model.cell_triangles()

        # create an unstructured triangular grid instance
        triangulation = tri.Triangulation(nodes_x, nodes_y, triangles)
        contours = \
            ax.tricontourf(triangulation, field, cmap="twilight", alpha=0.5)

        if show_scale:
            plt.colorbar(contours, ax=ax)

    def draw(self):
        self.ax.axis('equal')

    def show(self):
        import matplotlib.pyplot as plt
        plt.show()

def render(mesh, field=None, ax=None,
         # mesh options
         show_edges=True,
         # contour options
         show_scale=True
    ):
    artist = PlaneArtist(PlaneModel(mesh))

    #
    # plot the finite element mesh
    #
    if show_edges:
        artist.draw_outlines()

    if field is not None:
        artist.draw_surfaces(field=field, show_scale=show_scale)

    artist.draw() 
    return artist
