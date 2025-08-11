#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
"""
Some implementation notes:

- glTF defines +Y as up.
- glTF uses a right-handed coordinate system, that is, the cross product of +X and +Y yields +Z.
- The front of a glTF asset faces +Z.

- Rotations are given as quaternions stored as a tuple (x,y,z,w),
  where the w-component is the cosine of half of the rotation angle.
  For example, the quaternion [ 0.259, 0.0, 0.0, 0.966 ] describes a rotation
  about 30 degrees, around the x-axis.
- The identity rotation is (0, 0, 0, 1.0)
"""

"""
The glTF file format is supported by 
[COMSOL](https://www.comsol.com/blogs/how-to-export-and-share-your-3d-result-plots-as-gltf-files)
"""
import itertools

import numpy as np
import pygltflib
from scipy.spatial.transform import Rotation

import veux
from .canvas import Canvas, Line, Mesh, Node
from veux import utility
from veux.config import NodeStyle, MeshStyle, LineStyle, DrawStyle

GLTF_T = {
    "float32": pygltflib.FLOAT,
    "uint8":   pygltflib.UNSIGNED_BYTE,
    "uint16":  pygltflib.UNSIGNED_SHORT,
    "uint32":  pygltflib.UNSIGNED_INT,
}

EYE3 = np.eye(3, dtype="float32")


def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1

