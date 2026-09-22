#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
# Copyright (c) 2025, Claudio M. Perez
# All rights reserved.  No warranty, explicit or implicit, is provided.
#
# This source code is licensed under the BSD 2-Clause License.
# See LICENSE file or https://opensource.org/licenses/BSD-2-Clause
#
from collections import defaultdict
from veux.state  import StateSeries, BasicState, GroupSeriesSE3, GroupStateSE3, GroupStateSO3, Rotation
from xsection.library import Rectangle
import warnings

import numpy as np

from pathlib import Path
from urllib.parse import urlparse
try:
    import orjson as json
except ImportError:
    import json

from veux.frame._section import SectionGeometry

class Model:
    def __iter__(self):
        # this method allows: nodes, cells = Model(mesh)
        return iter((self.nodes, self.cells))

    def make_state(self, state, **kwds):
        # This just needs to return an opaque object that can be passed into the methods below
        return state 
    
    def node_marker(self, tag):
        return self._node_marker

    def node_position(self, tag, **kwds): ...

    def node_information(self, tag): ...

    def iter_cells_tags(self, filt=None): ...

    def cell_matches(self, tag, type): ...

    def cell_type(self, tag):       ... # line triangle quadrilateral 

    def cell_exterior(self, tag):   ...

    def cell_interior(self, tag):   ...

    def cell_quadrature(self, tag):  return []

    def cell_prototypes(self):  return []

    def cell_rotation(self, tag, state): raise NotImplementedError

    def cell_position(self, tag, state): raise NotImplementedError

    def cell_outline(self,  tag):   ...

    def cell_information(self, tag): ...

    def cell_triangles(self, tag):  ...


# Constants
_EYE3 = np.eye(3)

_OUTLINES = {
    None:      None,
    "square":  np.array([[-1., -1.],
                         [ 1., -1.],
                         [ 1.,  1.],
                         [-1.,  1.]])/4.0,

    "tee":     np.array([[ 6.0,  0.0],
                         [ 6.0,  4.0],
                         [-6.0,  4.0],
                         [-6.0,  0.0],
                         [-2.0,  0.0],
                         [-2.0, -8.0],
                         [ 2.0, -8.0],
                         [ 2.0,  0.0]])/10
}


def _is_frame(el):
    name = el["type"].lower()
    return     "beam"  in name \
            or "dfrm"  in name \
            or "frame" in name

def _is_truss(el):
    name = el["type"].lower()
    return "truss" in name #or "twonodelink" in name


def _is_plane(el):
    name = el["type"].lower()
    return "quad" in name or "shell" in name or "tri" in name \
        or "q4" in name or "plate" in name

def _is_solid(el):
    name = el["type"].lower()
    return "brick" in name or "tetra" in name

def _is_link(el):
    name = el["type"].lower()
    return "link" in name

def _orient_frame(xi, xj, angle):
    """
    Calculate the coordinate transformation vector.
    xi is the location of node I, xj node J,
    and `angle` is the rotation about the local axis in degrees

    By default local axis 2 is always in the 1-Z plane, except if the object
    is vertical and then it is parallel to the global X axis.
    The definition of the local axes follows the right-hand rule.
    """

    # The local 1 axis points from node I to node J
    dx, dy, dz = e1 = xj - xi
    # Global z
    E3 = np.array([0, 0, 1])

    # In Sap2000, if the element is vertical, the local y-axis is the same as the
    # global x-axis, and the local z-axis can be obtained by cross-multiplying
    # the local x-axis with the local y-axis.
    if dx == 0 and dy == 0:
        e2 = np.array([1, 0, 0])

    # Otherwise, the plane composed of the local x-axis and the local
    # y-axis is a vertical plane. In this
    # case, the local z-axis can be obtained by the cross product of the local
    # x-axis and the global z-axis.
    else:
        e2 = np.cross(E3, e1)

    e3 = np.cross(e1, e2)

    # Rotate the local axis using the Rodrigue rotation formula
    # convert from degrees to radians
    angle = angle / 180 * np.pi
    e3r = e3 * np.cos(angle) + np.cross(e1, e3) * np.sin(angle)
    # Finally, the normalized local z-axis is returned
    return e3r / np.linalg.norm(e3r)


