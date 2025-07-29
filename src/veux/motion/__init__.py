#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Copyright (c) 2025, Claudio M. Perez
# All rights reserved.  No warranty, explicit or implicit, is provided.
#
# This source code is licensed under the BSD 2-Clause License.
# See LICENSE file or https://opensource.org/licenses/BSD-2-Clause
#
from .frame import Motion, skin_frames


import numpy as np
from scipy.spatial.transform import Rotation

import pygltflib

from veux.canvas.gltf import GLTF_T


def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1

def _create_mesh(canvas,
                  positions,
                  texcoords,
                  joints_0,
                  weights_0,
                  indices,
                  skin_idx=None,
                  material=None):
    
    gltf = canvas.gltf
    joints_0  = np.array(joints_0,  dtype=canvas.index_t)
    weights_0 = np.array(weights_0, dtype=canvas.float_t)
    indices   = np.array(indices,   dtype=canvas.index_t).reshape(-1)

    jnt_bytes = joints_0.tobytes()
    wts_bytes = weights_0.tobytes()

    # Accessors
    positions = np.array(positions, dtype=canvas.float_t)
    ver_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=canvas._push_data(positions.tobytes(), pygltflib.ARRAY_BUFFER),
        componentType=GLTF_T[canvas.float_t],
        count=len(positions),
        type="VEC3",
        min=positions.min(axis=0).tolist(),
        max=positions.max(axis=0).tolist()
    ))

    texcoords = np.array(texcoords, dtype=canvas.float_t)
    tex_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=canvas._push_data(texcoords.tobytes(), pygltflib.ARRAY_BUFFER),
        componentType=GLTF_T[canvas.float_t],
        count=len(texcoords),
        type="VEC2"
    ))

    jnt_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=canvas._push_data(jnt_bytes, pygltflib.ARRAY_BUFFER),
        componentType=GLTF_T[canvas.index_t],
        count=len(joints_0),
        type="VEC4"
    ))

    wts_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=canvas._push_data(wts_bytes, pygltflib.ARRAY_BUFFER),
        componentType=GLTF_T[canvas.float_t],
        count=len(weights_0),
        type="VEC4"
    ))


    idx_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=canvas._push_data(indices.tobytes(), pygltflib.ELEMENT_ARRAY_BUFFER),
        componentType=GLTF_T[canvas.index_t],
        count=len(indices),
        type="SCALAR",
        min=[int(indices.min())],
        max=[int(indices.max())]
    ))

    # Create the Mesh
    mesh = pygltflib.Mesh(
        primitives=[
            pygltflib.Primitive(
                attributes=pygltflib.Attributes(
                    POSITION=ver_accessor,
                    JOINTS_0=jnt_accessor,
                    WEIGHTS_0=wts_accessor,
                    TEXCOORD_0=tex_accessor
                ),
                material=material,
                indices=idx_accessor,
                mode=pygltflib.TRIANGLES
            )
        ],
        name="FrameSkinMesh"
    )

    mesh_idx = _append_index(gltf.meshes, mesh)

    #
    # 4) Create a Node referencing the mesh + skin
    #
    mesh_node_idx = _append_index(gltf.nodes, pygltflib.Node(
        mesh=mesh_idx,
        skin=skin_idx,
        name="FrameSkinMeshNode"
    ))

    # Put it in the scene
    if not gltf.scenes or len(gltf.scenes)==0:
        gltf.scenes = [pygltflib.Scene(nodes=[])]

    gltf.scenes[0].nodes.append(mesh_node_idx)



