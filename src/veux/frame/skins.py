#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
import warnings
from collections import defaultdict

import numpy as np
from scipy.spatial.transform import Rotation

import pygltflib
from pygltflib import FLOAT, UNSIGNED_SHORT
from pygltflib import AnimationChannelTarget

from veux.config import MeshStyle
from veux.utility.earcut import earcut


def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1

def create_extrusion(model, canvas, config=None):
    """
    Builds a single skinned mesh for all frame elements in the reference (undeformed) configuration.
    Returns a dictionary mapping (element_name, cross_section_index) -> glTF node index,
    so you can update those node transforms later.

    :param model: The dictionary-like structural model (with 'assembly', .cell_section, .frame_orientation, etc.)
    :param gltf:  A pygltflib.GLTF2 object in which we will insert geometry, nodes, and the skin.
    :param config: Optional dict with style info, scale, etc.
    :return: extrusion = {(element_name, j): node_index, ...}
    """
    gltf = canvas.gltf

    if config is None:
        config = {
            "style": MeshStyle(color="gray"),
            "scale": 1.0,      # Factor for cross-sectional outline
            "outline": "",
        }

    # Some placeholders to accumulate geometry
    positions   = []  # Vertex positions in the mesh's BIND pose (local coords for each ring)
    joints_0    = []  # glTF's JOINTS_0 attribute
    weights_0   = []  # glTF's WEIGHTS_0 attribute
    texcoords   = []  # If you want to store local or UV coords
    indices     = []  # Triangles for side faces
    cap_indices = []  # Triangles for end caps

    # We also need to track each cross-section Node (joint) and its inverseBindMatrix
    joint_nodes    = []     # glTF node indices
    inverse_bind_matrices = []     # 4x4 float32 arrays (one per joint)
    skin_nodes = {}                  # (element_name, j) -> glTF node index

    def _make_matrix(translation, rotmat):
        """Build a 4x4 transform from translation + 3x3 rotation matrix."""
        M = np.eye(4, dtype=canvas.float_t)
        M[:3, :3] = rotmat
        M[:3,  3] = translation
        return M

    # We’ll need to keep track of how many vertices so far, to build faces correctly
    global_vertex_offset = 0

    #------------------------------------------------------
    # 1) Loop over each element in the model
    #    Build cross-section nodes (reference config)
    #    Accumulate geometry into a single big mesh
    #------------------------------------------------------
    for element_name, el in model["assembly"].items():
        outline_0 = model.cell_section(el["name"], 0)
        if outline_0 is None:
            continue

        # For reference config, just read the original coordinates
        X = np.array(el["crd"])  # shape: (nen, 3)
        nen = len(X)
        noe = len(outline_0)  # number of edges in cross-section outline
        outline_scale = config.get("scale", 1.0)

        # Each cross-section j gets its own Node in glTF
        # We'll get a reference orientation from model.frame_orientation(...).T
        R_all = [model.frame_orientation(el["name"]).T]*nen

        for j in range(nen):
            # 1A) Create a node for cross section j
            node = pygltflib.Node()
            node.translation = X[j,:].tolist()

            # Convert the rotation matrix to a quaternion
            rot_mat = R_all[j]
            qx, qy, qz, qw = Rotation.from_matrix(rot_mat).as_quat()
            node.rotation = [qx, qy, qz, qw]

            this_node_idx = _append_index(gltf.nodes, node)

            # Record in extrusion
            skin_nodes[(element_name, j)] = this_node_idx

            # 1B) Compute the bind pose for this cross section
            M_bind    = _make_matrix(X[j,:], rot_mat)
            M_bind_inv = np.linalg.inv(M_bind)
            inverse_bind_matrices.append(M_bind_inv)
            joint_nodes.append(this_node_idx)

            # 1C) Append the ring geometry in local coords
            #     (i.e. how the ring is positioned relative to node’s origin)
            #     For a pure reference, we can treat ring coords as cross-section local
            outline_j = model.cell_section(el["name"], j).copy()
            outline_j[:,1:] *= outline_scale

            for k, edge in enumerate(outline_j):
                # edge is (x, y, z) in local cross-section coords
                positions.append(edge.astype(canvas.float_t))

                # JOINTS_0 & WEIGHTS_0: rigidly bound to this cross-section's node
                joints_0.append([len(joint_nodes)-1, 0, 0, 0])  # Single joint index
                weights_0.append([1.0, 0.0, 0.0, 0.0])

                # Optional: store a cheap local texcoord
                texcoords.append([
                    j/(nen-1) if (nen>1) else 0.0,
                    k/(noe-1) if (noe>1) else 0.0
                ])

                # Build side faces by connecting ring (j) to ring (j-1)
                if j>0 and k<noe-1:
                    indices.append([
                        global_vertex_offset + noe*j + k,
                        global_vertex_offset + noe*j + (k+1),
                        global_vertex_offset + noe*(j-1) + k
                    ])
                    indices.append([
                        global_vertex_offset + noe*j + (k+1),
                        global_vertex_offset + noe*(j-1) + (k+1),
                        global_vertex_offset + noe*(j-1) + k
                    ])

                elif j>0 and k == (noe-1):
                    # wrap-around
                    indices.append([
                        global_vertex_offset + noe*j + k,
                        global_vertex_offset + noe*j,
                        global_vertex_offset + noe*(j-1) + k
                    ])
                    indices.append([
                        global_vertex_offset + noe*j,
                        global_vertex_offset + noe*(j-1),
                        global_vertex_offset + noe*(j-1) + k
                    ])

        # End for j in range(nen)

        # Earcut-based end caps for j=0 and j=nen-1
        try:
            front_outline = model.cell_section(el["name"], 0)[:,1:]
            front_idx     = earcut(front_outline)
            j0_offset     = global_vertex_offset
            # ring 0 has vertices [j0_offset .. j0_offset + noe -1]

            back_outline  = model.cell_section(el["name"], nen-1)[:,1:]
            back_idx      = earcut(back_outline)
            jN_offset     = global_vertex_offset + noe*(nen-1)

            # Convert earcut output to global indices
            for tri in front_idx:
                cap_indices.append([
                    j0_offset + tri[0],
                    j0_offset + tri[1],
                    j0_offset + tri[2],
                ])
            for tri in back_idx:
                cap_indices.append([
                    jN_offset + tri[0],
                    jN_offset + tri[1],
                    jN_offset + tri[2],
                ])
        except Exception as e:
            warnings.warn(f"Earcut failed for element '{element_name}' in ref config: {e}")

        # Increase global_vertex_offset now that we’ve added nen rings
        global_vertex_offset += nen * noe

    # Combine side + cap indices
    indices.extend(cap_indices)

    if len(positions)==0 or len(indices)==0:
        # No geometry
        return skin_nodes
    
    skin = _create_skin(canvas, inverse_bind_matrices, joint_nodes)
    _create_mesh(canvas, skin, positions, texcoords, joints_0,  weights_0, indices)
    return skin_nodes