def read_model(filename:str, shift=None, verbose=False)->dict:
    if isinstance(filename, str) and filename.endswith(".tcl"):
        import opensees.tcl
        try:
            with open(filename, "r") as f:
                interp = opensees.tcl.exec(f.read(), silent=True, analysis=False)
        except UnicodeDecodeError:
            with open(filename, "r", encoding="latin1") as f:
                interp = opensees.tcl.exec(f.read(), silent=True, analysis=False)
        return interp.serialize()

    elif isinstance(filename, str) and (
        filename.endswith(".s2k") or filename.endswith(".$2k") or filename.endswith(".$br")) or filename.endswith(".b2k"):
        from xcsi import Job
        model = Job(filename).instance().model
        return model.asdict()

    elif isinstance(filename, str) and filename.endswith(".inp"):
        from xcae import Project as Job
        model = Job(filename).instance().model
        return model.asdict()

    elif isinstance(filename, str) and filename.endswith(".vtk"):
        import meshio
        from .plane import PlaneModel
        return PlaneModel(meshio.read(filename))

    elif isinstance(filename, str) and filename.endswith(".inp"):
        pass

    try:
        with open(filename,"r") as f:
            sam = json.loads(f.read())

    except TypeError:
        sam = json.loads(filename.read())

    return sam


def read_state(res_file,
               model=None,
               rotation=None,
               position=None,
               time=None,
               scale=None,
               transform=None,
               recover_rotations=None,
               **opts):
    """
    """

    # Turn res_file into res
    if hasattr(res_file, "read"):
        import yaml
        res = yaml.load(res_file, Loader=yaml.Loader)

    elif isinstance(res_file, (str,Path)):
        res_path = urlparse(res_file)
        if "json" in res_path[2]:
            with open(res_path[2], "r") as f:
                res = json.loads(f.read())
        else:
            with open(res_path[2], "r") as f:
                res = yaml.load(f, Loader=yaml.Loader)

        if res_path[4]: # query parameters passed
            res = res[int(res_path[4].split("=")[-1])]
    else:
        res = res_file


    #
    # Create the object
    #
    if model.ndm == model.ndf:
        if isinstance(res, np.ndarray) and len(res.shape) > 1:
            vectors = {
                i: res[i] for i in range(len(res))
            }

        elif isinstance(res, np.ndarray) and res.shape[0] == len(model.iter_node_tags()):
            vectors = {tag: res[i]  for i, tag in enumerate(model.iter_node_tags())}

        elif isinstance(res, np.ndarray):
            # TODO: need to get node-dof mapping
            raise NotImplementedError

        elif callable(res):
            vectors = {tag: res(tag) for tag in model.iter_node_tags()}

        else:
            vectors = res

        return BasicState(vectors, model, transform=transform, scale=scale)


    else:
        # Create a GroupStateSE<n>
        xdof = slice(0,model.ndm)
        rdof = 2 if model.ndm == 2 else slice(3, 6)
        if transform is None:
            transform = np.eye(6)

        if isinstance(res, np.ndarray):
            raise NotImplementedError

        elif callable(res):
            # eg, state=model.nodeDisp
            position_state = BasicState(
                {k: transform[:3,:model.ndm]@res(k)[xdof] for k in model.iter_node_tags()},
                model,
                time=time,
                scale=scale
            )
            if model.ndm == 2:
                rotation_state = GroupStateSO3({
                        k: Rotation.from_rotvec([0, 0, res(k)[rdof]]) 
                        for k in model.iter_node_tags()
                    }, 
                    model, 
                    # scale=scale, 
                    transform=transform[3:,3:], 
                    time=time)
            else:
                rotation_state = GroupStateSO3({
                        k: Rotation.from_rotvec(res(k)[rdof]) 
                        for k in model.iter_node_tags()
                    }, 
                    model, 
                    # scale=scale, 
                    transform=transform[3:,3:], 
                    time=time
                )

        # FEDEAS
        elif isinstance(res, dict) and ("IterationHistory" in res or "ConvergedHistory" in res):

            history = StateSeries(res, model,
                        transform =transform,
                        recover_rotations=recover_rotations
                    )

            if recover_rotations is not None:
                history = GroupSeriesSE3(history, model, recover_rotations=recover_rotations, transform=transform)

            if time is not None:
                return history[time]
            else:
                # TODO: This function should never return a series;
                # implement create_series for that
                return history

        # res is a Dict from node tag to nodal values
        elif isinstance(res, dict):
            position_state = BasicState(
                {k: transform[:3,:model.ndm]@v[xdof] for k,v in res.items()}, 
                model, 
                time=time,
                scale=scale
            )
            if model.ndm == 2:
                rotation_state = GroupStateSO3({
                        k: Rotation.from_rotvec([0, 0, v[rdof]]) if len(v[rdof]) == 1 else Rotation.from_quat(v[rdof])
                        for k,v in res.items()
                    },
                    model, 
                    scale=scale, 
                    transform=transform[3:,3:], 
                    time=time
                )
            else:
                rotation_state = GroupStateSO3(
                        {
                            k: Rotation.from_rotvec(v[rdof])
                            for k,v in res.items()
                        },
                        model,
                      # scale=scale,
                        transform=transform[3:,3:],
                        time=time
                    )

        if callable(position):
            position_state = BasicState(
                {k: transform[:3,:model.ndm]@position(k)[xdof] for k in model.iter_node_tags()},
                model, 
                time=time,
                scale=scale
            )

        if callable(rotation) and model.ndm==2:
            rotation_state = GroupStateSO3(
                {k: Rotation.from_rotvec([0,0,rotation(k)]) for k in model.iter_node_tags()},
                model,
                transform=transform[3:,3:],
                time=time,
                # scale=scale
            )

        elif callable(rotation) and model.ndm==3:
            rotation_state = GroupStateSO3(
                {k: Rotation.from_quat(rotation(k)) for k in model.iter_node_tags()},
                model, 
                transform=transform[3:,3:],
                time=time,
                # scale=scale
            )

        return GroupStateSE3((position_state, rotation_state), model)



