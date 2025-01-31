from pathlib import Path

from compas_viewer import Viewer
from compas_viewer.config import Config

from compas import json_load
from compas_grid.elements import BeamElement
from compas_grid.elements import ColumnHeadCrossElement
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
column_head = ColumnHeadCrossElement(width=150, height=150, length=300, offset=210)
beam = BeamElement(width=300, height=300)

model.add_column_head(column_head, edges_beams[0])
model.add_beam(beam, edges_beams[0])

# =============================================================================
# Add Interaction
# =============================================================================
model.add_interaction(column_head, beam)
model.add_modifier(column_head, beam)

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
viewer.scene.add(model.cell_network.polygons)
viewer.scene.add(model.geometry)
viewer.show()
