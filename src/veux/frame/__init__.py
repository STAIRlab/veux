#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Claudio M. Perez
#
import warnings
from collections import defaultdict
import numpy as np
Array = np.ndarray

import shps.rotor as so3
from veux.model  import Model,FrameModel
from veux.state  import State, BasicState
from veux.config import Config, LineStyle, NodeStyle, MeshStyle
from ._section import SectionGeometry

class FrameArtist:
    ndm:    int
    ndf:    int
    model:  "FrameModel"
    canvas: "Canvas"

    def __init__(self,
                 model_data,
                 ndf=None,
                 #
                 config=None,
                 # Model
                 loc=None,
                 model_config=None,
                 # Canvas
                 canvas=None,
                 #
                 **kwds):
        
        if config is None:
            config = {}

        self.config = config
        self.canvas = canvas
        vert = config.get("vertical", 2)

        self.ndm = 3

        if ndf is None:
            ndf = 6

#       elif ndf == 3:
#           self.ndm = 2

        if vert == canvas.vertical:
            R = np.eye(3)
        elif vert == 2 and canvas.vertical == 3:
            R = np.array(((1,0, 0),
                          (0,0,-1),
                          (0,1, 0)))
        elif vert == 3 and canvas.vertical == 2:
            R = np.array(((1, 0, 0),
                          (0, 0, 1),
                          (0,-1, 0)))

        self._plot_rotation = R
        R = np.eye(3)

        if not isinstance(model_data, Model):
            if loc is None and isinstance(model_config, dict) and "shift" in model_config:
                loc = model_config.pop("shift")

            self.model = model = FrameModel(model_data, shift=loc, rot=R,
                                            **(model_config or {}))
        else:
            self.model = model = model_data


        # Define transformation from DOFs in `state` variables to plot
        # coordinates
        from scipy.linalg import block_diag
        if model.ndf == 1 and model.ndm == 2:
            self.dofs2plot = R@np.array(((0,),
                                         (0,),
                                         (1,)))

        elif model.ndf == 2 and model.ndm == 2:
            self.dofs2plot = R@np.array(((1, 0),
                                         (0, 1),
                                         (0, 0)))

        elif ndf == 3 and model.ndm == 2:
            self.dofs2plot = block_diag(*[R]*2)@np.array(((1,0, 0),
                                                          (0,1, 0),
                                                          (0,0, 0),

                                                          (0,0, 0),
                                                          (0,0, 0),
                                                          (0,0, 1)))

        elif ndf == 3 and model.ndm == 3:
            self.dofs2plot = block_diag(*[R]*2)@np.array(((1,0, 0),
                                                          (0,1, 0),
                                                          (0,0, 1),

                                                          (0,0, 0),
                                                          (0,0, 0),
                                                          (0,0, 0)))
        else:
            self.dofs2plot = block_diag(*[R]*2)

        self.displ_states = {}

    def plot_scatter(self, vertices, label=None, style=None, color=None, scale=1.0):
        """
        Plot a scatter of vertices in the canvas.
        """
        if style is None:
            style = NodeStyle(color=color or "#808080", scale=scale)

        self.canvas.plot_nodes([self._plot_rotation@x for x in vertices], style=style)

    def _config_sketch(self,  sketch):
        strokes = {"outline", "surface", "axes", "contour", "marker", "info"}
        return {
            stroke: {
                k: v.get(stroke, None) for k, v in self.config["sketches"][sketch].items()
            } for stroke in strokes
        }

    def _add_displ_case(self, state, name=None, scale=1.0):

        if name in self.displ_states:
            self.displ_states[name].update(state)
        else:
            self.displ_states[name] = state

        return name


    def add_state(self, res_file, scale=1.0, sketch_config=None, **state_config):

        if not isinstance(res_file, (dict, Array, State)):
            state = self.model.wrap_state(res_file,
                               scale=scale,
                               transform=self.dofs2plot,
                               **state_config)
        else:
            state = res_file

        # If dict of dicts, assume its a collection of responses, 
        # otherwise, just a single response
        if isinstance(state, dict) and isinstance(next(iter(state.values())), dict):
            for k, v in state.items():
                self._add_displ_case(v, name=k, scale=scale)

        elif isinstance(state, dict):
            self._add_displ_case(BasicState(state, self.model,
                                            scale=scale,
                                            transform=self.dofs2plot))

        else:
            self._add_displ_case(state, scale=scale)


    def add_point_displacements(self, displ, scale=1.0, name=None):
        displ_array = self.displ_states[name]
        for i,n in enumerate(self.model.iter_node_tags()):
            for dof in displ[n]:
                displ_array[i, dof] = 1.0

        displ_array[:,3:] *= scale/100
        displ_array[:,:3] *= scale
        return name


    def add_elem_data(self, config=None):

        N = 3
        for type in self.model.cell_prototypes():
            name = type["name"]
            ni = len(type["instances"])
            coords = np.zeros((ni*(N+1),self.ndm))
            coords.fill(np.nan)
            for i,crd in enumerate(self.model.cell_position(type["instances"])):
                coords[(N+1)*i:(N+1)*i+N,:] = np.linspace(*crd, N)

            coords = coords.reshape(-1,4,3)[:,-3]

            self.canvas.plot_hover(coords, data=type["properties"],
                                   style=NodeStyle(shape="sphere"),
                                   label=name)

    def _draw_sketch(self, state, config):
        if config["outline"] is not None:
            self.draw_outlines(state, config=config["outline"])

        if config["surface"] is not None:
            self.draw_surfaces(state, config=config["surface"])

        if config["marker"] is not None \
            and "node" in config["marker"] \
            and config["marker"]["node"]["show"]:
            self.draw_nodes(state, config=config["marker"])

        if config["axes"] is not None:
            self.draw_axes(state, config=config["axes"])

        if True: #"hover" in config:
            try:
                self.add_elem_data(config=None)#config["hover"])
            except Exception as e:
                warnings.warn(str(e))

    def draw_contours(self, state=None, field=None, config=None, scale=1.0):
        pass

    def skin_elements(self, config):
        pass

    def draw_skeleton(self, skins, state=None, config=None, scale=1.0):
        pass

    def _draw_diagram_x(self, field, scale=1.0, config=None):
        pass

    def draw_diagrams(self, field,  scale=1.0, config=None, color=None):
        """
        Draws diagram fields on line-like elements (frame and truss) as vertical extrusions.

        Parameters
        ----------
        field : callable
            A function taking (element_tag: int, x: float) and returning a scalar field value.
            x ∈ [0, 1] is the normalized local coordinate along the element.
        scale : float, optional
            Scale factor for the diagram magnitudes (applied vertically). Default is 1.0.
        config : dict, optional
            Optional style configuration. Uses 'frame' entry if provided.
        """

        Ra = self._plot_rotation
        model = self.model

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["surface"] for type, conf in SketchConfig().items() if "surface" in conf}
            config.setdefault("frame", {})["show"] = True

        if not config.get("frame", {}).get("show", True):
            return

        offset = np.zeros(3)
        offset[2] = 1.0  # vertical direction

        nodes = []
        triangles = []
        node_index = 0
        Rm = np.array([[0, 0, 0],
                       [0, 0, 1],
                       [0,-1, 0]])

        if hasattr(field, "x"):
            xe = field.x
            ye = field.y
        else:
            xe = None 
            ye = None

        for tag in model.iter_cell_tags():
            if not model.cell_matches(tag, "frame") and not model.cell_matches(tag, "truss"):
                continue

            X = model.cell_position(tag)
            X = np.array([Ra @ x for x in X])  # rotate to view coordinates
            Re = model.frame_orientation(tag)
            if Re is None:
                continue
            
            N = 0
            for i,(xi, yi) in enumerate(zip(*field(tag))):
                L = np.linalg.norm(X[0] - X[1])
                x_ = (1 - xi) * X[0] + xi * X[1]
                y_ = np.array(yi)*scale
                nodes.append(x_)
                nodes.append(x_ + Ra@Re.T@Rm@Re@Ra.T@y_)
                N += 1
            N -= 1


            # Add two triangles per segment
            for i in range(N):
                n0 = node_index + 2 * i
                n1 = node_index + 2 * i + 1
                n2 = node_index + 2 * i + 3
                n3 = node_index + 2 * i + 2

                triangles.append([n0, n1, n2])
                triangles.append([n0, n2, n3])

            node_index += 2 * (N + 1)

        if len(triangles) > 0:
            self.canvas.plot_mesh(np.array(nodes), 
                                  np.array(triangles), 
                                  style=MeshStyle(color=(color or "red"),
                                                  alpha=0.5))
        

    def _draw_frame_lines(self, state=None, config=None, scale=1.0, style=None, skip=None):
        """
        """

        Ra = self._plot_rotation
        model = self.model

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["outline"] for type, conf in SketchConfig().items() if "outline" in conf}
            if style is not None:
                config["frame"]["style"] = style
                config["plane"]["style"] = style
                config["solid"]["style"] = style

        if skip is not None:
            for type in skip:
                config[type]["show"] = False

        if state is not None:
            state = self.model.wrap_state(state, scale=scale, transform=self.dofs2plot)
            # Because "state" is given as opposed to position/displacement, we assume
            # linearized rotations for now.
            config["frame"]["basis"] = "Hermite"

        N = 20 if state is not None and config["frame"]["basis"] is not None else 2
        do_frames = False
        ne = sum(1 for tag in model.iter_cell_tags() 
                 if model.cell_matches(tag, "frame") or model.cell_matches(tag, "truss"))
        frames = np.zeros((ne*(N+1),3))
        frames.fill(np.nan)

        j = 0 # frame element counter
        for tag in model.iter_cell_tags():
            if model.cell_matches(tag, "frame"): # or model.cell_matches(tag, "truss"):
                if not config["frame"]["show"]:
                    continue

                if config["frame"]["basis"] is None or not model.cell_matches(tag, "frame"):
                    # Draw a straight line between nodes
                    do_frames = True
                    frames[(N+1)*j:(N+1)*j+N,:] = np.linspace(*[
                        Ra@xn for xn in model.cell_position(tag, state)[[0,-1],:]
                    ], N)

                else:
                    do_frames = True
                    Q = model.frame_orientation(tag)
                    X = model.cell_position(tag)
                    u = [xi - Xi for Xi, xi in zip(X, model.cell_position(tag, state=state))]
                    R = [model.node_rotation(node, state=state) for node in model.cell_nodes(tag)]


                    frames[(N+1)*j:(N+1)*j+N,:] = [Ra@v for v in  
                                                    _hermite_cubic(X,
                                                                 Q=Q,
                                                                 u = [Q@u[0],          Q@u[1]],
                                                                 v = [Q@so3.log(R[0]), Q@so3.log(R[1])],
                                                                 npoints=N).T]
                j += 1


        if do_frames and config["frame"]["show"]:
            self.canvas.plot_lines(frames[:,:self.ndm], style=config["frame"]["style"])



    def draw_outlines_(self, state=None, config=None, scale=1.0, style=None, skip=None):
        """
        Draw the outlines of the model elements such as frames, planes, and solids.
        Interpolate if possible. This is expensive.

        Parameters
        ----------
        state : dict, np.ndarray, callable, optional
            The state of the model, see :ref:`State`. Default is None.
        config : dict, optional
            Configuration dictionary for drawing outlines. If None, a default configuration is loaded from SketchConfig. Default is None.
        scale : float, optional
            Scaling factor for the model. Default is 1.0.
        """

        Ra = self._plot_rotation
        model = self.model

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["outline"] for type, conf in SketchConfig().items() if "outline" in conf}
            if style is not None:
                config["frame"]["style"] = style
                config["plane"]["style"] = style
                config["solid"]["style"] = style

        if skip is not None:
            for type in skip:
                config[type]["show"] = False

        if state is not None:
            state = self.model.wrap_state(state, scale=scale, transform=self.dofs2plot)
            # Because "state" is given as opposed to position/displacement, we assume
            # linearized rotations for now.
            config["frame"]["basis"] = "Hermite"

        self._draw_frame_lines(state=state, config=config, scale=scale, style=style, skip=skip)


        quadrs = []
        trians = []
        solids = []
        for tag in model.iter_cell_tags():

            if model.cell_matches(tag, "plane") and config["plane"]["show"]:
                idx = model.cell_exterior(tag)
                if len(idx) == 4:
                    quadrs.append([*idx, idx[0]])
                elif len(idx) == 3:
                    trians.append([*idx, idx[0]])

            elif model.cell_matches(tag, "solid") and config["solid"]["show"]:
                # TODO: get cell faces
                idx = model.cell_exterior(tag)
                solids.append(idx)

        nodes = np.array([Ra@x for x in model.node_position(state=state)])

        # Add a small offset to the lines to avoid z-fighting with any surfaces
        if self.model.ndm == 2:
            nodes += Ra@[0, 0, 0.01]

        if len(quadrs) > 0 and config["plane"]["show"]:
            self.canvas.plot_lines(nodes, indices=np.array(quadrs),
                                   style=config["plane"]["style"])

        if len(trians) > 0 and config["plane"]["show"]:
            self.canvas.plot_lines(nodes, indices=np.array(trians),
                                   style=config["plane"]["style"])

        if len(solids) > 0 and config["solid"]["show"]:
            self.canvas.plot_lines(nodes, indices=np.array(solids),
                                          style=config["solid"]["style"])

    def draw_outlines(self, state=None, config=None, scale=1.0, style=None, skip=None):
        """
        Draw the outlines of the model elements such as frames, planes, and solids.
        Interpolate if possible.

        Parameters
        ----------
        state : dict, np.ndarray, callable, optional
            The state of the model, see :ref:`State`. Default is None.
        config : dict, optional
            Configuration dictionary for drawing outlines. If None, a default configuration is loaded from SketchConfig. Default is None.
        scale : float, optional
            Scaling factor for the model. Default is 1.0.
        """

        Ra = self._plot_rotation
        model = self.model

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["outline"] for type, conf in SketchConfig().items() if "outline" in conf}
            if style is not None:
                config["frame"]["style"] = style
                config["plane"]["style"] = style
                config["solid"]["style"] = style

        if skip is not None:
            for type in skip:
                config[type]["show"] = False

        if state is not None:
            state = self.model.wrap_state(state, scale=scale, transform=self.dofs2plot)
            # Because "state" is given as opposed to position/displacement, we assume
            # linearized rotations for now.
            config["frame"]["basis"] = "Hermite"

        self._draw_frame_lines(state=state, config=config, scale=scale, style=style, skip=skip)

        lines  = []
        quadrs = []
        trians = []
        strokes = defaultdict(list)
        for tag in model.iter_cell_tags():

            if model.cell_matches(tag, "plane") and config["plane"]["show"]:
                idx = model.cell_exterior(tag)
                if len(idx) == 4:
                    quadrs.append([*idx, idx[0]])
                elif len(idx) == 3:
                    trians.append([*idx, idx[0]])

            elif model.cell_matches(tag, "solid") and config["solid"]["show"]:
                # TODO: get cell faces
                idx = model.cell_exterior(tag)
                if idx:
                    strokes[len(idx)].append(idx)
                    # solids.append(idx)
            
            elif model.cell_matches(tag, "truss"):
                lines.append(model.cell_exterior(tag))


        nodes = np.array([Ra@x for x in model.node_position(state=state)])

        # Add a small offset to the lines to avoid z-fighting with any surfaces
        if self.model.ndm == 2:
            nodes += Ra@[0, 0, 0.01]
        
        self.canvas.set_data(nodes, key="node_vertices")


        if len(quadrs) > 0 and config["plane"]["show"]:
            self.canvas.plot_lines("node_vertices", indices=np.array(quadrs),
                                   style=config["plane"]["style"])

        if len(trians) > 0 and config["plane"]["show"]:
            self.canvas.plot_lines("node_vertices", indices=np.array(trians),
                                   style=config["plane"]["style"])

        # if len(solids) > 0 and config["solid"]["show"]:
        #     self.canvas.plot_lines("node_vertices", indices=np.array(solids),
        #                                   style=config["solid"]["style"])
        
        for group in strokes.values():
            if len(group):
                self.canvas.plot_lines("node_vertices", indices=np.array(group),
                                            style=config["solid"]["style"])

        if len(lines) > 0:
            self.canvas.plot_lines("node_vertices", indices=np.array(lines),
                                    style=config["frame"]["style"])


    def draw_sections(self,
                      state=None, rotation=None, position=None, scale=1.0,
                      mesh_style=None, config=None):
        """
        Draw beam elements with extruded cross-sections. By default, cross-sectional
        information is extracted from the model by various means.
        For `fiber <https://xara.so/user/manual/section/ShearFiber.html>`__ sections the outline is automatically computed
        using exterior fibers.

        Parameters
        ----------
        state : dict, np.ndarray, callable, optional
            The state of the model, see :ref:`State`. Default is None, in which case the reference state of the model is rendered.
        rotation : np.ndarray, optional
            A callable that returns a quaternion representing the rotation of a given node. In OpenSeesRT models, the `nodeRotation <https://xara.so/user/manual/output/nodeRotation.html>`_ method of a ``Model`` object is typically used.
        config : dict, optional
            Configuration dictionary for drawing surfaces. If None, a default configuration is used based on the SketchConfig.
        scale : float, optional
            Scale factor for the state transformation. Default is 1.0.

        """
        model = self.model
        Ra = self._plot_rotation

        if state is not None or rotation is not None or position is not None:
            state = model.wrap_state(state, 
                                     rotation=rotation, 
                                     position=position, 
                                     scale=scale,
                                     transform=self.dofs2plot)

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["surface"] for type, conf in SketchConfig().items() if "surface" in conf}

        if mesh_style is not None:
            config["frame"]["style"] = mesh_style

        # Draw extruded frames
        from veux.frame import extrude
        extrude.draw_extrusions3(model,
                                canvas=self.canvas,
                                state=state,
                                Ra=Ra,
                                config=config["frame"])


    def draw_samples(self, style=None):
        if style is None :
            style = NodeStyle(color="blue")

        for tag in self.model.iter_cell_tags():
            for x, w in self.model.cell_quadrature(tag):
                # style.scale = np.sqrt(w)*10
                self.canvas.plot_nodes([x], style=style)


    def draw_surfaces(self,
                      state=None, field=None,  # States
                      normal=None,
                      config=None, scale=1.0, style=None): # Drawing
        """
        Draws surfaces on the canvas based on the provided state, field, layer, and configuration.

        Parameters
        ----------
        state : dict, np.ndarray, callable, optional
            The state of the model, see :ref:`State`. Default is None, in which case the reference state of the model is rendered.
        field : dict, optional
            A dictionary representing the field values at each node. If provided, the field values will be plotted on the mesh.
        config : dict, optional 
            Configuration dictionary for drawing surfaces. If None, a default configuration is used based on the SketchConfig.
        scale : float, optional 
            Scale factor for the state transformation. Default is 1.0.
        """

        model = self.model
        Ra = self._plot_rotation

        if state is not None:
            state = model.wrap_state(state, scale=scale, transform=self.dofs2plot)

        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["surface"] for type, conf in SketchConfig().items() if "surface" in conf}
            config["frame"]["show"] = True
            if style is not None:
                config["frame"]["style"] = style
                config["plane"]["style"] = style

        # Draw extruded frames
        if "frame" in config and config["frame"]["show"]:
            from veux.frame import extrude
            extrude.draw_extrusions3(model,
                                    canvas=self.canvas,
                                    state=state,
                                    Ra = Ra,
                                    config=config["frame"])

        # Draw filled mesh for cell-like elements
        triangles = []
        if "plane" in config and config["plane"]["show"]:
            nodes = np.array([Ra@model.node_position(tag,state=state) for tag in model.iter_node_tags()])

            for tag in model.iter_cell_tags():
                if not model.cell_matches(tag, "frame"):
                    triangles.extend(model.cell_triangles(tag))

        if len(triangles) > 0:
            mesh = self.canvas.plot_mesh(nodes, np.array(triangles), style=config["plane"]["style"])

            if field is not None:
                if isinstance(field, dict):
                    field = np.array([field[node] for node in model.iter_node_tags()])
                elif callable(field):
                    field = np.array([field(tag) for tag in model.iter_node_tags()])
                self.canvas.plot_mesh_field(mesh, field=field)

        return

    def draw_nodes(self,
                   state=None,
                   data=None, label=None, config=None, size=None, scale=1.0):
        
        R = self._plot_rotation 

        from veux.config import SketchConfig
        if config is None:
            config = {type: conf["marker"] 
                      for type, conf in SketchConfig().items() if "marker" in conf}

        if size is not None:
            config["node"]["style"].scale = size

        if state is not None:
            state = self.model.wrap_state(state, scale=scale, transform=self.dofs2plot)

        if state is not None and hasattr(state,"rotation") and state.rotation is not None and self.model.ndm == 3:
            rotations = [
                R@self.model.node_rotation(tag, state=state) for tag in self.model.iter_node_tags()
            ]
        else:
            rotations = None

        coord = np.array([R@self.model.node_position(tag, state=state) for tag in self.model.iter_node_tags()])
        
        self.canvas.plot_nodes(coord[:,:self.ndm], label=label,
                               rotations=rotations,
                               style=config["node"]["style"])

        if state is None:
            self.canvas.plot_hover(coord[:,:self.ndm],
                                   label="node",
                                   keys=["tag", "crd"],
                                   data=[[str(k), list(map(str, R.T@coord[i]))]
                                       for i,k in enumerate(self.model.iter_node_tags())])

    def draw_edges(self, state=None, config=None, scale=1.0):
        pass

    def draw_axes(self, state=None, config=None, extrude=False):
        Ra = self._plot_rotation
        if config is None:
            from veux.config import SketchConfig
            config = {type: conf["axes"] for type, conf in SketchConfig().items() if "axes" in conf}
            config["frame"]["show"] = True

        ne = sum(1 for tag in self.model.iter_cell_tags() if self.model.cell_matches(tag, "frame"))
        xyz, uvw = np.nan*np.zeros((2, ne, 3, 3))
        i = 0
        for _,tag in enumerate(self.model.iter_cell_tags()):
            if not self.model.cell_matches(tag, "frame"):
                continue

            axes = self.model.frame_orientation(tag)
            if axes is None or not config["frame"]["show"]:
                continue

            crd = self.model.cell_position(tag, state=state) #el["crd"]
            scale = np.linalg.norm(crd[-1] - crd[0])/15
            coord = sum(i for i in crd)/len(self.model.cell_indices(tag))
            xyz[i,:,:] = np.array([Ra@coord]*3)
            uvw[i,:,:] = scale*axes
            i += 1

        self.canvas.plot_vectors(xyz.reshape(ne*3,3),
                                 np.array([Ra@v for v in uvw.reshape(ne*3,3)]),
                                 extrude=extrude)


    def draw_origin(self, **kwds):
        xyz = np.zeros((3,3))
        uvw = self._plot_rotation.T*kwds.get("scale", 1.0)

        self.canvas.plot_vectors(xyz, uvw, **kwds)

