import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri

def _plot_grid(x,y, ax=None, **kwargs):
    ax = ax or plt.gca()
    segs1 = np.stack((x,y), axis=2)
    segs2 = segs1.transpose(1,0,2)
    ax.add_collection(LineCollection(segs1, **kwargs))
    ax.add_collection(LineCollection(segs2, **kwargs))

    ax.autoscale()


# converts quad elements into tri elements
def _quads_to_tris(quads):
    tris = [
        [None for j in range(3)] for i in range(2*len(quads))
    ]
    for i in range(len(quads)):
        j = 2*i
        tris[j][0] = quads[i][0]
        tris[j][1] = quads[i][1]
        tris[j][2] = quads[i][2]
        tris[j + 1][0] = quads[i][2]
        tris[j + 1][1] = quads[i][3]
        tris[j + 1][2] = quads[i][0]
    return tris

class PlaneModel:
    def __init__(self, mesh):
        self.recs = []
        self.tris = []

        if isinstance(mesh, tuple):
            self.nodes, elems = mesh
            self.recs = [
    #            tuple(i-1 for i in elem) for elem in elems.values() if len(elem) == 4
                tuple(i   for i in elem) for elem in elems.values() if len(elem) == 4
            ]

        else:
            # assume mesh is a meshio object
            self.nodes = {i: list(coord) for i, coord in enumerate(mesh.points)}
            for blk in mesh.cells:
                if blk.type == "triangle":
                    self.tris = self.tris + [
                        tuple(int(i) for i in elem) for elem in blk.data
                    ]
                elif blk.type == "quad":
                    self.recs = self.recs + [
                        tuple(int(i) for i in elem) for elem in blk.data
                    ]
 
    def cell_exterior(self):
        return self.tris + self.recs 

    def node_position(self, tag=None):
        return np.array(list(self.nodes.values()))

    def cell_triangles(self):
        node_tag_to_index = {tag: i for i, tag in enumerate(self.nodes.keys())}
        return [
                tuple(node_tag_to_index[tag] for tag in elem)
                for elem in self.tris + _quads_to_tris(self.recs)
        ]


class PlaneArtist:
    def __init__(self, model, ax=None, **kwds):
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

        #
        # Plot solution contours
        #
        nodes_x, nodes_y = self.model.node_position().T

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
        plt.show()


def render(mesh, solution, ax=None,
         # mesh options
         show_edges=True,
         # contour options
         show_scale=True
    ):
    #
    # Extract mesh information
    #
    recs = []
    tris = []

    if isinstance(mesh, tuple):
        nodes, elems = mesh
        recs = [
#            tuple(i-1 for i in elem) for elem in elems.values() if len(elem) == 4
             tuple(i   for i in elem) for elem in elems.values() if len(elem) == 4
        ]

    else:
        # assume mesh is a meshio object
        nodes = {i: list(coord) for i, coord in enumerate(mesh.points)}
        for blk in mesh.cells:
            if blk.type == "triangle":
                tris = tris + [
                    tuple(int(i) for i in elem) for elem in blk.data
                ]
            elif blk.type == "quad":
                recs = recs + [
                    tuple(int(i) for i in elem) for elem in blk.data
                ]


    elements = tris + recs


    #
    # Set up canvas
    #
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure


    #
    # plot the finite element mesh
    #
    if show_edges:
        _draw_outlines(nodes, elements, ax=ax)


    #
    # Plot solution contours
    #
    nodes_x, nodes_y = zip(*nodes.values())

    # convert all elements into triangles
    node_tag_to_index = {tag: i for i, tag in enumerate(nodes.keys())}
    elements_all_tris = [
            tuple(node_tag_to_index[tag] for tag in elem)
            for elem in tris + _quads_to_tris(recs)
    ]

    # create an unstructured triangular grid instance
    triangulation = tri.Triangulation(nodes_x, nodes_y, elements_all_tris)
    contours = \
        ax.tricontourf(triangulation, solution, cmap="twilight", alpha=0.5)


    if show_scale:
        plt.colorbar(contours, ax=ax)
    ax.axis('equal')
    return ax


def render(mesh, field=None, ax=None,
         # mesh options
         show_edges=True,
         # contour options
         show_scale=True
    ):
    #
    # Extract mesh information
    #

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
