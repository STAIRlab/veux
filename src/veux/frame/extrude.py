#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
import sys
import warnings
import numpy as np
from scipy.spatial.transform import Rotation

import shps.curve

import veux
import veux.frame
from veux.utility.earcut import earcut, flatten as flatten_earcut
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


def draw_extrusions3(model, canvas, state=None, config=None):
    if config is None:
        config = {"style": MeshStyle(color="gray")}

    scale = config.get("scale", 1.0)

    # 1) Build local geometry
    #----------------------------------------------------------
    I = 0
    caps = []
    e = ExtrusionCollection([], [], [], set(), set())
    for tag in model.iter_cell_tags():

        X_ref = np.array(model.cell_position(tag))
        nen = len(X_ref)

        if state is not None:
            u = state.cell_array(tag, state.position)
            x = shps.curve.displace(X_ref, u, nen)
            R = state.cell_array(tag, state.rotation)
        else:
            x = X_ref
            R = [model.frame_orientation(tag).T]*nen

        sections = [model.frame_section(tag, i) for i in range(len(x))]
        si = sections[0]
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

        if len(si.exterior()) > 25:
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

    # canvas.plot_lines( np.array([
    #         coords[idx] if (j+1)%3 else nan
    #         for j,idx in enumerate(np.array(triang).reshape(-1))
    # ]))
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

    canvas.plot_lines(tri_points,
                      style=config["line_style"])


def draw_extrusions(model, canvas, state=None, config=None):
    ndm = 3

    coords = [] # Global mesh coordinates
    triang = []
    caps   = []
    locoor = [] # Local mesh coordinates, used for textures

    if config is None:
        config = {
                "style": MeshStyle(color="gray")
        }

    scale_section = config["scale"]


    I = 0
    # Track outlines with excessive edges (eg, circles) to later avoid showing
    # their edges
    no_outline = set()
    for tag in model.iter_cell_tags():

        section = model.frame_section(tag)
        if section is None:
            continue

        outline_scale = scale_section

        nen  = len(model.cell_nodes(tag))

        Xi = model.cell_position(tag)
        if state is not None:
            glob_displ = state.cell_array(tag, state.position)
            X = shps.curve.displace(Xi, glob_displ, nen).T
            R = state.cell_array(tag, state.rotation)
        else:
            outline_scale *= 0.99
            X = np.array(Xi)
            R = [model.frame_orientation(tag).T]*nen


        noe = len(section.exterior())
        try:
            face_i = model.frame_section(tag, 0).exterior()[:,1:]
            face_j = model.frame_section(tag, 1).exterior()[:,1:]
            caps.append(I+np.array(earcut(face_i)))
            caps.append(I+(nen-1)*noe + np.array(earcut(face_j)))
        except Exception as e:
            warnings.warn(f"Earcut failed with message: {e}")

        # Loop over sample points along element length to assemble
        # `coord` and `triang` arrays
        for j in range(nen):
            section = model.frame_section(tag, j) # TODO: Pass float between 0 and 1 instead of j
            outline = section.exterior().copy()
            outline[:,1:] *= outline_scale
            # Loop over section edges
            for k,edge in enumerate(outline):
                # Append rotated section coordinates to list of coordinates
                coords.append(X[j, :] + R[j]@edge)
                locoor.append([ (j+0)/nen+0.1,  0.1+(k+0)/(noe+0) ])

                if j == 0:
                    # Skip the first section
                    continue

                elif k < noe-1:
                    triang.extend([
                        [I+    noe*j + k,   I+    noe*j + k + 1,    I+noe*(j-1) + k],
                        [I+noe*j + k + 1,   I+noe*(j-1) + k + 1,    I+noe*(j-1) + k]
                    ])
                else:
                    # elif j < N-1:
                    triang.extend([
                        [I+    noe*j + k,    I + noe*j , I+noe*(j-1) + k],
                        [      I + noe*j, I + noe*(j-1), I+noe*(j-1) + k]
                    ])

                if len(outline) > 25:
                    no_outline.add(len(triang)-1)
                    no_outline.add(len(triang)-2)

        I += nen*noe

    triang = [list(reversed(i)) for i in triang]

    if len(triang) == 0:
        return

    mesh = canvas.plot_mesh(coords, triang, local_coords=locoor, style=config["style"])

    if len(caps) > 0:
        for cap in caps:
            try:
                canvas.plot_mesh(mesh.vertices, cap, style=config["style"])
            except:
                pass


    IDX = np.array((
        (0, 2),
        (0, 1)
    ))

    triang = [list(reversed(i)) for i in triang]

    nan = np.zeros(ndm)*np.nan
    coords = np.array(coords)
    if "tran" in config["outline"]:
        tri_points = np.array([
            coords[idx]  if (j+1)%3 else nan
            for j,idx in enumerate(np.array(triang).reshape(-1))
        ])
    elif "long" in config["outline"]:
        tri_points = np.array([
            coords[i]  if j%2 else nan
            for j,idx in enumerate(np.array(triang)) for i in idx[IDX[j%2]] if j not in no_outline
        ])
    else:
        return

    canvas.plot_lines(tri_points,
                      style=config["line_style"]
    )

