# Claudio Perez
# Summer 2024
import yaml
import json
import numpy as np
from pathlib import Path
from urllib.parse import urlparse
from scipy.spatial.transform import Rotation

from veux.config import LineStyle, MeshStyle

class State:
    time: float
#   node_array : np.array
#   cell_array : np.array

class so3:
    @classmethod
    def exp(cls, vect):
        return Rotation.from_rotvec(vect).as_matrix()


def read_state(res_file, model=None, only=None, time=None, scale=None, transform=None, recover=None, **opts):

    if hasattr(res_file, "read"):
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
#   show_objects = opts.get("show_objects", set())
    recover_rotations = recover # "iter" if "iter" in show_objects else \
                                # "incr" if "incr" in show_objects else None


    if isinstance(res, np.ndarray) or callable(res):
        return BasicState(res, model, transform=transform, scale=scale, time=time)

    # FEDEAS
    elif "IterationHistory" in res or "ConvergedHistory" in res:

        history = StateSeries(res, model,
                    transform =transform,
                    recover_rotations=recover_rotations
                  )

        if recover_rotations is not None:
            history = GroupSeriesSE3(history, model, recover_rotations=recover_rotations, transform=transform)

        if time is not None:
            return history[time]
        else:
            return history


    # Dict of state dicts
    elif isinstance(next(iter(res.values())), dict):
        return {
            k: BasicState(v, model, transform=transform, scale=scale)
                for k,v in res.items()
        }

    # Dict from node tag to nodal values
    else:
        return BasicState(res, model, transform=transform, scale=scale)



class BasicState(State):
    # spatial distribution of a solution
    def __init__(self, data, model, scale=1.0, fn=None, transform=None, time=None):
        """
        data: callable|dict|array
        """
        self.model  = model
        self.time   = time
        self.position   = slice(0, 3)
        self.line_style = LineStyle()
        self.mesh_style = MeshStyle()

        # Handle data
        if isinstance(data, np.ndarray):
            self.ndf = data.shape[1] if len(data.shape) > 1 else 1
            data = {tag: data[i]  for i, tag in enumerate(model.iter_node_tags())}
        else:
            self.ndf = model.ndf

        if self.ndf == 2 or (self.model.ndm == 3 == self.ndf):
            self.rotation = None
        elif self.model.ndm == 2:
            self.rotation = 2
        elif self.model.ndm == 3:
            self.rotation = slice(3, None)

        if callable(data): # OpenSees
            # fn is something like nodeDisp or nodeEigenvector
            data = {tag: data(tag) for tag in model.iter_node_tags()}

        # Handle remaining arguments; by now data should be a dict
        if scale is not None:
            data = {k: scale*np.array(val) for k, val in data.items()}

        if transform is not None:
            data = {k: transform@np.atleast_1d(val) for k, val in data.items()}

        self._data  : dict  = data
        self._scale : float = scale

    def __repr__(self):
        return f"<BasicState {self._data}>"


    def node_array(self, tag=None, dof=None):
        # ordered by dof
        if tag is None:
            if dof is None:
                return np.array([self._data[tag] for tag in self.model.iter_node_tags()])
            else:
                return np.array([self._data[tag][dof] for tag in self.model.iter_node_tags()])

        elif dof is None:
            return self._data[tag]

        else:
            return self._data[tag][dof]


    def cell_array(self, tag,
                    dof: int  =None,
                    loc: float=None,
                    node=None,
                    incr=None):

        # incr: init,conv,iter

        return np.array([
                u for n in self.model.cell_nodes(tag)
                    for u in self.node_array(n, dof)
        ])
        return np.array([
                [u for u in self.node_array(n, dof)]
                for n in self.model.cell_nodes(tag)
        ])


class Series:
    @property
    def times(self):
        return np.array(list(self._hist.keys()))

    def node_array(self, tag, dof):
        return np.array([self[time].node_array(tag, dof) for time in self.times])

    def __getitem__(self, time):
        if time < 0:
            return list(self._hist.values())[time]["converged"]
        else:
            return self._hist[time]["converged"]


class GroupSeriesSE3(Series):
    def __init__(self, series: "StateSeries", model, transform=None, **kwds):
        self.model  = model
        if transform is None:
            transform = np.eye(6)

        rotation = GroupSeriesSO3(series, model, transform=transform[3:,3:], **kwds)
        position = series

        self._hist = {
            time: {
                "converged": GroupStateSE3((position[time], rotation[time]), model, time=time)
            } for time in series.times
        }


