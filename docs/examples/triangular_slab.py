from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.geometry import Vector
from compas.geometry import Line
from compas.geometry import Rotation
from compas.geometry import Scale
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Projection
from compas.geometry import Transformation
from compas.geometry import Point
from compas.geometry import earclip_polygon
from compas.geometry import boolean_intersection_polygon_polygon
from compas.geometry import boolean_union_polygon_polygon
from compas.geometry import is_parallel_vector_vector
from compas.geometry import intersection_segment_segment
from compas.geometry import distance_point_point
from compas.geometry import midpoint_point_point
from compas.geometry import offset_polygon
from compas_cgal.triangulation import conforming_delaunay_triangulation
from compas.datastructures import Mesh
from compas.datastructures.mesh.slice import mesh_slice_plane
from compas_snippets.viewer_live import ViewerLive
from math import pi
from math import sqrt
from math import radians
from math import sin
from math import floor
from math import ceil
from typing import *
from compas_snippets.polygon import cut_polygon_with_plane
from compas_grid.element_plate import PlateElement
from compas_grid.element_column import ColumnElement
from compas_grid.element_column_head import ColumnHeadElement
from compas_model.models import Model
from compas_model.models import GroupNode


# Parameters
QUARTER_WIDTH : float = 3000
QUARTER_DEPTH : float = 3000
QUARTER_DIVISIONS : int = 12
BOARD_THICKNESS = 40
COLUMN_HEAD_RADIUS : float = 350
COLUMN_HEAD_BOTTOM_0 : float = 20
COLUMN_HEAD_BOTTOM_1 : float = 100
COLUMN_RADIUS : float = 150
EQUAL_RIB_ANGLE : float = 5*0
RIB_INLCINATION_0 : float = 200
RIB_INLCINATION_1 : float = 350
COLUMN_HEAD_BASE_WIDTH : float = 100
BOUNDARY_OFFSET_0 : float = BOARD_THICKNESS*1
BOUNDARY_OFFSET_1 = Vector(BOARD_THICKNESS*0.5, BOARD_THICKNESS*0.5, 0)





model : Model = Model(name="triangular_slab")
slab_quarter : GroupNode = model.add_group("slab_quarter")
ribs_diagonal : GroupNode = model.add_group("ribs_diagonal", slab_quarter)
ribs_boundary : GroupNode = model.add_group("ribs_boundary", slab_quarter)
floor_level : GroupNode = model.add_group("floor_level", slab_quarter)
column : GroupNode = model.add_group("column", slab_quarter)

# Slice the mesh by the two side planes, take the largest mesh.
def slice_and_select_largest(mesh, plane):
    mesh_pair = mesh_slice_plane(mesh, plane)
    if mesh_pair:
        if mesh_pair[0].aabb().volume < mesh_pair[1].aabb().volume:
            mesh_pair = mesh_pair[::-1]
        return mesh_pair[0]
    return mesh

def loft_two_polygons(polygon1: Polygon, polygon2: Polygon, triangulate=False) -> Mesh:


    v : List[Point] = polygon1.points + polygon2.points
    f = []

    # Top and bottom faces
    if triangulate:
        top_faces = earclip_polygon(polygon1)
        f.extend(top_faces)
        for top_face in top_faces:
            bottom_face = [i+len(polygon1.points) for i in top_face]
            bottom_face.reverse()
            f.append(bottom_face)
    else:
        top_faces = []
        bottom_faces = []
        for i in range(len(polygon1.points)):
            top_faces.append(i)
            bottom_faces.append(i+len(polygon1.points))
        bottom_faces.reverse()
        f.append(top_faces)
        f.append(bottom_faces)

    # Side faces
    n = len(polygon1.points)
    for i in range(len(polygon1.points)):
        if triangulate:
            f.append([i, (i+1)%n, (i+1)%n+n])
            f.append([(i+1)%n+n, i+n, i])
        else:
            f.append([i, (i+1)%n, (i+1)%n+n, i+n])

    mesh = Mesh.from_vertices_and_faces(v, f)
    mesh.unify_cycles()
    return mesh


