from typing import Any, Tuple
from compas import json_load
from compas.geometry import Line, midpoint_line, Box, Frame, Polygon, Vector, Point, Polyline
from compas.geometry import Transformation
from compas.datastructures import Graph, CellNetwork, Mesh
from compas.tolerance import TOL
from compas_viewer import Viewer
from compas_viewer.scene import ViewerSceneObject
from collections import OrderedDict
from compas_grid.element_beam import BeamElement
from compas_grid.element_plate import PlateElement
from compas_grid.element_column import ColumnElement
from compas_grid.element_column_head import ColumnHeadElement
from compas_grid.elements.interface_cutter import CutterInterface
from compas_model.models import Model
from compas_model.elements import Element
from compas.colors import Color

# Classes as Datastructures,
# CellNetwork - from from_mesh, from_graph, from_lines
# Model


#######################################################################################################
# INPUT | VIEWER FOR DEBUGGING
#######################################################################################################
PRECISION: int = 3
rhino_geometry: dict[str, list[Any]] = json_load("data/crea/crea_4x4.json")
viewer: Viewer = Viewer(show_grid=False)
viewer.renderer.rendermode = "ghosted"


#######################################################################################################
# GRAPH
# Do not rely on the direction
#######################################################################################################
def create_ordered_line(point1: Point, point2: Point) -> Line:
    """
    Create a Line object with the correct orientation based on the comparison of xyz coordinates,
    with priority given to the z coordinate.

    Parameters
    ----------
    point1 : Point
        The first point.
    point2 : Point
        The second point.

    Returns
    -------
    Line
        The Line object with the correct orientation.
    """
    if point1[2] < point2[2]:
        return Line(point1, point2)
    elif point1[2] > point2[2]:
        return Line(point2, point1)
    elif point1[0] < point2[0]:
        return Line(point1, point2)
    elif point1[0] > point2[0]:
        return Line(point2, point1)
    elif point1[1] < point2[1]:
        return Line(point1, point2)
    else:
        return Line(point2, point1)


# Create Graph from lines and mesh face edges
lines_from_user_input: list[Line] = []
for key, geometries in rhino_geometry.items():
    if len(geometries) == 0:
        continue
    if isinstance(geometries[0], Line):
        for line in geometries:
            lines_from_user_input.append(create_ordered_line(line[0], line[1]))
    elif isinstance(geometries[0], Mesh):
        for mesh in geometries:
            for line in mesh.to_lines():
                lines_from_user_input.append(create_ordered_line(line[0], line[1]))

graph: Graph = Graph.from_lines(lines_from_user_input, precision=PRECISION)

#######################################################################################################
# CELL NETWORK
#######################################################################################################


# Convert Graph to CellNetwork using vertices and edges
cell_network: CellNetwork = CellNetwork()
cell_network_edge_keys: dict[str, Tuple[int, int]] = {}
cell_network_vertex_keys: dict[str, int] = {}

# Add vertices to CellNetwork and store geometric keys
for node in graph.nodes():
    xyz: list[float] = graph.node_attributes(node, "xyz")
    cell_network.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
    cell_network_vertex_keys[TOL.geometric_key(xyz, precision=PRECISION)] = node

# Add edges to CellNetwork and store geometric keys
for edge in graph.edges():
    uv: Tuple[int, int] = edge
    cell_network.add_edge(*uv)
    cell_network_edge_keys[TOL.geometric_key(graph.edge_midpoint(uv), precision=PRECISION)] = uv  # remoce, use vertex keys instead

#######################################################################################################
# GEOMETRIC ATTRIBUTES: is_column, is_beam, is_floor, is_facade, is_core
# Attribute can also be known by checking z coordinate.
#######################################################################################################

# Define attributes for Columns and Beams using geometric keys
for key, geometries in rhino_geometry.items():
    parts: list[str] = key.split("::")
    attribute_key: str = f"is_{parts[1].lower()}"

    for g in geometries:
        if isinstance(g, Line):
            # Edges - midpoint key
            cell_network.edge_attribute(
                cell_network_edge_keys[TOL.geometric_key(midpoint_line(g), precision=PRECISION)],  # two end points
                attribute_key,
                True,
            )
        elif isinstance(g, Mesh):
            # Faces - four vertices
            gkeys: dict[int, str] = g.vertex_gkey(precision=PRECISION)
            v: list[int] = [cell_network_vertex_keys[key] for _, key in gkeys.items() if key in cell_network_vertex_keys]

            if len(v) == 4:
                cell_network.add_face(v, attr_dict={attribute_key: True})


