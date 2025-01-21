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
from veux.utility.earcut import earcut
from veux.model import read_model
from veux.errors import RenderError
from veux.config import MeshStyle


def draw_extrusions2(model, canvas, state=None, config=None):
    """
    Draw extruded frame elements into 'canvas' as a simple mesh (side faces + end caps),
    optionally applying displacements/rotations from 'state'.

    'Extrusion' handles building the side + cap faces in local coords, then we map them 
    to global coords using each ring’s X[j] + R[j].

    The final mesh is plotted with 'canvas.plot_mesh'. Then, if config["outline"] 
    includes 'tran' or 'long', we also call 'canvas.plot_lines' for edges or cross-hatching.
    """

    from shps.frame.extrude import Extrusion

    ndm = 3

    if config is None:
        config = {"style": MeshStyle(color="gray")}
    scale_section = config.get("scale", 1.0)

    #----------------------------------------------------------
    # 1) Build local geometry (side + caps)
    #----------------------------------------------------------
    extr = Extrusion(model, scale=scale_section, do_end_caps=True)
    local_positions = extr.vertices()    # Nx3 (local coords)
    triangles       = extr.triangles()   # Mx3
    ring_ranges     = extr.ring_ranges() # [((elem_name,j), start_idx, end_idx), ...]

    if len(triangles) == 0:
        return

    # Create a global array for final coordinates
    coords = np.zeros_like(local_positions, dtype=float)

    # Build 'locoor' for local texture or param 
    # for each vertex.
    locoor = [None]*len(local_positions)

    #----------------------------------------------------------
    # 2) For each ring, apply the global transform X[j] + R[j]@local_pt
    #    from either the reference config or the 'state'
    #----------------------------------------------------------
    for ((elem_name, j), start_idx, end_idx) in ring_ranges:
        el  = model["assembly"][elem_name]
        nen = len(el["nodes"])

        # Original coords for this element
        X_ref = np.array(el["crd"])  # shape (nen, 3)

        if state is not None:
            # Displacements
            glob_displ = state.cell_array(elem_name, state.position)
            # returns a (3, nen) array.
            X_def = shps.curve.displace(X_ref, glob_displ, nen).T

            R_all = state.cell_array(elem_name, state.rotation)  # list of 3x3 or (nen, 3x3)
        else:
            # If no state, just do reference
            X_def = X_ref.T  # shape (3, nen)
            R_all = [model.frame_orientation(elem_name).T]*nen

        # For ring j, we have a 3x1 translation = X_def[:, j]
        # and a rotation R_all[j], which is 3x3
        trans_j = X_def[:, j]
        rot_j   = R_all[j]

        # For each vertex i in [start_idx, end_idx), transform
        for i in range(start_idx, end_idx):
            local_pt = local_positions[i]      # shape (3,)
            # Global coords
            coords[i] = trans_j + rot_j @ local_pt

            # locoor? The original code sets something like
            #   locoor.append([ (j+0)/nen+0.1, 0.1+(k+0)/(noe+0 ) ])
            # But we no longer track the "k" directly, so let's store a placeholder.
            # Or we can store extr.texcoords() if you do that in your Extrusion class.
            locoor[i] = [(j+0)/max(nen,1)+0.1, 0.1]  # minimal

    #----------------------------------------------------------
    # 3) Reverse triangle winding
    #----------------------------------------------------------
    triang = [list(reversed(face)) for face in triangles]

    #----------------------------------------------------------
    # 4) Plot the main mesh
    #----------------------------------------------------------
    canvas.plot_mesh(coords, triang, local_coords=locoor, style=config["style"])

    if "outline" not in config:
        return

    #----------------------------------------------------------
    # 5) Draw edges
    #----------------------------------------------------------
    nan = np.array([0,0,0], dtype=float)*np.nan
    IDX = np.array(((0,2),(0,1)))  # from your code

    if "tran" in config["outline"]:
        #   tri_points = [ coords[idx] if (j+1)%3 else nan for j,idx in enumerate(np.array(triang).reshape(-1)) ]
        tri_flat = np.array(triang).reshape(-1)
        tri_points = []
        for j, idx in enumerate(tri_flat):
            # after each 3rd vertex, we insert a nan
            tri_points.append(coords[idx])
            if (j+1)%3 == 0:
                tri_points.append(nan)
        tri_points = np.array(tri_points)
        canvas.plot_lines(tri_points, style=config.get("line_style", None))

    elif "long" in config["outline"]:
        # replicate that logic for "long"
        # tri_points = [ coords[i] if j%2 else nan for j,face in enumerate(triang) for i in face[IDX[j%2]] ]
        # Omit "if j not in no_outline" since it's the original logic 
        # for skipping edges on big outlines.
        tri_points = []
        tri_array  = np.array(triang)
        for j, face in enumerate(tri_array):
            # each face is [i0,i1,i2]
            # pick out face[IDX[j%2]] => [face[idx0], face[idx1]]
            # then for each i in that pair, we do coords[i], unless we do the 'nan' row
            if j%2 == 0:
                # put a nan row to separate from previous?
                tri_points.append(nan)
            i0 = face[IDX[j%2][0]]
            i1 = face[IDX[j%2][1]]
            tri_points.append(coords[i0])
            tri_points.append(coords[i1])

        tri_points = np.array(tri_points)
        canvas.plot_lines(tri_points, style=config.get("line_style", None))

    return

def draw_extrusions(model, canvas, state=None, config=None):
    #
    #     x-------o---------o---------o
    #   /       /         /
    # x--------o<--------o---------o
    # |        |       / ^
    # |        |     /   |
    # |        |   /     |
    # |        | /       |
    # x--------o-------->o---------o
    #
    ndm = 3

    coords = [] # Global mesh coordinates
    triang = [] # Triangle indices into coords
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
    for i,el in enumerate(model["assembly"].values()):
        tag  = el["name"]

        outline = model.cell_section(el["name"])
        if outline is None:
            continue

        outline_scale = scale_section

        nen  = len(el["nodes"])

        noe = len(outline) # number of outline edges
        if state is not None:
            glob_displ = state.cell_array(tag, state.position)
            X = shps.curve.displace(el["crd"], glob_displ, nen).T
            R = state.cell_array(tag, state.rotation)
        else:
            outline = outline*0.99
            outline_scale *= 0.99
            X = np.array(el["crd"])
            R = [model.frame_orientation(tag).T]*nen


        try:
            caps.append(I+np.array(earcut(model.cell_section(tag, 0)[:,1:])))
            caps.append(I+(nen-1)*noe + np.array(earcut(model.cell_section(tag, 1)[:,1:])))
        except Exception as e:
            warnings.warn(f"Earcut failed with message: {e}")


        # Loop over sample points along element length to assemble
        # `coord` and `triang` arrays
        for j in range(nen):
            outline = model.cell_section(tag, j).copy() # TODO: Pass float between 0 and 1 instead of j
            outline[:,1:] *= outline_scale
            # Loop over section edges
            for k,edge in enumerate(outline):
                # Append rotated section coordinates to list of coordinates
                coords.append(X[j, :] + R[j]@edge)
                locoor.append(
                             [ (j+0)/nen+0.1,  0.1+(k+0)/(noe+0) ]
                )


                if j == 0:
                    # Skip the first section
                    continue

                elif k < noe-1:
                    triang.extend([
                        # Tie two triangles to this edge
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