def _create_skin(canvas, ibms, joint_nodes):
    #---------------------------------------------
    # 2) Create a Skin referencing given joints
    #---------------------------------------------
    gltf = canvas.gltf

    # Flatten the inverse bind matrices into an Nx16 float32 array
    ibm_array = np.array(ibms, dtype=canvas.float_t).reshape(-1,16)

    # Create accessor to inverse bind matrices and skin
    skin = pygltflib.Skin(
        inverseBindMatrices=_append_index(gltf.accessors, pygltflib.Accessor(
            bufferView=canvas._push_data(ibm_array.tobytes(), target=None),
            componentType=FLOAT,
            count=len(ibms),
            type="MAT4"
        )),
        joints=joint_nodes,
        skeleton=joint_nodes[0] if len(joint_nodes)>0 else 0,
        name="FrameExtrusionSkin"
    )

    if not gltf.skins:
        gltf.skins = []

    return _append_index(gltf.skins, skin)

def _create_mesh(canvas, skin_idx,
                  positions, 
                  texcoords, 
                  joints_0,  
                  weights_0, 
                  indices):
    
    gltf = canvas.gltf
    #---------------------------------------------
    # 3) Build the big mesh with {POSITION, JOINTS_0, WEIGHTS_0, TEXCOORD_0}
    #---------------------------------------------
    positions = np.array(positions, dtype=canvas.float_t)
    texcoords = np.array(texcoords, dtype=canvas.float_t)
    joints_0  = np.array(joints_0,  dtype=canvas.index_t)
    weights_0 = np.array(weights_0, dtype=canvas.float_t)
    indices   = np.array(indices,   dtype=canvas.index_t).reshape(-1)

    pos_bytes = positions.tobytes()
    tex_bytes = texcoords.tobytes()
    jnt_bytes = joints_0.tobytes()
    wts_bytes = weights_0.tobytes()
    idx_bytes = indices.tobytes()

    pos_bv_idx = canvas._push_data(pos_bytes, pygltflib.ARRAY_BUFFER)
    tex_bv_idx = canvas._push_data(tex_bytes, pygltflib.ARRAY_BUFFER)
    jnt_bv_idx = canvas._push_data(jnt_bytes, pygltflib.ARRAY_BUFFER)
    wts_bv_idx = canvas._push_data(wts_bytes, pygltflib.ARRAY_BUFFER)
    idx_bv_idx = canvas._push_data(idx_bytes, pygltflib.ELEMENT_ARRAY_BUFFER)

    # Accessors
    gltf.accessors.append(pygltflib.Accessor(
        bufferView=pos_bv_idx,
        componentType=FLOAT,
        count=len(positions),
        type="VEC3",
        min=positions.min(axis=0).tolist(),
        max=positions.max(axis=0).tolist()
    ))
    pos_accessor_idx = len(gltf.accessors)-1

    tex_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=tex_bv_idx,
        componentType=FLOAT,
        count=len(texcoords),
        type="VEC2"
    ))

    jnt_accessor_idx = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=jnt_bv_idx,
        componentType=UNSIGNED_SHORT,
        count=len(joints_0),
        type="VEC4"
    ))

    wts_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
        bufferView=wts_bv_idx,
        componentType=FLOAT,
        count=len(weights_0),
        type="VEC4"
    ))

    idx_accessor = pygltflib.Accessor(
        bufferView=idx_bv_idx,
        componentType=UNSIGNED_SHORT,
        count=len(indices),
        type="SCALAR",
        min=[int(indices.min())],
        max=[int(indices.max())]
    )
    gltf.accessors.append(idx_accessor)
    idx_accessor_idx = len(gltf.accessors)-1

    # Create the Primitive and Mesh
    mesh = pygltflib.Mesh(
        primitives=[
            pygltflib.Primitive(
                attributes=pygltflib.Attributes(
                    POSITION=pos_accessor_idx,
                    JOINTS_0=jnt_accessor_idx,
                    WEIGHTS_0=wts_accessor,
                    TEXCOORD_0=tex_accessor
                ),
                indices=idx_accessor_idx,
                mode=pygltflib.TRIANGLES
            )
        ],
        name="FrameExtrusionMesh"
    )

    if not gltf.meshes:
        gltf.meshes = []

    mesh_idx = _append_index(gltf.meshes, mesh)

    #---------------------------------------------
    # 4) Create a Node referencing the mesh + skin
    #---------------------------------------------
    gltf.nodes.append(pygltflib.Node(
        mesh=mesh_idx,
        skin=skin_idx,
        name="FrameExtrusionMeshNode"
    ))
    mesh_node_idx = len(gltf.nodes)-1

    # Put it in the scene
    if not gltf.scenes or len(gltf.scenes)==0:
        gltf.scenes = [pygltflib.Scene(nodes=[])]

    gltf.scenes[0].nodes.append(mesh_node_idx)