def loft_multiple_polygons(polygons: List[Polygon], triangulate=False) -> Mesh:
    v: List[Point] = []
    f: List[List[int]] = []

    # Collect vertices from all polygons
    for polygon in polygons:
        v.extend(polygon.points)

    # # Top and bottom faces
    # if triangulate:
    #     top_faces = earclip_polygon(polygons[0])
    #     f.extend(top_faces)
    #     for top_face in top_faces:
    #         bottom_face = [i+len(polygons[0].points)*(len(polygons)-1) for i in top_face]
    #         bottom_face.reverse()
    #         f.append(bottom_face)
    # else:
    #     top_faces = []
    #     bottom_faces = []
    #     for i in range(len(polygons[0].points)):
    #         top_faces.append(i)
    #         bottom_faces.append(i+len(polygons[0].points)*(len(polygons)-1))
    #     bottom_faces.reverse()
    #     f.append(top_faces)
    #     f.append(bottom_faces)

    # Side faces
    n = len(polygons[0].points)
    for i in range(len(polygons) - 1):
        for j in range(n):
            if triangulate:
                f.append([i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n])
                f.append([(i + 1) * n + (j + 1) % n, (i + 1) * n + j, i * n + j])
            else:
                f.append([i * n + j,
                          i * n + (j + 1) % n,
                          (i + 1) * n + (j + 1) % n,
                          (i + 1) * n + j])

    mesh = Mesh.from_vertices_and_faces(v, f)
    # mesh.unify_cycles()
    return mesh


# Base polygon where diagonals placed
quarter_polygon : Polygon = Polygon([
    [0, 0, 0],
    [QUARTER_WIDTH, 0, 0],
    [QUARTER_WIDTH, QUARTER_DEPTH, 0],
    [0, QUARTER_DEPTH, 0],
])

quarter_polygon_offset : Polygon = Polygon([
    [0, 0, 0],
    [QUARTER_WIDTH-BOUNDARY_OFFSET_0, 0, 0],
    [QUARTER_WIDTH-BOUNDARY_OFFSET_0, QUARTER_DEPTH-BOUNDARY_OFFSET_0, 0],
    [0, QUARTER_DEPTH-BOUNDARY_OFFSET_0, 0],
])

quarter_block : Polygon = Polygon([
    [0, 0, 0],
    [QUARTER_WIDTH, 0, 0],
    [QUARTER_WIDTH, QUARTER_DEPTH, 0],
    [0, QUARTER_DEPTH, 0],
])

############################################################################################################
# Ribs
############################################################################################################

# Vertical boards
quarter_lines : List[Line] = []
quarter_polygons: List[Polygon] = []
temp : Any = []

quarter_line : Line = Line(quarter_polygon[0], quarter_polygon[1]).scaled(1*sqrt(2))

quarter_line = Line(quarter_line.start+quarter_line.direction*(COLUMN_HEAD_RADIUS-BOUNDARY_OFFSET_1[0]), quarter_line.end)

quarter_line.translate(BOUNDARY_OFFSET_1) # offset also inside to duplicate boundary ribs

beam_shapes : List[Mesh] = []

offset_direction : Vector = Vector.cross(quarter_line.direction, Vector.Zaxis())*BOARD_THICKNESS*0.5
quarter_line_offseted : Polygon = Polygon([
    quarter_line.start+offset_direction,
    quarter_line.end+offset_direction,
    quarter_line.end-offset_direction,
    quarter_line.start-offset_direction])
cut_polygon : Polygon = quarter_polygon_offset.transformed(Scale.from_factors([1.00,1.00,1],Frame(quarter_polygon[2])))

border_plane0 : Plane = Plane(quarter_polygon_offset[2],  quarter_polygon_offset[1]-quarter_polygon_offset[2])
border_plane1 : Plane = Plane(quarter_polygon_offset[2], quarter_polygon_offset[2]-quarter_polygon_offset[3])

