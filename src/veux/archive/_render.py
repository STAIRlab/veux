#!/bin/env python

__version__ = "0.0.4"

# # Synopsis
#
# >`render.py [<options>] <model-file>`
#
# >**Chrystal Chern**, and **Claudio Perez**
# 
#
# This script plots the geometry of a structural
# model given a SAM JSON file. The SAM JSON structure
# was developed by the NHERI SimCenter.
#
#
# # Installation
#
# The simplest way to install this script is to run
# 
#     $ python render.py --install
#
# from a terminal that has python installed, in a
# directory containing the `render.py` file. This
# will install the following packages:

REQUIREMENTS = """
pyyaml
scipy
numpy
plotly
matplotlib
"""

# ## Matlab
# In order to install the Matlab bindings, open Matlab in a
# directory containing the files `render.py` and `render.m`,
# and run the following command in the Matlab interpreter:
#
#     render --install
#
# Once this process is complete, the command `render` can be
# called from Matlab, just as described below for the command
# line.
#
# # Usage
# This script can be used either as a module, or as a command
# line utility. When invoked from the command line on
# **Windows**, {NAME} should be `python -m render`. For example:
#
#     python -m render model.json --axes 2 --view elev
#
# The script may be invoked with the following options:

HELP = """
usage: {NAME} <sam-file>
       {NAME} --setup ...
       {NAME} [options] <sam-file>
       {NAME} [options] <sam-file> <res-file>
       {NAME} --section <py-file>#<py-object>

Generate a plot of a structural model.

Positional Arguments:
  <sam-file>                     JSON file defining the structural model.
  <res-file>                     JSON or YAML file defining a structural
                                 response.

Options:
  DISPLACEMENTS
  -s, --scale  <scale>           Set displacement scale factor.
  -d, --disp   <node>:<dof>...   Apply a unit displacement at node with tag
                                 <node> in direction <dof>.
  VIEWING
  -V, --view   {{elev|plan|sect}}  Set camera view.
      --vert   <int>             Specify index of model's vertical coordinate
      --hide   <object>          Hide <object>; see '--show'.
      --show   <object>          Show <object>; accepts any of:
                                    {{origin|frames|frames.displ|nodes|nodes.displ|extrude}}

  MISC.
  -o, --save   <out-file>        Save plot to <out-file>.
  -C, --conf   <conf-file>
  -c

  BACKEND
  --canvas <canvas>              trimesh, gnu, plotly, matplotlib

      --install                  Install script dependencies.
      --setup                    Run setup operations.
      --script {{sam|res}}
      --version                  Print version and exit.
  -h, --help                     Print this message and exit.



  <dof>        {{long | tran | vert | sect | elev | plan}}
               {{  0  |   1  |   2  |   3  |   4  |   5 }}
  <object>     {{origin|frames|frames.displ|nodes|nodes.displ}}
    origin
    frames
    nodes
    legend
    extrude                      extrude cross-sections
    outline                      outline extrusion
    triads
    x,y,z

    fibers
"""

EXAMPLES="""
Examples:
    Plot the structural model defined in the file `sam.json`:
        $ {NAME} sam.json

    Plot displaced structure with unit translation at nodes
    5, 3 and 2 in direction 2 at scale of 100:

        $ {NAME} -d 5:2,3:2,2:2 -s100 --vert 2 sam.json
"""

# The remainder of this script is broken into the following sections:
#
# - Data shaping / Misc.
# - Kinematics
# - Plotting
# - Command line processing
#

# Configuring
#============
# The following configuration options are available:

Config = lambda : {
  "show_objects": ["frames", "frames.displ", "nodes", "legend", "elastica"],
  "mode_num"    : None,
  "hide_objects": ["origin"],
  "sam_file":     None,
  "res_file":     None,
  "write_file":   None,
  "displ":        defaultdict(list),
  "scale":        100.0,
  "vert":         2,
  "view":         "iso",
  "plotter":      "matplotlib",

  "camera": {
      "view": "iso",               # iso | plan| elev[ation] | sect[ion]
      "projection": "orthographic" # perspective | orthographic
  },

  "displacements": {"scale": 100, "color": "#660505"},

  "objects": {
      "origin": {"color": "black"},
      "frames" : {
          "displaced": {"color": "red", "npoints": 20}
      },
      "nodes": {
          "default": {"size": 3, "color": "#000000"},
          "displaced" : {},
          "fixed"  : {},
      },
      "sections": {"scale": 1.0}
  },
  "save_options": {
      # Options for when writing to an HTML file.
      "html": {
          "include_plotlyjs": True,
          "include_mathjax" : "cdn",
          "full_html"       : True
      }
  }
}

def _apply_config(conf, opts):
    for k,v in conf.items():
        if isinstance(v,dict):
            _apply_config(v, opts[k])
        else:
            opts[k] = v


import sys, os
from collections import defaultdict

try:
    import yaml
    import numpy as np
    Array = np.ndarray
    FLOAT = np.float32
    from scipy.linalg import block_diag

except:
    # prevent undefined variables when run in install mode
    yaml = None
    Array = list
    FLOAT =  float


# Data shaping / Misc.
#----------------------------------------------------

# The following functions are used for reshaping data
# and carrying out other miscellaneous operations.

class RenderError(Exception): pass

