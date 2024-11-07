from compas import json_load
from compas_grid.grid_model import GridModel
from compas.geometry import Point, Scale, Frame, Line, Polygon, Polyline
from compas_viewer import Viewer
from compas_viewer.scene import ViewerSceneObject
from compas.datastructures import Graph
from compas.datastructures import CellNetwork
from compas.datastructures import Mesh
from compas.tolerance import TOL
from compas.geometry import midpoint_line
from typing import *



#######################################################################################################
# COMPAS geometry from Rhino is stored in a JSON file using following keys: 
# Line::Column
# Line::Beam
# Mesh::Floor
# Mesh::Facade
# Mesh::Core
#######################################################################################################
viewer: Viewer = Viewer(show_grid=False)
# JSON
rhino_geometry : Dict[str, List[Any]] = json_load('data/crea/crea.json')


#######################################################################################################
# CellNetwork
# Create Graph from lines
# Convert Graph to CellNetwork
# Add attributes: is_beam, is_column, level, surface_type, etc
#######################################################################################################

# Create Graph from lines
graph : Graph = Graph.from_lines(rhino_geometry["Line::Column"] + rhino_geometry["Line::Beam"])

# Convert Graph to CellNetwork using vertices and edges.
# Also, store the geometric keys of vertices and edges for attributes.
cell_network : CellNetwork = CellNetwork()
cell_network_edge_keys : Dict[str, Tuple[int, int]] = {}
cell_network_vertex_keys : Dict[str, int] = {}
precision : int = 3

for node in graph.nodes():
    xyz : List[float] = graph.node_attributes(node, "xyz")
    cell_network.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
    cell_network_vertex_keys[TOL.geometric_key(xyz, precision=precision)] = node

for edge in graph.edges():
    uv : Tuple[int, int] = edge
    cell_network.add_edge(*uv)
    cell_network_edge_keys[TOL.geometric_key(graph.edge_midpoint(uv), precision=precision)] = uv

# Attributes: Columns and Beams are defined by geometric keys
for key, geometries in rhino_geometry.items():
    
    parts : List[str] = key.split("::")
    attribute_key = f"is_{parts[1].lower()}"
    
    for g in geometries:
        # Edges - midpoint key - lines will always have a matching key, since the graph is created from lines.
        if isinstance(g, Line):
            cell_network.edge_attribute(
                cell_network_edge_keys[TOL.geometric_key(midpoint_line(g), precision=precision)], 
                attribute_key, 
                True)
        # Cells - four vertices - faces might not have a matching key, check this.
        elif isinstance(g, Mesh):
            viewer.scene.add(g)
            gkeys: Dict[int, str] = g.vertex_gkey(precision=precision)
            v : List[int] = []
            for _, key in gkeys.items():
                if key in cell_network_vertex_keys:
                    v.append(cell_network_vertex_keys[key])

            if len(v) == 4:
                cell_network.add_face(v, attr_dict={attribute_key: True})

            

#######################################################################################################
# GridModel 
# TODO: elements
#######################################################################################################


#######################################################################################################
# Viewer
#######################################################################################################


# for edge in cell_network.edges_where({"is_column": True}):
#     viewer.scene.add(cell_network.edge_line(edge), color=(0, 0, 255), linewidth=1)

# for edge in cell_network.edges_where({"is_beam": True}):
#     viewer.scene.add(cell_network.edge_line(edge), color=(255, 0, 0), linewidth=1)
    
# for face in cell_network.faces_where({"is_floor": True}):
#     viewer.scene.add(cell_network.faces_to_mesh([face]), color=(255, 0, 0), linewidth=1)
    
# for face in cell_network.faces_where({"is_facade": True}):
#     viewer.scene.add(cell_network.faces_to_mesh([face]), color=(0, 255, 0), linewidth=1)

# for face in cell_network.faces_where({"is_core": True}):
#     viewer.scene.add(cell_network.faces_to_mesh([face]), color=(255, 255, 0), linewidth=1)

# # viewer.scene.add(cell_network.faces_to_mesh(list(cell_network.faces_where({"is_facade": True}))))
# # for key, geometries in rhino_geometry.items():
# #     viewer_scene_object : ViewerSceneObject = viewer.scene.add(geometries)
# #     viewer_scene_object.name = key
# viewer.show()