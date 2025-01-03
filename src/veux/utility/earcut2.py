#!/usr/bin/env python3

"""
author:  Nils Olofsson
email:   nils.olovsson@gmail.com
website: http://nilsolovsson.se
date:    2021-02-28
license: MIT

https://nils-olovsson.se/articles/ear_clipping_triangulation/
https://bitbucket.org/nils_olovsson/ear_clipping_triangulation/src/master/
"""

import numpy as np

# ==============================================================================
#
# Geometry
#
# ==============================================================================

def getExtents(vertices):
    """
    Get the extents, axis aligned bounding box, of the set of vertices.
    """
    return np.array([
        np.min(vertices[:,0]), # left
        np.min(vertices[:,1]), # bottom
        np.max(vertices[:,0]), # right
        np.max(vertices[:,1])  # top
    ])

def vertexNormal(v0, v1, v2):
    """
    Compute the 2D vertex normal, for placing rendered vertex numbers.
    """
    e0 = v1 - v0
    e1 = v2 - v1
    n0 = np.array([e0[1], -e0[0]])
    n1 = np.array([e1[1], -e1[0]])
    l0 = np.linalg.norm(e0)
    l1 = np.linalg.norm(e1)
    
    #n = n0 + n1
    #n = l0*n0 + l1*n1
    n = 0.5*(1.0/l0*n0 + 1.0/l1*n1)
    n = 1.0 / np.linalg.norm(n) * n
    return n

def computeNormals(vertices):
    """
    Compute the 2D vertex normals of the polygon, for placing rendered
    vertex numbers.
    """
    n,m = vertices.shape
    normals = np.zeros(vertices.shape)
    for i in range(n):
        v0 = vertices[i-1,:]
        v1 = vertices[i,:]
        v2 = vertices[(i+1)%n,:]
        normals[i,:] = vertexNormal(v0,v1,v2)

    return normals

def angleCCW(a, b):
    """
    Counter clock wise angle (radians) from normalized 2D vectors a to b
    """
    dot = a[0]*b[0] + a[1]*b[1]
    det = a[0]*b[1] - a[1]*b[0]
    angle = np.arctan2(det, dot)
    if angle<0.0 :
        angle = 2.0*np.pi + angle
    return angle

def _is_convex(triangle):
    """
    Determine if vertex lies on the convex hull of the polygon.
    """
    vertex_prev, vertex, vertex_next = triangle
    a = vertex_prev - vertex
    b = vertex_next - vertex
    internal_angle = angleCCW(b, a)
    return internal_angle <= np.pi

def insideTriangle(triangle, p):
    """
        Determine if a vertex p is inside (or "on") a triangle made of the
        points a->b->c
        http://blackpawn.com/texts/pointinpoly/
    """
    a, b, c = triangle
    #Compute vectors
    v0 = c - a
    v1 = b - a
    v2 = p - a

    # Compute dot products
    dot00 = np.dot(v0, v0)
    dot01 = np.dot(v0, v1)
    dot02 = np.dot(v0, v2)
    dot11 = np.dot(v1, v1)
    dot12 = np.dot(v1, v2)

    # Compute barycentric coordinates
    denom = dot00*dot11 - dot01*dot01
    if abs(denom) < 1e-20:
        return True
    invDenom = 1.0 / denom
    u = (dot11*dot02 - dot01*dot12) * invDenom
    v = (dot00*dot12 - dot01*dot02) * invDenom

    # Check if point is in triangle
    return (u >= 0) and (v >= 0) and (u + v < 1)


def earcut(vertices, max_iterations=0):
    """
        Triangulation of a polygon in 2D.
        Assumption that the polygon is simple, i.e has no holes, is closed and
        has no crossings and also that it the vertex order is counter clockwise.
        https://geometrictools.com/Documentation/TriangulationByEarClipping.pdf
    """

    n, m = vertices.shape
    indices = np.zeros([n-2, 3], dtype=int)


    vertlist = DoubleLinkedList()
    for i in range(0, n):
        vertlist.append(i)

    index_counter = 0
    it_counter = 0

    # Simplest possible algorithm. Create list of indexes.
    # Find first ear vertex. Create triangle. Remove vertex from list
    # Do this while number of vertices > 2.
    node = vertlist.first

    while vertlist.size > 2 and (max_iterations<=0 or max_iterations>index_counter):
        i = node.prev.data
        j = node.data
        k = node.next.data

        vert_prev = vertices[i,:]
        vert_crnt = vertices[j,:]
        vert_next = vertices[k,:]

        is_convex = _is_convex((vert_prev, vert_crnt, vert_next))
        is_ear = True
        if is_convex:
            test_node = node.next.next
            while test_node!=node.prev and is_ear:
                vert = vertices[test_node.data,:]
                is_ear = not insideTriangle((vert_prev, vert_crnt, vert_next), vert)
                test_node = test_node.next
        else:
            is_ear = False

        if is_ear:
            indices[index_counter, :] = np.array([i, j, k], dtype=int)
            index_counter += 1
            vertlist.remove(node.data)
        it_counter += 1
        node = node.next
    indices = indices[0:index_counter, :]
    return indices, vertlist.flatten()


class Node:
    """
    Node element in a DoubleLinkedList.
    Each node in a valid list is associated with a value/data element and
    with its left and right neighbor.
    [Prev. node]<--[Node]-->[Next node]
                        |
                    [Data]
    """

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoubleLinkedList:
    """
    A double linked list. Each element keeps a reference to both left and
    right neighbor. This allows e.g. for easy removal of elements.
    The list is circular and is usually considered traversed when the next element
    is the same element as when when we started.
    """

    def __init__(self):
        self.first = None
        self.size  = 0

    def __str__(self):
        if self.first==None:
            return '[]'
        msg = '['
        msg += str(self.first.data)
        node = self.first.next
        while node != self.first:
            msg += ', ' + str(node.data)
            node = node.next
        msg += ']'
        return msg

    def append(self, data):
        self.size += 1
        if self.first == None:
            self.first = Node(data)
            self.first.prev = self.first
            self.first.next = self.first
            return
        node = Node(data)
        last = self.first.prev
        node.prev = last
        node.next = self.first
        last.next = node
        self.first.prev = node

    def remove(self, item):
        if self.first==None:
            return
        rmv = None
        node = self.first
        if node.data == item:
            rmv = node
        node = node.next
        while not rmv and node != self.first:
            if node.data == item:
                rmv = node
            node = node.next
        if rmv:
            nxt = rmv.next
            prv = rmv.prev
            prv.next = nxt
            nxt.prev = prv
            self.size -= 1
            if rmv == self.first:
                self.first = nxt
            if rmv == self.first:
                self.first = None
        return

    def count(self):
        if self.first==None:
            return 0
        i = 1
        node = self.first.next
        while node != self.first:
            i+=1
            node = node.next
        return i

    def flatten(self):
        if self.first==None:
            return []
        l = []
        node = self.first
        l.append(node.data)
        node = self.first.next
        while node != self.first:
            l.append(node.data)
            node = node.next
        return l

