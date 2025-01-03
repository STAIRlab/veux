#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio Perez
from .canvas import Canvas
import trimesh
import numpy as np

class TrimeshCanvas(Canvas):
    def __init__(self, config=None):
        self.scene = trimesh.Scene()
        self.config = config

    def plot_lines(self, coords, **kwds):
        import trimesh.path.entities
        import trimesh.path.path
#       edges = (~np.isnan(coords[:,0])).nonzero()
#       edges = np.vstack([edges,np.roll(edges,-1)],dtype="float32").T
#       print(edges, edges.shape)
#       self.scene.add_geometry(
#               trimesh.path.path.Path3D(
#                   **trimesh.path.exchange.misc.edges_to_path(edges, coords))
#               trimesh.path.entities.Line(coords)
#       )

    def plot_mesh(self,vertices, indices):
        import trimesh
        mesh = trimesh.Trimesh(vertices=vertices,
                               faces=indices)
        # set the mesh face colors to white
        mesh.visual.face_colors = [250, 250, 250, 250]
        self.scene.add_geometry(mesh)

    def write(self, filename):
        import trimesh
        opts = self.config

        if "glb" in filename[-3:]:
            with open(filename,"wb+") as f:
                f.write(trimesh.exchange.gltf.export_glb(self.scene))

        elif "gltf" in filename[-4:]:
            import json
            with open(filename,"w+") as f:
                json.dump(trimesh.exchange.gltf.export_gltf(self.scene), f)

