import veux
from veux.canvas.gltf import GltfLibCanvas
from veux.motion import Motion
import math
import numpy as np


def position_to_quaternion(position, reference=(0, 0, 1.0)):
    """
    Convert the position vector of a pendulum's mass to a quaternion describing its rotation.

    Parameters:
        position (numpy.ndarray): A 3-element array representing the position vector of the mass.

    Returns:
        numpy.ndarray: A 4-element array representing the quaternion in [x, y, z, w] format (GLTF standard).
    """

    position = np.asarray(position)

    # Normalize the position vector to obtain the direction of the pendulum
    direction = position / np.linalg.norm(position)

    # Default orientation (aligned with z-axis)
    z_axis = np.array(reference, dtype=float) #np.array([0.0, 0.0, 1.0])
    z_axis /= np.linalg.norm(z_axis)

    # Compute the axis of rotation (cross product of z-axis and direction)
    rotation_axis = np.cross(z_axis, direction)
    axis_norm = np.linalg.norm(rotation_axis)

    if axis_norm < 1e-6:  # Handle the case where direction is nearly aligned with the z-axis
        if direction[2] > 0:  # No rotation needed
            return np.array([0.0, 0.0, 0.0, 1.0])
        else:  # 180-degree rotation around any perpendicular axis (e.g., x-axis)
            return np.array([1.0, 0.0, 0.0, 0.0])

    rotation_axis /= axis_norm  # Normalize the rotation axis

    # Compute the angle of rotation (dot product and arccos)
    cos_theta = np.dot(z_axis, direction)
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))

    # Compute the quaternion
    half_angle = angle / 2
    sin_half_angle = np.sin(half_angle)

    quaternion = np.array([
        rotation_axis[0] * sin_half_angle,  # x
        rotation_axis[1] * sin_half_angle,  # y
        rotation_axis[2] * sin_half_angle,  # z
        np.cos(half_angle)                 # w
    ])

    return quaternion


def _create_positions(L, n, rx, ry, wx, wy, dt=1, reference=(0, 0, 1.0)):
    """
    Generate positions of a pendulum tip such that x and y projections move sinusoidally.

    Parameters:
        L (float): Length of the pendulum.
        n (int): Number of samples.
        rx (float): Amplitude of the x projection.
        ry (float): Amplitude of the y projection.
        wx (float): Angular frequency of the x projection.
        wy (float): Angular frequency of the y projection.
        dt (float): Time step between samples.
        reference (tuple): Reference axis (default is z-axis).

    Returns:
        list: A list of 3D position vectors.
    """
    positions = []
    reference = np.array(reference, dtype=float) / np.linalg.norm(reference)

    # Find orthogonal vectors to the reference direction
    if np.allclose(reference, [0, 0, 1]):
        u = np.array([1, 0, 0])
        v = np.array([0, 1, 0])
    else:
        u = np.cross(reference, [0, 0, 1])
        u /= np.linalg.norm(u)
        v = np.cross(reference, u)
        v /= np.linalg.norm(v)

    for i in range(n):
        t = i * dt

        # Compute x and y sinusoidal displacements
        x_disp = rx * np.sin(wx * t)
        y_disp = ry * np.cos(wy * t)

        # Compute z displacement to maintain the length constraint
        xy_length_squared = x_disp**2 + y_disp**2
        if xy_length_squared > L**2:
            raise ValueError("Amplitude and length constraints are inconsistent.")

        z_disp = np.sqrt(L**2 - xy_length_squared)

        # Combine displacements in the reference frame
        position = x_disp * u + y_disp * v + z_disp * reference
        positions.append(position)

    return positions


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

def render_pendulum(length, displacements=None):

    # 1) Make pendulum geometry
    #    Define two vertices for a line: pivot at (0,0,0), tip at (0, -L, 0)
    canvas = GltfLibCanvas()
    lines = canvas.plot_lines(
        vertices=np.array([[0, 0, 0], [0, -length, 0]],dtype=float),
        indices=[[0, 1]],
    )

    node = lines[0].id

    # 2) Create a motion
    motion = Motion()

    for time, rotation in zip(*_create_rotations()):
        motion.set_node_rotation(lines[0].id, rotation, time=time)

    motion.add_to(canvas)

    veux.serve(canvas)


def render_pendulum03(length, displacements=None):
    L = length

    # 1) Make pendulum geometry
    #    Define two vertices for a line: pivot at (0,0,0), tip at (0, -L, 0)
    vertices = np.array([[0, 0, 0], [0, -L, 0]],dtype=float)
    canvas = GltfLibCanvas()

    nodes = canvas.plot_nodes(vertices, skin=True)

    lines = canvas.add_lines([[0, 1]], skin_nodes=nodes)

    mass = nodes[1].id

    # 2) Create a motion
    motion = Motion(time_step=0.5)

    tip = (0, -L, 0)

    for position in _create_positions(L, 40, 0.3*L, 0.3*L, 0.8, 0.8, dt=0.5, reference=tip):
        motion.set_node_position(mass, position)
        rotation = position_to_quaternion(position, reference=tip)
        motion.set_node_rotation(mass, rotation)
        motion.advance()

    motion.add_to(canvas)

    canvas.write("a.glb")
    veux.serve(canvas)


if __name__ == "__main__":
    render_pendulum03(2.0)


