import numpy as np
import warnings 
from veux.frame._section import SectionGeometry




class _FrameElement:
    def __init__(self, 
                 tag, 
                 vmodel, 
                 xmodel=None, 
                 section_override=None):
        self._tag = tag
        self._vmodel = vmodel
        self._xmodel = xmodel
        self._section_override = section_override
        self._elem_data = vmodel.cell_properties(tag)
    
    def sample_section(self, index)-> "SectionGeometry":
        if self._section_override is not None:
            return self._section_override

        if self._tag in self._vmodel._frame_outlines:
            return self._vmodel._frame_outlines[self._tag][index]
        elif "sections" in self._elem_data:
            return self._vmodel._frame_section(self._elem_data["sections"][index])
        else: 
            return self._vmodel._frame_section(None)


    def sample_points(self):
        if self._xmodel is not None:
            return self._xmodel.eleResponse(self._tag, "integrationPoints")
        elif self._tag in self._vmodel._frame_outlines:
            return np.linspace(0, 1, len(self._vmodel._frame_outlines[self._tag]))
        else:
            return [0,1]

    def sample_weights(self):
        pass