def deform_extrusion(model, canvas, state, skin_nodes, config=None):
    """
    Given a 'state' that contains the updated (displaced/rotated) coordinates for each element’s cross section,
    update the glTF nodes' translation/rotation accordingly.

    :param model:    The same structural model used in draw_extrusions_ref.
    :param gltf:     The glTF2 object that already has nodes, a skin, etc.
    :param state:    Some data structure that can provide displacements & rotations for each (element, cross section).
    :param skin_nodes: Dict returned by draw_extrusions_ref -> {(element_name, j): node_index, ...}
    :param config:   Optional dict for additional settings (e.g. scale, etc).


    The skinned mesh in glTF will automatically show the new shape
    as the viewer or engine processes the node transforms.
    """
    gltf = canvas.gltf 

    if config is None:
        config = {}

    for element_name, el in model["assembly"].items():
        # If we have no displacement/rotation for this element in 'state', skip
        if element_name not in state.element_names:
            continue

        # Number of cross sections
        nen = len(el["nodes"])

        # Displacements & rotations from 'state' for each cross-section
        # E.g.:
        pos_all = state.cell_array(el["name"], state.position)  # shape (nen, 3?)
        rot_all = state.cell_array(el["name"], state.rotation)  # shape (nen, 3x3) ?

        # Original coordinates
        X_ref = np.array(el["crd"])  # shape (nen, 3)

        for j in range(nen):
            # Look up the node index in glTF
            if (element_name, j) not in skin_nodes:
                continue
            node_idx = skin_nodes[(element_name, j)]

            # Deformed translation
            x_def = X_ref[j,:] + pos_all[j,:]
            gltf.nodes[node_idx].translation = x_def.tolist()

            # Deformed rotation
            R_def = rot_all[j]  # presumably a 3x3 array
            qx, qy, qz, qw = Rotation.from_matrix(R_def).as_quat()
            gltf.nodes[node_idx].rotation = [qx, qy, qz, qw]