class GltfLibCanvas(Canvas):
    vertical = 2

    def __init__(self, config=None):
        self.config = config
        self._data = {}

        #                 x, y, z, scalar
        self._rotation = [0, 0, 0, 1] #[-0.7071068, 0, 0, 0.7071068]
        # equivalent rotation matrix:
        self._rotation_matrix = np.eye(3) #np.array([[1,  0, 0],
                                          #[0,  0, 1],
                                          #[0, -1, 0]])

        self.index_t = "uint32"
        self.float_t = "float32"

        self.gltf = pygltflib.GLTF2(
            scene=0,
            scenes=[pygltflib.Scene(nodes=[])],
            nodes=[],
            meshes=[],
            accessors=[],
            materials=[
                pygltflib.Material(
                    name="black",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[0, 0, 0, 1]
                    )
                ),
                pygltflib.Material(
                    name="white",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[1, 1, 1, 1]
                    )
                ),
                pygltflib.Material(
                    name="red",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[1, 0, 0, 1]
                    )
                ),
                pygltflib.Material(
                    name="green",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[0, 1, 0, 1]
                    )
                ),
                pygltflib.Material(
                    name="blue",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[0, 0, 1, 1]
                    )
                ),
                pygltflib.Material(
                    name="gray",
                    doubleSided=True,
                    alphaMode=pygltflib.MASK,
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[0.80, 0.80, 0.80, 1]
                    )
                ),
                pygltflib.Material(
                    name="hidden",
                    alphaMode=pygltflib.BLEND,  # Enables transparency
                    doubleSided=True,
#                   extensions={"KHR_materials_unlit": {}},
                    pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                        baseColorFactor=[1, 1, 1, 0]
                    )
                )
                #                 pygltflib.Material(
                #                     name="metal",
                #                     doubleSided=True,
                # #                   alphaMode=pygltflib.MASK,
                #                     occlusionTexture=pygltflib.OcclusionTextureInfo(index=1),
                # #                   emissiveFactor=[0.8,0.8,0.8],
                #                     pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                #                         metallicFactor=0.0,
                #                         roughnessFactor=1.0,
                # #                       baseColorFactor=[0.8, 0.8, 0.8, 1],
                #                         baseColorTexture=pygltflib.TextureInfo(index=0),
                #                         metallicRoughnessTexture=pygltflib.TextureInfo(index=1),
                #                     )
                #                 ),
            ],
            bufferViews=[],
            buffers=[pygltflib.Buffer(byteLength=0)],
        )
        self.gltf._glb_data = bytes()


        # Map pairs of (color, alpha) to material's index in material list
        self._color = {(m.name,m.pbrMetallicRoughness.baseColorFactor[3]) if m.pbrMetallicRoughness else (m.name, 0): i
                       for i,m in enumerate(self.gltf.materials)}
        
        self._arrows = {}

        self._node_markers = {}

        #
        # load assets for steel material
        #
        if False:
            for i,file in enumerate(("rust.jpg", "occlusionRoughnessMetallic.png")):
                path  = str(veux.assets/"metal"/file)
                image = pygltflib.Image()
                image.uri = path
                self.gltf.images.append(image)
                self.gltf.textures.append(pygltflib.Texture(source=i, name=path))

            self.gltf.convert_images(pygltflib.ImageFormat.DATAURI)

    def _init_fixed_node(self, points, triangles, x=True, y=True, z=True):
        points_access  = self.position_accessor_index
        indices_access = self.indices_accessor_index

        # Initialize an array for vertex colors, defaulting to a base color
        vertex_colors = np.tile(np.array([0.5, 0.5, 0.5, 1.0], dtype=self.float_t), (len(points), 1))

        # For each triangle, check if the face lies on a plane fixed along given axes
        # and set the corresponding vertices to white if so.
        for tri in triangles:
            # Extract vertices of the triangle
            v0, v1, v2 = points[tri[0]], points[tri[1]], points[tri[2]]

            # Check if all vertices share the same coordinate on any fixed axis
            if x and (np.isclose(v0[0], v1[0]) and np.isclose(v1[0], v2[0])):
                # Set vertices of this triangle to white
                for vi in tri:
                    vertex_colors[vi] = [1.0, 1.0, 1.0, 1.0]
            if y and (np.isclose(v0[1], v1[1]) and np.isclose(v1[1], v2[1])):
                for vi in tri:
                    vertex_colors[vi] = [1.0, 1.0, 1.0, 1.0]
            if z and (np.isclose(v0[2], v1[2]) and np.isclose(v1[2], v2[2])):
                for vi in tri:
                    vertex_colors[vi] = [1.0, 1.0, 1.0, 1.0]


        color_accessor_index = len(self.gltf.accessors)
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=self._push_data(vertex_colors.astype(self.float_t).tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(vertex_colors),
                type=pygltflib.VEC4,
                max=vertex_colors.max(axis=0).tolist(),
                min=vertex_colors.min(axis=0).tolist(),
            )
        )

        # Create a new material that uses vertex colors directly, e.g., an unlit material.
        # The specifics of creating a material that respects vertex colors depend on your material setup.
        fixed_material = pygltflib.Material(
            name="FixedAxesMaterial",
            pbrMetallicRoughness=pygltflib.PBRMetallicRoughness(
                baseColorFactor=[1.0, 1.0, 1.0, 1.0],  # base color white
                metallicFactor=0.0,
                roughnessFactor=1.0,
            ),
            # Depending on your renderer, you might need to enable vertex colors
        )

        self.gltf.materials.append(fixed_material)
        material_index = len(self.gltf.materials) - 1

        # Create a new mesh primitive using the POSITION and COLOR_0 attributes.
        self.gltf.meshes.append(
            pygltflib.Mesh(
                primitives=[
                    pygltflib.Primitive(
                        mode=pygltflib.TRIANGLES,
                        attributes=pygltflib.Attributes(
                            POSITION=points_access,
                            COLOR_0=color_accessor_index
                        ),
                        material=material_index,
                        indices=indices_access
                    )
                ]
            )
        )
        return len(self.gltf.meshes) - 1


    def _find_marker(self, style: NodeStyle):
        key = (style.color, style.scale)
        if key not in self._node_markers:
            self._node_markers[key] = self._init_marker(style)

        return self._node_markers[key]


    def _init_marker(self, style: NodeStyle):
        #
        #
        #
        index_t = self.index_t
        points = style.scale*np.array(
            [
                [-1.0, -1.0,  1.0],
                [ 1.0, -1.0,  1.0],
                [-1.0,  1.0,  1.0],
                [ 1.0,  1.0,  1.0],
                [ 1.0, -1.0, -1.0],
                [-1.0, -1.0, -1.0],
                [ 1.0,  1.0, -1.0],
                [-1.0,  1.0, -1.0],
            ],
            dtype=self.float_t,
        )/10

        triangles = np.array(
            [
                [0, 1, 2],
                [3, 2, 1],
                [1, 0, 4],
                [5, 4, 0],
                [3, 1, 6],
                [4, 6, 1],
                [2, 3, 7],
                [6, 7, 3],
                [0, 2, 5],
                [7, 5, 2],
                [5, 7, 4],
                [6, 4, 7],
            ],
            dtype=index_t,
        )
        triangles_binary_blob = triangles.flatten().tobytes()

        self.gltf.accessors.extend([
            pygltflib.Accessor(
                bufferView=self._push_data(triangles_binary_blob,
                                           pygltflib.ELEMENT_ARRAY_BUFFER),
                componentType=GLTF_T[index_t],
                count=triangles.size,
                type=pygltflib.SCALAR,
                max=[int(triangles.max())],
                min=[int(triangles.min())],
            ),
            pygltflib.Accessor(
                bufferView=self._push_data(points.tobytes(),
                                           pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(points),
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        ])


        indices_access = len(self.gltf.accessors)-2
        points_access  = len(self.gltf.accessors)-1
        self.gltf.meshes.append(
               pygltflib.Mesh(
                 primitives=[
                     pygltflib.Primitive(
                         mode=pygltflib.TRIANGLES,
                         attributes=pygltflib.Attributes(POSITION=points_access),
                         material=self._get_material(style),
                         indices=indices_access
                     )
                 ]
               )
        )

        return len(self.gltf.meshes) - 1

    def _init_nodes(self, style: NodeStyle):
        #
        #
        #
        index_t = self.index_t
        points = style.scale*np.array(
            [
                [-1.0, -1.0,  1.0],
                [ 1.0, -1.0,  1.0],
                [-1.0,  1.0,  1.0],
                [ 1.0,  1.0,  1.0],
                [ 1.0, -1.0, -1.0],
                [-1.0, -1.0, -1.0],
                [ 1.0,  1.0, -1.0],
                [-1.0,  1.0, -1.0],
            ],
            dtype=self.float_t,
        )/10

        triangles = np.array(
            [
                [0, 1, 2],
                [3, 2, 1],
                [1, 0, 4],
                [5, 4, 0],
                [3, 1, 6],
                [4, 6, 1],
                [2, 3, 7],
                [6, 7, 3],
                [0, 2, 5],
                [7, 5, 2],
                [5, 7, 4],
                [6, 4, 7],
            ],
            dtype=index_t,
        )
        triangles_binary_blob = triangles.flatten().tobytes()

        self.gltf.accessors.extend([
            pygltflib.Accessor(
                bufferView=self._push_data(triangles_binary_blob,
                                           pygltflib.ELEMENT_ARRAY_BUFFER),
                componentType=GLTF_T[index_t],
                count=triangles.size,
                type=pygltflib.SCALAR,
                max=[int(triangles.max())],
                min=[int(triangles.min())],
            ),
            pygltflib.Accessor(
                bufferView=self._push_data(points.tobytes(),
                                           pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(points),
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        ])


        indices_access = len(self.gltf.accessors)-2
        points_access  = len(self.gltf.accessors)-1
        self.gltf.meshes.append(
               pygltflib.Mesh(
                 primitives=[
                     pygltflib.Primitive(
                         mode=pygltflib.TRIANGLES,
                         attributes=pygltflib.Attributes(POSITION=points_access),
                         material=self._get_material(style),
                         indices=indices_access
                     )
                 ]
               )
        )

        self._node_mesh = len(self.gltf.meshes) - 1

    def _use_asset(self, name, scale, rotation, material):
        pass

    def _get_material(self, style: DrawStyle)->int:
        if hasattr(style,"alpha"):
            alpha = style.alpha
        else:
            alpha = 1.0

        color = style.color

        rgb = None
        if (color, alpha) in self._color:
            return self._color[(color,alpha)]

        elif isinstance(color, str) and color[0] == "#":
            # Remove leading hash in hex
            hx  = color.lstrip("#")
            # Convert hex to RGB
            rgb = [int(hx[i:i+2], 16)/255 for i in (0, 2, 4)]

        elif isinstance(color, tuple):
            rgb = color

        elif isinstance(color, str):
            for key,a in self._color:
                if color == key:
                    rgb = self.gltf.materials[self._color[(key,a)]].pbrMetallicRoughness.baseColorFactor[:3]

        if rgb is None:
            raise TypeError("Unexpected type for color")

        # Store index for new material
        self._color[(color, alpha)] = len(self.gltf.materials)
        # Create and add new material
        self.gltf.materials.append(
            pygltflib.Material(
                name=str(color),
                doubleSided=True,
                alphaMode=pygltflib.BLEND,
                pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                    baseColorFactor=[*rgb, alpha]
                )
            ),
        )
        return self._color[(color, alpha)]


    def _push_data(self, data, target=None, byteStride=None)->int:
        self.gltf.bufferViews.append(
                pygltflib.BufferView(
                    buffer=0,
                    byteStride=byteStride,
                    byteOffset=self.gltf.buffers[0].byteLength,
                    byteLength=len(data),
                    target=target,
                )
        )

        self.gltf._glb_data += data
        self.gltf.buffers[0].byteLength += len(data)
        return len(self.gltf.bufferViews)-1


    def plot_nodes(self, vertices, label = None, style=None, data=None, rotations=None, skin=False, **kwds):
        nodes = []

        # if not hasattr(self, "_node_mesh"):
        #     self._init_nodes(style or NodeStyle())

        marker = self._find_marker(style or NodeStyle())

        if rotations is None:
            rotations = itertools.repeat([0, 0, 0, 1.0])
        else:
            try:
                rotations = Rotation.from_matrix([self._rotation_matrix@R for R in rotations]).as_quat().tolist()
            except ValueError:
                rotations = Rotation.from_rotvec([self._rotation_matrix@R for R in rotations]).as_quat().tolist()


        for coord, rotation in zip(vertices, rotations):
            index = _append_index(self.gltf.nodes, pygltflib.Node(
                    mesh=marker,
                    rotation=rotation,
                    translation=(self._rotation_matrix@coord).tolist(),
                )
            )
            if not skin:
                self.gltf.scenes[0].nodes.append(index)
            nodes.append(Node(id=index))

        return nodes

    def add_lines(self, lines: list, style=None, skin_nodes=None):
        """
        Add skinned lines to the glTF object that connect pairs of nodes specified in `lines`.
        The lines will deform as the corresponding nodes are translated.

        :param lines: A list of pairs of indices (i, j), where i and j are node indices.
        :param access_vertices: The accessor index for initial positions of the nodes.
        """
        gltf = self.gltf
        scene = gltf.scenes[0]
        EYE4 = np.eye(4, dtype=self.float_t)

        # Validate that all node indices in `lines` exist in gltf.nodes
        max_node_idx = len(gltf.nodes) - 1
        for i, j in lines:
            if i > max_node_idx or j > max_node_idx:
                raise ValueError(f"Node indices {i} or {j} in `lines` are out of range for `gltf.nodes`.")


        # Create joints (one per node) and bind the lines to them
        if skin_nodes is not None:
            joint_nodes = list({skin_nodes[idx].id for pair in lines for idx in pair})  # Unique joint indices
        else:
            joint_nodes = list({idx for pair in lines for idx in pair})  # Unique joint indices

        joint_node_to_index = {node: i for i, node in enumerate(joint_nodes)}

        points = np.zeros((len(joint_nodes), 3), dtype=self.float_t)

        ver_accessor = _append_index(self.gltf.accessors, pygltflib.Accessor(
                bufferView=self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(points),
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        )
    
        # Create skeleton
        skeleton_root_node = pygltflib.Node(name="LineSkeleton", 
                                            children=joint_nodes)
        skeleton_root_idx = _append_index(gltf.nodes, skeleton_root_node)
        scene.nodes.append(skeleton_root_idx)

        # Inverse bind matrices
        inverse_bind_matrices = []
        for joint_node in joint_nodes:
            # Compute the transform matrix for the bind pose
            node = gltf.nodes[joint_node]
            t_matrix = np.eye(4, dtype=self.float_t)
            t_matrix[:3, 3] = node.translation if node.translation else [0.0, 0.0, 0.0]
            rotation_matrix = Rotation.from_quat(node.rotation).as_matrix() if node.rotation else EYE3
            t_matrix[:3, :3] = rotation_matrix #* (node.scale if node.scale else 1.0)
            # t_matrix = np.linalg.inv(t_matrix)

            # inverse_bind_matrices.append(np.array(t_matrix, dtype=self.float_t).T)
            inverse_bind_matrices.append(EYE4)

        # Add buffer view and accessor for the inverse bind matrices
        # Flatten inverse bind matrices for glTF format
        ibm_array = np.array(inverse_bind_matrices, dtype=self.float_t).reshape(-1, 16)

        ibm_accessor_idx = _append_index(gltf.accessors, pygltflib.Accessor(
            bufferView=self._push_data(ibm_array.tobytes(), target=None),
            componentType=GLTF_T[self.float_t],
            count=len(joint_nodes),
            type="MAT4"
        ))

        # Create the skin
        if not gltf.skins:
            gltf.skins = []
        skin_idx = len(gltf.skins)
        gltf.skins.append(pygltflib.Skin(
            inverseBindMatrices=ibm_accessor_idx,
            joints=joint_nodes,
            skeleton=skeleton_root_idx,  # Root joint
            name="LineSkin"
        ))

        # Create the index buffer for the lines
        # indices = []
        joints_0 = []
        weights_0 = []
        for i, j in lines:
            # indices.extend([i, j])
            joints_0.extend([
                [joint_node_to_index[i], 0, 0, 0],
                [joint_node_to_index[j], 0, 0, 0]
            ])
            weights_0.extend([
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0]
            ])

        index_array = np.array(lines, dtype=self.index_t).reshape(-1)

        # Add buffer view and accessor

        index_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(pygltflib.Accessor(
            bufferView=self._push_data(index_array.tobytes(),pygltflib.ELEMENT_ARRAY_BUFFER),
            componentType=GLTF_T[self.index_t],
            count=len(index_array),
            type="SCALAR",
            min=[int(index_array.min())],
            max=[int(index_array.max())]
        ))

        # Create the line mesh

        joints_0_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(pygltflib.Accessor(
            bufferView=self._push_data(np.array(joints_0, dtype=self.index_t).tobytes(), pygltflib.ARRAY_BUFFER),
            componentType=GLTF_T[self.index_t],
            count=len(joints_0),
            type="VEC4"
        ))

        weights_0_array = np.array(weights_0, dtype=self.float_t)
        weights_0_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(pygltflib.Accessor(
            bufferView=self._push_data(weights_0_array.tobytes(), pygltflib.ARRAY_BUFFER),
            componentType=GLTF_T[self.float_t],
            count=len(weights_0),
            type="VEC4"
        ))

        # Create the line mesh
        mesh_idx = len(gltf.meshes)
        line_mesh = pygltflib.Mesh(
            primitives=[
                pygltflib.Primitive(
                    attributes=pygltflib.Attributes(
                        POSITION=ver_accessor,
                        JOINTS_0=joints_0_accessor_idx,
                        WEIGHTS_0=weights_0_accessor_idx
                    ),
                    indices=index_accessor_idx,
                    mode=pygltflib.LINES,
                    material=self._get_material(style or LineStyle())
                )
            ], name="LineSkinMesh")
        gltf.meshes.append(line_mesh)

        # Create a node for the line mesh
        mesh_node = _append_index(gltf.nodes, pygltflib.Node(
            mesh=mesh_idx, 
            skin=skin_idx, 
            # rotation=self._rotation,
            name="LineSkinMeshNode"
        ))

        # Add the new node to the scene
        scene.nodes.append(mesh_node)

    def set_data(self, data, key):

        points = np.array(data, dtype=self.float_t)
        self.gltf.accessors.extend([
            pygltflib.Accessor(
                bufferView=self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(points),
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        ])

        self._data[key] = {"access_index": len(self.gltf.accessors)-1}


    def _make_line_strip(self, indices, vertices, points_access, material):
        
        # `n` adjusts indices by the number of nan rows that were removed so far
        if not isinstance(vertices, (int, str)):
            n  = sum(np.isnan(vertices[:indices[0],0]))
        else:
            n = 0

        indices_array = indices - np.dtype(self.index_t).type(n)

        indices_binary_blob = indices_array.tobytes()

        if len(indices_array) <= 1:
            import warnings
            warnings.warn(indices_array)
            return None

        self.gltf.accessors.extend([
            pygltflib.Accessor(
                bufferView=self._push_data(indices_binary_blob,
                                            pygltflib.ELEMENT_ARRAY_BUFFER),
                componentType=GLTF_T[self.index_t],
                count=indices_array.size,
                type=pygltflib.SCALAR,
                max=[int(indices_array.max())],
                min=[int(indices_array.min())],
            )
        ])
        self.gltf.meshes.append(
                pygltflib.Mesh(
                    primitives=[
                        pygltflib.Primitive(
                            mode=pygltflib.LINE_STRIP,
                            attributes=pygltflib.Attributes(POSITION=points_access),
                            material=material,
                            # most recently added accessor
                            indices=len(self.gltf.accessors)-1,
                            # TODO: use this mechanism to add annotation data
                            extras={},
                        )
                    ]
                )
        )

        self.gltf.nodes.append(pygltflib.Node(
                mesh=len(self.gltf.meshes)-1,
                rotation=self._rotation
            )
        )

        self.gltf.scenes[0].nodes.append(
            len(self.gltf.nodes)-1
        )

        return Line(id=len(self.gltf.nodes)-1)

    def plot_lines(self, vertices, indices=None, style: LineStyle | None = None, **node_kwds):
        """
        Add a batch of disconnected line-segments to the scene as a *single*
        glTF primitive (mode = LINES).

        Parameters
        ----------
        vertices : array_like, int, or str
            • (N, 3) array – NaNs may delimit poly-lines  
            • accessor index/name – reuse an existing POSITION accessor
        indices : sequence[array_like] | None
            If given, each item is a vertex-index list describing one poly-line.
            Consecutive pairs are turned into independent segments.  If omitted
            and ``vertices`` is an array with NaNs, the index list is generated
            automatically.
        style   : LineStyle, optional
            Passed to ``_get_material``.
        **node_kwds
            Extra kwargs for the created glTF ``Node`` (e.g. “name”, “matrix”, ...).

        Returns
        -------
        int
            Index of the new ``Node`` in ``self.gltf.nodes``.
        """
        #
        # 1.  Material
        #
        material_idx = self._get_material(style or LineStyle())

        # ------------------------------------------------------------------
        # 2.  POSITION accessor
        # ------------------------------------------------------------------
        if isinstance(vertices, (int, str)):
            # Re-use an accessor that caller has already stored.
            points_access = self.get_data(vertices)["access_index"]
            n_vertices = self.gltf.accessors[points_access].count
            # When the caller passes indices, we trust them to
            # reference this existing accessor correctly.
            verts_map = None          # identity
        else:
            return self.plot_lines_old(vertices, indices, style, **node_kwds)
            vertices = np.asarray(vertices, dtype=self.float_t)
            if vertices.ndim != 2 or vertices.shape[1] != 3:
                raise ValueError("vertices must be (N,3)")

            # Strip NaN rows – these are *delimiters*, never emitted.
            finite_mask = np.isfinite(vertices[:, 0])
            points = vertices[finite_mask]
            if points.size == 0:
                return None  # nothing to draw

            buf_view = self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER)
            self.gltf.accessors.append(
                pygltflib.Accessor(
                    bufferView=buf_view,
                    componentType=GLTF_T[self.float_t],
                    count=len(points),
                    type=pygltflib.VEC3,
                    min=points.min(axis=0).tolist(),
                    max=points.max(axis=0).tolist(),
                )
            )
            points_access = len(self.gltf.accessors) - 1
            n_vertices = len(points)

            # Map original row index to new compact index
            verts_map = np.full(len(vertices), -1, dtype=self.index_t)
            verts_map[finite_mask] = np.arange(n_vertices, dtype=self.index_t)

        # ------------------------------------------------------------------
        # 3.  Build flat SCALAR index list (pairs)
        # ------------------------------------------------------------------
        seg_idx = []
        if indices is not None:
            for poly in indices:
                poly = np.asarray(poly, dtype=self.index_t)
                if verts_map is not None:
                    poly = verts_map[poly]          # translate to compact space
                if len(poly) < 2:
                    continue
                # consecutive pairs
                for i in range(len(poly) - 1):
                    a, b = poly[i], poly[i + 1]
                    if a != b:                      # skip degenerate
                        seg_idx.extend((a, b))
        else:
            if verts_map is None:
                raise ValueError("Automatic index generation needs vertices array.")
            current = []
            for src_idx, compact_idx in enumerate(verts_map):
                if compact_idx == -1:               # NaN delimiter
                    current.clear()
                    continue
                current.append(compact_idx)
                if len(current) >= 2:
                    # last two points form a segment
                    seg_idx.extend(current[-2:])
        if not seg_idx:
            return None

        seg_idx = np.asarray(seg_idx, dtype=self.index_t)
        if seg_idx.max() >= n_vertices:
            raise ValueError("Index out of range for POSITION accessor.")


        # ------------------------------------------------------------------
        # Create lines
        # ------------------------------------------------------------------

        #
        # INDICES accessor
        # 
        idx_view = self._push_data(seg_idx.tobytes(), pygltflib.ELEMENT_ARRAY_BUFFER)
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=idx_view,
                componentType=GLTF_T[self.index_t],
                count=seg_idx.size,
                type=pygltflib.SCALAR,
                min=[int(seg_idx.min())],
                max=[int(seg_idx.max())],
            )
        )
        idx_acc = len(self.gltf.accessors) - 1

        #
        # Primitive, Mesh, and Node
        #
        primitive = pygltflib.Primitive(
            attributes={"POSITION": points_access},
            indices=idx_acc,
            mode=pygltflib.LINES,
            material=material_idx,
        )
        self.gltf.meshes.append(pygltflib.Mesh(primitives=[primitive]))
        mesh_idx = len(self.gltf.meshes) - 1

        self.gltf.nodes.append(pygltflib.Node(mesh=mesh_idx, **node_kwds))
        node_idx = len(self.gltf.nodes) - 1

        self.gltf.scenes[0].nodes.append(node_idx)

        return Line(id=node_idx)

    def plot_lines_old(self, vertices, indices=None, style: LineStyle=None, **kwds):

        lines = []
        material = self._get_material(style or LineStyle())

        points_access = None 

        if isinstance(vertices, (int, str)):
            points_access = self.get_data(vertices)["access_index"]

        else:
            # vertices is given with nans separating line groups, but
            # GLTF does not accept nans so we have to filter these
            # out, and add distinct meshes for each line group
            assert np.all(np.isnan(vertices[np.isnan(vertices[:,0]), :]))
            points  = np.array(vertices[~np.isnan(vertices[:,0]),:], dtype=self.float_t)

            if points.size == 0:
                return

            self.gltf.accessors.append(
                pygltflib.Accessor(
                    bufferView=self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER),
                    componentType=GLTF_T[self.float_t],
                    count=len(points),
                    type=pygltflib.VEC3,
                    max=points.max(axis=0).tolist(),
                    min=points.min(axis=0).tolist(),
                )
            )
            points_access = len(self.gltf.accessors) - 1


        if indices is None:
            # Get indices by splitting at nans
            indices_ = utility.split(np.arange(len(vertices), dtype=self.index_t), np.nan, vertices[:,0])
        else:
            indices_ = list(map(lambda x: np.array(x, dtype=self.index_t), indices))

        for indices in indices_:
            if (line := self._make_line_strip(indices, vertices, points_access, material)) is None:
                continue
            lines.append(line)

        return lines

    def plot_vectors(self, locs, vecs, label=None, extrude=False, **kwds):
        ne = len(vecs)
        if not extrude:
            for j in range(3):
                style = kwds.get("line_style", LineStyle(color=("red", "green", "blue")[j]))
                X = np.zeros((ne*3, 3))*np.nan
                for i in range(j,ne,3):
                    X[i*3,:] = locs[i]
                    X[i*3+1,:] = locs[i] + vecs[i]
                self.plot_lines(X, style=style, label=label)
        else:
            for j in range(3):
                style = kwds.get("line_style", LineStyle(color=("red", "green", "blue")[j]))
                X = np.zeros((ne*3, 3))*np.nan
                for i in range(j,ne,3):
                    self.draw_arrow(locs[i], vector=vecs[i], style=style)


    def draw_arrow(self, location, rotation=None, size=None, vector=None, style=None):
        from veux.assets import create_arrow

        def quaternion_from_x_to_vec(v):
            """
            Returns a rotation that rotates [1,0,0] onto the vector v.
            """
            # Convert to float np.array and normalize
            v = np.array(v, dtype=float)
            if np.allclose(v, 0):
                raise ValueError("Target vector must be non-zero.")
            v_norm = v / np.linalg.norm(v)

            # The reference "from" vector is the unit x-axis
            x_axis = np.array([1.0, 0.0, 0.0])

            # Check if they are already the same (no rotation) or exactly opposite
            dot_val = np.dot(x_axis, v_norm)
            if np.isclose(dot_val, 1.0):
                # Same direction, set to identity quaternion
                return Rotation.from_quat([0.0, 0.0, 0.0, 1.0])
            elif np.isclose(dot_val, -1.0):
                # Opposite direction, 180 deg rotation about any axis perpendicular to x
                # e.g., about [0,1,0]
                return Rotation.from_rotvec(np.pi * np.array([0, 1, 0]))

            # Otherwise, compute rotation axis as cross(x_axis, v_norm) and rotation angle
            axis = np.cross(x_axis, v_norm)
            axis /= np.linalg.norm(axis)
            angle = np.arccos(dot_val)

            return Rotation.from_rotvec(angle * axis)

        if style is None:
            style = DrawStyle(color="red")

        if vector is not None:
            size = np.linalg.norm(vector)
            rotation = quaternion_from_x_to_vec(vector/size).as_quat().tolist()

        if style.color not in self._arrows:
            self._arrows[style.color] = create_arrow(self, size, style)

        arrow = self._arrows[style.color]

        index = _append_index(self.gltf.nodes, pygltflib.Node(
                mesh=arrow,
                rotation=rotation,
                translation=(self._rotation_matrix@location).tolist(),
            )
        )
        self.gltf.scenes[0].nodes.append(index)

    
    def draw_skin(self, vertices, triangles):
        pass

    def plot_mesh(self, vertices, triangles, local_coords=None, style=None,
                  joints_0=None, 
                  weights_0=None,
                  skin=None,
                  node_name=None,
                  mesh_name=None,
                  **kwds) -> tuple:

        material  = self._get_material(style or MeshStyle())

        if isinstance(triangles, int):
            index_access = triangles
        else:
            triangles = np.array(triangles, dtype=self.index_t)
            self.gltf.accessors.extend([
                pygltflib.Accessor(
                    bufferView=self._push_data(triangles.flatten().tobytes(), pygltflib.ELEMENT_ARRAY_BUFFER),
                    componentType=GLTF_T[self.index_t],
                    count=triangles.size,
                    type=pygltflib.SCALAR,
                    max=[int(triangles.max())],
                    min=[int(triangles.min())],
                )
            ])
            index_access = len(self.gltf.accessors)-1

        if isinstance(vertices, int):
            point_access = vertices
        else:
            points    = np.array(vertices, dtype=self.float_t)
            self.gltf.accessors.extend([
                pygltflib.Accessor(
                    bufferView=self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER),
                    componentType=GLTF_T[self.float_t],
                    count=len(points),
                    type=pygltflib.VEC3,
                    max=points.max(axis=0).tolist(),
                    min=points.min(axis=0).tolist(),
                )
            ])
            point_access = len(self.gltf.accessors)-1

