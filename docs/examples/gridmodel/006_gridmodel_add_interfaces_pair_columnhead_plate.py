from pathlib import Path

from compas_viewer import Viewer
from compas_viewer.config import Config

from compas import json_load
from compas.geometry import Polygon
from compas_grid.elements import ColumnHeadCrossElement
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

# =============================================================================
# Add Elements to CellNetwork Edge
# =============================================================================
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))
faces_floors = list(model.cell_network.faces_where({"is_floor": True}))

column_head = ColumnHeadCrossElement(width=150, height=150, length=300, offset=210)
plate = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)

model.add_column_head(column_head, edges_beams[0])
model.add_floor(plate, faces_floors[0], 100)

# =============================================================================
# Add Interaction
# =============================================================================
model.add_interaction(column_head, plate)
model.add_modifier(column_head, plate)

# =============================================================================
# Visualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer.scene.add(model.cell_network.lines)
# viewer.scene.add(model.cell_network.polygons)
viewer.scene.add(model.geometry)
viewer.show()
