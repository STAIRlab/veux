import numpy as np
from scipy.spatial import Delaunay

def find_edges_with(i, edge_set):
    return (
             [j for (x,j) in edge_set if x==i],
             [j for (j,x) in edge_set if x==i]
    )

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

def remove_collinear_points(points, tol=2e-4):
    """
    Remove points that are collinear with their neighbors in a polygon.

    Parameters:
        points: list of (x, y) tuples defining the polygon vertices.
                The polygon is assumed to be closed (first and last points are connected).
        tol: tolerance to decide if the area of the triangle is effectively zero.
    
    Returns:
        A new list of points with collinear points removed.
    """
    if len(points) < 3:
        return points.copy()

    # Check if the polygon is closed (i.e., first equals last)
    closed = np.array_equal(points[0], points[-1])
    # Work with the non-repeated version if the polygon is closed.
    pts = points[:-1] if closed else points.copy() #np.unique(, axis=0)

    new_points = []
    n = len(pts)
    total_area = 0.5 * abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + [points[0]])))

    # Loop over each point, treating the polygon as cyclic.
    for i in range(n):
        prev = pts[(i - 1) % n]
        curr = pts[i]
        nxt = pts[(i + 1) % n]
        # Compute twice the area of the triangle
        area = abs(prev[0] * (curr[1] - nxt[1]) +
                   curr[0] * (nxt[1]  - prev[1]) +
                   nxt[0]  * (prev[1] - curr[1]))*0.5
        # Only keep the current point if the area is larger than tol.
        if area/total_area > tol:
            new_points.append(curr)

    # Re-close the polygon if necessary.
    if closed and new_points:
        new_points.append(new_points[0])
    return np.array(new_points)

def _add_edge(edges, i, j, only_outer=True):
    """
    Add an edge between the i-th and j-th points,
    if not in the list already
    """
    if (i, j) in edges or (j, i) in edges:
        # already added
        assert (j, i) in edges, "Can't go twice over same directed edge?"
        if only_outer:
            # if both neighboring triangles are in shape, it's not a boundary edge
            edges.remove((j, i))
        return
    edges.add((i, j))


def _alpha_default(points, tri) -> float:
    """
    Compute a simple 'default' alpha for an alpha-shape,
    assuming the Delaunay triangles are roughly equilateral.

    :param points: (N,2) array of 2D point locations
    :param tri: A scipy.spatial.Delaunay object built from `points`
    :return: A float alpha
    """

    # tri.simplices is an (M,3) array of indices into `points`
    simplices = tri.simplices

    # Collect all edges by pairs of indices from each simplex
    # Note: each triangle contributes edges (i,j), (j,k), (k,i)
    edges = []
    for simplex in simplices:
        i, j, k = simplex
        edges.append((i, j))
        edges.append((j, k))
        edges.append((k, i))

    # Convert edges list to a unique set so we don't repeat edges
    # (small performance optimization)
    edges = set(tuple(sorted(edge)) for edge in edges)

    # Compute lengths of all edges
    lengths = []
    for (i, j) in edges:
        pi = points[i]
        pj = points[j]
        lengths.append(np.linalg.norm(pi - pj))

    lengths = np.array(lengths)
    # We could use the mean, but here we use median for robustness
    median_length = np.median(lengths)

    # Equilateral triangle of side length a has circumscribed circle radius a/sqrt(3).
    # We'll just pick alpha ~ median_length / sqrt(3).
    alpha = median_length / np.sqrt(3)

    return 1/alpha

def _max_pairwise_distance(points: np.ndarray) -> float:
    """
    Return the maximum Euclidean distance between any two points
    in a set of 2D points.

    :param points: (n, 2) array of 2D points
    :return: The largest Euclidean distance between any pair
    """

    from scipy.spatial.distance import cdist
    # Edge case: if there is 0 or 1 point, max distance is 0
    if points.shape[0] < 2:
        return 0.0

    # Compute all pairwise distances
    dist_matrix = cdist(points, points, 'euclidean')

    # Return the maximum distance
    return float(dist_matrix.max())

def alpha_shape(points, alpha=None, only_outer=True, radius=None, bound_ratio=None, tri=None):
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

    if tri is None:
        tri = Delaunay(points)

    if bound_ratio is not None:
        assert radius is None
        assert alpha is None
        radius = _max_pairwise_distance(points) * bound_ratio
    if radius is not None:
        alpha = 1/radius
    if alpha is None:
        alpha = _alpha_default(points, tri)

    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.simplices:
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
        if circum_r < 1/alpha:
            _add_edge(edges, ia, ib, only_outer=only_outer)
            _add_edge(edges, ib, ic, only_outer=only_outer)
            _add_edge(edges, ic, ia, only_outer=only_outer)

    # return points[stitch_boundaries(edges)]
    # return stitch_boundaries(edges)
    # return edges
    first_bound = stitch_boundaries(edges)[0]
    # return np.array(list(reversed([points[i] for edge in first_bound for i in edge])))
    ordered_points = np.array([points[i] for edge in first_bound for i in edge])
    _, idx = np.unique(ordered_points, return_index=True, axis=0)

    ordered_unique_points = ordered_points[np.sort(idx)]
    return remove_collinear_points(ordered_unique_points)
    # return ordered_points