#       # Expecting morph_targets as an iterable of target arrays (each of shape (n,3))
#       morph_targets = kwds.get("morph_targets", None)
#       targets = []
#       if morph_targets is not None:
#           for mt in morph_targets:
#               mt_arr = np.array(mt, dtype=self.float_t)
#               self.gltf.accessors.extend([
#                   pygltflib.Accessor(
#                       bufferView=self._push_data(mt_arr.tobytes(), pygltflib.ARRAY_BUFFER),
#                       componentType=GLTF_T[self.float_t],
#                       count=len(mt_arr),
#                       type=pygltflib.VEC3,
#                       max=mt_arr.max(axis=0).tolist(),
#                       min=mt_arr.min(axis=0).tolist(),
#                   )
#               ])
#               mt_accessor = len(self.gltf.accessors)-1
#               targets.append({"POSITION": mt_accessor})

        mesh = pygltflib.Mesh(
                primitives=[
                    pygltflib.Primitive(
                        mode=pygltflib.TRIANGLES,
                        attributes=pygltflib.Attributes(
                            POSITION=point_access
                        ),
                        material=material,
                        indices=index_access,
                     )
                ]
            )

        if mesh_name is not None:
            mesh.name = mesh_name

        if joints_0 is not None:
            joints_0  = np.array(joints_0,  dtype="uint16")
            mesh.primitives[0].attributes.JOINTS_0 = _append_index(self.gltf.accessors, pygltflib.Accessor(
                bufferView=self._push_data(joints_0.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T["uint16"],
                count=len(joints_0),
                type="VEC4"
            ))

        if weights_0 is not None:
            weights_0 = np.array(weights_0, dtype=self.float_t)
            mesh.primitives[0].attributes.WEIGHTS_0 = _append_index(self.gltf.accessors, pygltflib.Accessor(
                bufferView=self._push_data(weights_0.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(weights_0),
                type="VEC4"
            ))


        if local_coords is not None:
            locoor = np.array(local_coords, dtype=self.float_t)
            self.gltf.accessors.extend([
                pygltflib.Accessor(
                    bufferView=self._push_data(locoor.tobytes(), pygltflib.ARRAY_BUFFER),
                    componentType=GLTF_T[self.float_t],
                    count=len(locoor),
                    type=pygltflib.VEC2,
                    max=locoor.max(axis=0).tolist(),
                    min=locoor.min(axis=0).tolist(),
                )
            ])
            mesh.primitives[0].attributes.TEXCOORD_0 = len(self.gltf.accessors) -1
        
        #
        # 4) Create a Node referencing the mesh + skin
        #
        self.gltf.nodes.append(pygltflib.Node(
                mesh=_append_index(self.gltf.meshes, mesh),
                rotation=self._rotation
            )
        )
        if node_name is not None:
            self.gltf.nodes[-1].name = node_name

        if skin is not None:
            self.gltf.nodes[-1].skin = skin

        # Add to scene
        scene_node = len(self.gltf.nodes)-1
        self.gltf.scenes[0].nodes.append(scene_node)

        return Mesh(id=scene_node,
                    vertices=point_access, 
                    indices=index_access)


    def plot_mesh_field(self, mesh_handle, field,
                        colormap="rainbow4", # "cet_CET_R1",# "cet_CET_D13"#"twilight", #"viridis", 
                        vmin=None, vmax=None,
                        **kwds) -> tuple:
        """
        Draw a mesh colored by a scalar field.
        
        :param vertices: Nx3 array of vertex positions
        :param triangles: Mx3 array of triangle indices
                          (or an int referencing an existing accessor)
        :param field: length-N array (one scalar per vertex)
        :param style: optional style info
        :param colormap: name of a matplotlib colormap or something similar
        :param vmin, vmax: optionally set the data range for mapping
        :param kwds: other keywords
        """

        # Determine color array from field
        color_array = self._map_field_to_colors(field, colormap, vmin, vmax)

        color_array = color_array.astype(self.float_t)
        self.gltf.accessors.extend([
            pygltflib.Accessor(
                bufferView=self._push_data(color_array.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(color_array),
                type=pygltflib.VEC4,  # RGBA
                max=color_array.max(axis=0).tolist(),
                min=color_array.min(axis=0).tolist(),
            )
        ])
        color_access = len(self.gltf.accessors) - 1

        # Attach the color accessor to the existing mesh’s attributes
        mesh_idx = self.gltf.nodes[mesh_handle.id].mesh
        self.gltf.meshes[mesh_idx].primitives[0].attributes.COLOR_0 = color_access

        return mesh_handle

    def _map_field_to_colors(self, field, 
                             colormap="cet_CET_D13", #"rainbow4", #"viridis", 
                             vmin=None, vmax=None):
        """
        """
        try:
            import colorcet as cc
            field = np.asarray(field, dtype=np.float64)

            # Normalisation
            if vmin is None:
                vmin = np.nanmin(field)
            if vmax is None:
                vmax = np.nanmax(field)

            # avoid divide-by-zero
            span = vmax - vmin or 1.0
            t = np.clip((field - vmin) / span, 0.0, 1.0)


            try:
                cmap = cc.cm[colormap]
            except KeyError as e:
                raise ValueError(f"Unknown ColorCET colormap '{colormap}'.") from e

            colors = cmap(t)
            return colors

        except:
            import matplotlib
            import matplotlib.cm

            field = np.array(field, dtype=np.float64)
            if vmin is None:
                vmin = field.min()
            if vmax is None:
                vmax = field.max()

            norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
            cmap = matplotlib.cm.get_cmap(colormap)

            colors = cmap(norm(field))
            return colors


    def to_glb(self)->bytes:
        return b"".join(self.gltf.save_to_bytes())

    def write(self, filename=None):

        self.gltf.save(filename)

#       if "glb" in filename[-3:]:
#           glb = b"".join(self.gltf.save_to_bytes())
#           with open(filename,"wb+") as f:
#               f.write(glb)

