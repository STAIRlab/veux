#
import matplotlib.pyplot as plt
import matplotlib.tri as tri


class PlaneArtist:
    def __init__(self, model, **kwds):

        import matplotlib.pyplot as plt
        _,self.ax = plt.subplots()

        self.model = model

    def _draw_nodes(self, nodes):
        self.ax.scatter(*zip(*nodes.values()))
        for k,v in nodes.items():
            self.ax.annotate(k, v)

    def draw(self):
        pass

    def show(self):
        import matplotlib.pyplot as plt
        plt.show()


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


# plot edges from a finite element mesh
def _draw_plane_mesh(nodes, elements, ax):
    for element in elements:
        x = [nodes[element[i]][0] for i in range(len(element))]
        y = [nodes[element[i]][1] for i in range(len(element))]
        ax.fill(x, y, edgecolor='black', ls="-", lw=0.5, fill=False)


def render(mesh, solution, ax=None,
         # mesh options
         show_edges=True,
         # contour options
         show_scale=True
    ):
    #
    # Extract mesh information
    #
    quads = []
    elements_tris = []

    if isinstance(mesh, tuple):
        nodes, elems = mesh
        quads = quads + [
#            tuple(i-1 for i in elem) for elem in elems.values() if len(elem) == 4
             tuple(i   for i in elem) for elem in elems.values() if len(elem) == 4
        ]

    else:
        # assume mesh is a meshio object
        nodes = {i: list(coord) for i, coord in enumerate(mesh.points)}
        for blk in mesh.cells:
            if blk.type == "triangle":
                elements_tris = elements_tris + [
                    tuple(int(i) for i in elem) for elem in blk.data
                ]
            elif blk.type == "quad":
                quads = quads + [
                    tuple(int(i) for i in elem) for elem in blk.data
                ]


    elements = elements_tris + quads


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
        _draw_plane_mesh(nodes, elements, ax=ax)


    #
    # Plot solution contours
    #
    nodes_x, nodes_y = zip(*nodes.values())

    # convert all elements into triangles
    node_tag_to_index = {tag: i for i, tag in enumerate(nodes.keys())}
    elements_all_tris = [
            tuple(node_tag_to_index[tag] for tag in elem)
            for elem in elements_tris + _quads_to_tris(quads)
    ]

    # create an unstructured triangular grid instance
    triangulation = tri.Triangulation(nodes_x, nodes_y, elements_all_tris)
    contours = \
        ax.tricontourf(triangulation, solution, cmap="twilight", alpha=0.5)

    if show_scale:
        plt.colorbar(contours, ax=ax)
    ax.axis('equal')
    return ax

