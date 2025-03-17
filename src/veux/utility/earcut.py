"""
An adaptation of mapbox/earcut.js, derived from the port
by joshuaskelly

Adapted from:
  https://github.com/joshuaskelly/earcut-python
"""
import math
import numpy as np

__all__ = ['earcut', 'deviation', 'flatten']

def earcut1(vertices):
    """
    Triangulate a simple polygon using the mapbox_earcut library.

    Parameters:
      vertices (list or ndarray): A list or array of [x, y] coordinates of the polygon vertices in order.

    Returns:
      triangles (ndarray): An (n, 3) array of indices into `vertices`, each row representing a triangle.
    """
    import mapbox_earcut as earcut
    if np.array_equal(vertices[0], vertices[-1]):
        vertices = vertices[:-1]

    # Convert the list of coordinates to a flat list
    flattened = np.array(vertices).reshape(-1,2) #.flatten()

    # Perform triangulation
    triangle_indices = earcut.triangulate_float64(flattened, np.array([len(vertices)]))

    # Convert the flat list of indices into a (n, 3) array
    triangles = np.array(triangle_indices).reshape(-1, 3)

    return triangles

class _PointLink:
    def __init__(self, i, x, y):
    # vertice index in coordinates array
        self.i = i

        # vertex coordinates
        self.x = x
        self.y = y

        # previous and next vertice nodes in a polygon ring
        self.prev = None
        self.next = None

        # z-order curve value
        self.z = None

        # previous and next nodes in z-order
        self.prevZ = None
        self.nextZ = None

        # indicates whether this is a steiner point
        self.steiner = False
    
    def append(self, data):
        pass

    def __getitem__(self, i):
        if i == 0:
            return self.x 
        if i == 1: 
            return self.y 
        else:
            raise IndexError

    @property 
    def shape(self):
        # TODO: Return coordinates
        return


def _point_in_triangle(a, b, c, p):
    "check if a point lies within a convex triangle"
    ax, ay = a 
    bx, by = b
    cx, cy = c
    px, py = p
    return (cx - px) * (ay - py) - (ax - px) * (cy - py) >= 0 and \
           (ax - px) * (by - py) - (bx - px) * (ay - py) >= 0 and \
           (bx - px) * (cy - py) - (cx - px) * (by - py) >= 0


def _valid_diagonal(a, b):
    "check if a diagonal between two polygon nodes is valid (lies in polygon interior)"
    return a.next.i != b.i and a.prev.i != b.i and not intersectsPolygon(a, b) and \
        locallyInside(a, b) and locallyInside(b, a) and middleInside(a, b)


def _points_equal(a, b):
    "check if two points are equal"
    return a[0] == b[0] and a[1] == b[1]



def intersects(p1, q1, p2, q2):
    "check if two segments intersect"
    if (_points_equal(p1, q1) and _points_equal(p2, q2)) or (_points_equal(p1, q2) and _points_equal(p2, q1)):
        return True

    return _triangle_area(p1, q1, p2) > 0 != _triangle_area(p1, q1, q2) > 0 and \
           _triangle_area(p2, q2, p1) > 0 != _triangle_area(p2, q2, q1) > 0

# def compareX(a, b):
#     return a.x - b.x

def intersectsPolygon(a, b):
    "check if a polygon diagonal intersects any polygon segments"
    do = True
    p = a

    while do or p != a:
        do = False
        if (p.i != a.i and p.next.i != a.i and p.i != b.i and p.next.i != b.i and intersects(p, p.next, a, b)):
            return True

        p = p.next

    return False


def locallyInside(a, b):
    "check if a polygon diagonal is locally inside the polygon"
    if _triangle_area(a.prev, a, a.next) < 0:
        return  _triangle_area(a, b, a.next) >= 0 and _triangle_area(a, a.prev, b) >= 0
    else:
        return _triangle_area(a, b, a.prev) < 0 or _triangle_area(a, a.next, b) < 0