#       for i,label in enumerate(kwds.get("label", [])):
#           self.canvas.annotate(label, (xyz+uvw)[i]+off[i])

    def draw(self):
        # Background
        default = self.config["sketches"]["default"]
        if "origin" in default and default["origin"]["axes"]["show"]:
            origin = default["origin"]
            self.draw_origin(line_style=origin["axes"]["style"],
                                  scale=origin["axes"]["scale"],
                                  label=origin["axes"]["label"])

        # Reference
        if ("reference" in self.config["sketches"] \
                and self.config["sketches"]["reference"]):
            self._draw_sketch(None, config=self._config_sketch("reference"))

        elif len(self.displ_states) == 0:
            self._draw_sketch(None, config=self._config_sketch("default"))

        # Deformations
        for layer, state in self.displ_states.items():
            self._draw_sketch(config=self._config_sketch("displaced"),
                        state=state)

        self.canvas.build()
        return self

    def save(self, filename):
        self.canvas.write(filename)

    def _repr_html_(self):
        from veux.viewer import Viewer
        viewer = Viewer(self,
                        size=(800, 600),
                        hosted=False,
                        show_quit=False,
                        standalone=False)
        html = viewer.get_html()
        return html

    def repl(self):
        from opensees.repl.__main__ import OpenSeesREPL
        self.canvas.plt.ion()

        try:
            from IPython import get_ipython
            get_ipython().run_magic_line('matplotlib')
        except:
            pass

        repl = OpenSeesREPL()

        def plot(*args):
            if len(args) == 0:
                return self.draw()

            elif hasattr(self, "plot_"+args[0]):
                return getattr(self, "plot_"+args[0])(*args[1:])

            elif hasattr(self, args[0]):
                return getattr(self, args[0])(*args[1:])

        repl.interp._interp.createcommand("plot", plot)
        # repl.interp._interp.createcommand("show", lambda *args: self.canvas.show())
        repl.repl()


