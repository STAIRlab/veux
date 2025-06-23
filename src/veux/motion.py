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
from pygltflib import FLOAT

from veux.canvas.gltf import GLTF_T
from veux.config import MeshStyle, LineStyle
from veux.utility.earcut import earcut

def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1

from veux.frame.extrude import ExtrusionCollection, add_extrusion
from shps.frame.extrude import FrameMesh

def skin_frames(model, artist, config=None):
    """
    REFACTORED TO USE ExtrusionCollection

    Builds a skinned mesh for all frame elements in the reference (undeformed) configuration.
    Returns a dictionary mapping (element_name, j) -> glTF node index
    """
    if config is None:
        config = {
            "style": MeshStyle(color="gray"),
            "scale": 1.0,
            "outline": "",
        }
    scale = config.get("scale", 1.0)
    canvas = artist.canvas 
    Ra = artist._plot_rotation


    #
    # Create a skeleton root node
    #
    gltf = canvas.gltf
    skeleton_root_node = pygltflib.Node(name="FrameExtrusionSkeletonRoot", children=[])
    skeleton_root_idx = _append_index(gltf.nodes, skeleton_root_node)
    gltf.scenes[0].nodes.append(skeleton_root_idx)

    #
    joint_nodes = skeleton_root_node.children
    ibms = []
    skin_nodes = {}
    joint_elements = []

    def _bind_inv(translation, rotmat):
        M = np.eye(4, dtype=canvas.float_t)
        M[:3,:3] = rotmat
        M[:3, 3] = translation
        return np.linalg.inv(M).T

    #
    # 3) For each ring, create a glTF Node (joint),
    #    and assign ring vertices to that joint
    #
    I = 0
    joints_0    = [] #np.zeros((num_vertices,4), dtype=canvas.index_t)
    weights_0   = [] #np.zeros((num_vertices,4), dtype=canvas.float_t)
    e = ExtrusionCollection([], [], [], set(), set())
    for tag in model.iter_cell_tags():
        if not model.cell_matches(tag, "frame"):
            continue

        X = np.array([Ra@model.node_position(n) for n in model.cell_nodes(tag)])
        R = [Ra@model.frame_orientation(tag).T]*len(X)

        sections = [model.frame_section(tag, i) for i in range(len(X))]

        if sections[0] is None or sections[-1] is None:
            continue

        extr = FrameMesh(len(X),
                        [s.exterior() for s in sections],
                        scale=scale,
                        do_end_caps=False)

        I += add_extrusion(extr, e, X, R, I)

        for j, start_idx, end_idx in extr.ring_ranges():
            #
            node = pygltflib.Node()
            node.translation =  X[j].tolist()
            node.rotation    =  Rotation.from_matrix(R[j]).as_quat().tolist()

            skin_nodes[(tag, j)] = _append_index(gltf.nodes, node)

            # add to skeleton root
            joint = _append_index(joint_nodes, skin_nodes[(tag, j)])
            joint_elements.append((tag, j))

            ibms.append(_bind_inv(X[j], R[j]))

            for i in range(start_idx, end_idx):
                # Mark all vertices as belonging 100% to this joint
                joints_0.append( [joint, 0., 0., 0.])
                weights_0.append([  1.0, 0., 0., 0.])

    # 4) Create the Skin referencing these joints
    #------------------------------------------------------
    skin = _create_skin(canvas, ibms, joint_nodes, skeleton_root_idx)

    # 5) Build the mesh
    #------------------------------------------------------
    if len(e.coords):
        canvas.plot_mesh(e.coords,
                        [list(reversed(face)) for face in e.triang],
                        joints_0=joints_0,
                        weights_0=weights_0,
                        skin=skin,
                        mesh_name="FrameSkinMesh",
                        node_name="FrameSkinMeshNode",
        )

    return skin_nodes, joint_nodes, joint_elements


def _create_skin(canvas, ibms, joint_nodes, skeleton):
    "Create a Skin referencing given joints and add to skeleton"
    gltf = canvas.gltf

    # Flatten the inverse bind matrices into an Nx16 float32 array
    ibm_array = np.array(ibms, dtype=canvas.float_t).reshape(-1,16)

    # Create accessor to inverse bind matrices and skin
    skin = pygltflib.Skin(
        inverseBindMatrices=_append_index(gltf.accessors, pygltflib.Accessor(
            bufferView=canvas._push_data(ibm_array.tobytes(), target=None),
            componentType=GLTF_T[canvas.float_t],
            count=len(ibms),
            type="MAT4"
        )),
        joints=joint_nodes,
        skeleton=skeleton,
        name="FrameExtrusionSkin"
    )

    if not gltf.skins:
        gltf.skins = []

    return _append_index(gltf.skins, skin)


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
    Given a 'state' that contains the updated (displaced/rotated) coordinates for each element’s cross section,
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


