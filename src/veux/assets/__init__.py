import pygltflib
import numpy as np
from veux.canvas.gltf import GLTF_T
import math

def create_cube(canvas, style):
    #
    #
    #
    index_t = canvas.index_t # "uint8"
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
        dtype=canvas.float_t,
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

    canvas.gltf.accessors.extend([
        pygltflib.Accessor(
            bufferView=canvas._push_data(triangles_binary_blob,
                                        pygltflib.ELEMENT_ARRAY_BUFFER),
            componentType=GLTF_T[index_t],
            count=triangles.size,
            type=pygltflib.SCALAR,
            max=[int(triangles.max())],
            min=[int(triangles.min())],
        ),
        pygltflib.Accessor(
            bufferView=canvas._push_data(points.tobytes(),
                                        pygltflib.ARRAY_BUFFER),
            componentType=GLTF_T[canvas.float_t],
            count=len(points),
            type=pygltflib.VEC3,
            max=points.max(axis=0).tolist(),
            min=points.min(axis=0).tolist(),
        )
    ])


    indices_access = len(canvas.gltf.accessors)-2 # indices
    points_access  = len(canvas.gltf.accessors)-1 # points
    canvas.gltf.meshes.append(
            pygltflib.Mesh(
                primitives=[
                    pygltflib.Primitive(
                        mode=pygltflib.TRIANGLES,
                        attributes=pygltflib.Attributes(POSITION=points_access),
                        material=canvas._get_material(style),
                        indices=indices_access
                    )
                ]
            )
    )

    return len(canvas.gltf.meshes) - 1


def create_arrow(canvas, body_length,
                 style,
                 head_length=None,
                 head_diameter=None,
                 body_diameter=None):
    """
    Create an arrow mesh along the +X axis.

    Parameters:
        canvas: An object with .gltf, .float_t, .index_t, and _push_data.
        style: An object used for style (e.g., material, scale).
        body_length: Length of the cylindrical body.
        head_length: Length of the arrow head (defaults to 0.25 * body_length).
        head_diameter: Diameter of the arrow head base (defaults to 2 x body_diameter).
        body_diameter: Diameter of the cylindrical body (defaults to 0.05 * body_length).

    Returns:
        The index of the new mesh in canvas.gltf.meshes.
    """
    if body_diameter is None:
        body_diameter = 0.1 * body_length
    if head_length is None:
        head_length = 0.5 * body_length
    if head_diameter is None:
        head_diameter = 2.5 * body_diameter

    # Number of segments around the circle.
    n_seg = 35

    # Lists to collect vertices and triangle indices.
    vertices = []
    triangles = []

    # Helper function to add a vertex and return its index.
    def add_vertex(pt):
        vertices.append(pt)
        return len(vertices) - 1

    #
    # Cylinder (body) along x from 0 to body_length.
    #
    # Compute radius for the cylinder.
    cyl_radius = body_diameter / 2.0

    # Generate circle vertices for the front (x=0) and back (x=body_length) faces.
    front_indices = []
    back_indices = []
    for i in range(n_seg):
        angle = 2 * np.pi * i / n_seg
        y = cyl_radius * np.cos(angle)
        z = cyl_radius * np.sin(angle)
        front_indices.append(add_vertex((        0.0, y, z)))
        back_indices.append( add_vertex((body_length, y, z)))

    # Add center vertices for the end caps.
    front_center = add_vertex((        0.0, 0.0, 0.0))
    back_center  = add_vertex((body_length, 0.0, 0.0))

    # Cylinder side: for each segment, create two triangles forming a quad.
    for i in range(n_seg):
        next_i = (i + 1) % n_seg
        triangles.append((front_indices[i], back_indices[i], back_indices[next_i]))
        triangles.append((front_indices[i], back_indices[next_i], front_indices[next_i]))

    # Cylinder caps.
    # Front cap (at x=0): triangles fan around the front_center.
    for i in range(n_seg):
        next_i = (i + 1) % n_seg
        # Winding order chosen so that normals point inward (if desired)
        triangles.append((front_center, front_indices[next_i], front_indices[i]))

    # Back cap (at x=body_length): triangles fan around back_center.
    for i in range(n_seg):
        next_i = (i + 1) % n_seg
        triangles.append((back_center, back_indices[i], back_indices[next_i]))

    #
    # Arrow head (cone)
    #
    # Cone extends along x from body_length to body_length+head_length.
    # Compute radius for the cone base.
    cone_radius = head_diameter / 2.0

    # Add tip of the cone.
    tip = add_vertex((body_length + head_length, 0.0, 0.0))

    # Generate the circle for the cone base (at x=body_length).
    cone_base_indices = []
    for i in range(n_seg):
        angle = 2 * math.pi * i / n_seg
        y = cone_radius * math.cos(angle)
        z = cone_radius * math.sin(angle)
        cone_base_indices.append(add_vertex((body_length, y, z)))

    # Add center of the cone base (for capping the cone).
    cone_center = add_vertex((body_length, 0.0, 0.0))

    # Cone side: for each segment, create a triangle connecting
    # two adjacent base vertices to the tip.
    for i in range(n_seg):
        next_i = (i + 1) % n_seg
        triangles.append((cone_base_indices[i], cone_base_indices[next_i], tip))

    # Cone base cap: fan triangles around the cone_center.
    for i in range(n_seg):
        next_i = (i + 1) % n_seg
        triangles.append((cone_center, cone_base_indices[i], cone_base_indices[next_i]))


    #
    # Create accessors
    #

    # Convert vertices to a NumPy array of shape (N,3) with the canvas float type.
    points = np.array(vertices, dtype=canvas.float_t)
    # Convert triangle indices to a flat array with the canvas index type.
    triangles_array = np.array(triangles, dtype=canvas.index_t)
    indices_accessor_index = len(canvas.gltf.accessors)
    points_accessor_index = indices_accessor_index + 1

    canvas.gltf.accessors.extend([
        pygltflib.Accessor(
            bufferView=canvas._push_data(triangles_array.flatten().tobytes(),
                                         pygltflib.ELEMENT_ARRAY_BUFFER),
            componentType=GLTF_T[canvas.index_t],
            count=triangles_array.size,
            type=pygltflib.SCALAR,
            max=[int(triangles_array.max())],
            min=[int(triangles_array.min())],
        ),
        pygltflib.Accessor(
            bufferView=canvas._push_data(points.tobytes(),
                                         pygltflib.ARRAY_BUFFER),
            componentType=GLTF_T[canvas.float_t],
            count=len(points),
            type=pygltflib.VEC3,
            max=points.max(axis=0).tolist(),
            min=points.min(axis=0).tolist(),
        )
    ])

    # Append the mesh to the canvas.
    canvas.gltf.meshes.append(
        pygltflib.Mesh(
            primitives=[
                pygltflib.Primitive(
                    mode=pygltflib.TRIANGLES,
                    attributes=pygltflib.Attributes(POSITION=points_accessor_index),
                    material=canvas._get_material(style),
                    indices=indices_accessor_index
                )
            ]
        )
    )

    return len(canvas.gltf.meshes) - 1