def _elastic_curve(x: Array, v: list, L:float, tangent=False)->Array:
    "compute points along Euler's elastica"
    if len(v) == 2:
        ui, uj, (vi, vj) = 0.0, 0.0, v
    else:
        ui, vi, uj, vj = v
    xi = x/L                        # local coordinate
    if not tangent:
        N1 = 1.-3.*xi**2+2.*xi**3
        N2 = L*(xi-2.*xi**2+xi**3)
        N3 = 3.*xi**2-2*xi**3
        N4 = L*(xi**3-xi**2)
        y = ui*N1 + vi*N2 + uj*N3 + vj*N4
        return y.flatten()

    else:
        M3 = 1 - xi
        M4 = 6/L*(xi-xi**2)
        M5 = 1 - 4*xi+3*xi**2
        M6 = -2*xi + 3*xi**2
        return (ui*M3 + vi*M5 + uj*M4 + vj*M6).flatten()


def _hermite_cubic(
        coord: Array,
        displ: Array = None,        #: Displacements
        u: Array = None,     #: Displacements at two nodes
        v: Array = None,     #: Rotation vectors at two nodes
        Q = None,
        npoints: int = 10,
        tangent: bool = False
    ):
    n = npoints
    #           (------ndm------)
    reps = 4 if len(coord[0])==3 else 2

    from scipy.linalg import block_diag
    # 3x3 rotation into local system
    # Q = rotation(coord, vect)
    # Element length
    L = np.linalg.norm(coord[-1] - coord[0])

    if u is not None:
        (li, ti, vi), (lj, tj, vj) = u
        (si, ei, pi), (sj, ej, pj) = v
    else:
        # Local displacements
        u_local = block_diag(*[Q]*reps)@displ
        # longitudinal, transverse, vertical, section, elevation, plan
        li, ti, vi, si, ei, pi = u_local[:6]
        lj, tj, vj, sj, ej, pj = u_local[6:]

    Lnew  = L + lj - li
    xaxis = np.linspace(0.0, Lnew, n)

    plan_curve = _elastic_curve(xaxis, [ti, pi, tj, pj], Lnew)
    elev_curve = _elastic_curve(xaxis, [vi,-ei, vj,-ej], Lnew)

    local_curve = np.stack([xaxis + li, plan_curve, elev_curve])

    return Q.T@local_curve + coord[0][None,:].T