class Motion:
    """
    A helper class that accumulates multiple "states" (deformed configurations)
    and creates a time-based glTF Animation. Each call to add_state() adds
    a new keyframe at the next time step.
    """

    def __init__(self, artist=None, time_step=1.0, name="BeamDeformations"):
        """
        :param canvas:   An instance of your GltfCanvas (with .gltf).
        :param extrusion: Dict {(element_name, j): gltf_node_index, ...}
                         returned by draw_extrusions_ref().
        :param time_step: The time increment for each added state (seconds, or frames).
        :param name: The name of the final glTF animation.
        """
        self.model = artist.model
        self.artist = artist
        self.canvas = artist.canvas

        self.time_step = time_step
        self.current_time = 0.0
        self.anim_name = name

        self._keyframes = defaultdict(lambda: {"translation": [], "rotation": []})

        self._section_skins = None
    

    def advance(self, time=None):
        if time is None:
            self.current_time += self.time_step
        else:
            self.current_time = time

    def set_mode_state():
        pass

    def set_node_position(self, node, position, time=None):
        if time is None: 
            time = self.current_time

        self._keyframes[node]["translation"].append((time, position))

    def set_node_rotation(self, node, rotation, time=None):
        if time is None: 
            time = self.current_time

        self._keyframes[node]["rotation"].append((time, rotation))


    def set_field(self, field, time=None):
        """
        Record a keyframe for a node scale
        """
        if time is None:
            time = self.current_time
        if not hasattr(self, '_mesh_morph_keyframes'):
            self._mesh_morph_keyframes = []

        model = self.model
        field = [
            field(model.cell_nodes(element)[j]) for element,j in self._joint_elements
        ]
        self._mesh_morph_keyframes.append((time, field))


    def draw_sections(self,
                      state=None, rotation=None, position=None, warp=None,
                      time=None):
        """
        Given a 'state' that has deformed positions and rotations for each element’s cross-section,
        record a new keyframe at the current time.

        :param state:  Some data structure that can provide displacements & rotations
                       for each (element, cross_section_index).
        """
        if self._section_skins is None:
            self._section_skins, self._joint_nodes, self._joint_elements = \
                skin_frames(self.model, self.artist,
                            config=self.artist._config_sketch("default")["surface"]["frame"])
        skin_nodes = self._section_skins

        state = self.model.wrap_state(state, 
                                rotation=rotation, 
                                position=position,
                                transform=self.artist.dofs2plot)
        model = self.model
        Ra = self.artist._plot_rotation
        # For each element in the model
        for tag in model.iter_cell_tags():
            if not model.cell_matches(tag, "frame"):
                continue

            R0 = model.frame_orientation(tag).T
            # X_ref = model.cell_position(element_name)
            nen = len(model.cell_nodes(tag))

            # Displacements & rotations from 'state'
            pos_all = np.array([
                Ra@model.node_position(node, state=state) for node in model.cell_nodes(tag)
            ])
            rot_all = [Ra@Ri@R0 for Ri in state.cell_array(tag, state.rotation)]

            for j in range(nen):
                # look up the glTF node index
                key = (tag, j)
                if key not in skin_nodes:
                    continue

                # compute final position for cross section j
                x_def = pos_all[j] #X_ref[j] + pos_all[j]
                # convert rotation matrix -> quaternion
                qx, qy, qz, qw = Rotation.from_matrix(rot_all[j]).as_quat()

                # store a keyframe
                self.set_node_position(skin_nodes[key], (x_def[0], x_def[1], x_def[2]))
                self.set_node_rotation(skin_nodes[key], (qx, qy, qz, qw))


    def add_to(self, canvas):
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

        # Create multiple samplers and channels:
        #   - For each node, we have two samplers (translation, rotation)
        #   - Then two channels referencing those samplers

        # We'll need to record the sampler index for each node property as we build them
        # so we can attach channels referencing the correct sampler.
        node_position_sampler_index = {}
        node_rotation_sampler_index = {}

        # 2) Flatten and encode data for each node
        # Do them all in a single big set of buffers—time values and output values.
        # However, each node gets its own Sampler, because it has distinct times/values
        # in this implementation.
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
                    input=-1,    # placeholder, fill them after creating Accessors
                    output=-1,   #
                    interpolation="LINEAR"
                ))
                node_position_sampler_index[node_idx] = sampler_index_t
                # Temporarily store the arrays so we can embed them in the glTF buffer
                # after building all samplers.
                anim.samplers[sampler_index_t].extras = {
                    "times_array": np.array([k[0] for k in pos_keyframes], dtype=canvas.float_t),
                    "vals_array":  np.array([k[1] for k in pos_keyframes], dtype=canvas.float_t)
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
                    "vals_array":  np.array([k[1] for k in rot_keyframes],   dtype=canvas.float_t)
                }

        # 3)
        for node_idx in self._keyframes:
            if node_idx in node_position_sampler_index:
                # Channel for translation
                anim.channels.append(pygltflib.AnimationChannel(
                    sampler=node_position_sampler_index[node_idx],
                    target=pygltflib.AnimationChannelTarget(
                        node=node_idx,
                        path="translation"
                    )
                ))

            if node_idx in node_rotation_sampler_index:
                # Channel for rotation
                anim.channels.append(pygltflib.AnimationChannel(
                    sampler=node_rotation_sampler_index[node_idx],
                    target=pygltflib.AnimationChannelTarget(
                        node=node_idx,
                        path="rotation"
                    )
                ))


        # --- Add Warp Animation Channels for Each Joint ---
        # This helper repurposes the joint node's scale (using its x-component)
        # to store the warp value.
    
        # If warp keyframes were recorded, add per-joint warp channels.
        if hasattr(self, '_mesh_morph_keyframes'):
            # self._joint_nodes should be a list of joint node indices in the same order as the warp values.
            _add_warp_animation_to_joints(anim, self._joint_nodes, self._mesh_morph_keyframes, canvas)


        # 4) Insert the time / value data into buffers.
        #    Create BufferViews and Accessors, then set up each sampler's input/output
        #    to reference the newly created accessor indices.
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

            # If path=="translation" we have 3 floats, if path=="rotation" we have 4.
            # But we already know shape from sampler.extras["vals_array"].shape
            val_type = "VEC3" if sampler.extras["vals_array"].shape[1]==3 else "VEC4"

            # For morph weights, glTF expects a VEC? array; since we have one target, it is VEC1.
            if sampler.extras["vals_array"].shape[1] == 1:
                val_type = "SCALAR"

            vals_accessor_idx = _append_index(gltf.accessors, pygltflib.Accessor(
                bufferView=canvas._push_data(sampler.extras["vals_array"].tobytes()),
                byteOffset=0,
                componentType=FLOAT,
                count=len(sampler.extras["vals_array"]),
                type=val_type
            ))

            sampler.input  = time_accessor_idx
            sampler.output = vals_accessor_idx

            # Remove extras so we dont JSON-serialize large arrays
            del sampler.extras["times_array"]
            del sampler.extras["vals_array"]

        # 5) Attach this new Animation to the glTF
        if not gltf.animations:
            gltf.animations = []

        _append_index(gltf.animations, anim)


