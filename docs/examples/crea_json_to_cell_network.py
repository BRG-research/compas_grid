from typing import Dict, List, Any, Tuple
from compas import json_load
from compas.geometry import Line, midpoint_line, Box, Frame
from compas.datastructures import Graph, CellNetwork, Mesh
from compas.tolerance import TOL
from compas_viewer import Viewer
from compas_viewer.scene import ViewerSceneObject
from collections import OrderedDict

# Constants
PRECISION: int = 3

# Load the JSON data
rhino_geometry: Dict[str, List[Any]] = json_load('data/crea/crea.json')

#######################################################################################################
# GRAPH AND CELL NETWORK
#######################################################################################################

# Create Graph from lines
graph: Graph = Graph.from_lines(rhino_geometry["Line::Column"] + rhino_geometry["Line::Beam"])

# Convert Graph to CellNetwork using vertices and edges
cell_network: CellNetwork = CellNetwork()
cell_network_edge_keys: Dict[str, Tuple[int, int]] = {}
cell_network_vertex_keys: Dict[str, int] = {}

# Add vertices to CellNetwork and store geometric keys
for node in graph.nodes():
    xyz: List[float] = graph.node_attributes(node, "xyz")
    cell_network.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
    cell_network_vertex_keys[TOL.geometric_key(xyz, precision=PRECISION)] = node

# Add edges to CellNetwork and store geometric keys
for edge in graph.edges():
    uv: Tuple[int, int] = edge
    cell_network.add_edge(*uv)
    cell_network_edge_keys[TOL.geometric_key(graph.edge_midpoint(uv), precision=PRECISION)] = uv    
    
#######################################################################################################
# GEOMETRIC ATTRIBUTES: is_column, is_beam, is_floor, is_facade, is_core
#######################################################################################################

# Define attributes for Columns and Beams using geometric keys
for key, geometries in rhino_geometry.items():
    parts: List[str] = key.split("::")
    attribute_key: str = f"is_{parts[1].lower()}"

    for g in geometries:
        if isinstance(g, Line):
            # Edges - midpoint key
            cell_network.edge_attribute(
                cell_network_edge_keys[TOL.geometric_key(midpoint_line(g), precision=PRECISION)],
                attribute_key,
                True
            )
        elif isinstance(g, Mesh):
            # Faces - four vertices
            gkeys: Dict[int, str] = g.vertex_gkey(precision=PRECISION)
            v: List[int] = [cell_network_vertex_keys[key] for _, key in gkeys.items() if key in cell_network_vertex_keys]

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
    coord_dict: Dict[float, List[int]] = {}
    for node in graph.nodes():
        value: float = round(graph.node_attributes(node, coord)[0], 3)
        if value not in coord_dict:
            coord_dict[value] = []
        coord_dict[value].append(node)

    sorted_coord_dict: OrderedDict[float, List[int]] = OrderedDict(sorted(coord_dict.items()))

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
        face_nodes: List[int] = cell_network.face_vertices(face)
        face_values: List[int] = [cell_network.vertex_attribute(node, attr_name) for node in face_nodes]
        cell_network.face_attribute(face, attr_name, min(face_values))
    
    cell_network.attributes["max_"+attr_name] = len(sorted_coord_dict)
            
# Run the method for x, y, and z coordinates
partition_and_assign_attributes(graph, cell_network, "x", "u")
partition_and_assign_attributes(graph, cell_network, "y", "v")
partition_and_assign_attributes(graph, cell_network, "z", "w")

#######################################################################################################
# VIEWER
#######################################################################################################

# Initialize Viewer
viewer: Viewer = Viewer(show_grid=False)

# Viewer: Add elements to the scene
lines = [cell_network.edge_line(edge) for edge in cell_network.edges_where({"is_column": True})]
viewer.scene.add(lines, color=(0, 0, 255), linewidth=1, name="is_column")

# Add beam edges to the scene
beam_lines = [cell_network.edge_line(edge) for edge in cell_network.edges_where({"is_beam": True})]
viewer.scene.add(beam_lines, color=(255, 0, 0), linewidth=1, name="is_beam")

# Add floor faces to the scene
floor_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_floor": True})]
viewer.scene.add(floor_faces, color=(255, 0, 0), linewidth=1, name="is_floor")

# Add facade faces to the scene
facade_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_facade": True})]
viewer.scene.add(facade_faces, color=(0, 255, 0), linewidth=1, name="is_facade")

# Add core faces to the scene
core_faces = [cell_network.faces_to_mesh([face]) for face in cell_network.faces_where({"is_core": True})]
viewer.scene.add(core_faces, color=(255, 255, 0), linewidth=1, name="is_core")

viewer.scene.add(cell_network.faces_to_mesh(list(cell_network.faces_where({"is_floor": True, "w": 5}))),  color=(255, 0, 0), name="floor_5")

# for vertex, attributes in cell_network.vertices(True):
#     viewer.scene.add(Box(xsize=attributes["w"]*100, frame=Frame([attributes["x"], attributes["y"], attributes["z"]+1000])))
#     viewer.scene.add(Box(xsize=attributes["v"]*100, frame=Frame([attributes["x"], attributes["y"]+1000, attributes["z"]])))
#     viewer.scene.add(Box(xsize=attributes["u"]*100, frame=Frame([attributes["x"]+1000, attributes["y"], attributes["z"]])))

# Add geometries to the viewer scene
# for key, geometries in rhino_geometry.items():
#     viewer_scene_object: ViewerSceneObject = viewer.scene.add(geometries)
#     viewer_scene_object.name = key

# Show the viewer
viewer.show()