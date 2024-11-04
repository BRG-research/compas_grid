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
from compas.datastructures import Mesh
from compas.datastructures.mesh.slice import mesh_slice_plane
from compas_snippets.viewer_live import ViewerLive
from math import pi
from math import sqrt
from typing import *
from compas_snippets.polygon import cut_polygon_with_plane


# Parameters
quarter_width: float = 3000
quarter_depth: float = 3000
quarter_divisions: int = 12
angle: float = pi * 0.5
board_thickness = 40
corner_offset: float = 500
equal_end: bool = True
inclination_0: float = 350
inclination_1: float = 50
capitel_width: float = 100
quarter_lines_offset = Vector(board_thickness * 0.5, board_thickness * 0.5, 0)


def loft_two_polygons(polygon1: Polygon, polygon2: Polygon, triangulate=False) -> Mesh:
    v: List[Point] = polygon1.points + polygon2.points
    f = []

    # Top and bottom faces

    if triangulate:
        top_faces = earclip_polygon(polygon1)
        f.extend(top_faces)
        for top_face in top_faces:
            bottom_face = [i + len(polygon1.points) for i in top_face]
            bottom_face.reverse()
            f.append(bottom_face)
    else:
        top_faces = []
        bottom_faces = []
        for i in range(len(polygon1.points)):
            top_faces.append(i)
            bottom_faces.append(i + len(polygon1.points))
        bottom_faces.reverse()
        f.append(top_faces)
        f.append(bottom_faces)

    # Side faces
    n = len(polygon1.points)
    for i in range(len(polygon1.points)):
        if triangulate:
            f.append([i, (i + 1) % n, (i + 1) % n + n])
            f.append([(i + 1) % n + n, i + n, i])
        else:
            f.append([i, (i + 1) % n, (i + 1) % n + n, i + n])

    mesh = Mesh.from_vertices_and_faces(v, f)
    mesh.unify_cycles()
    return mesh


# Base polygon where diagonals placed
quarter_polygon: Polygon = Polygon(
    [
        [0, 0, 0],
        [quarter_width, 0, 0],
        [quarter_width, quarter_depth, 0],
        [0, quarter_depth, 0],
    ]
)

quarter_polygon_offset: Polygon = Polygon(
    [
        [0, 0, 0],
        [quarter_width - board_thickness * 1.0, 0, 0],
        [quarter_width - board_thickness * 1.0, quarter_depth - board_thickness, 0],
        [0, quarter_depth - board_thickness, 0],
    ]
)

quarter_block: Polygon = Polygon(
    [
        [0, 0, 0],
        [quarter_width, 0, 0],
        [quarter_width, quarter_depth, 0],
        [0, quarter_depth, 0],
    ]
)


# Vertical boards
quarter_lines: List[Line] = []
quarter_polygons: List[Polygon] = []
temp: Any = []

quarter_line: Line = Line(quarter_polygon[0], quarter_polygon[1]).scaled(1 * sqrt(2))
quarter_line = Line(quarter_line.start + quarter_line.direction * corner_offset, quarter_line.end)

quarter_line.translate(quarter_lines_offset)

beam_shapes: List[Mesh] = []

offset_direction: Vector = Vector.cross(quarter_line.direction, Vector.Zaxis()) * board_thickness * 0.5
quarter_line_offseted: Polygon = Polygon(
    [quarter_line.start + offset_direction, quarter_line.end + offset_direction, quarter_line.end - offset_direction, quarter_line.start - offset_direction]
)
cut_polygon: Polygon = quarter_polygon_offset.transformed(Scale.from_factors([1.00, 1.00, 1], Frame(quarter_polygon[2])))

border_plane0: Plane = Plane(quarter_polygon_offset[2], quarter_polygon_offset[1] - quarter_polygon_offset[2])
border_plane1: Plane = Plane(quarter_polygon_offset[2], quarter_polygon_offset[2] - quarter_polygon_offset[3])

# Slice planes
slice_plane_point: Point = midpoint_point_point(quarter_polygon_offset[1], quarter_polygon_offset[2])
slice_plane_normal: Vector = Vector.cross(quarter_polygon_offset[2] - quarter_polygon_offset[1], Vector.Zaxis())
slice_plane_0: Plane = Plane(slice_plane_point, slice_plane_normal)
slice_plane_point = midpoint_point_point(quarter_polygon_offset[2], quarter_polygon_offset[3])
slice_plane_normal = Vector.cross(quarter_polygon_offset[3] - quarter_polygon_offset[2], Vector.Zaxis())
slice_plane_1: Plane = Plane(slice_plane_point, slice_plane_normal)

print(slice_plane_0)