class GroupStateSE3(State):
    def __init__(self, data, model, time=None):
        self.model  = model
        self._data  = data
        self.time   = time
        self.position = 10
        self.rotation = 20
        self.line_style = LineStyle()
        self.mesh_style = MeshStyle()

        if isinstance(data, tuple):
            self._position = data[0]
            self._rotation = data[1]


    def cell_array(self, tag, dof=None):
        # Note: cant return numpy array, because
        # rotation is different from position
        return [
                self.node_array(node, dof)
                for node in self.model.cell_nodes(tag)
        ]

    def node_array(self, tag, dof):
        if dof == self.position:
            return  self._position.node_array(tag, slice(0,3))
        elif dof == self.rotation:
            return  self._rotation.node_array(tag)
        else:
            return (self._position.node_array(tag),
                    self._rotation.node_array(tag))


class GroupStateSO3(State):
    def __init__(self, data, model, time=None, transform=None):
        self.model  = model
        self.time   = time

        self._data  = data

        if transform is None:
            transform = np.eye(3)
        self._R0 = Rotation.from_matrix(transform)

    def cell_array(self, tag=None):
        if tag is None:
            return np.array([self.cell_array(tag) for tag in self.model.iter_node_tags()])

        Rref = self.model.frame_orientation(tag).T

        return np.array([
            self.node_array(n)@Rref for n in self.model.cell_nodes(tag)
        ])

    def node_array(self, tag=None):
        if tag is None:
            return np.array([self.node_array(tag) for tag in self.model.iter_node_tags()])

        return self._data.get(tag, self._R0).as_matrix()



class StateSeries(Series): # temporal distribution of states
    def __init__(self, soln: "FedeasPost", model, transform=None, scale=None,
                       recover_rotations=None):

        self.model  = model

        self._elements  = model["assembly"]
        self._locations = None
        self._rotations = None
        self._have_iter = "IterationHistory" in soln
        self._recover_rotations = recover_rotations

        # Create history

        self._hist = {}
        time = None
        last = None
        history = soln.get("IterationHistory", soln["ConvergedHistory"])
        i = 0
        for s in history:
            if time != s["Time"]:
                # Store last converged state
                if time is not None:
                    self._hist[time].update({
                        "converged": BasicState(last["U"],  model, transform=transform, scale=scale, time=time),
                        "increment": BasicState(last["DU"], model, transform=transform, scale=scale, time=time),
                    })

                # move time forward
                time = s["Time"]

                # Initialize iteration at new time
                i    = 0
                self._hist[time] = {
                    "iterations": {}
                }
                if "DDU" in s:
                    self._hist[time]["iterations"][i] = BasicState(s["DDU"], model, transform=transform, scale=scale, time=time)

            else:
                i += 1
                self._hist[time]["iterations"][i] = \
                    BasicState(s["DDU"], model, transform=transform, scale=scale, time=time)

            last = s

        time = s["Time"]
        self._hist[time].update({
            "converged": BasicState(last["U"],  model, transform=transform, scale=scale, time=time),
            "increment": BasicState(last["DU"], model, transform=transform, scale=scale, time=time),
        })


    def values(self, incr=None):
        for time in self.times:

            if incr is None:
                yield self[time]

            elif incr == "iter":
                for state in self._hist[time]["iterations"].values():
                    yield state

            elif incr=="conv":
                yield self._hist[time]["increment"]


class GroupSeriesSO3(Series):
    def __init__(self, series: "StateSeries", model, recover_rotations="init", transform=None):
        self.model  = model
        self._series = series
        #
        # Reconstruct group
        #

        if transform is None:
            transform = np.eye(3)

        R0   = Rotation.from_matrix(transform)
        last = {n: R0 for n in self.model.iter_node_tags()}
        hist = self._hist = {}
        time = None
        for incr in series.values(incr=recover_rotations):
            if time != incr.time:
                if time is not None:
                    # Save the converged state at last time
                    hist[time] = {
                        "converged": GroupStateSO3(last, model, time=time)
                    }

                time = incr.time

            last = {
                tag: Rotation.from_rotvec(incr.node_array(tag)[3:])*last[tag]
                for tag in self.model.iter_node_tags()
            }

        # Recover the final converged state
        time = incr.time
        last = {
            tag: Rotation.from_rotvec(incr.node_array(tag)[3:])*last[tag]
            for tag in self.model.iter_node_tags()
        }
        hist[time] = {
            "converged": GroupStateSO3(last, model, time=time)
        }


    def __getitem__(self, time)->GroupStateSO3:
        return self._hist[time]["converged"]