# Slice planes
slice_plane_point : Point = midpoint_point_point(quarter_polygon_offset[1], quarter_polygon_offset[2])
slice_plane_normal : Vector = Vector.cross(quarter_polygon_offset[2]-quarter_polygon_offset[1], Vector.Zaxis())
slice_plane_0 : Plane = Plane(slice_plane_point, slice_plane_normal)
slice_plane_point = midpoint_point_point(quarter_polygon_offset[2], quarter_polygon_offset[3])
slice_plane_normal = Vector.cross(quarter_polygon_offset[3]-quarter_polygon_offset[2], Vector.Zaxis())
slice_plane_1 : Plane = Plane(slice_plane_point, slice_plane_normal)


max_z_0 : float = 0
max_z_1 : float = 0
max_z_2 : float = 0

angle : float = Vector.angle(quarter_polygon[1]-quarter_polygon[0], quarter_polygon[1]-quarter_polygon[2])
rib_arc : List[Point] = []

quarter_lines_rotated = []
for i in range(QUARTER_DIVISIONS+1):

    # Linear interpolation of divisions
    t : float = i / QUARTER_DIVISIONS

    # Rotate the line and its polygon
    rotation : Rotation = Rotation.from_axis_and_angle([0,0,1], angle * t, point=BOUNDARY_OFFSET_1)
    quarter_line_rotated : Line = quarter_line.transformed(rotation)


    # Intersect the rotated line with the offset polygon and replace the line end point with the intersection point
    for j in range(len(quarter_polygon_offset.points)):
        segment : Line = Line(quarter_polygon[j], quarter_polygon[(j+1)%len(quarter_polygon)])
        result : List[float] = intersection_segment_segment(quarter_line_rotated, segment)
        if result[0]:
            quarter_line_rotated = Line(quarter_line_rotated.start, Point(*result[0]))
            break

    # Offset lines by hard thickness
    offset_direction : Vector = Vector.cross(quarter_line_rotated.direction, Vector.Zaxis())*BOARD_THICKNESS*0.5
    quarter_line_rotated_offset0 : Line = quarter_line_rotated.translated(offset_direction)

    quarter_line_rotated_offset1 : Line = quarter_line_rotated.translated(-offset_direction)

    if (i > 0):
        quarter_lines_rotated.append(quarter_line_rotated_offset0)
        # temp.append(quarter_line_rotated_offset1)

    if (i < QUARTER_DIVISIONS):
        quarter_lines_rotated.append(quarter_line_rotated_offset1)
        # temp.append(quarter_line_rotated_offset0)


    # Extend the line by the thickness
    # quarter_line_rotated : Line = Line(quarter_line_rotated.start, quarter_line_rotated.end+quarter_line_rotated.direction*BOARD_THICKNESS)
    l_prime : float = 0

    # Create polygon of a plate
    if EQUAL_RIB_ANGLE !=0:
        rad : float = radians(EQUAL_RIB_ANGLE)
        rib_length : float = quarter_line_rotated.start.distance_to_point(quarter_line_rotated.end)
        capitel_length : float = (quarter_line_rotated.start+Vector(0, 0, RIB_INLCINATION_1)+quarter_line_rotated.direction*COLUMN_HEAD_BASE_WIDTH).distance_to_point(quarter_line_rotated.start+Vector(0, 0, RIB_INLCINATION_1))
        l : float = rib_length - capitel_length
        l_prime = (l * sin(rad)) / sin(pi*0.5 - rad)
    else:
        l_prime = RIB_INLCINATION_1-RIB_INLCINATION_0

    quarter_polygon_rotated : Polygon = Polygon(
        [
            quarter_line_rotated.start,
            quarter_line_rotated.end,
            quarter_line_rotated.end+Vector(0, 0, RIB_INLCINATION_1-l_prime),
            quarter_line_rotated.start+Vector(0, 0, RIB_INLCINATION_1)+quarter_line_rotated.direction*COLUMN_HEAD_BASE_WIDTH,
            quarter_line_rotated.start+Vector(0, 0, RIB_INLCINATION_1),
        ]
    )



    # Find the lowest and highest points
    if i == 0:
        max_z_0 = quarter_polygon_rotated[2].z

    if i == QUARTER_DIVISIONS:
        max_z_2 = quarter_polygon_rotated[2].z

    if i == int(floor(QUARTER_DIVISIONS*0.5)) or i == int(ceil(QUARTER_DIVISIONS*0.5)):
        max_z_1 = max(quarter_polygon_rotated[2].z, max_z_1)


    # if RIB_INLCINATION_0 != RIB_INLCINATION_1:
    #     quarter_polygon_rotated.points.insert(3,  quarter_line_rotated.start+Vector(0, 0, RIB_INLCINATION_1)+quarter_line_rotated.direction*COLUMN_HEAD_BASE_WIDTH,)

    # Offset the two polygons in both sides
    normal = Vector.cross(quarter_polygon_rotated[1]-quarter_polygon_rotated[0],quarter_polygon_rotated[-1]-quarter_polygon_rotated[0]).unitized()
    quarter_polygon_offset_rotated_0 : Polygon = quarter_polygon_rotated.translated(normal*BOARD_THICKNESS*0.5)
    quarter_polygon_offset_rotated_1 : Polygon = quarter_polygon_rotated.translated(normal*-BOARD_THICKNESS*0.5)

    # Collect points for column head
    rib_arc.append(quarter_polygon_rotated[0]+normal*BOARD_THICKNESS*0.5)
    rib_arc.append(quarter_polygon_rotated[0]-normal*BOARD_THICKNESS*0.5)

    # Loft the two polygons
    mesh = loft_two_polygons(quarter_polygon_offset_rotated_0, quarter_polygon_offset_rotated_1, False)

    # Initial mesh slicing
    split_mesh = slice_and_select_largest(mesh, border_plane0)

    # Further mesh slicing
    split_mesh = slice_and_select_largest(split_mesh, border_plane1)

    # Append the final split mesh to beam_shapes
    beam_shapes.append(split_mesh)

    ############################################################################################################
    # Create beam_elements and add them to the model
    ############################################################################################################
    element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
        polygon=quarter_polygon_rotated,
        thickness=BOARD_THICKNESS,
        frame = Frame(quarter_polygon_rotated[2], quarter_line_rotated.direction, Vector.Zaxis()),
        name = "rib_vertical_" + str(i),
        shape = split_mesh
    )

    model.add_element(element_plate, ribs_diagonal)