#######################################################################################################
# SPATIAL ATTRIBUTES: u (x-axis), v (y-axis), w (level)
#######################################################################################################


def partition_and_assign_attributes(graph: Graph, cell_network: CellNetwork, coord: str, attr_name: str) -> None:
    """
    Partition cell_network_vertex_keys by a specified coordinate, sort the dictionary,
    and assign the attributes to the cell network vertices.

    Parameters
    ----------
    graph : Graph
        The graph containing the nodes.
    cell_network : CellNetwork
        The cell network to which the attributes will be assigned.
    coord : str
        The coordinate by which to partition ('x', 'y', or 'z').
    attr_name : str
        The name of the attribute to assign ('u', 'v', or 'w').
    """
    coord_dict: dict[float, list[int]] = {}
    for node in graph.nodes():
        value: float = round(graph.node_attributes(node, coord)[0], 3)
        if value not in coord_dict:
            coord_dict[value] = []
        coord_dict[value].append(node)

    sorted_coord_dict: OrderedDict[float, list[int]] = OrderedDict(sorted(coord_dict.items()))

    for level, (value, nodes) in enumerate(sorted_coord_dict.items()):
        for j, node in enumerate(nodes):
            cell_network.vertex_attribute(node, attr_name, level)

    # Edge UVW, by taking the minimum of the two vertices
    for edge in cell_network.edges():
        u: int = cell_network.vertex_attribute(edge[0], attr_name)
        v: int = cell_network.vertex_attribute(edge[1], attr_name)
        cell_network.edge_attribute(edge, attr_name, min(u, v))

    # Face UVW, by taking the minimum of all the vertices
    for face in cell_network.faces():
        face_nodes: list[int] = cell_network.face_vertices(face)
        face_values: list[int] = [cell_network.vertex_attribute(node, attr_name) for node in face_nodes]
        cell_network.face_attribute(face, attr_name, min(face_values))

    cell_network.attributes["max_" + attr_name] = len(sorted_coord_dict)


# Run the method for x, y, and z coordinates
partition_and_assign_attributes(graph, cell_network, "x", "u")
partition_and_assign_attributes(graph, cell_network, "y", "v")
partition_and_assign_attributes(graph, cell_network, "z", "w")

#######################################################################################################
# MODEL
# Crate model with the following elements:
# - BeamElement
# - PlateElement
# - ColumnElement
# - ColumnHeadElement
# TODO: The direction of the edges in the CellNetwork must be checked
# Annotate column head faces types, design of colum head very specific ibcluding faces
# Column head quadrants + frame, columnhead class, based on the valency of the node you have cases:  corner, boundary, internal vertices. Align column head with the overal frame system
#######################################################################################################
cell_network_columns: list[tuple[int, int]] = list(cell_network.edges_where({"is_column": True}))  # Order as in the model
cell_network_beams: list[tuple[int, int]] = list(cell_network.edges_where({"is_beam": True}))  # Order as in the model
cell_network_floors: list[int] = list(cell_network.faces_where({"is_floor": True}))  # Order as in the model

model: Model = Model()
columns = model.add_group("columns")
column_heads = model.add_group("column_heads")
beams = model.add_group("beams")
floors = model.add_group("floors")

map_column_head_to_cell_network_vertex: dict[Element, int] = {}
map_column_to_cell_network_edge: dict[Element, Tuple[int, int]] = {}
map_beam_to_cell_network_edge: dict[Element, Tuple[int, int]] = {}

# vertex_node = {}
# edge_node = {}

# for vertex in cell_network.vertices():
#     node = model.add_element(...)
#     vertex_node[vertex] = node

# for edge in cell_network.edges():
#     node = model.add_element(...)
#     edge_node[edge] = node


width, depth, height, column_head_offset = 150, 150, 300, 210