def clean_model(sam:dict, shift: Array = None, rot=None)->dict:
    """
    Process OpenSees JSON output and return dict with the form:

        {<elem tag>: {"crd": [<coordinates>], ...}}
    """
    try:
        sam = sam["StructuralAnalysisModel"]
    except KeyError:
        pass

    ndm = 3
    R = np.eye(ndm) if rot is None else rot

    geom = sam.get("geometry", sam.get("assembly"))
    if shift is None:
        shift = np.zeros(ndm)
    else:
        shift = np.asarray(shift)
    try:
        #coord = np.array([R@n.pop("crd") for n in geom["nodes"]], dtype=FLOAT) + shift
        coord = np.array([R@n["crd"] for n in geom["nodes"]], dtype=FLOAT) + shift
    except:
        coord = np.array([R@[*n.pop("crd"), 0.0] for n in geom["nodes"]], dtype=FLOAT) + shift

    nodes = {
            n["name"]: {**n, "crd": coord[i], "idx": i}
                for i,n in enumerate(geom["nodes"])
    }

    ndm = len(next(iter(nodes.values()))["crd"])


    try:
        trsfm = {t["name"]: t for t in sam["properties"]["crdTransformations"]}
    except KeyError:
        trsfm = {}

    elems =  {
      e["name"]: dict(
        **e,
        crd=np.array([nodes[n]["crd"] for n in e["nodes"]], dtype=FLOAT),
        trsfm=trsfm[e["crdTransformation"]]
            if "crdTransformation" in e and e["crdTransformation"] in trsfm
            else dict(yvec=R@e["yvec"] if "yvec" in e else None)
      ) for e in geom["elements"]
    }

    try:
        sections = {s["name"]: s for s in sam["properties"]["sections"]}
    except:
        sections = {}

    output = dict(nodes=nodes, assembly=elems, coord=coord, sam=sam, sections=sections, ndm=ndm)

    if "prototypes" in sam:
        output.update({"prototypes": sam["prototypes"]})

    return output

# Alpha shape utilities
#-----------------------------------------------------------------------
def find_edges_with(i, edge_set):
    i_first = [j for (x,j) in edge_set if x==i]
    i_second = [j for (j,x) in edge_set if x==i]
    return i_first,i_second

def stitch_boundaries(edges):
    edge_set = edges.copy()
    boundary_lst = []
    while len(edge_set) > 0:
        boundary = []
        edge0 = edge_set.pop()
        boundary.append(edge0)
        last_edge = edge0
        while len(edge_set) > 0:
            i,j = last_edge
            j_first, j_second = find_edges_with(j, edge_set)
            if j_first:
                edge_set.remove((j, j_first[0]))
                edge_with_j = (j, j_first[0])
                boundary.append(edge_with_j)
                last_edge = edge_with_j
            elif j_second:
                edge_set.remove((j_second[0], j))
                edge_with_j = (j, j_second[0])  # flip edge rep
                boundary.append(edge_with_j)
                last_edge = edge_with_j

            if edge0[0] == last_edge[1]:
                break

        boundary_lst.append(boundary)
    return boundary_lst

