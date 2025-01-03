"""
"""
import numpy as np


def _is_clockwise(polygon):
    """
    Check if a polygon is defined in clockwise order.
    """
    return np.sum((polygon[1:, 0] - polygon[:-1, 0]) * (polygon[1:, 1] + polygon[:-1, 1])) > 0

def _is_convex(a, b, c):
    """
    Check if three points make a convex corner.
    """
    ax, ay = a
    bx, by = b
    cx, cy = c
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0

def _is_ear(polygon, i):
    """
    Check if a vertex at index `i` forms an ear in the polygon.
    """
    prev_idx = (i - 1) % len(polygon)
    next_idx = (i + 1) % len(polygon)
    p_prev = polygon[prev_idx]
    p_curr = polygon[i]
    p_next = polygon[next_idx]

    # Triangle formed by the current vertex and its neighbors
    ear_triangle = np.array([p_prev, p_curr, p_next])

    # Check if the triangle is convex
    if not _is_convex(p_prev, p_curr, p_next):
        return False

    # Check if any other vertex lies inside the triangle
    for j, point in enumerate(polygon):
        if j not in [prev_idx, i, next_idx]:
            if _is_point_in_triangle(point, ear_triangle):
                return False

    return True

def _is_point_in_triangle(p, triangle):
    """
    Check if a point `p` is inside the triangle defined by three vertices.
    """
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    a, b, c = triangle
    b1 = sign(p, a, b) < 0
    b2 = sign(p, b, c) < 0
    b3 = sign(p, c, a) < 0

    return b1 == b2 == b3

def earcut1(polygon_vertices):
    """
    Triangulate a concave polygon using the ear clipping algorithm.

    Parameters:
        polygon_vertices (array-like): List or numpy array of (x, y) coordinates defining the polygon.

    Returns:
        list of tuple: Indices of triangles as (i, j, k) referencing the input vertices.
    """
    # Coerce input to numpy array
    polygon_vertices = np.asarray(polygon_vertices, dtype=float)

    if len(polygon_vertices) < 3:
        raise ValueError("A polygon must have at least 3 vertices to triangulate.")

    # Ensure the polygon is in counter-clockwise order
    if _is_clockwise(polygon_vertices):
        polygon_vertices = polygon_vertices[::-1]

    # Copy vertices and initialize the triangle list
    polygon = polygon_vertices.tolist()
    triangles = []

    # Loop until the polygon is reduced to three vertices
    while len(polygon) > 3:
        for i in range(len(polygon)):
            if _is_ear(polygon_vertices, i):
                # Add the ear triangle to the result
                prev_idx = (i - 1) % len(polygon)
                next_idx = (i + 1) % len(polygon)
                triangles.append((prev_idx, i, next_idx))

                # Remove the ear vertex from the polygon
                del polygon[i]
                break

    # Add the last remaining triangle
    triangles.append((0, 1, 2))

    return triangles


def earcut2(polycoord):
    """
    Triangulate a simple polygon using the ear clipping algorithm.

    Parameters:
    polycoord (list or ndarray): A list or array of [x, y] coordinates of the polygon vertices in order.

    Returns:
    triangles (ndarray): An (n, 3) array of indices into polycoord, each row representing a triangle.
    """

    def is_convex(a, b, c):
        """Check if the angle formed by points a, b, c is convex."""
        return (b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0]) < 0

    def point_in_triangle(a, b, c, p):
        """Check if point p is inside triangle abc."""
        # Barycentric coordinate method
        detT = (b[1] - c[1])*(a[0] - c[0]) + (c[0] - b[0])*(a[1] - c[1])
        if detT == 0:
            return False
        l1 = ((b[1] - c[1])*(p[0] - c[0]) + (c[0] - b[0])*(p[1] - c[1])) / detT
        l2 = ((c[1] - a[1])*(p[0] - c[0]) + (a[0] - c[0])*(p[1] - c[1])) / detT
        l3 = 1 - l1 - l2
        return (0 < l1 < 1) and (0 < l2 < 1) and (0 < l3 < 1)

    # Convert to numpy array for easier indexing
    poly = np.array(polycoord)
    n = len(poly)
    if n < 3:
        raise ValueError("A polygon must have at least 3 vertices.")

    # Ensure the polygon is counter-clockwise
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += (poly[j][0] - poly[i][0]) * (poly[j][1] + poly[i][1])
    if area > 0:
        poly = poly[::-1]

    indices = list(range(len(poly)))
    triangles = []

    while len(indices) > 3:
        ear_found = False
        for i in range(len(indices)):
            prev_idx = indices[i - 1]
            curr_idx = indices[i]
            next_idx = indices[(i + 1) % len(indices)]

            a = poly[prev_idx]
            b = poly[curr_idx]
            c = poly[next_idx]

            if is_convex(a, b, c):
                # Check if any other vertex is inside the triangle abc
                ear = True
                for idx in indices:
                    if idx in (prev_idx, curr_idx, next_idx):
                        continue
                    p = poly[idx]
                    if point_in_triangle(a, b, c, p):
                        ear = False
                        break
                if ear:
                    triangles.append([prev_idx, curr_idx, next_idx])
                    del indices[i]
                    ear_found = True
                    break

        if not ear_found:
            print(polycoord)
            raise ValueError("No ear found. The polygon might be not simple or is degenerate.")

    # Add the last remaining triangle
    triangles.append([indices[0], indices[1], indices[2]])

    return np.array(triangles)


