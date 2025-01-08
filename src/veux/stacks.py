"""
TODO: Add morph targets
"""
import math
import struct
import numpy as np
import pygltflib

from veux.canvas.gltf import GltfLibCanvas


class GltfLibAnimation:
    """
    A utility class that manages animations for a glTF scene.
    It owns a GltfLibCanvas instance which holds geometry, nodes, etc.
    """

    def __init__(self, config=None):
        # Create a new canvas (or you can pass in an existing one, if you prefer)
        self.canvas = GltfLibCanvas(config=config)

    def add_rotation_animation(self, node_index, times, quaternions, path="rotation"):
        """
        Attach a keyframed quaternion-rotation animation to a node in the scene.

        :param node_index: index of the node in self.canvas.gltf.nodes
        :param times:      list/array of timestamps
        :param quaternions: list/array of (x, y, z, w) quaternions
        :param path:       "rotation" (for rotating the node), or "translation", etc.
        """
        gltf = self.canvas.gltf

        # Convert times/quaternions to binary
        time_bytes = b"".join([struct.pack("<f", t) for t in times])
        quat_bytes = b"".join([struct.pack("<4f", *q) for q in quaternions])

        # Create new BufferViews for time & quaternions
        time_buffer_view_idx = self.canvas._push_data(time_bytes, target=None)
        quat_buffer_view_idx = self.canvas._push_data(quat_bytes, target=None)

        # Create Accessors for time & quaternions
        time_accessor = pygltflib.Accessor(
            bufferView=time_buffer_view_idx,
            byteOffset=0,
            componentType=pygltflib.FLOAT,
            count=len(times),
            type=pygltflib.SCALAR,
            min=[times[0]] if times else [0],
            max=[times[-1]] if times else [0]
        )
        gltf.accessors.append(time_accessor)
        time_accessor_idx = len(gltf.accessors) - 1

        quat_accessor = pygltflib.Accessor(
            bufferView=quat_buffer_view_idx,
            byteOffset=0,
            componentType=pygltflib.FLOAT,
            count=len(quaternions),
            type=pygltflib.VEC4
        )
        gltf.accessors.append(quat_accessor)
        quat_accessor_idx = len(gltf.accessors) - 1

        # Create AnimationSampler & AnimationChannel
        sampler = pygltflib.AnimationSampler(
            input=time_accessor_idx,
            output=quat_accessor_idx,
            interpolation="LINEAR"
        )
        channel = pygltflib.AnimationChannel(
            sampler=0,  # within this animation's local array
            target=pygltflib.AnimationChannelTarget(
                node=node_index,
                path=path
            )
        )

        # Build the Animation object
        new_animation = pygltflib.Animation(
            samplers=[sampler],
            channels=[channel],
            name="MyAnimation"
        )

        # Append to glTF's animations
        if gltf.animations is None:
            gltf.animations = []
        gltf.animations.append(new_animation)

    def save(self, filename="scene.glb"):
        """Delegate to the canvas to write out the final GLB."""
        self.canvas.write(filename)
        print(f"Saved: {filename}")


#-----------------------

def quaternion_multiply(q1, q2):
    """
    Standard quaternion multiply: q1 * q2
    q1, q2 are (x, y, z, w)
    """
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    return (x, y, z, w)

def main():
    # 1) Create glTF animation helper
    anim = GltfLibAnimation()

    # 2) Make pendulum geometry
    #    We'll define two vertices for a line: pivot at (0,0,0), tip at (0, -2, 0)
    L = 2.0
    pendulum_verts = np.array([[0,  0, 0],
                               [0, -L, 0]],
                              dtype=float)
    # Indices for a single line (two points)
    pendulum_indices = [[0, 1]]

    # Plot it onto the canvas
    anim.canvas.plot_lines(
        vertices=pendulum_verts,
        indices=pendulum_indices,
    )

    # The newly added line is in a new node at the end of gltf.nodes
    pendulum_node_index = len(anim.canvas.gltf.nodes) - 1

    # 3) Build the time samples and quaternions for a simple 3D swing
    period = 2.0
    num_samples = 10
    amplitude_degs_z = 45
    amplitude_degs_x = 10

    amp_z = math.radians(amplitude_degs_z)
    amp_x = math.radians(amplitude_degs_x)
    omega = 2 * math.pi / period

    times = []
    quaternions = []

    for i in range(num_samples):
        t = i * (period / (num_samples - 1)) if (num_samples > 1) else 0
        angle_z = amp_z * math.cos(omega * t)
        angle_x = amp_x * math.sin(omega * t)

        # Convert to quaternions
        half_z = angle_z / 2
        half_x = angle_x / 2

        qZ = (0.0, 0.0, math.sin(half_z), math.cos(half_z))
        qX = (math.sin(half_x), 0.0, 0.0, math.cos(half_x))

        qTotal = quaternion_multiply(qZ, qX)

        times.append(t)
        quaternions.append(qTotal)

    # 4) Add an animation to rotate our pendulum node
    anim.add_rotation_animation(pendulum_node_index, times, quaternions)

    # 5) Save everything to disk
    anim.save("pendulum.glb")


if __name__ == "__main__":
    main()

