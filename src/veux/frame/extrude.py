#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio M. Perez
#
import sys
import warnings
import numpy as np
from scipy.spatial.transform import Rotation

import shps.curve

import veux
import veux.frame
from veux.model import read_model
from veux.errors import RenderError
from veux.config import MeshStyle
from shps.frame.extrude import FrameMesh
from dataclasses import dataclass

@dataclass
class ExtrusionCollection:
    triang: list
    coords: list
    caps: list
    no_outline: set
    in_outline: set

def add_extrusion(extr, e, x, R, I, caps=None):

    ring_ranges = extr.ring_ranges()

    p = extr.vertices()
    indices = extr.triangles()

    if len(indices) == 0 or len(ring_ranges) == 0:
        return 0

    e.triang.extend([I + T for T in indices])

    for (j, start_idx, end_idx) in ring_ranges:
        for i in range(start_idx, end_idx):
            e.coords.append(x[j] + R[j] @ p[i])

    if caps:
        nen = len(x)
        noe = ring_ranges[0][-1]
        caps[0].append(            I+np.arange(noe))
        caps[1].append((nen-1)*noe+I+np.arange(noe))

    return len(indices)


def draw_extrusions3(model, canvas, state=None, config=None, Ra=None):
    if config is None:
        config = {"style": MeshStyle(color="gray")}
    if Ra is None:
        Ra = np.eye(3)

    scale = config.get("scale", 1.0)

    # 1) Build local geometry
    #----------------------------------------------------------
    I = 0
    caps = []
    e = ExtrusionCollection([], [], [], set(), set())
    for tag in model.iter_cell_tags():
        if not model.cell_matches(tag, "frame"):
            continue

        R0 = model.frame_orientation(tag)
        if R0 is None:
            warnings.warn(f"Frame {tag} has no orientation")
            continue
        else:
            R0 = R0.T

        X_ref = np.array([
            Ra@model.node_position(node) for node in model.cell_nodes(tag)
        ])
        nen = len(X_ref)

        if state is not None:
            x = np.array([
                Ra@model.node_position(node, state=state) for node in model.cell_nodes(tag)
            ])
            # u = state.cell_array(tag, state.position)
            # x = shps.curve.displace(X_ref, u, nen)
            R = [Ra@Ri@R0 for Ri in state.cell_array(tag, state.rotation)]
        else:
            x = X_ref
            R = [Ra@R0 for _ in range(nen)]

        sections = [model.frame_section(tag, i) for i in range(len(x))]
        if sections[0] is None or sections[-1] is None:
            continue

        icap, jcap = [], []
        #
        # Exterior
        #
        extr = FrameMesh(len(x),
                        [s.exterior() for s in sections],
                        scale=scale,
                        do_end_caps=False)

        ne = add_extrusion(extr, e, x, R, I, [icap, jcap])

        si = sections[0]
        if len(si.exterior()) > 35:
            for i in range(ne):
                e.no_outline.add(I+i)

        #
        # Interior
        #
        ni = 0
        for i in range(len(si.interior())):
            if si.interior()[i] is None or len(si.interior()[i]) == 0:
                continue

            extr = FrameMesh(len(x),
                    [s.interior()[i] for s in sections],
                    scale=scale,
                    do_end_caps=False)
        
            nij = add_extrusion(extr, e, x, R, I+ne+ni, [icap, jcap])
            for i in range(nij):
                # e.no_outline.add(I+ne+ni+i)
                e.in_outline.add(I+ne+ni+i)
            ni += nij

        I += ni + ne

        #
        # Caps
        #
        try:
            face = si.triangles()

        except Exception as ex:
            warnings.warn(f"Earcut failed with message: {ex}")
            continue

        iicap = [ i for j in icap for i in j ]
        ijcap = [ i for j in jcap for i in j ]
        caps.extend([
            [iicap[i] for i in face],
            [ijcap[i] for i in face]
        ])


    # Draw mesh
    if e.coords:
        mesh = canvas.plot_mesh(e.coords,
                     [list(reversed(face)) for face in e.triang],
                     style=config["style"])

    # Draw caps
    if len(caps) > 0:
        for cap in caps:
            try:
                canvas.plot_mesh(mesh.vertices, cap, style=config["style"])
            except Exception as ex:
                print(ex)

    # Draw outlines
    if "outline" not in config:
        return

    triang = e.triang
    nan = np.array([0,0,0], dtype=float)*np.nan
    IDX = np.array(((0,2),(0,1)))
    coords = np.array(e.coords)

    if "tran" in config["outline"]:
        tri_points = np.array([
            coords[idx]  if (j+1)%3 else nan
            for j,idx in enumerate(np.array(triang).reshape(-1))
        ])

    elif "long" in config["outline"]:
        tri_points = np.array([
            coords[i]  if j%2 else nan
            for j,idx in enumerate(np.array(triang)) for i in idx[IDX[j%2]] if j not in e.no_outline
        ])
    else:
        return

    if len(tri_points):
        canvas.plot_lines(tri_points,
                      style=config["line_style"])