class FrameModel:

    def __init__(self,
                 sam:dict,
                 shift = None,
                 frame_outlines=None,
                 frame_shape = None,
                 frame_samples=None,
                 node_marker=None,
                 node_marker_scale=1.0,
                 xmodel=None,
                 **kwds):

        # number of dimensions of artist, not model?
        nda = 3
        R = np.eye(nda) #if rot is None else rot

        if shift is None:
            shift = np.zeros(nda)
        else:
            shift = np.asarray(shift)


        self._xmodel = xmodel
        self._node_marker = node_marker
        if node_marker_scale is not None and node_marker is not None:
            self._node_marker.points *= node_marker_scale
        #
        self._data = _from_opensees(sam, shift, R)# output

        self.ndm = self._data["ndm"]
        self.ndf = self._data["ndf"]

        #
        # Section data
        #
        from .frame._section import SectionGeometry

        # 1) Supplementary data
        self._frame_sections = {}
        self._frame_samples = frame_samples
        for name,section in self._data["sections"].items():
            try:
                _add_section_shape(section, 
                                   self._data["sections"], 
                                   self._frame_sections, 
                                   self.ndm, 
                                   self._xmodel)
            except:
                # fails for shell sections with fibers
                pass

        self._frame_sections = {
            k: SectionGeometry(v) for k,v in self._frame_sections.items() if len(v) > 0
        }


        self._frame_outlines = {}
        if isinstance(frame_outlines, dict):

            for key, polygons in frame_outlines.items():
                if hasattr(polygons, "exterior"):
                    self._frame_outlines[key] = [polygons]
                elif isinstance(polygons, list) and all(hasattr(i, "exterior") for i in polygons):
                    self._frame_outlines[key] = polygons
                elif hasattr(polygons[0][0], "__len__"):
                    # list of numpy arrays
                    self._frame_outlines[key] = [SectionGeometry(i) for i in polygons]
                else:
                    self._frame_outlines[key] = [SectionGeometry(polygons)]

        elif frame_outlines is None and "extrude_outline" not in kwds:
            # TODO: Make this dict of list of sections
            try:
                self._frame_outlines = _get_frame_outlines(self)
            except:
                # Was failing for shell fiber sections
                self._frame_outlines = {}

        # 2) Default extrusion
        self._extrude_default = SectionGeometry(_OUTLINES[kwds.get("extrude_default", "square")])

        # 3) Forced extrusion
        if "extrude_outline" in kwds and frame_shape is None:
            frame_shape = kwds["extrude_outline"]

        if frame_shape is not None:
            if hasattr(frame_shape, "exterior"):
                self._frame_shape = SectionGeometry(
                                          exterior=frame_shape.exterior(),
                                          interior=frame_shape.interior(),
                                          warping=kwds.get("section_warping", None))

            elif isinstance(kwds["extrude_outline"], str):
                self._frame_shape = SectionGeometry(_OUTLINES[kwds["extrude_outline"]])
            else:
                raise ValueError("extrude_outline must be a SectionGeometry or a string")
        else:
            self._frame_shape = None

        self._extrude_scale   = kwds.get("extrude_scale",   1.0)


    def __getitem__(self, key):
        # TODO: Remove this method
        return self._data[key]
    
    def node_marker(self, tag):
        return self._node_marker

    def wrap_state(self,
                    state=None,
                    position=None,
                    rotation=None,
                    scale=None, 
                    transform=None, 
                    recover_rotations=None,
                    **kwds):
        """
        Parameters
        ==========
        state : dict, np.ndarray, callable, optional
            The state of the model, see :ref:`State`. Default is None, in which case the reference state of the model is rendered.
        rotation : np.ndarray, optional
            A callable that returns a quaternion representing the rotation of a given node. In OpenSeesRT models, the `nodeRotation <https://xara.so/user/manual/output/nodeRotation.html>`_ method of a ``Model`` object is typically used.
        """
        if position is not None or rotation is not None or isinstance(state, (dict, np.ndarray)) or callable(state):
            if self.ndm == self.ndf:
                # TODO: This should be gurranteed to return a BasicState;
                # perhaps call the one in plane/__init__.py
                return read_state(state,
                                model=self,
                                scale=scale,
                                transform=transform)
            else:
                # TODO: This should be gurranteed to return a GroupStateSEn
                return read_state(
                                state,
                                position=position,
                                rotation=rotation,
                                model=self,
                                scale=scale,
                                transform=transform,
                                recover_rotations=recover_rotations)
        else:
            return state

    def cell_nodes(self, tag=None):
        if tag is None:
            if not hasattr(self, "_cell_nodes"):
                self._cell_nodes = {k: e["nodes"] for k, e in self["assembly"].items()}
            return self._cell_nodes
        else:
            return self["assembly"][tag]["nodes"]

    def cell_indices(self, tag=None):
        if not hasattr(self, "_cell_indices"):
            self._cell_indices = {
                elem["name"]: tuple(self.node_indices(n) for n in elem["nodes"])
                for elem in self["assembly"].values()
            }

        if tag is not None:
            return self._cell_indices[tag]
        else:
            return self._cell_indices

    def cell_properties(self, tag=None):
        if tag is not None:
            return self["assembly"][tag]

    def cell_prototypes(self)->"iter":
        exclude_keys = {"type", "instances", # "nodes",
                        "crd", "crdTransformation"}

        if not self["prototypes"]:
            elem_types = defaultdict(dict)

            for elem in self["assembly"].values():
                if not self.cell_matches(elem["name"], "frame"):
                    continue
                type = elem["type"]
                if type not in elem_types:
                    elem_types[type]["name"] = type
                    elem_types[type]["variants"] = []
                    elem_types[type]["instances"] = [elem["name"]]
                    elem_types[type]["properties"] = {
                        k: v for k,v in elem.items() if k not in exclude_keys
                    }
                else:
                    elem_types[type]["instances"].append(elem["name"])


            elem_types = list(elem_types.values())
        else:
            elem_types = [
                {
                    "name": f"{elem['type']}<{elem['name']}>",
                    "instances": [self["assembly"][i]["name"] for i in elem["instances"]],
                    "properties":  [
                        [str(v) for k,v in elem.items() if k not in exclude_keys]
                        #for _ in range(len(elem["instances"]))
                    ]*(len(elem["instances"])),
                    "coords": [self["assembly"][i]["crd"] for i in elem["instances"]],
                    "keys":   [k for k in elem.keys() if k not in exclude_keys]

                } for elem in self["prototypes"].get("elements", [])
            ]
        return elem_types

    def iter_node_tags(self):
        for tag in self["nodes"]:
            yield tag

    def iter_cell_tags(self):
        for tag in self["assembly"]:
            yield tag

    def node_properties(self, tag=None)->dict:
        return self["nodes"][tag]

    def node_indices(self, tag=None):
        if not hasattr(self, "_node_indices"):
            self._node_indices = {
                tag: i for i, tag in enumerate(self["nodes"])
            }
        return self._node_indices[tag]

    def node_rotation(self, tag=None, state=None):
        if self.ndm == self.ndf:
            return _EYE3

        if state is None:
            eye = np.eye(3)
            if tag is None:
                return [eye for i in self.iter_node_tags()]
            else:
                return eye

        else:
            return state.node_array(tag, dof=state.rotation)

    def node_position(self, tag=None, state=None):

        if tag is None:
            pos = np.array([n["crd"] for n in self["nodes"].values()])
        else:
            pos = self["nodes"][tag]["crd"]

        if state is not None:
            pos = pos + state.node_array(tag, dof=state.position)

        return pos

    def cell_matches(self, tag, type=None)->bool:
        elem = self["assembly"][tag]

        if type == "prism":
            return _is_frame(elem) and (
                "prism" in elem["type"].lower()
                or "elastic" in elem["type"].lower()
            )
        if type == "frame":
            return _is_frame(elem)
        
        if type == "truss":
            return _is_truss(elem)

        if type == "plane":
            return _is_plane(elem)
        
        if type == "solid":
            return _is_solid(elem) 

        return False

    def cell_position(self, tag, state=None):
        if isinstance(tag, list):
            return np.array([[
                    self.node_position(node, state) for node in self["assembly"][t]["nodes"]
                ] for t in tag
            ])
        else:
            return np.array([ self.node_position(node, state)
                              for node in self["assembly"][tag]["nodes"] ])

    def frame_element(self, tag):
        """
        Iterate over all frame elements in the model.
        """
        from veux.frame._element import _FrameElement
        from veux.frame._section import SectionGeometry
        if self.cell_matches(tag, "truss"):
            return _FrameElement(
                tag=tag,
                vmodel=self,
                xmodel=self._xmodel,
                samples=2
            )

        if self.cell_matches(tag, "frame"):
            frame_shape = self._frame_shape

            if frame_shape is None and self.ndm == 2:
                frame_shape = SectionGeometry([[-1,0],[1,0]])
            

            return _FrameElement(tag=tag,
                                vmodel=self,
                                xmodel=self._xmodel,
                                samples=self._frame_samples,
                                section_override=frame_shape
            )

    def cell_exterior(self, tag):
        """
        return an array of node indices that outline the cell's boundary.
        This is related to finding an Eulerian path through the element's
        connectivity graph.
        """
        type = self["assembly"][tag]["type"].lower()

        if "frm" in type or "beamcol" in type:
            return self.cell_indices(tag)
        
        elif self.cell_matches(tag, "truss"):
            return self.cell_indices(tag)

        elif ("quad" in type or \
              "shell" in type and ("q" in type) or ("mitc" in type) \
                or ("thick" in type) or ("plate" in type)):
            return self.cell_indices(tag)[:4]


        elif ("tri" in type or \
              "shell" in type and ("t" in type)):
            return self.cell_indices(tag)

        elif "tetra" in type:
            indices = self.cell_indices(tag)
            return [indices[i] for i in [0, 1, 2, 3, 0, 2, 3, 1]]

        elif "brick" in type or "hex" in type:
            i = self.cell_indices(tag)
            if len(i) == 8:
                return [
                    i[j] for j in (0, 1, 2, 3, 0, 4, 5, 6, 7, 4, 5, 1, 2, 6, 7, 3)
                ]
            else:
                # TODO: Currently not handling higher-order bricks
                return []

        return []

    def cell_quadrature(self, tag):
        if self.cell_matches(tag, "frame"):
            if self.cell_matches(tag, "prism"):
                return []
            rule = self["assembly"][tag].get("integration", None)
            if rule is None:
                return []
            
            n = len(self["assembly"][tag]["sections"])
            from shps.gauss import iquad
            for xi, wt in zip(*iquad(n=n, rule=rule["type"].lower(), bounds=(0, 1))):
                yield xi, wt

    def cell_interpolation(self, tag):
        pass

    def cell_triangles(self, tag):
        """
        """
        type = self["assembly"][tag]["type"].lower()

        if self.cell_matches(tag, "frame"):
            return []

        elif ("tri" in type or
             ("shell" in type and ("dkgt" in type))):
            return [self.cell_indices(tag)]

        elif ("quad" in type or
             ("shell" in type and ("q" in type) or ("mitc" in type) or ("thick" in type))):
            nodes = self.cell_indices(tag)

            if len(nodes) == 3:
                return nodes

            if len(nodes) in {4,8,9}:
                return [[nodes[0], nodes[1], nodes[2]],
                        [nodes[2], nodes[3], nodes[0]]]

        elif "tetra" in type:
            nodes = self.cell_indices(tag)
            return [[nodes[0], nodes[2], nodes[1]],
                    [nodes[0], nodes[1], nodes[3]],
                    [nodes[0], nodes[3], nodes[2]],
                    [nodes[1], nodes[2], nodes[3]]]

        elif "brick" in type:
            nodes = self.cell_indices(tag)

            if len(nodes) == 8:
                triangles = []
                for face in ((0, 3, 2, 1), (0, 1, 5, 4), (0, 4, 7, 3),
                             (6, 7, 4, 5), (6, 2, 3, 7), (6, 5, 1, 2)):
                    triangles.extend([
                            [nodes[face[0]], nodes[face[1]], nodes[face[2]]],
                            [nodes[face[2]], nodes[face[3]], nodes[face[0]]]
                    ])
                return triangles

        return []


    def _frame_section(self, tag):
        # print(f"{tag = }")
        # This is called by the _FrameElement to get the section geometry for a given element tag.
        if tag is None:
            return self._extrude_default

        return self._frame_sections[int(tag)] \
               if int(tag) in self._frame_sections else self._extrude_default

    def frame_section(self, tag, coord=None)->"SectionGeometry":
        """
        called by extrude3 and Motion

        tag: Element tag
        coord: float in [0,1] indicating the position along the element length where the
        """
        # 
        from .frame._section import SectionGeometry

        if not self.cell_matches(tag, "frame"):
            return None


        # # Initialize frame outlines
        # if self._frame_outlines is None:
        #     # TODO: Make this dict of list of sections
        #     self._frame_outlines = _get_frame_outlines(self)

        if self._frame_shape is not None:
            return self._frame_shape

        # sections = []
        # if self._extrude_outline is not None:
        #     sections = [
        #         SectionGeometry(self._extrude_outline.exterior()*self._section_area(tag, 0))
        #     ]*2 #*self._extrude_scale

        # elif tag in self._frame_outlines:
        #     sections = self._frame_outlines[tag]

        # elif self._extrude_default is not None:
        #     sections = [self._extrude_default]*2 #*self._extrude_scale
        elem = self.frame_element(tag)
        sections = [elem.sample_section(i) for i in elem.simple_samples()]


        # We have sections[], now get the section at the given coordinate
        if len(sections) == 0:
            # print(f"Empty sections for {tag}", file=sys.stderr)
            return

        elif len(sections) == 1:
            return sections[0]

        # Interpolate coord
        elif len(sections) >= 2:
            def interpolate(values, x):
                n = len(values) - 1
                idx = np.clip(int(x * n), 0, n - 1)  # Find the lower bound index
                t = x * n - idx  # Fractional part for interpolation
                return (1 - t) * values[idx] + t * values[idx + 1]

            if coord is None:
                coord = 0.5

            exterior = np.array([s.exterior() for s in sections])
            interior = np.array([s.interior() for s in sections])
            return SectionGeometry(
                interpolate(exterior, coord),
                interpolate(interior, coord)
            )


    def frame_orientation(self, tag, state=None):
        el  = self["assembly"][tag]
        xyz = el["crd"]

        v1  = xyz[-1] - xyz[0]
        L   = np.linalg.norm(v1)
        e1  = v1/L

        if self.ndm == 2:
            v2 =  -np.cross(e1, np.array([0, 0, 1]))
            # v2 =   np.cross(e1, np.array([0, 1, 0]))


        if self.cell_matches(tag, "truss"):
            v3 = _orient_frame(el["crd"][0], el["crd"][1], 0)
            v2 = -np.cross(e1, v3)
        else:
            trsfm = el.get("trsfm", el.get("crdTransformation", {}))
            if trsfm is None:
                trsfm = {}

            if "yvec" in trsfm and trsfm["yvec"] is not None:
                v2  = np.array(trsfm["yvec"])

            elif "vecxz" in trsfm:
                v13 =  np.atleast_1d(trsfm["vecxz"])
                v2  = -np.cross(e1,v13)

            else:
                v3 = _orient_frame(el["crd"][0], el["crd"][1], 0)
                v2  = -np.cross(e1,v3)

        e2 = v2 / np.linalg.norm(v2)
        v3 = np.cross(e1,e2)
        e3 = v3 / np.linalg.norm(v3)
        return np.stack([e1,e2,e3])