# print(max_z_0, max_z_1, max_z_2)
# temp.append(Polygon(rib_arc))


############################################################################################################
# Vertical side-boards
# Create two side boards if the boundary thickness is greater than zero.
############################################################################################################
if BOUNDARY_OFFSET_0 > 0:

    vertical_extension : float = 0.15 if EQUAL_RIB_ANGLE == 0.0 else 1.0

    cut_plane : Plane = Plane(
        quarter_polygon_offset[2],
        Vector.cross(quarter_polygon[0]-quarter_polygon[2], Vector.Zaxis())
    )


    offset0 : Vector = Vector(-BOUNDARY_OFFSET_0*1.0, 0, 0)
    edge0 : Line = Line(quarter_polygon[1], quarter_polygon[2])
    edge0 = Line(edge0.start, edge0.end+edge0.direction*BOUNDARY_OFFSET_0)
    side0 : Polygon = Polygon([
        edge0.start+offset0,
        edge0.end+offset0,
        edge0.end+Vector(0, 0, max_z_1+BOUNDARY_OFFSET_0*vertical_extension)+offset0,
        edge0.start+Vector(0, 0, max_z_0+BOUNDARY_OFFSET_0*vertical_extension)+offset0,

    ])


    element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
        polygon=side0,
        thickness=BOUNDARY_OFFSET_0,
        frame = Frame(quarter_polygon[2], quarter_polygon[1], Vector.Zaxis()),
        name = "rib_boundary_" + str(i),
    )

    mesh_split = slice_and_select_largest(element_plate.shape, cut_plane)
    element_plate.shape = mesh_split


    model.add_element(element_plate, ribs_boundary)

    offset1 : Vector = Vector(0, -BOUNDARY_OFFSET_0*1.0, 0)
    edge1 : Line = Line(quarter_polygon[3], quarter_polygon[2])
    edge1 = Line(edge1.start, edge1.end+edge1.direction*BOUNDARY_OFFSET_0)
    side1 : Polygon = Polygon([
        edge1.start+offset1,
        edge1.end+offset1,
        edge1.end+Vector(0, 0, max_z_1+BOUNDARY_OFFSET_0*vertical_extension)+offset1,
        edge1.start+Vector(0, 0, max_z_2+BOUNDARY_OFFSET_0*vertical_extension)+offset1,
    ])


    element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
        polygon=side1,
        thickness=BOUNDARY_OFFSET_0,
        frame = Frame(quarter_polygon[2], quarter_polygon[1], Vector.Zaxis()),
        name = "rib_boundary" + str(i),
    )

    mesh_split = slice_and_select_largest(element_plate.shape, cut_plane)
    element_plate.shape = mesh_split

    model.add_element(element_plate, ribs_boundary)

