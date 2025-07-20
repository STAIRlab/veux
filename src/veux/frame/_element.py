
import numpy as np
Array = np.ndarray
from veux.frame._section import SectionGeometry

import shps.rotor as so3

def _elastic_curve(x: Array, v: list, L:float, tangent=False)->Array:
    "compute points along Euler's elastica"
    ui, vi, uj, vj = v

    xi = x/L                        # local coordinate
    if not tangent:
        N1 = 1.-3.*xi**2+2.*xi**3
        N2 = L*(xi-2.*xi**2+xi**3)
        N3 = 3.*xi**2 - 2*xi**3
        N4 = L*(xi**3 - xi**2)
        y = ui*N1 + vi*N2 + uj*N3 + vj*N4
        return y.flatten()

    else:
        M3 = 1 - xi
        M4 = 6/L*(xi-xi**2)
        M5 = 1 - 4*xi+3*xi**2
        M6 = -2*xi + 3*xi**2
        return (ui*M3 + vi*M5 + uj*M4 + vj*M6).flatten()


def _hermite_cubic(
        xi,
        coord: Array,
        u: Array = None,     #: Displacements at two nodes
        v: Array = None,     #: Rotation vectors at two nodes
        Q = None,
        tangent: bool = False
    ):

    # Element length
    L = np.linalg.norm(coord[-1] - coord[0])

    (li, ti, vi), (lj, tj, vj) = u
    (si, ei, pi), (sj, ej, pj) = v

    Lnew  = L + lj - li
    xaxis = np.array([xi*Lnew])

    plan_curve = _elastic_curve(xaxis, [ti, pi, tj, pj], Lnew)
    elev_curve = _elastic_curve(xaxis, [vi,-ei, vj,-ej], Lnew)

    local_curve = np.stack([xaxis + li, plan_curve, elev_curve])

    return Q.T@local_curve + coord[0][None,:].T



class _FrameState:
    pass

class _GaussSample:
    def __init__(self, index):
        self.index = index

class _SimpleSample:
    def __init__(self, index):
        self.index = index

class _FrameElement:
    def __init__(self, 
                 tag, 
                 vmodel, 
                 xmodel=None, 
                 samples: int = None,
                 section_override=None,
                 interpolation=None):

        if samples is None:
            samples = len(vmodel.cell_nodes(tag))

        self._tag = tag
        self._vmodel = vmodel
        self._xmodel = xmodel
        self._section_override = section_override
        self._elem_data = vmodel.cell_properties(tag)

        # Set section source
        section_source = "Default"
        if self._tag in self._vmodel._frame_outlines:
            section_source = "External"
        elif "sections" in self._elem_data:
            section_source = "Internal"
        
        self._section_source = section_source

        #

        # set _gauss_sample_points
        self._gauss_sample_points = []
        if self._xmodel is not None:
            self._gauss_sample_points = self._xmodel.eleResponse(self._tag, "integrationPoints")

        self._gauss_sections = [
            self._vmodel._frame_section(tag)
            for tag in self._elem_data.get("sections", [])
        ]    

        # Simple samples
        if samples is not None:
            self._simple_sample_points = np.linspace(0, 1.0, samples)
        elif section_source == "External":
            self._simple_sample_points = np.linspace(0, 1.0, len(self._vmodel._frame_outlines[self._tag]))
        elif section_source == "Internal":
            self._simple_sample_points = np.linspace(0, 1.0, len(self._elem_data["sections"]))
        else:
            self._simple_sample_points = np.linspace(0, 1.0, 2)

        # Interpolate section geometry
    


    def sample_section(self, sample)-> "SectionGeometry":
        if self._section_override is not None:
            return self._section_override

        if self._section_source == "External":
            return self._vmodel._frame_outlines[self._tag][sample.index]

        elif self._section_source == "Internal":
            return self._vmodel._frame_section(self._elem_data["sections"][sample.index])

        else: 
            return self._vmodel._frame_section(None)


    def simple_samples(self):
        return (_SimpleSample(i) for i in range(len(self._simple_sample_points)))
    
    # def gauss_samples(self):
    #     return (_GaussSample(i)  for i in range(len(self._gauss_sample_points)))

    # Create states
    def gauss_state(self, state=None, positions=None, rotations=None):
        """
        Create a FrameState
        """

    def nodal_state(self, state=None, positions=None, rotations=None):
        """
        Create a FrameState
        """
        ...


    def sample_position(self, sample, state=None):
        xs = self._simple_sample_points[sample.index]
        model = self._vmodel
        Xi, Xj = self._vmodel.cell_position(self._tag)[[0,-1],:]
        X = Xi,Xj
        Xs = Xi + (
            (Xj - Xi) * self._simple_sample_points[sample.index]
        )

        if state is None:
            return Xs

        Q = model.frame_orientation(self._tag)
        u = [
            xi - X[i] for i,xi in enumerate(model.cell_position(self._tag, state=state)[[0,-1],:])
        ]
        R = [
            model.node_rotation(node, state=state) for node in model.cell_nodes(self._tag)
        ]
        x = _hermite_cubic(xs, X,
                Q=Q,
                u = [Q@u[0],          Q@u[1]],
                v = [Q@so3.log(R[0]), Q@so3.log(R[-1])]).T
        return x[0]

    def sample_rotation(self, sample, state=None):
        xs = self._simple_sample_points[sample.index]
        Rs = self._vmodel.frame_orientation(self._tag).T

        if state is None:
            return Rs
        
        model = self._vmodel
        Ri,*_,Rj = [
            model.node_rotation(node, state=state) for node in model.cell_nodes(self._tag)
        ]
        return so3.exp(xs*so3.log(Rj@Ri.T))@Ri@Rs

    def sample_material(self, sample, state=None):
        pass

    def sample_weight(self, sample):
        pass