def middleInside(a, b):
    "check if the middle point of a polygon diagonal is inside the polygon"
    do = True
    p = a
    inside = False
    px = (a.x + b.x) / 2
    py = (a.y + b.y) / 2

    while do or p != a:
        do = False
        if ((p.y > py) != (p.next.y > py)) and (px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x):
            inside = not inside

        p = p.next

    return inside

# link two polygon vertices with a bridge; if the vertices belong to the same ring, it splits polygon into two;
# if one belongs to the outer ring and another to a hole, it merges it into a single ring
def _split_polygon(a, b):
    a2 = _PointLink(a.i, a.x, a.y)
    b2 = _PointLink(b.i, b.x, b.y)
    an = a.next
    bp = b.prev

    a.next = b
    b.prev = a

    a2.next = an
    an.prev = a2

    b2.next = a2
    a2.prev = b2

    bp.next = b2
    b2.prev = bp

    return b2

def earcut(vertices, holes=None, dimensions=None):
    # print(vertices, holes, dimensions)
    # Convert to numpy array
    vertices = np.asarray(vertices)

    # Remove duplicate last point if it's the same as the first
    if len(vertices.shape)>1 and np.array_equal(vertices[0], vertices[-1]):
        vertices = vertices[:-1]

    dimensions = dimensions or 2

    data = vertices.flatten() # reshape(-1,2) #flatten() #

    hasHoles = holes and len(holes)
    outerLen =  holes[0] * dimensions if hasHoles else len(data)
    outerNode = _create_links(data, 0, outerLen, dimensions, True)
    triangles = []

    if not outerNode:
        return triangles

    minX = None
    minY = None
    maxX = None
    maxY = None
    x = None
    y = None
    size = None

    if hasHoles:
        outerNode = _purge_holes(data, holes, outerNode, dimensions)

    # if the shape is not too simple, we'll use z-order curve hash later; calculate polygon bbox
    if len(data) > 80 * dimensions:
        minX = maxX = data[0]
        minY = maxY = data[1]

        for i in range(dimensions, outerLen, dimensions):
            x = data[i]
            y = data[i + 1]
            if x < minX:
                minX = x
            if y < minY:
                minY = y
            if x > maxX:
                maxX = x
            if y > maxY:
                maxY = y

        # minX, minY and size are later used to transform coords into integers for z-order calculation
        size = max(maxX - minX, maxY - minY)

    _earcut_links(outerNode, triangles, dimensions, minX, minY, size)

    return triangles


def _create_links(data, start, end, dim, clockwise):
    "create a circular doubly linked list from polygon points in the specified winding order"
    i = None
    last = None

    if (clockwise == (_polygon_area(data, start, end, dim) > 0)):
        for i in range(start, end, dim):
            last = _insert_link(i, data[i], data[i + 1], last)

    else:
        for i in reversed(range(start, end, dim)):
            last = _insert_link(i, data[i], data[i + 1], last)

    if last and _points_equal(last, last.next):
        _remove_link(last)
        last = last.next

    return last


def _filter_points(start, end=None):
    "eliminate colinear or duplicate points"
    if not start:
        return start
    if not end:
        end = start

    p = start
    again = True

    while again or p != end:
        again = False

        if not p.steiner and (_points_equal(p, p.next) or _triangle_area(p.prev, p, p.next) == 0):
            _remove_link(p)
            p = end = p.prev
            if (p == p.next):
                return None

            again = True

        else:
            p = p.next

    return end