def alpha_shape(points, alpha=2.0, only_outer=True):
    from scipy.spatial import Delaunay
    """
    Compute the alpha shape (concave hull) of a set of points.
    :param points: np.array of shape (n,2) points.
    :param alpha: alpha value.
    :param only_outer: boolean value to specify if we keep only the outer border
    or also inner edges.
    :return: set of (i,j) pairs representing edges of the alpha-shape. (i,j) are
    the indices in the points array.
    """
    assert points.shape[0] > 3, "Need at least four points"

    def add_edge(edges, i, j):
        """
        Add an edge between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            assert (j, i) in edges, "Can't go twice over same directed edge right?"
            if only_outer:
                # if both neighboring triangles are in shape, it's not a boundary edge
                edges.remove((j, i))
            return
        edges.add((i, j))

    tri = Delaunay(points)
    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        # Computing radius of triangle circumcircle
        # www.mathalino.com/reviewer/derivation-of-formulas/derivation-of-formula-for-radius-of-circumcircle
        a = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = np.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = np.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        s = (a + b + c) / 2.0
        area = np.sqrt(s * (s - a) * (s - b) * (s - c))
        circum_r = a * b * c / (4.0 * area)
        if circum_r < alpha:
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    return points[stitch_boundaries(edges)]


def get_section_shape(section, sections=None, outlines=None):
    from scipy.spatial import ConvexHull

    # Rotation to change coordinates from x-y to z-y
    R = np.array(((0,-1),
                  (1, 0))).T

    # Treat aggregated sections
    if "section" in section:
        if section["section"] not in outlines:
            outlines[section["name"]] = get_section_shape(sections[section["section"]], sections, outlines)

    elif "bounding_polygon" in section:
        outlines[section["name"]] = [R@s for s in section["bounding_polygon"]]

    elif "fibers" in section:
        #outlines[section["name"]] = alpha_shape(np.array([f["coord"] for f in section["fibers"]]))
        points = np.array([f["coord"] for f in section["fibers"]])
        outlines[section["name"]] = points[ConvexHull(points).vertices]
    return outlines[section["name"]]

def get_section_geometries(model, renderer=None):

    sections, outlines = {}, {}
    for name,section in model["sections"].items():
        get_section_shape(section, model["sections"], outlines)

    return {
        # TODO: For now, only using the first of the element's cross
        #       sections
        elem["name"]: np.array([outlines[s] for s in elem["sections"]][0])

        for elem in model["assembly"].values() if "sections" in elem
    }

def read_displacements(res_file):

    if not isinstance(res_file, str):
        return yaml.load(res_file, Loader=yaml.Loader)

    from urllib.parse import urlparse
    res_path = urlparse(res_file)
    with open(res_path[2], "r") as f:
        res = yaml.load(f, Loader=yaml.Loader)
    if res_path[4]: # query parameters passed
        res = res[int(res_path[4].split("=")[-1])]

    return res

def read_model(filename:str, shift=None)->dict:
    import json
    try:
        with open(filename,"r") as f:
            sam = json.load(f)
    except TypeError:
        sam = json.load(filename)
    return sam



# Kinematics
#----------------------------------------------------

# The following functions implement various kinematic
# relations for standard frame models.

def elastic_curve(x: Array, v: Array, L:float)->Array:
    "compute points along Euler's elastica"
    if len(v) == 2:
        ui, uj, (vi, vj) = 0.0, 0.0, v
    else:
        ui, vi, uj, vj = v
    xi = x/L                        # local coordinates
    N1 = 1.-3.*xi**2+2.*xi**3
    N2 = L*(xi-2.*xi**2+xi**3)
    N3 = 3.*xi**2-2*xi**3
    N4 = L*(xi**3-xi**2)
    y = ui*N1 + vi*N2 + uj*N3 + vj*N4
    return y.flatten()

def elastic_tangent(x: Array, v: Array, L: float)->Array:
    if len(v) == 2:
        ui, uj, (vi, vj) = 0.0, 0.0, v
    else:
        ui, vi, uj, vj = v
    xi = x/L
    M3 = 1 - xi
    M4 = 6/L*(xi-xi**2)
    M5 = 1 - 4*xi+3*xi**2
    M6 = -2*xi + 3*xi**2
    return (ui*M3+vi*M5+uj*M4+vj*M6).flatten()

def orientation(xyz, yvec=None):
    """Create a rotation matrix between local E and global e basis
    """
    dx = xyz[-1] - xyz[0]
    L = np.linalg.norm(dx)
    e1 = dx/L
    e2 = np.array(yvec)
    v3 = np.cross(e1,e2)
    norm_v3 = np.linalg.norm(v3)

    e3 = v3 / norm_v3
    R = np.stack([e1,e2,e3])
    return R


def rotation(xyz: Array, vert=None)->Array:
    """Create a rotation matrix between local e and global E
    """
    if vert is None: vert = (0,0,1)
    dx = xyz[-1] - xyz[0]
    L = np.linalg.norm(dx)
    e1 = dx/L
    v13 = np.atleast_1d(vert)
    v2 = -np.cross(e1,v13)
    norm_v2 = np.linalg.norm(v2)
    if norm_v2 < 1e-8:
        v2 = -np.cross(e1,np.array([*reversed(vert)]))
        norm_v2 = np.linalg.norm(v2)
    e2 = v2 / norm_v2
    v3 =  np.cross(e1,e2)
    e3 = v3 / np.linalg.norm(v3)
    R = np.stack([e1,e2,e3])
    return R

def displaced_profile(
        coord: Array,
        displ: Array,        #: Displacements
        vect : Array = None, #: Element orientation vector
        npoints: int = 10,
        tangent: bool = False
    )->Array:
    n = npoints
    #           (------ndm------)
    reps = 4 if len(coord[0])==3 else 2

    # 3x3 rotation into local system
    Q = rotation(coord, vect)
    # Local displacements
    u_local = block_diag(*[Q]*reps)@displ
    # Element length
    L = np.linalg.norm(coord[-1] - coord[0])

    # longitudinal, transverse, vertical, section, elevation, plan
    li, ti, vi, si, ei, pi = u_local[:6]
    lj, tj, vj, sj, ej, pj = u_local[6:]

    Lnew = L + lj - li
    xaxis = np.linspace(0.0, Lnew, n)

    plan_curve = elastic_curve(xaxis, [ti, pi, tj, pj], Lnew)
    elev_curve = elastic_curve(xaxis, [vi,-ei, vj,-ej], Lnew)

    local_curve = np.stack([xaxis + li, plan_curve, elev_curve])

    if tangent:
        plan_tang = elastic_tangent(xaxis, [ti, pi, tj, pj], Lnew)
        elev_tang = elastic_tangent(xaxis, [vi,-ei, vj,-ej], Lnew)

        local_tang = np.stack([np.linspace(0,0,n), plan_tang, elev_tang])
        return (
            Q.T@local_curve + coord[0][None,:].T,
            Q.T@local_tang
        )

    return Q.T@local_curve + coord[0][None,:].T



VIEWS = { # pre-defined plot views
    "plan":    dict(azim=  0, elev= 90),
    "sect":    dict(azim=  0, elev=  0),
    "elev":    dict(azim=-90, elev=  0),
    "iso":     dict(azim= 45, elev= 35)
}

class SkeletalRenderer:
    def __init__(self, model, response=None, ndf=None, loc=None, vert=2, **kwds):
        self.ndm = 3

        if ndf is None: ndf = 6

        if vert == 3:
            R = np.eye(3)
        else:
            R = np.array(((1,0, 0),
                          (0,0,-1),
                          (0,1, 0)))

        self.plot_rotation = R

        self.model = clean_model(model, shift=loc, rot=R)

        # Create permutation matrix
        if self.model["ndm"] == 2:
            P = np.array(((1,0, 0),
                          (0,1, 0),
                          (0,0, 0),

                          (0,0, 0),
                          (0,0, 0),
                          (0,0, 1)))
        else:
            P = np.eye(6)

        self.dofs2plot = block_diag(*[R]*2)@P


        self.response_layers = defaultdict(lambda : np.zeros((len(self.model["nodes"]), ndf)))


        config = Config()
        if "config" in kwds:
            _apply_config(kwds.pop("config"), config)
        _apply_config(kwds, config)
        self.config = config


        plotter = config.get("plotter")
        if plotter == "matplotlib":
            self.canvas = MatplotlibCanvas()
        elif plotter == "plotly":
            self.canvas = PlotlyCanvas()
        elif plotter == "trimesh":
            self.canvas = TrimeshCanvas()
        else:
            raise ValueError("Unknown plotter " + str(plotter))

        self.canvas.config = config

    def add_point_displacements(self, displ, scale=1.0, name=None):
        displ_array = self.response_layers[name]
        for i,n in enumerate(self.model["nodes"]):
            for dof in displ[n]:
                displ_array[i, dof] = 1.0

        displ_array[:,3:] *= scale/100
        displ_array[:,:3] *= scale
        return name

    def add_displacement_case(self, displ, name=None, scale=1.0):
        tol = 1e-14
        displ_array = self.response_layers[name]

        for i,n in enumerate(self.model["nodes"]):
            try:
                displ_array[i,:] = self.dofs2plot@displ[n]
            except KeyError:
                pass

        # apply cutoff
        displ_array[np.abs(displ_array) < tol] = 0.0

        # apply scale
        displ_array *= scale
        return name


    def add_displacements(self, res_file, scale=1.0, name=None):
        model = self.model

        if not isinstance(res_file, (dict, Array)):
            displ = read_displacements(res_file)
        else:
            displ = res_file

        # Test type of first item in dict; if dict of dicts,
        # its a collection of responses, otherwise, just a
        # single response
        if isinstance(next(iter(displ.values())), dict):
            if name is not None:
                yield self.add_displacement_case(displ[name], name=name, scale=scale)
            else:
                for k, v in displ.items():
                    yield self.add_displacement_case(v, name=k, scale=scale)
        else:
            yield self.add_displacement_case(displ, scale=scale)


    def label_nodes(self): ...


    def plot_origin(self, scale):
        xyz = np.zeros((3,3))
        uvw = np.eye(3)*scale
        self.canvas.plot_vectors(xyz, uvw)

#   def plot_frame_axes(self):
#       for elem in self.model["assembly"].values():
#           xyz = (elem["crd"][-1] + elem["crd"][0])/2
#           uvw = np.eye(3)/np.linalg.norm(elem["crd"][-1] - elem["crd"][0])
#           self.canvas.plot_vectors(xyz, uvw)

    def add_elem_data(self):
        N = 3
        coords = np.zeros((len(self.model["assembly"])*(N+1),self.ndm))
        coords.fill(np.nan)
        for i,el in enumerate(self.model["assembly"].values()):
            coords[(N+1)*i:(N+1)*i+N,:] = np.linspace(*el["crd"], N)

        coords = coords.reshape(-1,4,3)[:,-3]

        x,y,z = coords.T
        keys  = ["tag",]
        frames = np.array(list(self.model["assembly"].keys()),dtype=FLOAT)[:,None]
        try:
            # TODO: Make this nicer
            self.canvas.data.append({
                    "name": "frames",
                    "x": x, "y": y, "z": z,
                    "type": "scatter3d","mode": "markers",
                    "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
                    "customdata": frames,
                    "opacity": 0
                    #"marker": {"opacity": 0.0,"size": 0.0, "line": {"width": 0.0}}
            })
        except:
            pass

    def add_elem_data(self):
        N = 3
        exclude_keys = {"type", "instances", "nodes", "crd", "crdTransformation"}

        if "prototypes" not in self.model:
            elem_types = defaultdict(lambda: defaultdict(list))
            for elem in self.model["assembly"].values():
                elem_types[elem["type"]]["elems"].append(elem["name"])
                elem_types[elem["type"]]["coords"].append(elem["crd"])
                elem_types[elem["type"]]["data"].append([
                    str(v) for k,v in elem.items() if k not in exclude_keys
                ])
                if "keys" not in elem_types[elem["type"]]:
                    elem_types[elem["type"]]["keys"] = [
                        k for k in elem.keys() if k not in exclude_keys
                    ]
        else:
            elem_types = {
                f"{elem['type']}<{elem['name']}>": {
                    "elems": [self.model["assembly"][i]["name"] for i in elem["instances"]],
                    "data":  [
                        [str(v) for k,v in elem.items() if k not in exclude_keys]
                        #for _ in range(len(elem["instances"]))
                    ]*(len(elem["instances"])),
                    "coords": [self.model["assembly"][i]["crd"] for i in elem["instances"]],
                    "keys":   [k for k in elem.keys() if k not in exclude_keys]

                } for elem in self.model["prototypes"]["elements"]
            }

        for name, elem in elem_types.items():
            coords = np.zeros((len(elem["elems"])*(N+1),self.ndm))
            coords.fill(np.nan)
            for i,crd in enumerate(elem["coords"]):
                coords[(N+1)*i:(N+1)*i+N,:] = np.linspace(*crd, N)

            # coords = coords.reshape(-1,4,N)[:,-N]
            coords = coords.reshape(-1,4,3)[:,-3]

            x,y,z = coords.T
            keys  = elem["keys"]
            data = np.array(elem["data"])

            # TODO: Make this nicer
            self.canvas.data.append({
                "name": name,
                "x": x, "y": y, "z": z,
                "type": "scatter3d", "mode": "markers", # "lines", #
                "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
                "customdata": data,
                "opacity": 0 if "zerolength" not in name.lower() else 0.6
                #"marker": {"opacity": 0.0,"size": 0.0, "line": {"width": 0.0}}
            })

    def plot_chords(self, assembly, displ=None, layer=None):
        frame = self.model
        nodes = self.model["nodes"]
        ndm   = self.model["ndm"]

        N = 2
        coords = np.zeros((len(frame["assembly"])*(N+1),self.ndm))
        coords.fill(np.nan)

        for i,el in enumerate(frame["assembly"].values()):
            coords[(N+1)*i:(N+1)*i+N,:] = np.linspace(el["crd"][0], el["crd"][-1], N)

            # exclude zero-length elements
            if "zero" not in el["type"].lower() and displ is not None:
                coords[(N+1)*i:(N+1)*i+N,:] += [
                    displ[nodes[n]["name"]][:ndm] for n in (el["nodes"][0], el["nodes"][-1])
                ]

        self.canvas.plot_lines(coords)


    def plot_extruded_frames(self, displ=None, rotations=None):
        from scipy.spatial.transform import Rotation

        sections = get_section_geometries(self.model, self)

        nodes = self.model["nodes"]
        # N = 2
        # N = 20 if displ is not None else 2
        N = 2 if displ is not None else 2

        coords = []
        triang = []
        I = 0
        for i,el in enumerate(self.model["assembly"].values()):
            # if int(el["name"]) < 30: continue
            try:
                sect = sections[el["name"]]
            except:
                if int(el["name"]) < 1e3:
                    sect = self.config["default_section"]
                else:
                    sect = np.array([
                        [-48, -48],
                        [ 48, -48],
                        [ 48,  48],
                        [-48,  48]])

            ne = len(sect)
            R  = rotation(el["crd"], None)
            if displ is not None:
                glob_displ = [
                    u for n in el["nodes"]
                        for u in displ[nodes[n]["idx"]]
                ]
                vect = None #np.array(el["trsfm"]["vecInLocXZPlane"])[axes]
                X,r = displaced_profile(el["crd"], glob_displ, vect=vect, npoints=N, tangent=True)
                X = X.T
                # R = [Rotation.from_mrp(v).as_matrix()@R for v in r.T]
                # R = [Rotation.from_rotvec(v).as_matrix()@R for v in r.T]
                # R = [Rotation.from_euler("xyz",v).as_matrix()@R for v in r.T]

                R = [Rotation.from_euler("xzy",v).as_matrix()@R for v in r.T]

            else:
                X  = np.linspace(el["crd"][0], el["crd"][-1], N)
                R = [R]*N

            for j in range(N):
                for k,edge in enumerate(sect):
                    coords.append(X[j  , :] + R[j].T@[0, *edge])
                    if j == 0:
                        continue

                    elif k < ne-1:
                        triang.extend([
                            [I+    ne*j + k, I+    ne*j + k + 1, I+ne*(j-1) + k],
                            [I+ne*j + k + 1, I+ne*(j-1) + k + 1, I+ne*(j-1) + k]
                        ])
                    else:
                        # elif j < N-1:
                        triang.extend([
                            [I+    ne*j + k,    I + ne*j , I+ne*(j-1) + k],
                            [      I + ne*j, I + ne*(j-1), I+ne*(j-1) + k]
                        ])

            I += N*ne

        if True:
            x,y,z = zip(*coords)
            i,j,k = zip(*triang)
            self.canvas.data.append({
                #"name": label if label is not None else "",
                "type": "mesh3d",
                "x": x, "y": y, "z": z, "i": i, "j": j, "k": k,
                "hoverinfo":"skip",
                "lighting": dict(ambient=0.9), #roughness=0.5, specular=0.2),
                "opacity": 1.0,
                "color": "gray",
                # "color": "white",
                # "opacity": 0.2
            })

        show_edges = True
        if show_edges:
            IDX = np.array((
                (0, 2),
                (0, 1)
            ))
            nan = np.zeros(self.ndm)*np.nan
            coords = np.array(coords)
            tri_points = np.array([
                coords[idx]  if (j+1)%3 else nan for j,idx in enumerate(np.array(triang).reshape(-1))
                # coords[i]  if j%2 else nan for j,idx in enumerate(np.array(triang)) for i in idx[IDX[j%2]]
            ])
            Xe, Ye, Ze = tri_points.T
            self.canvas.data.append({
                "type": "scatter3d",
                "mode": "lines",
                "x": Xe, "y": Ye, "z": Ze,
                "hoverinfo":"skip",
                "opacity": 1.0,
                "line": { "color": "black", "width": 5}
            })



    def plot_displaced_assembly(self, assembly, displ=None, label=None):
        frame = self.model
        nodes = self.model["nodes"]
        N = 10 if displ is not None else 2
        coords = np.zeros((len(frame["assembly"])*(N+1),self.ndm))
        coords.fill(np.nan)

        for i,el in enumerate(frame["assembly"].values()):
            # exclude zero-length elements
            if "zero" not in el["type"].lower() and displ is not None:
                glob_displ = [
                    u for n in el["nodes"]
                        for u in displ[nodes[n]["idx"]]
                ]
                vect = None #np.array(el["trsfm"]["vecInLocXZPlane"])[axes]
                coords[(N+1)*i:(N+1)*i+N,:] = displaced_profile(el["crd"], glob_displ, vect=vect, npoints=N).T
            else:
                coords[(N+1)*i:(N+1)*i+N,:] = np.linspace(*el["crd"], N)

        self.canvas.plot_lines(coords, color="red", label=label)

    def plot_nodes(self, displ=None, data=None):
        coord = self.model["coord"]
        if displ is not None:
            coord = coord + displ[:, :self.ndm]
        self.canvas.plot_nodes(coord, data=data)

    def add_triads(self, displ=None):
        ne = len(self.model["assembly"])
        xyz, uvw = np.nan*np.zeros((2, ne, 3, 3))

        for i,el in enumerate(self.model["assembly"].values()):
            scale = np.linalg.norm(el["crd"][-1] - el["crd"][0])/10
            coord = sum(i for i in el["crd"])/len(el["nodes"])
            xyz[i,:,:] = np.array([coord]*3)
            uvw[i,:,:] = scale*orientation(el["crd"], el["trsfm"]["yvec"])
#           self.canvas.plot_vectors(np.array([coord]*3), scale*rotation(el["crd"], el["trsfm"]["yvec"]))
        self.canvas.plot_vectors(xyz.reshape(ne*3,3), uvw.reshape(ne*3,3))


    def plot(self):
        if "frames" in self.config["show_objects"]:
            self.plot_chords(self.model["assembly"])
            try:
                self.add_elem_data()
            except:
                pass

        if "nodes" in self.config["show_objects"]:
            self.plot_nodes(data=list(np.array(list(self.model["nodes"].keys()),dtype=FLOAT)[:,None]))

        if "origin" in self.config["show_objects"]:
            self.plot_origin(self.config["scale"])

        if "triads" in self.config["show_objects"]:
            self.add_triads()

        for layer, displ in self.response_layers.items():
            if "chords" in self.config["show_objects"]:
                self.plot_chords(self.model["assembly"], displ=displ, layer=layer)
            self.plot_displaced_assembly(self.model["assembly"], displ=displ, label=layer)

        if "extrude" in self.config["show_objects"]:
            displ = None
            if len(self.response_layers) == 1:
                displ = next(iter(self.response_layers.values()))
            try:
                self.plot_extruded_frames(displ)
            except Exception as e:
                print("Warning -- ", e, file=sys.stderr)

        self.canvas.build()
        return self

    def write(self, filename):
        self.canvas.write(filename)

    def repl(self):
        from opensees.repl.__main__ import OpenSeesREPL
        self.canvas.plt.ion()

        try:
            from IPython import get_ipython
            # get_ipython().magic('%matplotlib')
            get_ipython().run_magic_line('matplotlib')
        except:
            pass

        repl = OpenSeesREPL()

        def plot(*args):
            if len(args) == 0:
                return self.plot()

            elif hasattr(self, "plot_"+args[0]):
                return getattr(self, "plot_"+args[0])(*args[1:])

            elif hasattr(self, args[0]):
                return getattr(self, args[0])(*args[1:])

        repl.interp._interp.createcommand("plot", plot)
        # repl.interp._interp.createcommand("show", lambda *args: self.canvas.show())
        repl.repl()


class Canvas:
    def build(self): ...
    def show(self): ...
    def write(self, filename=None): ...
    def plot_nodes(self, coords, label = None, props=None, data=None): ...

    def plot_lines(self, coords, label=None, props=None, color=None, width=None): ...

    def plot_vectors(self, locs, vecs, label=None, **kwds):
        ne = vecs.shape[0]
        for j in range(3):
            X = np.zeros((ne*3, 3))*np.nan
            for i in range(j,ne,3):
                X[i*3,:] = locs[i]
                X[i*3+1,:] = locs[i] + vecs[i]
            self.plot_lines(X, color=("red", "blue", "green")[j], label=label)

    def plot_mesh(self,vertices, triangles, **kwds): ...


class TrimeshCanvas(Canvas):
    def __init__(self, config=None):
        import trimesh
        self.scene = trimesh.Scene()
        self.config = config

    def plot_mesh(self,vertices, triangles):
        import trimesh
        mesh = trimesh.Trimesh(vertices=vertices,
                               faces=triangles)
        self.scene.add_geometry(mesh)

    def write(self, filename=None):
        import trimesh
        opts = self.config

        if "glb" in opts["write_file"][-3:]:
            with open(opts["write_file"],"wb+") as f:
                f.write(trimesh.exchange.gltf.export_glb(self.scene))

        elif "gltf" in opts["write_file"][-4:]:
            import json
            with open(opts["write_file"],"w+") as f:
                json.dump(trimesh.exchange.gltf.export_gltf(self.scene), f)

class MatplotlibCanvas:
    def __init__(self, ax=None):
        if ax is None:
            import matplotlib.pyplot as plt
            self.plt = plt
            _, ax = plt.subplots(1, 1, subplot_kw={"projection": "3d"})
            ax.set_autoscale_on(True)
            ax.set_axis_off()

        self.ax = ax

    def show(self):
        self.plt.show()

    def build(self):
        ax = self.ax
        opts = self.config
        aspect = [ub - lb for lb, ub in (getattr(ax, f'get_{a}lim')() for a in 'xyz')]
        aspect = [max(a,max(aspect)/8) for a in aspect]
        ax.set_box_aspect(aspect)
        ax.view_init(**VIEWS[opts["view"]])
        return ax

    def write(self, filename=None):
        self.ax.figure.savefig(self.config["write_file"])

    def plot_lines(self, coords, label=None, conf=None, color=None):
        props = conf or {"color": color or "grey", "alpha": 0.6, "linewidth": 0.5}
        self.ax.plot(*coords.T, **props)

    def plot_nodes(self, coords, label=None, conf=None, data=None):
        ax = self.ax
        props = {"color": "black",
                 "marker": "s",
                 "s": 0.1,
                 "zorder": 2
        }
        self.ax.scatter(*coords.T, **props)

    def plot_vectors(self, locs, vecs, alr=0.1, **kwds):
        self.ax.quiver(*locs, *vecs, arrow_length_ratio=alr, color="black")

    def plot_trisurf(self, xyz, ijk):
        ax.plot_trisurf(*xyz.T, triangles=ijk)



class PlotlyCanvas:
    def __init__(self, config=None):
        self.data = []
        self.config = config

    def show(self):
        self.fig.show(renderer="browser")

    def build(self):
        opts = self.config
        show_axis = "axis" in opts["show_objects"]
        show_grid = "grid" in opts["show_objects"]
        import plotly.graph_objects as go
        fig = go.Figure(dict(
                data=self.data,
                layout=go.Layout(
                  scene=dict(aspectmode='data',
                     xaxis = {"showspikes": "tick" in opts["show_objects"],
                              "showbackground": show_grid, "gridcolor": "gray" if show_grid else None},
                     yaxis = {"showspikes": "tick" in opts["show_objects"],
                              "showbackground": show_grid, "gridcolor": "gray" if show_grid else None},
                     zaxis = {"showspikes": "tick" in opts["show_objects"],
                              "showbackground": show_grid, "gridcolor": "gray" if show_grid else None},
                     xaxis_visible = "x" in opts["show_objects"],#show_axis,
                     yaxis_visible = "y" in opts["show_objects"],#show_axis,
                     zaxis_visible = "z" in opts["show_objects"],#show_axis,
                     camera=dict(
                         projection={"type": opts["camera"]["projection"]}
                     )
                  ),
#                 showlegend=("legend" in opts["show_objects"])
                )
            ))
        fig.update(layout_coloraxis_showscale=False)
        self.fig = fig
        return self

    def write(self, filename=None):
        opts = self.config
        if "html" in filename:
            import plotly
            fig = self.fig
            html = plotly.io.to_html(fig, div_id=str(id(self)), **opts["save_options"]["html"])
            with open(opts["write_file"],"w+") as f:
                f.write(html)
        elif "json" in opts["write_file"]:
            with open(opts["write_file"],"w+") as f:
                self.fig.write_json(f)

    def make_hover_data(self, data, ln=None):
        if ln is None:
            items = np.array([d.values for d in data])
            keys = data[0].keys()
        else:
            items = np.array([list(data.values())]*ln)
            keys = data.keys()
        return {
            "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
            "customdata": list(items),
        }


    def plot_nodes(self, coords, label = None, props=None, data=None):
        name = label or "nodes"
        x,y,z = coords.T
        keys  = ["tag",]

        data = {
                "name": name,
                "x": x, "y": y, "z": z,
                "type": "scatter3d","mode": "markers",
                "hovertemplate": "<br>".join(f"{k}: %{{customdata[{v}]}}" for v,k in enumerate(keys)),
                "customdata": data,
                "marker": {
                    "symbol": "square",
                    **self.config["objects"]["nodes"]["default"]
                },
                "showlegend": False
        }
        self.data.append(data)

    def plot_lines(self, coords, label=None, props=None, color=None, width=None):
        x,y,z = coords.T
        props = {"color": color or "#808080", "alpha": 0.6}
        data = {
            "name": label if label is not None else "",
            "type": "scatter3d",
            "mode": "lines",
            "x": x, "y": y, "z": z,
            "line": {"color": props["color"] if color is None else color, "width": width},
            "hoverinfo":"skip"
        }
        self.data.append(data)

    def plot_vectors(self, locs, vecs, label=None, **kwds):

        ne = vecs.shape[0]
        for j in range(3):
            X = np.zeros((ne*3, 3))*np.nan
            for i in range(j,ne,3):
                X[i*3,:] = locs[i]
                X[i*3+1,:] = locs[i] + vecs[i]
            self.data.append({
                "name": label if label is not None else "",
                "type": "scatter3d",
                "mode": "lines",
                "x": X.T[0], "y": X.T[1], "z": X.T[2],
                "line": {"color": ("red", "blue", "green")[j], "width": 4},
                "hoverinfo":"skip"
            })

    def plot_mesh(self, vertices, triangles):
        x,y,z = zip(*vertices)
        i,j,k = zip(*triangles)
        self.data.append({
            #"name": label if label is not None else "",
            "type": "mesh3d",
            "x": x, "y": y, "z": z, "i": i, "j": j, "k": k,
            "hoverinfo":"skip",
            "lighting": dict(ambient=0.9), #roughness=0.5, specular=0.2),
            "opacity": 1.0,
            "color": "gray",
            # "color": "white",
            # "opacity": 0.2
        })



# Script functions
#----------------------------------------------------

# Argument parsing is implemented manually because in
# the past I have found the standard library module
# `argparse` to be slow.

AXES = dict(zip(("long","tran","vert","sect","elev", "plan"), range(6)))

def dof_index(dof: str):
    try: return int(dof)
    except: return AXES[dof]


def parse_args(argv)->dict:
    opts = Config()
    if os.path.exists(".render.yaml"):
        with open(".render.yaml", "r") as f:
            presets = yaml.load(f, Loader=yaml.Loader)

        _apply_config(presets,opts)

    args = iter(argv[1:])
    for arg in args:
        try:
            if arg == "--help" or arg == "-h":
                print(HELP.format(NAME=sys.argv[0]))
                sys.exit()


            elif arg == "--gnu":
                opts["plotter"] = "gnu"
            elif arg == "--plotly":
                opts["plotter"] = "plotly"
            elif arg == "--canvas":
                opts["plotter"] = next(args)

            elif arg == "--install":
                try: install_me(next(args))
                # if no directory is provided, use default
                except StopIteration: install_me()
                sys.exit()

            elif arg == "--version":
                print(__version__)
                sys.exit()

            elif arg[:2] == "-d":
                node_dof = arg[2:] if len(arg) > 2 else next(args)
                for nd in node_dof.split(","):
                    node, dof = nd.split(":")
                    opts["displ"][int(node)].append(dof_index(dof))

            elif arg[:6] == "--disp":
                node_dof = next(args)
                for nd in node_dof.split(","):
                    node, dof = nd.split(":")
                    opts["displ"][int(node)].append(dof_index(dof))

            elif arg == "--conf":
                with open(next(args), "r") as f:
                    presets = yaml.load(f, Loader=yaml.Loader)
                _apply_config(presets,opts)


            elif arg[:2] == "-s":
                opts["scale"] = float(arg[2:]) if len(arg) > 2 else float(next(args))
            elif arg == "--scale":
                scale = next(args)
                if "=" in scale:
                    # looks like --scale <object>=<scale>
                    k,v = scale.split("=")
                    opts["objects"][k]["scale"] = float(v)
                else:
                    opts["scale"] = float(scale)

            elif arg == "--vert":
                opts["vert"] = int(next(args))

            elif arg == "--show":
                opts["show_objects"].extend(next(args).split(","))

            elif arg == "--hide":
                opts["show_objects"].pop(opts["show_objects"].index(next(args)))

            elif arg[:2] == "-V":
                opts["view"] = arg[2:] if len(arg) > 2 else next(args)
            elif arg == "--view":
                opts["view"] = next(args)

            elif arg == "--default-section":
                opts["default_section"] = np.loadtxt(next(args))

            elif arg[:2] == "-m":
                opts["mode_num"] = int(arg[2]) if len(arg) > 2 else int(next(args))

            elif arg == "--time":
                opts["time"] = next(args)

            elif arg[:2] == "-o":
                filename = arg[2:] if len(arg) > 2 else next(args)
                opts["write_file"] = filename
                if "html" in filename or "json" in filename:
                    opts["plotter"] = "plotly"


            # Final check on options
            elif arg[0] == "-" and len(arg) > 1:
                raise RenderError(f"ERROR - unknown option '{arg}'")

            elif not opts["sam_file"]:
                if arg == "-": arg = sys.stdin
                opts["sam_file"] = arg

            else:
                if arg == "-": arg = sys.stdin
                opts["res_file"] = arg

        except StopIteration:
            # `next(args)` was called in parse loop without successive arg
            raise RenderError(f"ERROR -- Argument '{arg}' expected value")

    return opts

def install_me(install_opt=None):
    import os
    import subprocess
    import textwrap
    if install_opt == "dependencies":
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *REQUIREMENTS.strip().split("\n")
        ])
        sys.exit()
    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup
    name = sys.argv[0]

    sys.argv = sys.argv[:1] + ["develop", "--user"]
    package = name[:-3].replace(".", "").replace("/","").replace("\\","")
    # if True:
    #     print(package)
    #     print(name[:-3])
    #     print(sys.argv)
    #     sys.exit()

    setup(name=package,
          version=__version__,
          description="",
          long_description=textwrap.indent(HELP, ">\t\t"),
          author="",
          author_email="",
          url="",
          py_modules=[package],
          scripts=[name],
          license="",
          install_requires=[*REQUIREMENTS.strip().split("\n")],
    )

TESTS = [
    (False,"{NAME} sam.json -d 2:plan -s"),
    (True, "{NAME} sam.json -d 2:plan -s50"),
    (True, "{NAME} sam.json -d 2:3    -s50"),
    (True, "{NAME} sam.json -d 5:2,3:2,2:2 -s100 --vert 2 sam.json")
]

def render(sam_file, res_file=None, noshow=False, **opts):
    # Configuration is determined by successively layering
    # from sources with the following priorities:
    #      defaults < file configs < kwds 

    config = Config()


    if sam_file is None:
        raise RenderError("ERROR -- expected positional argument <sam-file>")

    # Read and clean model
    if not isinstance(sam_file, dict):
        model = read_model(sam_file)
    else:
        model = sam_file

    if "RendererConfiguration" in model:
        _apply_config(model["RendererConfiguration"], config)

    _apply_config(opts, config)

    renderer = SkeletalRenderer(model, **config)

    # Read and clean displacements 
    # TODO: 
    # - remove `cases` var, 
    # - change add_displacements from being a generator
    # rename `name` parameter
    if res_file is not None:
        cases = renderer.add_displacements(res_file, scale=config["scale"],
                                           name=config["mode_num"])
        list(cases)

    elif config["displ"] is not None:
        cases = [renderer.add_point_displacements(config["displ"], scale=config["scale"])]

    if "Displacements" in model:
        cases.extend(renderer.add_displacements(model["Displacements"],scale=config["scale"],
                                                name=config["mode_num"]))


    # write plot to file if file name provided
    if config["write_file"]:
        renderer.plot()
        renderer.write(config["write_file"])

    else:
        renderer.plot()
        if not noshow:
            renderer.canvas.show()
        # renderer.repl()

    return renderer


if __name__ == "__main__":
    config = parse_args(sys.argv)

    try:
        render(**config)

    except (FileNotFoundError, RenderError) as e:
        # Catch expected errors to avoid printing an ugly/unnecessary stack trace.
        print(e, file=sys.stderr)
        print("         Run '{NAME} --help' for more information".format(NAME=sys.argv[0]), file=sys.stderr)
        sys.exit()

