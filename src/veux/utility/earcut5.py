"""
https://github.com/fuhao050403/EarClippingAlgorithm
"""
import math
import sys
import numpy as np

# ========================================================== #
# Vertices processing                                        #
# Input: 1. one outer polygon vertices list                  #
#        2. all inner polygon vertices lists                 #
# Output: an simple polygon which combine all inner polygons #
#         with original outer polygon, which be used for     #
#         performing ear clipping triangulation algorithm.   #
# ========================================================== #

def vertices_processing(outer_polygon, inner_polygon):
    # Storing max-x coordinate for calculate mutually visible vertices
    index_point_M = []
    # Storing max-x values for sorting purpose
    max_x_values = []
    for i in range(len(inner_polygon)):
        # Get first column(x axis value) of inner polygon
        row_x = [row[0] for row in inner_polygon[i]]
        # Get max value of first column
        max_x_value = max(row_x)

        # Append to the max-x value/coordinate arrays
        max_x_values += [max_x_value]
        index_point_M.append(row_x.index(max_x_value))
    # Sort that array by descending order
    sort_index = np.argsort(-1 * np.array(max_x_values)).tolist()

    # Reorder inner polygon by max x-value
    # which make polygon that has greater max x-value up to the top of the list
    inner_polygon = [inner_polygon[i] for i in sort_index]
    index_point_M = [index_point_M[i] for i in sort_index]

    for i in range(len(inner_polygon)):
        # Get index of mutual visible vertex on outer polygon for current inner polygon
        index_point_P = _find_mutual_vertices(outer_polygon.copy(), inner_polygon[i][index_point_M[i]])
        
        # Insert list which contains inner polygon information about to insert into outer
        insert_list = _shift_list(inner_polygon[i], -1 * index_point_M[i])
        insert_list += [inner_polygon[i][index_point_M[i]]]
        insert_list += [outer_polygon[index_point_P]]
        
        # Insert into outer polygon
        # Combine inner polygon into outer polygon as an new outer polygon
        outer_polygon[index_point_P + 1:index_point_P + 1] = insert_list

    return outer_polygon

def _find_mutual_vertices(outer, point_M):
    len_outer = len(outer)

    # ======================================================== #
    # Find index of intersected edge and coordinate of point I #
    # ======================================================== #

    # Get right-most x value for outer polygon
    outer_rightmost_x = max([row[0] for row in outer])

    # Line segment from M to x direction (p1 = point_M)
    p2 = [outer_rightmost_x, point_M[1]]

    # index_closest record the index of first vertex for the closest edge
    index_closest = -1
    x_smallest = outer_rightmost_x + 1
    point_I = []
    for j in range(len_outer):
        p3 = outer[j]
        p4 = outer[(j + 1) % len_outer]

        # Calculate intersected point between two lines
        # and check if this point is closer to point M
        coord_intersected = _line_segments_intersect(point_M, p2, p3, p4)

        if coord_intersected != None and coord_intersected[0] < x_smallest:
            x_smallest = coord_intersected[0]
            index_closest = j
            point_I = coord_intersected

    # ============================================================= #
    # Process after found point I and index of the edge it belongs  #
    # And try to find point P and eventually find index of mutually #
    # visible vertex on the outer polygon and return that value.    #
    # ============================================================= #

    # index of mutual visible vertex on the outer polygon
    index_visible_vertex = -1

    # First. Check if the intersected point is a vertex of outer polygon
    # If so, return result index value
    index_visible_vertex = outer.index(point_I) if point_I in outer else -1
    if index_visible_vertex != -1:
        return index_visible_vertex

    # Otherwise, intersected point is an interior point of an edge
    # Find point P on that edge
    point_P = (outer[index_closest]
               if outer[index_closest][0] > outer[(index_closest + 1) % len_outer][0]
               else outer[(index_closest + 1) % len_outer])

    # ============================================================= #
    # Now, triangle <M,I,P> has been decided. So we need to check   #
    # if any reflex vertices of outer polygon is located inside it. #
    # ============================================================= #

    # Pre-set result index as index of point P on the outer polygon
    index_visible_vertex = (index_closest
                            if outer[index_closest][0] > outer[(index_closest + 1) % len_outer][0]
                            else (index_closest + 1) % len_outer)

    minimum_angle = _angle_between_vectors(point_M, point_I, point_P)
    minimum_distance = _distance_between_points(point_M, point_P)

    for k in range(len_outer):
        # If current vertex is inside <M,I,P>
        if _is_point_inside(outer[k], point_M, point_I, point_P):
            # If current vertex is reflex and is not point P
            if _is_reflex(outer[k - 1], outer[k], outer[(k + 1) % len_outer]) and outer[k] != point_P:
                # Calculate angle and distance between candidate point and point_M
                angle = _angle_between_vectors(point_M, point_I, outer[k])
                distance = _distance_between_points(point_M, outer[k])

                # If outer[k] is located exactly on line <M,P> then choose the closer one
                if angle == minimum_angle and distance < minimum_distance:
                    index_visible_vertex = k
                    minimum_distance = distance
                # If not then choose the one with minimum angle
                elif angle < minimum_angle:
                    index_visible_vertex = k
                    minimum_angle = angle

    return index_visible_vertex