############################################################################################################
# Column-head
############################################################################################################
rib_arc.pop()
rib_arc_polygon : Polygon = Polygon(rib_arc)
points : List[Point] = []
for i in range(4):
    points.extend(rib_arc_polygon.rotated(radians(90*(i))))
quarter_column_head : Polygon = Polygon(points)


# TODO: Replace Scale with accurate measurements
column_head_hole_0 : Polygon = Polygon([[-COLUMN_RADIUS*0.5, -COLUMN_RADIUS*0.5, 0], [COLUMN_RADIUS*0.5, -COLUMN_RADIUS*0.5, 0], [COLUMN_RADIUS*0.5, COLUMN_RADIUS*0.5, 0], [-COLUMN_RADIUS*0.5, COLUMN_RADIUS*0.5, 0]])
column_head_hole_1 : Polygon = column_head_hole_0.translated(Vector(0, 0, RIB_INLCINATION_1+COLUMN_HEAD_BOTTOM_1))
column_head_0 : Polygon = quarter_column_head
column_head_1 : Polygon = quarter_column_head.translated(Vector(0, 0, RIB_INLCINATION_1))
column_head_2 : Polygon = Polygon(offset_polygon(column_head_0, -COLUMN_HEAD_BASE_WIDTH)).translated(Vector(0, 0, RIB_INLCINATION_1))
column_head_3 : Polygon = column_head_2.translated(Vector(0, 0, COLUMN_HEAD_BOTTOM_0))
column_head_4 : Polygon = Polygon(offset_polygon(quarter_column_head, COLUMN_HEAD_RADIUS-COLUMN_RADIUS-BOARD_THICKNESS*0.5)).translated(Vector(0, 0, RIB_INLCINATION_1+COLUMN_HEAD_BOTTOM_1))

def smooth_polygon(polygon: Polygon, iterations: int = 1, alpha: float = 0.5) -> Polygon:
    """
    Smooth a polygon by averaging each point with its neighboring points.

    Parameters
    ----------
    polygon : Polygon
        The input polygon to be smoothed.
    iterations : int, optional
        The number of smoothing iterations to perform. Default is 1.
    alpha : float, optional
        The smoothing factor. Default is 0.5.

    Returns
    -------
    Polygon
        The smoothed polygon.
    """
    points: List[Point] = polygon.points

    for _ in range(iterations):
        new_points: List[Point] = []
        for i in range(len(points)):
            prev_point = points[i - 1]
            curr_point = points[i]
            next_point = points[(i + 1) % len(points)]
            new_point = Point(
                alpha * (prev_point.x + next_point.x) / 2 + (1 - alpha) * curr_point.x,
                alpha * (prev_point.y + next_point.y) / 2 + (1 - alpha) * curr_point.y,
                alpha * (prev_point.z + next_point.z) / 2 + (1 - alpha) * curr_point.z
            )
            new_points.append(new_point)
        points = new_points

    return Polygon(points)