def deform_extrusion(model, canvas, state, skin_nodes, config=None):
    """
    Given a 'state' that contains the updated (displaced/rotated) coordinates 
    for each element’s cross section,
    update the glTF nodes' translation/rotation accordingly.

    The skinned mesh in glTF will automatically show the new shape
    as the viewer or engine processes the node transforms.
    """
    gltf = canvas.gltf 

    if config is None:
        config = {}

    for element_name, el in model["assembly"].items():

        # Number of cross sections
        nen = len(el["nodes"])
        # TODO: Make these consistent with draw_sections
        # Displacements and rotations from 'state' for each cross-section
        pos_all = state.cell_array(element_name, state.position)  # shape (nen, 3?)
        rot_all = state.cell_array(element_name, state.rotation)  # shape (nen, 3x3) ?

        # Original coordinates
        X_ref = np.array(el["crd"])  # shape (nen, 3)

        for j in range(nen):
            # Look up the node index in glTF
            if (element_name, j) not in skin_nodes:
                continue
            node_idx = skin_nodes[(element_name, j)]


            gltf.nodes[node_idx].translation = (X_ref[j,:] + pos_all[j,:]).tolist()
            gltf.nodes[node_idx].rotation = [*Rotation.from_matrix(rot_all[j] ).as_quat()]


def create_animation(artist, states=None, skin_nodes=None):

    # 2) Create the animation helper
    animation = Motion(artist)

    # 3) For each state, record a new keyframe
    for time in states.times:
        animation.draw_sections(state=states[time])
        animation.advance()

    animation.add_to(artist.canvas)
    return animation


def _animate(sam_file, res_file=None, vertical=None, **opts):
    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds
    from veux.frame import FrameArtist
    import veux.canvas.gltf
    from veux.model import read_model

    config = veux.config.Config()


    if sam_file is None:
        raise RenderError("Expected positional argument <sam-file>")

    if isinstance(sam_file, (str,)):
        model = read_model(sam_file)

    elif hasattr(sam_file, "asdict"):
        # Assuming an opensees.openseespy.Model
        model = sam_file.asdict()

    elif hasattr(sam_file, "read"):
        model = read_model(sam_file)


    if "RendererConfiguration" in model:
        veux.apply_config(model["RendererConfiguration"], config)

    veux.apply_config(opts, config)
    if vertical is not None:
        config["artist_config"]["vertical"] = vertical

    artist = FrameArtist(model, ndf=6,
                         config=config["artist_config"],
                         model_config=config["model_config"],
                         canvas=veux.canvas.gltf.GltfLibCanvas())


    if res_file is not None:
        if isinstance(res_file, str):
#           soln = artist.model.wrap_state(res_file)
            soln = veux.model.read_state(res_file, artist.model, **opts["state_config"])
        else:
            from veux.state import GroupSeriesSE3, StateSeries
            series = StateSeries(res_file, artist.model,
                transform = artist.dofs2plot,
                recover_rotations="conv"
            )
            soln = GroupSeriesSE3(series, artist.model, recover_rotations="conv", transform=artist.dofs2plot)

        if "time" not in opts:
            create_animation(artist, soln)
        else:
            skin_nodes,_ = skin_frames(artist.model, 
                                       artist.canvas,
                                        config=artist._config_sketch("default")["surface"]["frame"])
            deform_extrusion(artist.model, artist.canvas, soln, skin_nodes)

    return artist


if __name__ == "__main__":
    import sys
    from veux.errors import RenderError
    import veux.parser
    config = veux.parser.parse_args(sys.argv)

    try:
        artist = _animate(**config)

        # write plot to file if output file name provided
        if config["write_file"]:
            artist.save(config["write_file"])

        # Otherwise either create popup, or start server
        elif hasattr(artist.canvas, "popup"):
            artist.canvas.popup()

        elif hasattr(artist.canvas, "to_glb"):
            from veux.server import Server
            from veux.viewer import Viewer
            viewer = Viewer(artist, viewer=config["viewer_config"].get("name", None))
            port = config["server_config"].get("port", None)
            server = Server(viewer=viewer)
            server.run(port=port)

        elif hasattr(artist.canvas, "to_html"):
            import veux.server
            port = config["server_config"].get("port", None)
            server = veux.server.Server(html=artist.canvas.to_html())
            server.run(port=port)

    except (FileNotFoundError, RenderError) as e:
        # Catch expected errors to avoid printing an ugly/unnecessary stack trace.
        print(e, file=sys.stderr)
        print("         Run '{NAME} --help' for more information".format(NAME=sys.argv[0]), file=sys.stderr)
        sys.exit()