class FiberModel(Model):
    ndm = 2 
    ndf = 1
    def __init__(self, fibers, patches=None):
        self._fibers = fibers

    def iter_cell_tags(self):
        yield 1

    def cell_exterior(self):
        return 
        yield 

    def cell_interior(self):
        return 
        yield

    def wrap_state(self, state, **kwds):
        return state

    def cell_quadrature(self, tag):
        if tag == 1:
            for fiber in self._fibers:
                if "location"  in fiber:
                    x = fiber["location"]
                elif "coord" in fiber:
                    x = fiber["coord"]
                else:
                    x = fiber["y"], fiber["z"]
                yield (*x, 0), fiber["area"]


def _from_opensees(sam: dict, shift, R):
    # Process OpenSees JSON format

    # TODO?
    R = np.eye(3)

    try:
        sam = sam["StructuralAnalysisModel"]
    except KeyError:
        pass

    geom = sam.get("geometry", sam.get("assembly"))

#   ndm = len(next(iter(nodes.values()))["crd"])

    if len(geom["nodes"]) > 0:
        try:
            #coord = np.array([R@n.pop("crd") for n in geom["nodes"]], dtype=float) + shift
            coord = np.array([R@n["crd"] for n in geom["nodes"]], dtype=float) + R@shift
            ndm = 3
        except:
            try:
                coord = np.array([R@[*n["crd"], 0.0] for n in geom["nodes"]], dtype=float) + shift
                ndm = 2
            except:
                coord = np.array([
                    R@([*n["crd"], 0.0] if len(n["crd"]) == 2 else n["crd"]) for n in geom["nodes"]], dtype=float) + shift
                ndm = 2
    else:
        ndm = 3

    nodes = {
        n["name"]: {**n, "crd": coord[i], "idx": i}
            for i,n in enumerate(geom["nodes"])
    }

    try:
        ndf = next(iter(nodes.values())).get("ndf", None)
    except StopIteration:
        # No nodes
        ndf = 6

    trsfm = {}
    for t in sam.get("properties", {}).get("crdTransformations", []):
        trsfm[int(t["name"])] = {
            k: val for k,val in t.items() if k not in {"vecxz", "vecInLocXZPlane"}
        }
        if ndm == 3:
            trsfm[int(t["name"])]["vecxz"] = R@(t.get("vecxz", None) or t["vecInLocXZPlane"])

    def _make_transform(e):
        if "transform" in e and int(e["transform"]) in trsfm:
            return trsfm[int(e["transform"])]

        if "crdTransformation" in e and int(e["crdTransformation"]) in trsfm:
            return trsfm[int(e["crdTransformation"])]

        if "yvec" in e:
            return dict(yvec=R@e["yvec"])

    elems =  {
        e["name"]: dict(
            **e,
            crd=np.array([nodes[n]["crd"] for n in e["nodes"]], dtype=float),
            trsfm=_make_transform(e)
        ) for e in geom["elements"]
    }

    try:
        sections = {s["name"]: s for s in sam["properties"]["sections"]}
    except:
        sections = {}

    output = dict(nodes=nodes,
                  assembly=elems,
                  sam=sam,
                  sections=sections,
                  prototypes=sam.get("prototypes", {}),
                  ndm=ndm,
                  ndf=ndf
    )

    return output