for i in range(quarter_divisions + 1):
    # Linear interpolation of dicisions
    t: float = i / quarter_divisions

    # Rotate the line and its polygon
    rotation: Rotation = Rotation.from_axis_and_angle([0, 0, 1], angle * t, point=quarter_lines_offset)
    quarter_line_rotated: Line = quarter_line.transformed(rotation)

    # # Rotate the offset polygon
    # quarter_line_offseted_rotated : Polygon = quarter_line_offseted.transformed(rotation)
    # quarter_line_offseted_rotated_cut : Polygon = Polygon(boolean_intersection_polygon_polygon(cut_polygon, quarter_line_offseted_rotated))
    # quarter_polygons.append(quarter_line_offseted_rotated_cut)

    # Intersect the rotated line with the offset polygon and replace the line end point with the intersection point
    if equal_end:
        for j in range(len(quarter_polygon_offset.points)):
            segment: Line = Line(quarter_polygon_offset[j], quarter_polygon_offset[(j + 1) % len(quarter_polygon_offset)])
            result: List[float] = intersection_segment_segment(quarter_line_rotated, segment)
            if result[0]:
                quarter_line_rotated = Line(quarter_line_rotated.start, Point(*result[0]))
                break

    # Extend the line by the thickness
    quarter_line_rotated = Line(quarter_line_rotated.start, quarter_line_rotated.end + quarter_line_rotated.direction * board_thickness)

    # Create polygon
    quarter_polygon_rotated: Polygon = Polygon(
        [
            quarter_line_rotated.start,
            quarter_line_rotated.start + Vector(0, 0, inclination_0),
            quarter_line_rotated.start + Vector(0, 0, inclination_0) + quarter_line_rotated.direction * capitel_width,
            quarter_line_rotated.end + Vector(0, 0, inclination_1),
            quarter_line_rotated.end,
        ]
    )

    # Offset the two polygons in both sides
    normal = Vector.cross(quarter_polygon_rotated[1] - quarter_polygon_rotated[0], quarter_polygon_rotated[-1] - quarter_polygon_rotated[0])
    normal.unitize()
    quarter_polygon_offset_rotated_0: Polygon = quarter_polygon_rotated.translated(normal * board_thickness * 0.5)
    quarter_polygon_offset_rotated_1: Polygon = quarter_polygon_rotated.translated(normal * -board_thickness * 0.5)

    # Loft the two polygons
    mesh = loft_two_polygons(quarter_polygon_offset_rotated_0, quarter_polygon_offset_rotated_1, False)

    # Slice the mesh by the two side planes, take the largest mesh.
    mesh_pair0 = mesh_slice_plane(mesh, border_plane0)
    split_mesh = mesh

    if mesh_pair0:
        if mesh_pair0[0].aabb().volume < mesh_pair0[1].aabb().volume:
            mesh_pair0 = mesh_pair0[::-1]
        split_mesh = mesh_pair0[0]

    mesh_pair1 = mesh_slice_plane(split_mesh, border_plane1)

    if mesh_pair1:
        if mesh_pair1[0].aabb().volume < mesh_pair1[1].aabb().volume:
            mesh_pair1 = mesh_pair1[::-1]
        split_mesh = mesh_pair1[0]

    beam_shapes.append(split_mesh)

    #     if mesh_pair0[0].aabb().volume
    #     if mesh_pair0.b
    #     beam_shapes.append(mesh_pair0[0])
    # if mesh_pair1:
    #     beam_shapes.append(mesh_pair1[0])

    # temp.append(temp_polygon)

    #

    # Cut the the mesh by the side planes and always keep the biggest mesh
    # Cut Planes : border_plane0 and border_plane1

    # temp.append(quarter_line_rotated)
    # temp.append(Polyline(quarter_polygon_rotated.points))
    # temp.append(quarter_polygon_offset_rotated_0)
    # temp.append(quarter_polygon_offset_rotated_1)

    # # Get angle cut plane
    # quarter_line_z : Line = Line(quarter_line_rotated.start+Vector(0,0,inclination_0), quarter_line_rotated.end+Vector(0,0,inclination_1), 0)
    # is_parallel : bool = is_parallel_vector_vector(quarter_line_z.direction, quarter_line_rotated.direction)

    # plane_normal : Vector = Vector.Zaxis()
    # if (is_parallel == False):
    #     triangle_normal : Vector = Vector.cross(quarter_line_rotated.direction, quarter_line_z.direction)
    #     plane_normal : Vector = Vector.cross(quarter_line_z.direction, triangle_normal.unitized())

    # plane : Plane = Plane(quarter_line_z.start, plane_normal)

    # # Project polygon on the rotated plane
    # projection : Projection = Projection.from_plane_and_direction(plane, Vector.Zaxis())
    # quarter_line_offseted_rotated_cut_projected = quarter_line_offseted_rotated_cut.transformed(projection)
    # quarter_polygons.append(quarter_line_offseted_rotated_cut_projected)

    # # Cut the two polygons the plane
    # quarter_line_offseted_rotated_cut_cut = cut_polygon_with_plane(quarter_line_offseted_rotated_cut, capitel_base_cut_plane)
    # quarter_line_offseted_rotated_cut_projected_cut0 = cut_polygon_with_plane(quarter_line_offseted_rotated_cut_projected, capitel_base_cut_plane)
    # quarter_line_offseted_rotated_cut_projected_cut1 = cut_polygon_with_plane(quarter_line_offseted_rotated_cut_projected, Plane(capitel_base_cut_plane.point, -capitel_base_cut_plane.normal))
    # quarter_line_offseted_rotated_cut_projected_cut1.transform(Projection.from_plane_and_direction(capitel_base_cut_plane, Vector.Zaxis()))
    # # print(quarter_line_offseted_rotated_cut_projected_cut1)
    # def merge_two_polylines(polyline0: Polygon, polyline1: Polygon) :

    #     id0 : int = -1
    #     id1 : int = -1
    #     for j in range(len(polyline0)):
    #         line0 : Line = Line(polyline0[j], polyline0[(j+1)%len(polyline0)])
    #         for k in range(len(polyline1)):
    #             line1 : Line = Line(polyline1[k], polyline1[(k+1)%len(polyline1)])
    #             distance : float = distance_point_point(line0.midpoint, line1.midpoint)
    #             if (distance < 0.001):
    #                 id0 = j
    #                 id1 = k
    #                 break
    #     if (id0 == -1 or id1 == -1):
    #         return None

    #     def shift_left(lst, n):
    #         n : int = n % len(lst)  # To handle cases where n > len(lst)
    #         return lst[n:] + lst[:n]

    #     def shift_right(lst: list, n: int) -> list:
    #         n = n % len(lst)  # To handle cases where n > len(lst)
    #         return lst[-n:] + lst[:-n]

    #     points0 = list(polyline0.points)
    #     points1 = list(polyline1.points)
    #     points0 = shift_left(points0, id0+1)
    #     points1 = shift_left(points1, id1+1)

    #     return Polygon(points0 + points1[1:-1])
    #     return Polyline(points0), Polyline(points1)

    # merged_polyline = merge_two_polylines(quarter_line_offseted_rotated_cut_projected_cut0, quarter_line_offseted_rotated_cut_projected_cut1)
    # merged_polyline_xy = merged_polyline.transformed(Projection.from_plane_and_direction(Plane.worldXY(), -Vector.Zaxis()))

    # mesh = loft_two_polygons(merged_polyline, merged_polyline_xy, False)
    # temp.append(mesh)

    # quarter_polygons.append(quarter_line_offseted_rotated_cut_projected_cut0)
    # quarter_polygons.append(quarter_line_offseted_rotated_cut_projected_cut1)

    # Convert polygon to polylines
    # Find common edge by checking closest point distance to edge centers
    # Delete that segment and merge the two polylines
    # for j in range(len(quarter_line_offseted_rotated_cut_cut)-1):
    #     segment0 : Line = Line(quarter_line_offseted_rotated_cut_cut[j], quarter_line_offseted_rotated_cut_cut[(j+1)%len(quarter_line_offseted_rotated_cut_cut)])
    #     for k in range(len(quarter_line_offseted_rotated_cut_projected_cut0)):
    #         segment1 : Line = Line(quarter_line_offseted_rotated_cut_projected_cut1[k], quarter_line_offseted_rotated_cut_projected_cut1[(k+1)%len(quarter_line_offseted_rotated_cut_projected_cut1)])
    #         distance = distance_point_point(segment0.midpoint, segment1.midpoint)
    #         if (distance < 0.001):
    #             print("found the smallest distance")

    # quarter_line_offseted_rotated_cut_projected_cut1.transform(Projection.from_plane_and_direction(capitel_base_cut_plane, Vector.Zaxis()))
    # print(boolean_union_polygon_polygon(quarter_line_offseted_rotated_cut_projected_cut0, quarter_line_offseted_rotated_cut_projected_cut1))

    # quarter_polygons.append(boolean_union_polygon_polygon(
    #      quarter_line_offseted_rotated_cut_projected_cut0.transformed(Projection.from_plane_and_direction(Plane.worldXY(), -Vector.Zaxis())),
    #      quarter_line_offseted_rotated_cut_projected_cut1.transformed(Projection.from_plane_and_direction(Plane.worldXY(), -Vector.Zaxis()))))

    # polygon = Polygon.from_sides_and_radius_xy(10, 1000).transformed(Transformation.from_frame_to_frame(Frame.worldXY(), Frame.from_plane(capitel_base_cut_plane)))
    # temp.append(polygon)
    # print(quarter_line_offseted_rotated_cut_cut)

    # # Loft the two polygons
    # mesh = loft_two_polygons(quarter_line_offseted_rotated_cut, quarter_line_offseted_rotated_cut_projected, False)
    # # mesh = loft_two_polygons(quarter_line_offseted_rotated_cut_cut, quarter_line_offseted_rotated_cut_projected_cut, False)
    # beam_shapes.append(mesh)

    # Or rotate the line first
    # Then cut it.
    # Then move its end vertically.
    # Then plane normal.


# ViewerLive.run()
ViewerLive.clear()
ViewerLive.add(quarter_polygon)
ViewerLive.add(quarter_polygon_offset)
ViewerLive.add(quarter_lines)
ViewerLive.add(quarter_polygons)
ViewerLive.add(beam_shapes)
ViewerLive.add(temp)
ViewerLive.serialize()