def earcut3(polygon, tolerance=1e-6):
    """
    Improved Ear Clipping algorithm with pre-sorting and tolerance for degenerate cases
    """
    from shapely import Polygon
    if isinstance(polygon, Polygon):
        vertices = list(polygon.exterior.coords)[:-1]  # Ignore the last point because it's a repetition of the first
    else:
        vertices = polygon
        polygon = Polygon(vertices)

    if vertices[-1][0] == vertices[0][0] and vertices[-1][1] == vertices[0][1]:
        vertices = vertices[:-1]
    triangles = []

    # Sort vertices by x-coordinate
    vertices = sorted(vertices, key=lambda vertex: vertex[0])

    while len(vertices) > 3:
        for i in range(len(vertices)):
            a, b, c = vertices[i - 1], vertices[i], vertices[(i + 1) % len(vertices)]
            triangle = Polygon([a, b, c])

            # Adjusted checks for valid "ear"
            if triangle.is_valid and triangle.area > tolerance and triangle.contains(polygon):
                triangles.append(triangle)
                vertices.pop(i)
                break
        else:
            raise Exception("No valid ear found")

    if len(vertices) == 3:
        triangles.append(Polygon(vertices))

    return triangles


def earcut(polycoord):
    """
    Triangulate a simple polygon using the Earcut library.

    Parameters:
    polycoord (list or ndarray): A list or array of [x, y] coordinates of the polygon vertices in order.

    Returns:
    triangles (ndarray): An (n, 3) array of indices into polycoord, each row representing a triangle.
    """
    import mapbox_earcut as earcut
    if np.array_equal(polycoord[0], polycoord[-1]):
        polycoord = polycoord[:-1]

    # Convert the list of coordinates to a flat list
    flattened = np.array(polycoord).reshape(-1,2) #.flatten()

    # Perform triangulation
    triangle_indices = earcut.triangulate_float64(flattened, np.array([len(polycoord)]))

    # Convert the flat list of indices into a (n, 3) array
    triangles = np.array(triangle_indices).reshape(-1, 3)

    return triangles

earcut=earcut1

# try:
#     from mapbox_earcut import earcut as _earcut
#     import numpy as np
# 
#     def earcut(polygon_vertices):
#         """
#         Triangulate a concave polygon and return triangle indices.
# 
#         Parameters:
#             polygon_vertices (list of tuple): List of (x, y) coordinates defining the polygon.
# 
#         Returns:
#             list of tuple: Indices of triangles as (i, j, k) referencing the input vertices.
#         """
#         # Flatten the polygon vertices into a single list: [x0, y0, x1, y1, ...]
#         flattened_vertices = np.array(polygon_vertices).flatten()
# 
#         # Perform the triangulation
#         indices = _earcut(flattened_vertices, None, 2)  # '2' indicates 2D (x, y) coordinates
# 
#         # Group indices into triangles
#         triangles = [(indices[i], indices[i + 1], indices[i + 2]) for i in range(0, len(indices), 3)]
# 
#         return triangles
# 
#     print("OK")
# except Exception as e:
#     print(e)