class so3:
    @classmethod
    def exp(cls, vect):
        return Rotation.from_rotvec(vect).as_matrix()

def _add_moment(artist, loc, axis):
    import meshio
    mesh_data = meshio.read(veux.assets/'chrystals_moment.stl')
    coords = mesh_data.points

    coords = np.einsum('ik, kj -> ij',  coords,
                       so3.exp([0, 0, -np.pi/4])@so3.exp(axis))
    coords = 1e-3*coords + loc
    for i in mesh_data.cells:
        if i.type == "triangle":
            triangles =  i.data #mesh_data.cells['triangle']
            break

    artist.canvas.plot_mesh(coords, triangles)


def _render(sam_file, res_file=None, **opts):
    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds 

    config = veux.config.Config()


    if sam_file is None:
        raise RenderError("Expected positional argument <sam-file>")

    # Read and clean model
    if not isinstance(sam_file, dict):
        model = read_model(sam_file)
    else:
        model = sam_file

    if "RendererConfiguration" in model:
        veux.apply_config(model["RendererConfiguration"], config)

    veux.apply_config(opts, config)

    artist = veux.FrameArtist(model, **config)

    draw_extrusions3(artist.model, artist.canvas, config=opts)

    # -----------------------------------------------------------

    soln = veux.model.read_state(res_file, artist.model, **opts)
    if soln is not None:
        if "time" not in opts:
            soln = soln[soln.times[-1]]

        draw_extrusions3(artist.model, artist.canvas, soln, opts)
        # -----------------------------------------------------------
        _add_moment(artist,
                    loc  = [1.0, 0.0, 0.0],
                    axis = [0, np.pi/2, 0])
        # -----------------------------------------------------------

    artist.draw()
    return artist


if __name__ == "__main__":
    import veux.parser
    config = veux.parser.parse_args(sys.argv)

    try:
        artist = _render(**config)

        # write plot to file if output file name provided
        if config["write_file"]:
            artist.save(config["write_file"])


        # Otherwise either create popup, or start server
        elif hasattr(artist.canvas, "popup"):
            artist.canvas.popup()

        elif hasattr(artist.canvas, "to_glb"):
            import veux.server
            server = veux.server.Server(glb=artist.canvas.to_glb(),
                                        viewer=config["viewer_config"].get("name", None))
            server.run(config["server_config"].get("port", None))

        elif hasattr(artist.canvas, "to_html"):
            import veux.server
            server = veux.server.Server(html=artist.canvas.to_html())
            server.run(config["server_config"].get("port", None))

    except (FileNotFoundError, RenderError) as e:
        # Catch expected errors to avoid printing an ugly/unnecessary stack trace.
        print(e, file=sys.stderr)
        print("         Run '{NAME} --help' for more information".format(NAME=sys.argv[0]), file=sys.stderr)
        sys.exit()