def collect_outlines(model):
    return _get_frame_outlines(_from_opensees(model, 
                                              shift=[0, 0, 0], 
                                              R=np.eye(3)))


def _add_section_shape(section, sections, outlines, ndm, xmodel=None):
    tag = int(section["name"])
    if "section" in section:
        # Treat aggregated sections
        child_tag = int(section["section"])
        if child_tag not in outlines:
            _add_section_shape(sections[section["section"]], sections, outlines, ndm, xmodel)

        outlines[tag] = outlines[child_tag]
    
    elif xmodel is not None:
        if tag not in xmodel._objects["section"]:
            return
        sec_obj = xmodel._objects["section"][tag]
        if not hasattr(sec_obj, "_shape") or sec_obj._shape is None:
            return
        outlines[tag] = sec_obj._shape.exterior()

    elif "bounding_polygon" in section:
        # Rotation to change coordinates from x-y to z-y
        R = np.array(((0,-1),
                      (1, 0))).T
        outlines[tag] = [R@s for s in section["bounding_polygon"]]

    elif "fibers" in section and ndm > 2:
        points = np.array([
            f.get("coord", None) or f["location"] for f in section["fibers"]
        ])

        if len(points) == 1:
            A = sum(i["area"] for i in section["fibers"])

            if A is None:
                return

            b = d = np.sqrt(A)
            outlines[tag] = Rectangle(b, d).exterior()
            return

        elif len(points) > 2:
            try:
                from veux.utility.alpha_shape import alpha_shape
                alpha = alpha_shape(points, bound_ratio=0.01) #0.0025) #0.01) #0.03)#0.01)
                if len(alpha) > 0:
                    outlines[tag] =  alpha
            except Exception as e: #scipy.spatial._qhull.QhullError as e:
                warnings.warn("Failed to compute alpha shape")
                import scipy.spatial
                outlines[tag] = points[scipy.spatial.ConvexHull(points).vertices]




