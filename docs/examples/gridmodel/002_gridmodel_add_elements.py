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
# JSON file with the geometry of the model. Datasets: frame.json, crea_4x4.json
# =============================================================================
rhino_geometry = json_load(Path("data/frame.json"))
lines = rhino_geometry["Model::Line::Segments"]
surfaces = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================
model = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces)

edges_columns = list(model.cell_network.edges_where({"is_column": True}))  # Order as in the model
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))  # Order as in the model
faces_floors = list(model.cell_network.faces_where({"is_floor": True}))  # Order as in the model

# =============================================================================
# Add Column on a CellNetwork Edge
# =============================================================================
for edge in edges_columns:
    column_head = ColumnHeadCrossElement(width=150, height=150, length=300, offset=210)
    model.add_column_head(column_head, edge)

# =============================================================================
# Add ColumnHead on a CellNetwork Edge
# =============================================================================
for edge in edges_columns:
    column_square = ColumnElement(width=300, height=300)
    model.add_column(column_square, edge)

# =============================================================================
# Add Beams on a CellNetwork Edge
# =============================================================================
for edge in edges_beams:
    beam_square = BeamElement(width=300, height=300)
    model.add_beam(beam_square, edge)

# =============================================================================
# Add Plates on a CellNetwork Face
# =============================================================================
for face in faces_floors:
    plate = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
    model.add_floor(plate, face, 100)

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
