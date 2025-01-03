"""
https://github.com/pawlowiczf/Polygon-Triangulation/tree/main
"""
class Node:
    def __init__(self, color, next = None):
        self.color = color 
        self.next  = None 

        
def createLinkedList(colors):
    array = [Node(color) for color in colors]

    for idx in range( len(array) ):
        #
        pointer = array[idx]
        pointer.next = array[ ( idx + 1 ) % len(array) ]
    #
        
    return array[0]


def mapArray(polygon):
    #
    for a in range( len(polygon) ):
        #
        coords = polygon[a]
        polygon[a] = ( coords, a )
    
    return polygon

def Orientation(A, B, C):
    ax, ay = A 
    bx, by = B 
    cx, cy = C 

    return (ax - cx) * (by - cy) - (ay - cy) * (bx - cx)


def Position(A, B, C):
    #
    ax, ay = A 
    bx, by = B 
    cx, cy = C 

    answer = (ax - cx) * (by - cy) - (ay - cy) * (bx - cx)

    if answer > 0: return 1 
    if answer < 0: return -1
    return float('inf')


def inTriangle(pointA, pointB, pointC, pointInside):
    #
    number = 0
    number += Position(pointA, pointB, pointInside)
    number += Position(pointB, pointC, pointInside)
    number += Position(pointC, pointA, pointInside)

    if abs( number ) == 3:
        return True
    #
    return False

def searchForEar(polygon, vis, fillColor):
    #
    n = len(polygon)
    if n < 3:
        return []
    
    for a in range( n  ):
        #
        pointA = polygon[ (a - 1) % n ][0]
        pointB = polygon[ a % n ][0]
        pointC = polygon[ (a + 1) % n ][0]

        if Orientation(pointA, pointB, pointC) > 0:
            flag = True 

            for pointInside, index in polygon:
                if not ( pointInside in (pointA, pointB, pointC) ) and inTriangle(pointA, pointB, pointC, pointInside):
                    flag = False 
                    break

            if flag:    
                pol = [pointA, pointB, pointC]
                vis.add_polygon(pol, color = fillColor.color)
                return ( polygon[ (a - 1) % n ][1], a % n , polygon[ (a + 1) % n ][1] )

    return []

def earClippingAlgorithm(polygon, vis):
    #
    if len(polygon) == 0: return []
    
    polygon = mapArray(polygon)
    colors = [ "orange", "red", "green", "purple", "brown", "blue" ]
    fillColor = createLinkedList(colors)
    
    while len(polygon) >= 3:
        #
        index = searchForEar(polygon, vis, fillColor)
        if index == []: break
        polygon.pop( index[1] )
        fillColor = fillColor.next
    #

    return vis