import numpy as np
from veux.utility.earcut import earcut, flatten as flatten_earcut

def _clean_polygon(polygon, warping=None):
    """
    Remove duplicate points and collinear points from a polygon.
    """
    if polygon.shape[1] == 2:
        outline_3d = np.zeros((polygon.shape[0], 3))
        outline_3d[:,1:] = polygon
        polygon = outline_3d.copy()
        if warping is not None:
            for i,point in enumerate(outline_3d[:,1:]):
                polygon[i,0] = warping(point)

    points = np.unique(polygon, axis=0)
    # Order points by angle from centroid
    polygon = points[np.argsort( np.arctan2(points[:,2] - points[:,2].mean(), 
                                            points[:,1] - points[:,1].mean()))]
    return polygon

    #
    cleaned = []
    for i in range(len(polygon)):
        prev_idx = (i - 1) % len(polygon)
        next_idx = (i + 1) % len(polygon)
        if not np.allclose(polygon[i], polygon[prev_idx]) and not np.allclose(polygon[i], polygon[next_idx]):
            cleaned.append(polygon[i])
    return np.array(cleaned)


class SectionGeometry:
    def __init__(self, exterior, interior=None, warping=None):

        if interior is None:
            interior = []

        for i in range(len(interior)):
            interior[i] = _clean_polygon(interior[i])
        
        exterior = np.array(exterior)#np.unique(, axis=0)
        # exterior = _clean_polygon(exterior, warping)
        if exterior.shape[1] == 2:
            outline_3d = np.zeros((exterior.shape[0], 3))
            outline_3d[:,1:] = exterior
            exterior = outline_3d.copy()
            if warping is not None:
                for i,point in enumerate(outline_3d[:,1:]):
                    exterior[i,0] = warping(point)

        self._interior = interior
        self._exterior = exterior

    def triangles(self):
        
        face_i = [self.exterior()[:,1:]] + [
            s[:,1:] for s in self.interior() if s is not None and len(s) > 0
        ]

        return earcut(**flatten_earcut(face_i))

    def exterior(self, plane=False, close=False):
        if plane:
            return self._exterior[:,1:]

        return self._exterior

    def interior(self, plane=False, close=False)->list:
        if plane:
            print(self._interior)
            return [interior[:,1:] for interior in self._interior]
        return self._interior