def add_column_head(edge):
    axis: Line = cell_network.edge_line(edge)
    column_head_vertex: int = edge[1]
    if axis[0][2] > axis[1][2]:
        axis = Line(axis[1], axis[0])
        column_head_vertex = edge[0]

    # top rectangle
    polygon0: Polyline = Polyline(
        [
            Point(-width, -depth, -height) + Vector(0, -column_head_offset, 0),
            Point(width, -depth, -height) + Vector(0, -column_head_offset, 0),
            Point(width, -depth, -height) + Vector(column_head_offset, 0, 0),
            Point(width, depth, -height) + Vector(column_head_offset, 0, 0),
            Point(width, depth, -height) + Vector(0, column_head_offset, 0),
            Point(-width, depth, -height) + Vector(0, column_head_offset, 0),
            Point(-width, depth, -height) + Vector(-column_head_offset, 0, 0),
            Point(-width, -depth, -height) + Vector(-column_head_offset, 0, 0),
        ]
    )

    polygon1: Polyline = Polyline([Point(-width, -depth, 0), Point(width, -depth, 0), Point(width, depth, 0), Point(-width, depth, 0)])

    v: list[Point] = []
    f: list[list[int]] = []
    v.extend(polygon0.points)
    v.extend(polygon1.points)
    f.append([0, 1, 2, 3, 4, 5, 6, 7])
    f.append([3 + 8, 2 + 8, 1 + 8, 0 + 8])

    for i in range(4):
        f.append([i * 2, (i * 2 + 1) % 8, 8 + (i + 1) % 4, 8 + i])
        f.append([(i * 2 + 1) % 8, (i * 2 + 2) % 8, 8 + (i + 1) % 4])

    mesh: Mesh = Mesh.from_vertices_and_faces(v, f)

    element_column_head: ColumnHeadElement = ColumnHeadElement.from_mesh(mesh)
    # element_column_head: ColumnHeadElement = ColumnHeadElement.from_box(width=300, depth=300, height=300)
    element_column_head.frame = Frame(cell_network.vertex_point(column_head_vertex), [1, 0, 0], [0, 1, 0])
    model.add_element(element=element_column_head, parent=column_heads)

    map_column_head_to_cell_network_vertex[column_head_vertex] = element_column_head


def add_column(edge):
    axis: Line = cell_network.edge_line(edge)
    column_head_vertex: int = edge[1]
    if axis[0][2] > axis[1][2]:
        axis = Line(axis[1], axis[0])
        column_head_vertex = edge[0]

    element_column: ColumnElement = ColumnElement.from_square_section(width=width * 2, depth=depth * 2, height=axis.length)
    element_column.frame = Frame(axis.start, [1, 0, 0], [0, 1, 0])
    model.add_element(element=element_column, parent=columns)

    map_column_to_cell_network_edge[edge] = element_column


def add_interaction_column_and_column_head(edge):
    axis: Line = cell_network.edge_line(edge)
    column_head_vertex: int = edge[1]
    column_base_vertex: int = edge[0]
    if axis[0][2] > axis[1][2]:
        axis = Line(axis[1], axis[0])
        column_head_vertex = edge[0]
        column_base_vertex = edge[1]

    if column_head_vertex in map_column_head_to_cell_network_vertex:
        model.add_interaction(
            map_column_head_to_cell_network_vertex[column_head_vertex],
            map_column_to_cell_network_edge[edge],
            interaction=CutterInterface(polygon=map_column_head_to_cell_network_vertex[column_head_vertex].face_lowest, name="column_head_column_to_column"),
        )

    if column_base_vertex in map_column_head_to_cell_network_vertex:
        model.add_interaction(
            map_column_head_to_cell_network_vertex[column_base_vertex],
            map_column_to_cell_network_edge[edge],
            interaction=CutterInterface(polygon=map_column_head_to_cell_network_vertex[column_base_vertex].face_highest, name="column_head_column_to_column"),
        )


def add_beam(edge):
    axis: Line = cell_network.edge_line(edge)
    element: BeamElement = BeamElement.from_square_section(width=height, depth=depth * 2, height=axis.length)
    element.frame = Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1]))
    model.add_element(element=element, parent=columns)

    map_beam_to_cell_network_edge[edge] = element


