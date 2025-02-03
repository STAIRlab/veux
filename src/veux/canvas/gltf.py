#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
#
"""
The glTF file format is supported by [COMSOL](https://www.comsol.com/blogs/how-to-export-and-share-your-3d-result-plots-as-gltf-files)
"""

"""
Some implementation notes:
- glTF defines +Y as up.
- glTF uses a right-handed coordinate system, that is, the cross product of +X and +Y yields +Z.
- The front of a glTF asset faces +Z.


- All angles are in radians.
- Positive rotation is counterclockwise.
- Rotations are given as quaternions stored as a tuple (x,y,z,w),
  where the w-component is the cosine of half of the rotation angle.
  For example, the quaternion [ 0.259, 0.0, 0.0, 0.966 ] describes a rotation
  about 30 degrees, around the x-axis.
- The identity rotation is (0, 0, 0, 1.0)

"""
import sys
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
}

import numpy as np
import pygltflib

EYE3 = np.eye(3, dtype="float32")

def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1


class GltfLibCanvas(Canvas):
    vertical = 2

    def __init__(self, config=None):
        self.config = config

        #                          x, y, z, scalar
        self._rotation = [-0.7071068, 0, 0, 0.7071068]
        # equivalent rotation matrix:
        self._rotation_matrix = np.array([[1,  0, 0],
                                          [0,  0, 1],
                                          [0, -1, 0]])

        self.index_t = "uint16"
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
        # Reuse existing POSITION accessor indices assumed to be stored in self
        points_access = self.position_accessor_index  # previously stored index for POSITION accessor
        indices_access = self.indices_accessor_index  # previously stored index for indices accessor


        # Initialize an array for vertex colors, defaulting to a base color (e.g., gray)
        vertex_colors = np.tile(np.array([0.5, 0.5, 0.5, 1.0], dtype=self.float_t), (len(points), 1))

        # For each triangle, check if the face lies on a plane fixed along given axes
        # and set the corresponding vertices to white if so.
        for tri in triangles:
            # Extract vertices of the triangle
            v0, v1, v2 = points[tri[0]], points[tri[1]], points[tri[2]]

            # Check if all vertices share the same coordinate on any fixed axis:
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


        # Push the color data to the buffer and create a new accessor for vertex colors
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


    def _init_nodes(self, style: NodeStyle):
        #
        #
        #
        index_t = self.index_t # "uint8"
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


        indices_access = len(self.gltf.accessors)-2 # indices
        points_access  = len(self.gltf.accessors)-1 # points
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

        if (color, alpha) in self._color:
            return self._color[(color,alpha)]

        elif isinstance(color, str) and color[0] == "#":
            # Remove leading hash in hex
            hx  = color.lstrip("#")
            # Convert hex to RGB
            rgb = [int(hx[i:i+2], 16)/255 for i in (0, 2, 4)]

        elif isinstance(color, tuple):
            rgb = color

        else:
            raise TypeError("Unexpected type for color")

        # Store index for new material
        self._color[(color, alpha)] = len(self.gltf.materials)
        # Create and add new material
        self.gltf.materials.append(
            pygltflib.Material(
                name=str(color),
                doubleSided=True,
                alphaMode=pygltflib.MASK,
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

        if not hasattr(self, "_node_mesh"):
            self._init_nodes(style or NodeStyle())

        if rotations is None:
            rotations = itertools.repeat([0, 0, 0, 1.0])
        else:
            try:
                rotations = Rotation.from_matrix([self._rotation_matrix@R for R in rotations]).as_quat().tolist()
            except ValueError:
                rotations = Rotation.from_rotvec([self._rotation_matrix@R for R in rotations]).as_quat().tolist()


        for coord, rotation in zip(vertices, rotations):
            index = _append_index(self.gltf.nodes, pygltflib.Node(
                    mesh=self._node_mesh,
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
        # points = np.zeros((1,3), dtype=self.float_t) 
        # points = np.random.random((len(joint_nodes), 3))
        # for i in range(len(joint_nodes)):
        #     points[i] /= np.linalg.norm(points[i])*1e3
        # points = points.astype(self.float_t)

        # points = np.array([self._rotation_matrix.T@self.gltf.nodes[n].translation for n in joint_nodes], dtype=self.float_t)
        # points = np.array(_,dtype=self.float_t) #np.array([self._rotation_matrix.T@n for n in _], dtype=self.float_t)
        ver_accessor = _append_index(self.gltf.accessors, pygltflib.Accessor(
                bufferView=self._push_data(points.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.float_t],
                count=len(points),
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        )
    
        # Create Skeleton
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
        # ibm_array = np.array([ibm.flatten() for ibm in inverse_bind_matrices], dtype=self.float_t)

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

        # index_array = np.array(indices, dtype=self.index_t)#.flatten()
        index_array = np.array(lines, dtype=self.index_t).reshape(-1)#.flatten()
        # index_array = np.zeros((len(lines),2), dtype=self.index_t).reshape(-1)

        # Add buffer view and accessor for the line indices

        index_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(pygltflib.Accessor(
            bufferView=self._push_data(index_array.tobytes(),pygltflib.ELEMENT_ARRAY_BUFFER),
            componentType=GLTF_T[self.index_t],
            count=len(index_array),
            type="SCALAR",
            min=[int(index_array.min())],
            max=[int(index_array.max())]
        ))

        # Create the line mesh with skinning attributes
        joints_0_array  = np.array(joints_0, dtype=self.index_t)

        joints_0_accessor_idx = len(gltf.accessors)
        gltf.accessors.append(pygltflib.Accessor(
            bufferView=self._push_data(joints_0_array.tobytes(), pygltflib.ARRAY_BUFFER),
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


    def plot_lines(self, vertices, indices=None, style: LineStyle=None, vcache:str=None, **kwds):

        lines = []
        material = self._get_material(style or LineStyle())

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
            # `n` adjusts indices by the number of nan rows that were removed so far
            n  = sum(np.isnan(vertices[:indices[0],0]))
            indices_array = indices - np.dtype(self.index_t).type(n)

            indices_binary_blob = indices_array.tobytes()

            if len(indices_array) <= 1:
                import warnings
                warnings.warn(indices_array, file=sys.stderr)
                continue

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

            lines.append(Line(
                id=len(self.gltf.nodes)-1
            ))

        return lines
    
    def draw_arrow(self, location, rotation, size):
        from veux.assets import create_arrow

        index = _append_index(self.gltf.nodes, pygltflib.Node(
                mesh=create_arrow(self, size, DrawStyle(color="red")),
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


        mesh = pygltflib.Mesh(
                primitives=[
                    pygltflib.Primitive(
                        mode=pygltflib.TRIANGLES,
                        attributes=pygltflib.Attributes(
                            POSITION=point_access
                        ),
                        material=material,
                        indices=index_access,
                        targets=[
                            # TODO: implement morph targets
#                          pygltflib.Attributes(POSITION=point_access)
                        ]
                     )
                ]
            )

        if mesh_name is not None:
            mesh.name = mesh_name

        if joints_0 is not None:
            joints_0  = np.array(joints_0,  dtype=self.index_t)
            mesh.primitives[0].attributes.JOINTS_0 = _append_index(self.gltf.accessors, pygltflib.Accessor(
                bufferView=self._push_data(joints_0.tobytes(), pygltflib.ARRAY_BUFFER),
                componentType=GLTF_T[self.index_t],
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
                        colormap="twilight", #"viridis", 
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

        # Step 1. Determine color array from 'field'
        #         For demonstration, let's assume you have a helper
        #         that returns Nx4 RGBA in [0,1].
        color_array = self._map_field_to_colors(field, colormap, vmin, vmax)

        # Step 2. Plot the mesh (re-use plot_mesh) but we'll also attach colors
        # mesh_handle = self.plot_mesh(vertices, triangles, style=style, **kwds)

        # Step 3. Add color data as a separate accessor in the just-created mesh
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
                             colormap="twilight", #"viridis", 
                             vmin=None, vmax=None):
        """
        Convert 1D array of scalar values into Nx4 RGBA array in [0,1].
        """
        import matplotlib
        import matplotlib.cm

        field = np.array(field, dtype=np.float64)
        if vmin is None:
            vmin = field.min()
        if vmax is None:
            vmax = field.max()

        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        cmap = matplotlib.cm.get_cmap(colormap)
        
        # shape: (N, 4)
        colors = cmap(norm(field))
        # ensure Nx4
        return colors


    def to_glb(self)->bytes:
        return b"".join(self.gltf.save_to_bytes())

    def write(self, filename=None):

        self.gltf.save(filename)

#       if "glb" in filename[-3:]:
#           glb = b"".join(self.gltf.save_to_bytes())
#           with open(filename,"wb+") as f:
#               f.write(glb)