def _add_warp_animation_to_joints(anim, joint_nodes, warp_keyframes, canvas):
    # Sort warp keyframes by time.
    warp_keyframes.sort(key=lambda x: x[0])
    num_joints = len(joint_nodes)

    # Build per-joint keyframe data.
    joint_keyframes = [[] for _ in range(num_joints)]
    for t, warp_list in warp_keyframes:
        # Each warp_list must have num_joints values.
        for j in range(num_joints):
            joint_keyframes[j].append((t, warp_list[j]))

    # For each joint, create an animation channel targeting its scale.
    for j, node_index in enumerate(joint_nodes):
        times = np.array([t for t, _ in joint_keyframes[j]], dtype=canvas.float_t)
        # Pack the warp value in the x-component; keep y and z at 1.
        scale_values = np.array([[w, 1.0, 1.0] for _, w in joint_keyframes[j]], dtype=canvas.float_t)
        sampler_index = _append_index(anim.samplers, pygltflib.AnimationSampler(
            input=-1,
            output=-1,
            interpolation="LINEAR"
        ))
        anim.samplers[sampler_index].extras = {
            "times_array": times,
            "vals_array": scale_values
        }
        anim.channels.append(pygltflib.AnimationChannel(
            sampler=sampler_index,
            target=pygltflib.AnimationChannelTarget(
                node=node_index,
                path="scale"
            )
        ))


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