def add_interaction_beam_and_column_head(edge):
    beam_element: BeamElement = map_beam_to_cell_network_edge[edge]

    if edge[0] in map_column_head_to_cell_network_vertex:
        column_head_element = map_column_head_to_cell_network_vertex[edge[0]]
        model.add_interaction(
            column_head_element, beam_element, interaction=CutterInterface(polygon=column_head_element.face_nearest(beam_element.obb.frame.point), name="column_head_and_beam")
        )

    if edge[1] in map_column_head_to_cell_network_vertex:
        column_head_element = map_column_head_to_cell_network_vertex[edge[1]]
        model.add_interaction(
            column_head_element, beam_element, interaction=CutterInterface(polygon=column_head_element.face_nearest(beam_element.obb.frame.point), name="column_head_and_beam")
        )


def add_floor(face):
    width, depth, thickness = 3000, 3000, 200
    polygon: Polygon = Polygon([[-width, -depth, -thickness], [-width, depth, -thickness], [width, depth, -thickness], [width, -depth, -thickness]])
    plate_element: PlateElement = PlateElement.from_polygon_and_thickness(polygon, thickness)
    plate_element.frame = Frame(cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0])
    model.add_element(element=plate_element, parent=columns)

    for vertex in cell_network.face_vertices(face):
        if vertex in map_column_head_to_cell_network_vertex:
            column_head_element = map_column_head_to_cell_network_vertex[vertex]

            model.add_interaction(
                map_column_head_to_cell_network_vertex[vertex],
                plate_element,
                interaction=CutterInterface(polygon=column_head_element.face_nearest(plate_element.obb.frame.point), name="column_head_and_plate"),
            )


for edge in cell_network_columns:
    add_column_head(edge)

for edge in cell_network_columns:
    add_column(edge)

for edge in cell_network_columns:
    add_interaction_column_and_column_head(edge)

for edge in cell_network_beams:
    add_beam(edge)

for edge in cell_network_beams:
    add_interaction_beam_and_column_head(edge)

for face in cell_network_floors:
    add_floor(face)

#######################################################################################################
# VIEWER
#######################################################################################################

# # Add all edge to the viewer to see the directed graph
# for edge in cell_network.edges():
#     line: Line = cell_network.edge_line(edge)
#     # viewer.scene.add(line.vector, anchor=line.start, linecolor=Color.black())
#     viewer.scene.add(line, color=(0, 0, 0), linewidth=5)

# Add column edges to the scene
# lines = [cell_network.edge_line(edge) for edge in cell_network.edges_where({"is_column": True})]
# viewer.scene.add(lines, color=(0, 0, 255), linewidth=1, name="is_column")

# Add beam edges to the scene
# beam_lines = [cell_network.edge_line(edge) for edge in cell_network.edges_where({"is_beam": True})]
# viewer.scene.add(beam_lines, color=(255, 0, 0), linewidth=1, name="is_beam")

# # Add floor faces to the scene
# floor_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_floor": True})]
# viewer.scene.add(floor_faces, color=(255, 0, 0), linewidth=1, name="is_floor")

# # Add facade faces to the scene
# facade_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_facade": True})]
# viewer.scene.add(facade_faces, color=(0, 255, 0), linewidth=1, name="is_facade")

# # Add core faces to the scene
# core_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_core": True})]
# viewer.scene.add(core_faces, color=(255, 255, 0), linewidth=1, name="is_core")

# viewer.scene.add(cell_network.faces_to_mesh(list(cell_network.faces_where({"is_floor": True, "w": 5}))),  color=(255, 0, 0), name="floor_5")

# for vertex, attributes in cell_network.vertices(True):
#     viewer.scene.add(Box(xsize=attributes["w"]*100, frame=Frame([attributes["x"], attributes["y"], attributes["z"]+1000])))
#     viewer.scene.add(Box(xsize=attributes["v"]*100, frame=Frame([attributes["x"], attributes["y"]+1000, attributes["z"]])))
#     viewer.scene.add(Box(xsize=attributes["u"]*100, frame=Frame([attributes["x"]+1000, attributes["y"], attributes["z"]])))

# Show the viewer
for element in model.elements():
    geometry = element.geometry
    geometry.name = element.name
    viewer.scene.add(geometry)

for interaction in model.interactions():
    print(interaction)
    viewer.scene.add(interaction.frame_polygon(500), color=(255, 0, 0), linewidth=5)
for edge in model.graph.edges():
    print(edge)
    # viewer.scene.add(model.graph.edge_line(edge), color=(0, 0, 0), linewidth=5)
viewer.show()
