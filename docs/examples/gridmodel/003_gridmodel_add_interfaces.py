from pathlib import Path

from compas_viewer import Viewer
from compas_viewer.config import Config

from compas import json_load
from compas.geometry import Polygon
from compas_grid.elements import BeamElement
from compas_grid.elements import ColumnHeadCrossElement
from compas_grid.elements import ColumnElement
from compas_grid.elements import PlateElement
from compas_grid.models import GridModel

# =============================================================================
# JSON file with the geometry of the model. Datasets: data/frame.json, data/crea/crea_4x4.json
# =============================================================================
rhino_geometry = json_load(Path("data/frame.json"))
lines = rhino_geometry["Model::Line::Segments"]
surfaces = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================
model = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces)

# =============================================================================
# Add Column on a CellNetwork Edge
# Add ColumnHead on a CellNetwork Edge
# Add Beams on a CellNetwork Edge
# Add Plates on a CellNetwork Face
# =============================================================================
edges_columns = list(model.cell_network.edges_where({"is_column": True}))  # Order as in the model
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))  # Order as in the model
faces_floors = list(model.cell_network.faces_where({"is_floor": True}))  # Order as in the model

for edge in edges_columns:
    column_head = ColumnHeadCrossElement(width=150, height=150, length=300, offset=210)
    model.add_column_head(column_head, edge)

for edge in edges_columns:
    column_square = ColumnElement(width=300, height=300)
    model.add_column(column_square, edge)

for edge in edges_beams:
    beam_square = BeamElement(width=300, height=300)
    model.add_beam(beam_square, edge)

for face in faces_floors:
    plate = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
    model.add_floor(plate, face, 100)

# =============================================================================
# Add Interaction between Column and Column Head
# Add Interaction between Beam and Column Head.
# Add Interaction between Floor and Column Head.
# These mappings are used to find the interaction pairs from CellNetwork:
# self.column_head_to_vertex: dict[Element, int]
# self.column_to_edge: dict[Element, tuple[int, int]]
# self.beam_to_edge: dict[Element, tuple[int, int]]
# self.vertex_to_plates_and_faces: dict[int, list[tuple[Element, list[int]]]]
# =============================================================================
for edge in edges_columns:
    for i in range(2):
        if edge[i] in model.column_head_to_vertex:
            model.add_interaction(model.column_head_to_vertex[edge[i]], model.column_to_edge[edge])
            model.add_modifier(model.column_head_to_vertex[edge[i]], model.column_to_edge[edge])

for edge in edges_beams:
    for i in range(2):
        if edge[i] in model.column_head_to_vertex:
            model.add_interaction(model.column_head_to_vertex[edge[i]], model.beam_to_edge[edge])
            model.add_modifier(model.column_head_to_vertex[edge[i]], model.beam_to_edge[edge])

for vertex, plates_and_faces in model.vertex_to_plates_and_faces.items():
    if vertex in model.column_head_to_vertex:
        model.add_interaction(model.column_head_to_vertex[vertex], plates_and_faces[0][0])
        model.add_modifier(model.column_head_to_vertex[vertex], plates_and_faces[0][0])

# =============================================================================
# Visualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer.scene.add(model.geometry)
viewer.show()
