"""
TODO: Add morph targets
"""
import math
import struct
import numpy as np
import pygltflib

from veux.canvas.gltf import GltfLibCanvas


def _append_index(lst, item):
    lst.append(item)
    return len(lst) - 1


class GltfLibAnimation01:
    """
    A utility class that manages animations for a glTF scene.
    It owns a GltfLibCanvas instance which holds geometry, nodes, etc.
    """

    def __init__(self, canvas=None, name="MyAnimation"):
        if canvas is None:
            canvas = GltfLibCanvas(config=None)

        self.canvas = canvas

        gltf = canvas.gltf

        # Build the Animation object
        anim = pygltflib.Animation(
            samplers=[],
            channels=[],
            name=name
        )

        # Append to glTF's animations
        if gltf.animations is None:
            gltf.animations = []
        gltf.animations.append(anim)
        self.anim = anim


    def set_node_states(self, node_index, times, rotations, path="rotation"):
        """
        Attach a keyframed quaternion-rotation animation to a node in the scene.

        :param node_index: index of the node in self.canvas.gltf.nodes
        :param times:      list/array of timestamps
        :param quaternions: list/array of (x, y, z, w) quaternions
        :param path:       "rotation" (for rotating the node), or "translation", etc.
        """
        gltf = self.canvas.gltf
        canvas = self.canvas

        # Convert times/quaternions to binary
        time_bytes = b"".join([struct.pack("<f", t) for t in times])
        quat_bytes = b"".join([struct.pack("<4f", *q) for q in rotations])

        # Create Accessors for time & states
        time_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
                bufferView=canvas._push_data(time_bytes, target=None),
                byteOffset=0,
                componentType=pygltflib.FLOAT,
                count=len(times),
                type=pygltflib.SCALAR,
                min=[times[ 0]] if times else [0],
                max=[times[-1]] if times else [0]
            )
        )

        state_accessor = _append_index(gltf.accessors, pygltflib.Accessor(
            bufferView=canvas._push_data(quat_bytes, target=None),
            byteOffset=0,
            componentType=pygltflib.FLOAT,
            count=len(rotations),
            type=pygltflib.VEC4
        ))


        # Create AnimationSampler & AnimationChannel
        sampler = pygltflib.AnimationSampler(
            input=time_accessor,
            output=state_accessor,
            interpolation="LINEAR"
        )
        channel = pygltflib.AnimationChannel(
            sampler=0,  # within this animation's local array
            target=pygltflib.AnimationChannelTarget(
                node=node_index,
                path=path
            )
        )

        self.anim.samplers.append(sampler)
        self.anim.channels.append(channel)


    def save(self, filename="scene.glb"):
        """Delegate to the canvas to write out the final GLB."""
        self.canvas.write(filename)


def _create_rotations(
    period = 2.0,
    num_samples = 10,
    amplitude_degs_z = 45,
    amplitude_degs_x = 10):

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
    return times, quaternions 


def _test_pendulum():
    # 1) Create glTF animation helper
    anim = GltfLibAnimation01()

    # 2) Make pendulum geometry
    #    Define two vertices for a line: pivot at (0,0,0), tip at (0, -L, 0)
    L = 2.0
    anim.canvas.plot_lines(
        vertices=np.array([[0,  0, 0], [0, -L, 0]],dtype=float),
        indices=[[0, 1]],
    )

    # The newly added line is in a new node at the end of gltf.nodes
    node = len(anim.canvas.gltf.nodes) - 1

    times, rotations = _create_rotations()

    # 4) Add an animation to rotate our pendulum node
    anim.set_node_states(node, times, rotations)

    # 5) Save everything to disk
    anim.save("pendulum.glb")


def _test_pendulum02():
    from veux.frame.skins import VeuxAnimation
    # 1) Create glTF animation helper
    anim = VeuxAnimation()

    # 2) Make pendulum geometry
    #    Define two vertices for a line: pivot at (0,0,0), tip at (0, -L, 0)
    L = 2.0
    canvas = GltfLibCanvas()
    lines = canvas.plot_lines(
        vertices=np.array([[0,  0, 0], [0, -L, 0]],dtype=float),
        indices=[[0, 1]],
    )

    # The newly added line is in a new node at the end of gltf.nodes
    node = lines[0].id

    for time, rotation in zip(*_create_rotations()):
        anim.set_node_rotation(node, rotation, time=time)

    anim.apply(canvas)

    # 5) Save everything to disk
    canvas.write("pendulum02.glb")


if __name__ == "__main__":
    _test_pendulum()
    _test_pendulum02()