def draw_extrusions(model, canvas, state=None, config=None):
    ndm = 3

    coords = [] # Global mesh coordinates
    triang = []
    caps   = []
    locoor = [] # Local mesh coordinates, used for textures

    if config is None:
        config = {
                "style": MeshStyle(color="gray")
        }

    scale_section = config["scale"]


    I = 0
    # Track outlines with excessive edges (eg, circles) to later avoid showing
    # their edges
    no_outline = set()
    for tag in model.iter_cell_tags():

        section = model.frame_section(tag)
        if section is None:
            continue

        outline_scale = scale_section

        nen  = len(model.cell_nodes(tag))

        Xi = model.cell_position(tag)
        if state is not None:
            glob_displ = state.cell_array(tag, state.position)
            X = shps.curve.displace(Xi, glob_displ, nen).T
            R = state.cell_array(tag, state.rotation)
        else:
            outline_scale *= 0.99
            X = np.array(Xi)
            R = [model.frame_orientation(tag).T]*nen


        noe = len(section.exterior())
        try:
            face_i = model.frame_section(tag, 0).exterior()[:,1:]
            face_j = model.frame_section(tag, 1).exterior()[:,1:]
            caps.append(I+np.array(earcut(face_i)))
            caps.append(I+(nen-1)*noe + np.array(earcut(face_j)))
        except Exception as e:
            warnings.warn(f"Earcut failed with message: {e}")

        # Loop over sample points along element length to assemble
        # `coord` and `triang` arrays
        for j in range(nen):
            section = model.frame_section(tag, j) # TODO: Pass float between 0 and 1 instead of j
            outline = section.exterior().copy()
            outline[:,1:] *= outline_scale
            # Loop over section edges
            for k,edge in enumerate(outline):
                # Append rotated section coordinates to list of coordinates
                coords.append(X[j, :] + R[j]@edge)
                locoor.append([ (j+0)/nen+0.1,  0.1+(k+0)/(noe+0) ])

                if j == 0:
                    # Skip the first section
                    continue

                elif k < noe-1:
                    triang.extend([
                        [I+    noe*j + k,   I+    noe*j + k + 1,    I+noe*(j-1) + k],
                        [I+noe*j + k + 1,   I+noe*(j-1) + k + 1,    I+noe*(j-1) + k]
                    ])
                else:
                    # elif j < N-1:
                    triang.extend([
                        [I+    noe*j + k,    I + noe*j , I+noe*(j-1) + k],
                        [      I + noe*j, I + noe*(j-1), I+noe*(j-1) + k]
                    ])

                if len(outline) > 25:
                    no_outline.add(len(triang)-1)
                    no_outline.add(len(triang)-2)

        I += nen*noe

    triang = [list(reversed(i)) for i in triang]

    if len(triang) == 0:
        return

    mesh = canvas.plot_mesh(coords, triang, local_coords=locoor, style=config["style"])

    if len(caps) > 0:
        for cap in caps:
            try:
                canvas.plot_mesh(mesh.vertices, cap, style=config["style"])
            except:
                pass


    IDX = np.array((
        (0, 2),
        (0, 1)
    ))

    triang = [list(reversed(i)) for i in triang]

    nan = np.zeros(ndm)*np.nan
    coords = np.array(coords)
    if "tran" in config["outline"]:
        tri_points = np.array([
            coords[idx]  if (j+1)%3 else nan
            for j,idx in enumerate(np.array(triang).reshape(-1))
        ])
    elif "long" in config["outline"]:
        tri_points = np.array([
            coords[i]  if j%2 else nan
            for j,idx in enumerate(np.array(triang)) for i in idx[IDX[j%2]] if j not in no_outline
        ])
    else:
        return

    canvas.plot_lines(tri_points,
                      style=config["line_style"]
    )

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

    draw_extrusions(artist.model, artist.canvas, config=opts)

    # -----------------------------------------------------------

    soln = veux.state.read_state(res_file, artist.model, **opts)
    if soln is not None:
        if "time" not in opts:
            soln = soln[soln.times[-1]]

        draw_extrusions(artist.model, artist.canvas, soln, opts)
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