# Intersection between line(p1, p2) and line(p3, p4)
def _line_segments_intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0: # parallel
        return None
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    if ua < 0 or ua > 1: # out of range
        return None
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    if ub < 0 or ub > 1: # out of range
        return None
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    return [x, y]

# Calculate angle between two vectors
def _angle_between_vectors(p_center, p1, p2):
    v1 = [a - b for a, b in zip(p1, p_center)]
    v2 = [a - b for a, b in zip(p2, p_center)]
    angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return 180 * angle/ np.pi

# Calculate distance between two points
def _distance_between_points(p1, p2):
    return (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2

# Shifting list to left or right
def _shift_list(seq, n = 0):
    a = n % len(seq)
    return seq[-a:] + seq[:-a]

def earcut(polygon):
    """
    Ear Clipping triangulation algorithm
       
    Input: an polygon vertices list which gained from Vertices
           Processing part(previously mentioned)              
    Output: list of index of faces which triangulates input   
            polygon vertices.                                 

    For my purpose, only return index of vertices instead of the value of vertices

    """


    # Backup vertices array for finding index
    polygon_backup = polygon.copy()

    if len(polygon) == 3:
        return [[1, 2, 3]]

    faces = []
    while(len(polygon) > 3):
        # Found a ear
        ear_index = _find_ear(polygon)
        if(ear_index != -1):
            # Found a ear and find index of it in the backup vertices array
            try:
                prev_ind = polygon_backup.index(polygon[ear_index - 1])
                curr_ind = polygon_backup.index(polygon[ear_index])
                next_ind = polygon_backup.index(polygon[(ear_index + 1) % len(polygon)])
                faces.append([prev_ind, curr_ind, next_ind])
            except ValueError:
                print("value has not been found!")
        polygon.pop(ear_index)

    # While loop upabove ends when 3 elements left in polygon array
    # So append the last triangle manually
    try:
        prev_ind = polygon_backup.index(polygon[-1])
        curr_ind = polygon_backup.index(polygon[0])
        next_ind = polygon_backup.index(polygon[1])
        faces.append([prev_ind, curr_ind, next_ind])
    except ValueError:
        print("value has not been found!")

    return faces

# Find first possible ear of polygon
def _find_ear(polygon):
    for i in range(len(polygon)):
        prev_point = polygon[i - 1]
        curr_point = polygon[i]
        next_point = polygon[(i + 1) % len(polygon)]
        # Check if current point is a ear
        if _is_ear(prev_point, curr_point, next_point, polygon):
            # If ear, then return its index
            return i
        else:
            # If not ear, continue the loop find next possible ear
            continue
    return -1

# Check if ths specific point is a ear
# Ear has to be satified following 3 conditions:
# 1. No other points are located inside the triangle which formed by 3 points
# 2. Center point of 3 points(p2 in this case) has a concave curve
# 3. All 3 points are not on the same lane(area of triangle must greater than 0)
def _is_ear(p1, p2, p3, polygon):
    ear = _contains_no_points(p1, p2, p3, polygon) and \
          _is_convex(p1, p2, p3) and \
          _triangle_area(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]) > 0
    return ear

# Check center point of 3 points(curr in this case) has a convex curve
def _is_convex(prev, curr, next):
    return (prev[0] * (next[1] - curr[1]) + 
            curr[0] * (prev[1] - next[1]) + 
            next[0] * (curr[1] - prev[1])) > 0

# Check center point of 3 points(curr in this case) has a reflex curve
def _is_reflex(prev, curr, next):
    return (prev[0] * (next[1] - curr[1]) + 
            curr[0] * (prev[1] - next[1]) + 
            next[0] * (curr[1] - prev[1])) < 0

# Check no other points are located inside the triangle which formed by 3 points
def _contains_no_points(p1, p2, p3, polygon):
    for pn in polygon:
        if pn in (p1, p2, p3):
            continue
        elif _is_point_inside(pn, p1, p2, p3):
            return False
    return True

# Check specific point is located inside the triangle
EPSILON = math.sqrt(sys.float_info.epsilon)
def _is_point_inside(p, a, b, c):
    area  = _triangle_area(a[0], a[1], b[0], b[1], c[0], c[1])
    area1 = _triangle_area(p[0], p[1], b[0], b[1], c[0], c[1])
    area2 = _triangle_area(p[0], p[1], a[0], a[1], c[0], c[1])
    area3 = _triangle_area(p[0], p[1], a[0], a[1], b[0], b[1])
    areadiff = abs(area - sum([area1, area2, area3])) < EPSILON
    return areadiff

# Calculate area of the triangle formed by 3 points
def _triangle_area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)