column_head_4 = smooth_polygon(column_head_4, 10, 0.1)

column_head_polygons : List[Polygon] = [column_head_0, column_head_1, column_head_2, column_head_3, column_head_4]
column_head_element = ColumnHeadElement.from_loft(polygons=column_head_polygons, top_holes=[column_head_hole_0], bottom_holes=[column_head_hole_1])
model.add_element(column_head_element, column)

############################################################################################################
# Column
############################################################################################################

column_element = ColumnElement.from_round_section(radius=COLUMN_RADIUS, height=3000, name="column")
from compas_cgal.booleans import boolean_difference_mesh_mesh
from compas.geometry import Polyhedron
b = column_head_element.shape.to_vertices_and_faces(True)
a = column_element.shape.to_vertices_and_faces(True)
c = boolean_difference_mesh_mesh(a, b)
shape = Polyhedron(c[0], c[1])  # revise the Shape API
shape = shape.to_mesh()
column_element.shape = shape

model.add_element(column_element, column)


############################################################################################################
# Top boards
# TODO: boards by horizontal divisions
# TODO: boards by triangular divisions
############################################################################################################

# Cut the lines to fit the polygon
quarter_lines_rotated_cut : List[Line] = []
for quarter_line_rotated in quarter_lines_rotated:
    for j in range(len(quarter_polygon_offset.points)):
        segment : Line = Line(quarter_polygon_offset[j], quarter_polygon_offset[(j+1)%len(quarter_polygon_offset)])
        result : List[float] = intersection_segment_segment(quarter_line_rotated, segment)
        if result[0]:
            quarter_line_rotated = Line(quarter_line_rotated.start, Point(*result[0]))
            quarter_lines_rotated_cut.append(quarter_line_rotated)
            break

# Create the top plates polygons
top_plate_polygons : List[Polygon] = []
for i in range(0, len(quarter_lines_rotated_cut), 2):
    top_polygon = Polygon(
            [
                quarter_lines_rotated_cut[i].start,
                quarter_lines_rotated_cut[i].end,
                quarter_lines_rotated_cut[i+1].end,
                quarter_lines_rotated_cut[i+1].start,
            ]
        )
    
    temp.append(top_polygon)


    element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
        polygon=top_polygon,
        thickness=BOARD_THICKNESS,
        frame = Frame(quarter_polygon[2], quarter_polygon[1], Vector.Zaxis()),
        name = "top_plate" + str(i),
    )
    
    model.add_element(element_plate, floor_level)
    
    
    element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
        polygon=top_polygon.translated(Vector(0, 0, RIB_INLCINATION_0-BOARD_THICKNESS)),
        thickness=BOARD_THICKNESS,
        frame = Frame(quarter_polygon[2], quarter_polygon[1], Vector.Zaxis()),
        name = "top_plate" + str(i),
    )
    
    model.add_element(element_plate, floor_level)
    

# element_plate : PlateElement = PlateElement.from_polygon_and_thickness(
#     polygon=quarter_polygon,
#     thickness=-BOARD_THICKNESS,
#     frame = Frame(quarter_polygon[2], quarter_polygon[1], Vector.Zaxis()),
#     name = "top_plate" + str(i),
# )


# planes_0 = []
# planes_1 = []
# for element in model.elements():
#     if element.name.startswith("rib_vertical"):
#         planes_0.append(element.bottom.plane)
#         planes_1.append(element.top.plane)
# print(planes_0)


############################################################################################################
# Viewer
############################################################################################################

ViewerLive.clear()
elements = list(model.elements())
for element in elements:
    element.shape.name = element.name
    ViewerLive.add(element.shape)



# # # ViewerLive.add(quarter_polygon)
# # # ViewerLive.add(quarter_polygon_offset)
# # # ViewerLive.add(quarter_lines)
# # # ViewerLive.add(quarter_polygons)
# # # ViewerLive.add(beam_shapes)
ViewerLive.add(temp)
ViewerLive.serialize()

ViewerLive.run()