def _get_frame_outlines(model):
    xmodel = getattr(model, "_xmodel", None)
    section_outlines = {}
    for name,section in model["sections"].items():
        _add_section_shape(section, model["sections"], section_outlines, model.ndm, xmodel)

    # Function to check if list of lists is homogeneous
    homogeneous = lambda lst: (
            isinstance(lst, list) and \
              all(isinstance(x, list) and \
                  len(set(map(len, lst))) == 1 and all(isinstance(xx, list) and len(set(map(len, x))) == 1 for xx in x) for x in lst
              )
    )

    outlines = {}
    for elem in model["assembly"].values():
        if not model.cell_matches(elem["name"], "frame"):
            continue
        elem_shapes = []
        if "sections" in elem:
            elem_shapes = [
                SectionGeometry(section_outlines[int(i)]) for i in elem["sections"]
                if i in section_outlines and section_outlines[i] is not None
            ]
        elif "section" in elem: # Truss
            if int(elem["section"]) not in section_outlines:
                continue
            elem_shapes = [
                SectionGeometry(section_outlines[int(elem["section"])])
            ]*2

        if len(elem_shapes) != 0:
            outlines[elem["name"]] = elem_shapes

            # if not homogeneous(elem_shapes):
            #     elem_shapes = np.array(elem_shapes[0])
            # else:
            #     elem_shapes = np.array(elem_shapes)

            # outlines[elem["name"]] = [SectionGeometry(shape) for shape in elem_shapes]


    return outlines


"""
._frame_sectoins: dict[section_tag, SectionGeometry]


._frame
"""