def _earcut_links(ear: "_PointLink", triangles, dim, minX, minY, size, _pass=None):
    """main ear slicing loop which triangulates a polygon (given as a linked list)"""

    if not ear:
        return

    # interlink polygon nodes in z-order
    if not _pass and size:
        _index_curve(ear, float(minX), float(minY), size)

    stop = ear
    prev = None
    next = None

    # iterate through ears, slicing them one by one
    while ear.prev != ear.next:
        prev = ear.prev
        next = ear.next

        if isEarHashed(ear, minX, minY, size) if size else _is_ear(ear):
            # cut off the triangle
            triangles.append(prev.i // dim)
            triangles.append(ear.i  // dim)
            triangles.append(next.i // dim)

            _remove_link(ear)

            # skipping the next vertice leads to less sliver triangles
            ear  = next.next
            stop = next.next

            continue

        ear = next

        # if we looped through the whole remaining polygon and can't find any more ears
        if ear == stop:
            # try filtering points and slicing again
            if not _pass:
                _earcut_links(_filter_points(ear), triangles, dim, minX, minY, size, 1)

                # if this didn't work, try curing all small self-intersections locally
            elif _pass == 1:
                ear = cureLocalIntersections(ear, triangles, dim)
                _earcut_links(ear, triangles, dim, minX, minY, size, 2)

                # as a last resort, try splitting the remaining polygon into two
            elif _pass == 2:
                splitEarcut(ear, triangles, dim, minX, minY, size)

            break

# check whether a polygon node forms a valid ear with adjacent nodes
def _is_ear(ear):
    a = ear.prev
    b = ear
    c = ear.next

    if _triangle_area(a, b, c) >= 0:
        return False # reflex, can't be an ear

    # now make sure we don't have other points inside the potential ear
    p = ear.next.next

    while p != ear.prev:
        if _point_in_triangle(a, b, c, p) and _triangle_area(p.prev, p, p.next) >= 0:
                return False
        p = p.next

    return True

def isEarHashed(ear, minX, minY, size):
    a = ear.prev
    b = ear
    c = ear.next

    if _triangle_area(a, b, c) >= 0:
        return False # reflex, can't be an ear

    # triangle bbox; min & max were calculated like this for speed
    minTX = (a[0] if a[0] < c[0] else c[0]) if a[0] < b[0] else (b[0] if b[0] < c[0] else c[0])
    minTY = (a[1] if a[1] < c[1] else c[1]) if a[1] < b[1] else (b[1] if b[1] < c[1] else c[1])
    maxTX = (a[0] if a[0] > c[0] else c[0]) if a[0] > b[0] else (b[0] if b[0] > c[0] else c[0])
    maxTY = (a[1] if a[1] > c[1] else c[1]) if a[1] > b[1] else (b[1] if b[1] > c[1] else c[1])

    # z-order range for the current triangle bbox;
    minZ = _z_order(minTX, minTY, minX, minY, size)
    maxZ = _z_order(maxTX, maxTY, minX, minY, size)

    # first look for points inside the triangle in increasing z-order
    p = ear.nextZ

    while p and p.z <= maxZ:
        if p != ear.prev and p != ear.next and _point_in_triangle(a, b, c, p) and _triangle_area(p.prev, p, p.next) >= 0:
            return False
        p = p.nextZ

    # then look for points in decreasing z-order
    p = ear.prevZ

    while p and p.z >= minZ:
        if p != ear.prev and p != ear.next and _point_in_triangle(a, b, c, p) and _triangle_area(p.prev, p, p.next) >= 0:
            return False
        p = p.prevZ

    return True

# go through all polygon nodes and cure small local self-intersections
def cureLocalIntersections(start, triangles, dim):
    do = True
    p = start

    while do or p != start:
        do = False

        a = p.prev
        b = p.next.next

        if not _points_equal(a, b) and intersects(a, p, p.next, b) and locallyInside(a, b) and locallyInside(b, a):
            triangles.append(a.i // dim)
            triangles.append(p.i // dim)
            triangles.append(b.i // dim)

            # remove two nodes involved
            _remove_link(p)
            _remove_link(p.next)

            p = start = b

        p = p.next

    return p

# try splitting polygon into two and triangulate them independently
def splitEarcut(start, triangles, dim, minX, minY, size):
    # look for a valid diagonal that divides the polygon into two
    do = True
    a = start

    while do or a != start:
        do = False
        b = a.next.next

        while b != a.prev:
            if a.i != b.i and _valid_diagonal(a, b):
                # split the polygon in two by the diagonal
                c = _split_polygon(a, b)

                # filter colinear points around the cuts
                a = _filter_points(a, a.next)
                c = _filter_points(c, c.next)

                # run earcut on each half
                _earcut_links(a, triangles, dim, minX, minY, size)
                _earcut_links(c, triangles, dim, minX, minY, size)
                return

            b = b.next

        a = a.next


def _purge_holes(data, hole_indices, outerNode, dim):
    "Link every hole into the outer loop, producing a single-ring polygon without holes"
    queue = []
    i = None
    hole_count = len(hole_indices)
    start = None
    end = None
    lst = None

    for i in range(hole_count):
        start = hole_indices[i] * dim
        end =  hole_indices[i + 1] * dim if i < hole_count - 1 else len(data)
        lst = _create_links(data, start, end, dim, False)

        if (lst == lst.next):
            lst.steiner = True

        queue.append(_leftmost_node(lst))

    queue = sorted(queue, key=lambda i: i[0])

    # process holes from left to right
    for i in range(len(queue)):
        _remove_hole(queue[i], outerNode)
        outerNode = _filter_points(outerNode, outerNode.next)

    return outerNode


def _remove_hole(hole, outer_node):
    "find a bridge between vertices that connects hole with an outer ring and and link it"
    outer_node = _find_hole_bridge(hole, outer_node)
    if outer_node:
        b = _split_polygon(outer_node, hole)
        _filter_points(b, b.next)


def _find_hole_bridge(hole, outerNode):
    "David Eberly's algorithm for finding a bridge between hole and outer polygon"
    do = True
    p = outerNode
    hx = hole.x
    hy = hole.y
    qx = -math.inf
    m = None

    # find a segment intersected by a ray from the hole's leftmost point to the left;
    # segment's endpoint with lesser x will be potential connection point
    while do or p != outerNode:
        do = False
        if hy <= p.y and hy >= p.next.y and p.next.y - p.y != 0:
            x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y)

            if x <= hx and x > qx:
                qx = x

                if (x == hx):
                    if hy == p.y:
                        return p
                    if hy == p.next.y:
                        return p.next

                m = p if p.x < p.next.x else p.next

        p = p.next

    if not m:
        return None

    if hx == qx:
        return m.prev # hole touches outer segment; pick lower endpoint

    # look for points inside the triangle of hole point, segment intersection and endpoint;
    # if there are no points found, we have a valid connection;
    # otherwise choose the point of the minimum angle with the ray as connection point

    stop = m
    mx = m.x
    my = m.y
    tanMin = math.inf
    tan = None

    p = m.next

    while p != stop:
        hx_or_qx = hx if hy < my else qx
        qx_or_hx = qx if hy < my else hx

        if hx >= p.x and p.x >= mx and _point_in_triangle((hx_or_qx, hy), m, (qx_or_hx, hy), p):

            tan = abs(hy - p.y) / (hx - p.x) # tangential

            if (tan < tanMin or (tan == tanMin and p.x > m.x)) and locallyInside(p, hole):
                m = p
                tanMin = tan

        p = p.next

    return m

# interlink polygon nodes in z-order
def _index_curve(start, minX, minY, size):
    do = True
    p = start

    while do or p != start:
        do = False

        if p.z == None:
            p.z = _z_order(float(p.x), float(p.y), minX, minY, size)

        p.prevZ = p.prev
        p.nextZ = p.next
        p = p.next

    p.prevZ.nextZ = None
    p.prevZ = None

    _sort_links(p)

def _sort_links(L):
    """
    Simon Tatham's linked list merge sort algorithm
    http://www.chiark.greenend.org.uk/~sgtatham/algorithms/listsort.html
    """
    do = True
    i = None
    p = None
    q = None
    e = None
    tail = None
    merge_count = None
    pSize = None
    qSize = None
    inSize = 1

    while do or merge_count > 1:
        do = False
        p = L
        L = None
        tail = None
        merge_count = 0

        while p:
            merge_count += 1
            q = p
            pSize = 0
            for i in range(inSize):
                pSize += 1
                q = q.nextZ
                if not q:
                    break

            qSize = inSize

            while pSize > 0 or qSize > 0 and q:

                if pSize == 0:
                    e = q
                    q = q.nextZ
                    qSize -= 1

                elif qSize == 0 or not q:
                    e = p
                    p = p.nextZ
                    pSize -= 1

                elif p.z <= q.z:
                    e = p
                    p = p.nextZ
                    pSize -= 1

                else:
                    e = q
                    q = q.nextZ
                    qSize -= 1

                if tail:
                    tail.nextZ = e

                else:
                    L = e

                e.prevZ = tail
                tail = e

            p = q

        tail.nextZ = None
        inSize *= 2

    return L


def _z_order(x, y, minX, minY, size):
    "coordinate on a z-order curve of a point given coords and size of the data bounding box"

    # coords are transformed into non-negative 15-bit integer range
    x = int(32767 * (x - minX) // size)

    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555

    y = int(32767 * (y - minY) // size)
    y = (y | (y << 8)) & 0x00FF00FF
    y = (y | (y << 4)) & 0x0F0F0F0F
    y = (y | (y << 2)) & 0x33333333
    y = (y | (y << 1)) & 0x55555555

    return x | (y << 1)


def _leftmost_node(start):
    "find the leftmost node of a polygon ring"
    do = True
    p = start
    leftmost = start

    while do or p != start:
        do = False
        if p.x < leftmost.x:
            leftmost = p
        p = p.next

    return leftmost


def _insert_link(i, x, y, last):
    "create a node and optionally link it with previous one (in a circular doubly linked list)"
    p = _PointLink(i, x, y)

    if not last:
        p.prev = p
        p.next = p

    else:
        p.next = last.next
        p.prev = last
        last.next.prev = p
        last.next = p

    return p

def _remove_link(p):
    p.next.prev = p.prev
    p.prev.next = p.next

    if p.prevZ:
        p.prevZ.nextZ = p.nextZ

    if p.nextZ:
        p.nextZ.prevZ = p.prevZ


def deviation(data, holeIndices, dim, triangles)->float:
    """
    Return a percentage difference between the polygon area and its triangulation area.
    Used to verify correctness of triangulation
    """
    _len = len(holeIndices)
    hasHoles = holeIndices and len(holeIndices)
    outerLen = holeIndices[0] * dim if hasHoles else len(data)

    polygonArea = abs(_polygon_area(data, 0, outerLen, dim))

    if hasHoles:
        for i in range(_len):
            start = holeIndices[i] * dim
            end = holeIndices[i + 1] * dim if i < _len - 1 else len(data)
            polygonArea -= abs(_polygon_area(data, start, end, dim))

    trianglesArea = 0.0

    for i in range(0, len(triangles), 3):
        a = triangles[i] * dim
        b = triangles[i + 1] * dim
        c = triangles[i + 2] * dim
        trianglesArea += abs(
            (data[a] - data[c]) * (data[b + 1] - data[a + 1]) -
            (data[a] - data[b]) * (data[c + 1] - data[a + 1]))

    if polygonArea == 0.0 and trianglesArea == 0.0:
        return 0

    return abs((trianglesArea - polygonArea) / polygonArea)


# 
def _triangle_area(a, b, c)->float:
    "signed area of a triangle"
    return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])


def _polygon_area(data, start, end, dim)->float:
    sum = 0.0
    j = end - dim

    for i in range(start, end, dim):
        sum += (data[j] - data[i]) * (data[i + 1] + data[j + 1])
        j = i

    return sum


# Turn a polygon in a multi-dimensional array form (e.g. as in GeoJSON) into a form Earcut accepts
def flatten(data):
    dim = len(data[0][0])
    result = {
        'vertices': [],
        'holes':    [],
        'dimensions': dim
    }
    holeIndex = 0

    for i in range(len(data)):
        for j in range(len(data[i])):
            for d in range(dim):
                result['vertices'].append(float(data[i][j][d]))

        if i > 0:
            holeIndex += len(data[i - 1])
            result['holes'].append(holeIndex)

    return result

def unflatten(data):
    result = []

    for i in range(0, len(data), 3):
        result.append(tuple(data[i:i + 3]))

    return result