class VeuxAnimation:
    """
    A helper class that accumulates multiple "states" (deformed configurations)
    and creates a time-based glTF Animation. Each call to add_state() adds
    a new keyframe at the next time step.
    """

    def __init__(self, model=None, time_step=1.0, name="BeamDeformations"):
        """
        :param canvas:   An instance of your GltfCanvas (with .gltf).
        :param extrusion: Dict {(element_name, j): gltf_node_index, ...}
                         returned by draw_extrusions_ref().
        :param time_step: The time increment for each added state (seconds, or frames).
        :param name: The name of the final glTF animation.
        """
        self.model = model

        self.time_step = time_step
        self.current_time = 0.0
        self.anim_name = name

        # We'll store keyframes in a dictionary:
        #   self._keyframes[node_idx]["translation"] = [(t0, (x,y,z)), (t1, (x,y,z)), ...]
        #   self._keyframes[node_idx]["rotation"]    = [(t0, (qx,qy,qz,qw)), (t1, ...), ...]
        self._keyframes = defaultdict(lambda: {"translation": [], "rotation": []})
    

    def advance(self):
        self.current_time += self.time_step

    def set_mode_state():
        pass

    def add_node_position(self, node, position, time=None):
        if time is None: 
            time = self.current_time

        self._keyframes[node]["translation"].append((time, position))
        
    def add_node_rotation(self, node, rotation, time=None):
        if time is None: 
            time = self.current_time

        self._keyframes[node]["rotation"].append((time, rotation))
        

    def add_skin_state(self, state, skin_nodes):
        """
        Given a 'state' that has deformed positions & rotations for each element’s cross-section,
        record a new keyframe at the current time. Then advance self.current_time by self.time_step.
        
        :param model:  The same structural model used in draw_extrusions_ref().
        :param state:  Some data structure that can provide displacements & rotations
                       for each (element, cross_section_index).
        """
        model = self.model
        # For each element in the model
        for element_name, el in model["assembly"].items():
            if element_name not in state.element_names:
                # No data in this state for that element
                continue

            # number of cross sections
            nen = len(el["nodes"])

            # Original reference coordinates (before deformation)
            X_ref = np.array(el["crd"])  # (nen, 3)

            # Displacements & rotations from 'state'
            disp_all = state.cell_array(el["name"], state.position)   # shape (nen,3?)
            rot_all  = state.cell_array(el["name"], state.rotation)   # shape (nen,3x3)?

            for j in range(nen):
                # look up the glTF node index
                key = (element_name, j)
                if key not in skin_nodes:
                    continue

                node_idx = skin_nodes[key]

                # compute final position for cross section j
                x_def = X_ref[j] + disp_all[j]
                # convert rotation matrix -> quaternion
                R_def = rot_all[j]  # 3x3
                qx, qy, qz, qw = Rotation.from_matrix(R_def).as_quat()

                # store a keyframe
                self.add_node_position(skin_nodes[key], (x_def[0], x_def[1], x_def[2]))
                self.add_node_rotation(skin_nodes[key], (qx, qy, qz, qw))

    def apply(self, canvas):
        """
        Build a glTF Animation from the accumulated keyframes and
        then let the canvas write the final file.
        """
        gltf = canvas.gltf
    
        if not self._keyframes:
            return

        # 1) Create an Animation object
        anim = pygltflib.Animation(name=self.anim_name,
                                   samplers=[],
                                   channels=[])

        # We'll create multiple samplers and channels:
        #   - For each node, we have two samplers (translation, rotation)
        #   - Then two channels referencing those samplers

        # We'll need to record the *sampler index* for each node property as we build them
        # so we can attach channels referencing the correct sampler.
        node_position_sampler_index = {}
        node_rotation_sampler_index = {}

        # 2) Flatten & encode data for each node
        # We do them all in a single big set of buffers—time values and output values.
        # However, each node gets its own Sampler, because it has distinct times/values
        # in this naive implementation. (We could share times if they match exactly.)
        for node_idx, track_dict in self._keyframes.items():
            pos_keyframes = track_dict["translation"]  # list of (time, (x,y,z))
            rot_keyframes = track_dict["rotation"]     # list of (time, (qx,qy,qz,qw))

            if not pos_keyframes and not rot_keyframes:
                continue

            # Sort them by time just in case user added states out of order
            pos_keyframes.sort(key=lambda x: x[0])
            rot_keyframes.sort(key=lambda x: x[0])


            if pos_keyframes:
                # Create Sampler for translation
                sampler_index_t = _append_index(anim.samplers, pygltflib.AnimationSampler(
                    input=-1,    # placeholder, we fill them after we create Accessors
                    output=-1,   # also placeholder
                    interpolation="LINEAR"
                ))
                node_position_sampler_index[node_idx] = sampler_index_t
                # Temporarily store the arrays so we can embed them in the glTF buffer
                # after building all samplers.
                anim.samplers[sampler_index_t].extras = {
                    "times_array": np.array([k[0] for k in pos_keyframes], dtype=canvas.float_t),
                    "vals_array":  np.array([k[1] for k in pos_keyframes], dtype=canvas.float_t)  # shape (N,3)
                }
            
            if rot_keyframes:
                # Create Sampler for rotation
                sampler_index_r = _append_index(anim.samplers, pygltflib.AnimationSampler(
                    input=-1,
                    output=-1,
                    interpolation="LINEAR"
                ))
                node_rotation_sampler_index[node_idx] = sampler_index_r

                # Temporarily store the arrays so we can embed them in the glTF buffer
                # after building all samplers.
                anim.samplers[sampler_index_r].extras = {
                    "times_array": np.array([k[0] for k in rot_keyframes],   dtype=canvas.float_t),
                    "vals_array":  np.array([k[1] for k in rot_keyframes],   dtype=canvas.float_t)  # shape (N,4)
                }

        # 3) Now create Channels referencing each sampler
        for node_idx in self._keyframes:
            if node_idx in node_position_sampler_index:

                # Create a channel for translation
                anim.channels.append(pygltflib.AnimationChannel(
                    sampler=node_position_sampler_index[node_idx],
                    target=AnimationChannelTarget(
                        node=node_idx,
                        path="translation"
                    )
                ))

            if node_idx in node_rotation_sampler_index:
                # Create a channel for rotation
                anim.channels.append(pygltflib.AnimationChannel(
                    sampler=node_rotation_sampler_index[node_idx],
                    target=AnimationChannelTarget(
                        node=node_idx,
                        path="rotation"
                    )
                ))


        # 4) Insert the actual time / value data into glTF buffers.
        #    We'll create BufferViews and Accessors, then fix up each sampler's input/output
        #    to reference the newly created accessor indices.
        #    We'll do this "in bulk," iterating over new_animation.samplers
        for sampler in anim.samplers:

            # Accessors
            time_accessor_idx = _append_index(gltf.accessors, pygltflib.Accessor(
                bufferView=canvas._push_data(sampler.extras["times_array"].tobytes()),
                byteOffset=0,
                componentType=FLOAT,
                count=len(sampler.extras["times_array"]),
                type="SCALAR",
                min=[float(sampler.extras["times_array"].min())],
                max=[float(sampler.extras["times_array"].max())]
            ))

            # If path=="translation", we have 3 floats, if path=="rotation", we have 4.
            # But we already know shape from sampler.extras["vals_array"].shape
            val_type = "VEC3" if sampler.extras["vals_array"].shape[1]==3 else "VEC4"

            vals_accessor_idx = _append_index(gltf.accessors, pygltflib.Accessor(
                bufferView=canvas._push_data(sampler.extras["vals_array"].tobytes()),
                byteOffset=0,
                componentType=FLOAT,
                count=len(sampler.extras["vals_array"]),
                type=val_type
            ))

            # Now fix the sampler's input/output
            sampler.input  = time_accessor_idx
            sampler.output = vals_accessor_idx

            # remove extras so it won't try to JSON-serialize large arrays
            del sampler.extras["times_array"]
            del sampler.extras["vals_array"]


        # 5) Attach this new Animation to the glTF
        if not gltf.animations:
            gltf.animations = []

        i = _append_index(gltf.animations, anim)


def create_animation(artist, states, skin_nodes=None):

    # 1) Draw reference configuration with extrusions -> returns extrusion
    if skin_nodes is None:
        skin_nodes = create_extrusion(artist.model, artist.canvas)

    # 2) Create the animation helper
    animation = VeuxAnimation(artist.model, time_step=0.1)

    # 3) For each state, record a new keyframe
    for state in states:
        animation.add_skin_state(state, skin_nodes)
        animation.advance()

    animation.apply(artist.canvas)
    return animation



def _render(sam_file, res_file=None, **opts):
    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds
    
    from veux.model import read_model 

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

    skin_nodes = create_extrusion(artist.model, artist.canvas, config=opts)

    soln = veux.state.read_state(res_file, artist.model, **opts)
    if soln is not None:
        if "time" not in opts:
            create_animation(artist, soln, skin_nodes)
        else:
            deform_extrusion(artist.model, artist.canvas, soln, skin_nodes)

    # artist.draw()
    return artist


if __name__ == "__main__":
    import sys
    from veux.errors import RenderError
    import veux.parser
    config = veux.parser.parse_args(sys.argv)

    try:
        artist = _render(**config)

        # write plot to file if output file name provided
        if config["write_file"]:
            artist.save(config["write_file"])

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

