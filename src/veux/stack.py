class Stack:
    def __init__(self, artist):
        self.canvas = artist.canvas
        self.gltf = artist.canvas.gltf


import math
import pygltflib
from pygltflib import GLTF2, Scene, Node, Mesh, Material
from pygltflib import Buffer, BufferView, Accessor
from pygltflib import Animation, AnimationSampler, AnimationChannel, AnimationChannelTarget
from pygltflib import ELEMENT_ARRAY_BUFFER, ARRAY_BUFFER
from pygltflib import FLOAT, UNSIGNED_SHORT
from pygltflib import Primitive, Skin

# -----------------------------
# 1) Define geometry for a simple line
#    We'll have two points (pivot at origin, end at negative Y).
# -----------------------------
positions = [
    0.0,  0.0,  0.0,  # pivot vertex
    0.0, -1.0,  0.0   # tip of the pendulum
]
# Indices for a line segment
indices = [0, 1]

# Convert to bytes
import struct

# positions as 32-bit floats
positions_bytes = b"".join([struct.pack("<f", p) for p in positions])
# indices as 16-bit unsigned shorts
indices_bytes = b"".join([struct.pack("<H", i) for i in indices])

# Create one Buffer with both position and index data.
# We will place position data first, then index data.
combined_buffer = positions_bytes + indices_bytes

# -----------------------------
# 2) Create BufferViews and Accessors
# -----------------------------
position_buffer_view = BufferView(
    buffer=0,
    byteOffset=0,
    byteLength=len(positions_bytes),
    target=ARRAY_BUFFER
)
index_buffer_view = BufferView(
    buffer=0,
    byteOffset=len(positions_bytes),
    byteLength=len(indices_bytes),
    target=ELEMENT_ARRAY_BUFFER
)

# Accessor for positions
position_accessor = Accessor(
    bufferView=0,            # uses position_buffer_view
    byteOffset=0,
    componentType=FLOAT, 
    count=len(positions)//3,
    type="VEC3",
    min=[0.0, -1.0, 0.0],
    max=[0.0,  0.0,  0.0]
)

# Accessor for indices
index_accessor = Accessor(
    bufferView=1,            # uses index_buffer_view
    byteOffset=0,
    componentType=UNSIGNED_SHORT,
    count=len(indices),
    type="SCALAR",
    min=[0],
    max=[1]
)

# -----------------------------
# 3) Create a Mesh with a single line primitive
# -----------------------------
mesh_primitive = Primitive(
    attributes={"POSITION": 0}, # refers to the first accessor index in glTF's top-level list
    indices=1,                  # refers to the second accessor index in glTF's top-level list
    mode=pygltflib.LINES
)

mesh = Mesh(primitives=[mesh_primitive])

# -----------------------------
# 4) Create a Node to host our pendulum mesh.
#    This node will be rotated in the animation.
# -----------------------------
pendulum_node = Node(
    mesh=0,  # Will refer to the first (and only) mesh in glTF
    name="PendulumNode"
)

# -----------------------------
# 5) Build a simple harmonic motion animation.
#    We'll sample a few time points over one swing period.
# -----------------------------
period = 2.0   # seconds
num_samples = 10

times = []
rotations = []
amplitude_degs = 20  # ±20 degrees
amplitude_rads = math.radians(amplitude_degs)

for i in range(num_samples):
    t = i * (period / (num_samples - 1))
    angle = amplitude_rads * math.cos((2 * math.pi / period) * t)
    # Convert axis-angle to a quaternion for rotation about Z
    # Axis: Z = (0,0,1)
    # Angle = angle
    # Quaternion: q = [x, y, z, w]
    #   (where (x, y, z) = sin(angle/2)*axis, and w = cos(angle/2))
    half_angle = angle / 2
    sin_half = math.sin(half_angle)
    cos_half = math.cos(half_angle)
    qz = sin_half  # rotation around Z
    qw = cos_half
    
    times.append(t)
    # Rotation about Z axis
    rotations.append((0.0, 0.0, qz, qw))

# Pack times and rotation data into binary
time_bytes = b"".join([struct.pack("<f", t) for t in times])
rotation_bytes = b"".join([struct.pack("<4f", *r) for r in rotations])

# We'll create separate buffer views for time and rotation to keep it clear.
animation_time_buffer_view = BufferView(
    buffer=0,
    byteOffset=len(combined_buffer),  # appended after geometry
    byteLength=len(time_bytes),
    target=None  # Animation data does not need a GPU target
)

animation_rotation_buffer_view = BufferView(
    buffer=0,
    byteOffset=len(combined_buffer) + len(time_bytes),
    byteLength=len(rotation_bytes),
    target=None
)

# Accessors for the time and rotation
time_accessor = Accessor(
    bufferView=2,  # index of the animation_time_buffer_view (will be appended after we add geometry buffer views)
    byteOffset=0,
    componentType=FLOAT,
    count=len(times),
    type="SCALAR",
    min=[times[0]],
    max=[times[-1]]
)

rotation_accessor = Accessor(
    bufferView=3,  # index of the animation_rotation_buffer_view
    byteOffset=0,
    componentType=FLOAT,
    count=len(rotations),
    type="VEC4"
)

# Create the sampler: it defines how input data (time) maps to output data (rotation).
animation_sampler = AnimationSampler(
    input=2,      # index of the time accessor in glTF
    output=3,     # index of the rotation accessor in glTF
    interpolation="LINEAR"
)

# Create the channel: it defines which node and which property is being animated.
animation_channel = AnimationChannel(
    sampler=0,  # refers to the first (and only) sampler in this Animation
    target=AnimationChannelTarget(
        node=0,  # we'll animate pendulum_node (the first node in glTF)
        path="rotation"
    )
)

# Finally, assemble the Animation object
animation = Animation(
    samplers=[animation_sampler],
    channels=[animation_channel],
    name="PendulumSwing"
)

# -----------------------------
# 6) Assemble the GLTF
# -----------------------------
gltf = GLTF2(
    scenes=[Scene(nodes=[0])],  # there's a single scene with one node
    nodes=[pendulum_node],
    meshes=[mesh],
    animations=[animation],
    buffers=[Buffer(byteLength=len(combined_buffer) + len(time_bytes) + len(rotation_bytes))],
    bufferViews=[
        position_buffer_view,  # 0
        index_buffer_view,     # 1
        animation_time_buffer_view,    # 2
        animation_rotation_buffer_view # 3
    ],
    accessors=[
        position_accessor,  # 0
        index_accessor,     # 1
        time_accessor,      # 2
        rotation_accessor   # 3
    ]
)

# Insert the combined data (geometry + animation) into glTF's first buffer
gltf.buffers[0].uri = None  # We will embed the data (use data URI) or leave None to store externally
gltf._glb_data = combined_buffer + time_bytes + rotation_bytes

# -----------------------------
# 7) Save the GLTF file
# -----------------------------
gltf.save("pendulum.glb")

print("pendulum.gltf has been created.")

