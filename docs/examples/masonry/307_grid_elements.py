from pathlib import Path

import compas
from compas_grid import GridModel
from compas_grid.elements import BeamTProfileElement
from compas_grid.elements import BlockElement
from compas_grid.elements import ColumnElement
from compas.datastructures import Mesh
from compas.geometry import Translation
from compas.geometry import Frame
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================

rhino_geometry = compas.json_load(Path(__file__).parent.parent.parent.parent / "data" / "frame.json")
lines = rhino_geometry["lines"]
meshes = rhino_geometry["meshes"]

# =============================================================================
# Model
# =============================================================================

model = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=meshes)

edges_columns = list(model.cell_network.edges_where({"is_column": True}))  # Order as in the model
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))  # Order as in the model
faces_floors = list(model.cell_network.faces_where({"is_floor": True}))  # Order as in the model

# =============================================================================
# Add Column on a CellNetwork Edge
# =============================================================================

for edge in edges_columns:
    column = ColumnElement(300, 300)
    model.add_column(column, edge)

# =============================================================================
# Add Beams on a CellNetwork Edge
# =============================================================================

for edge_index in [0, 3]:
    beam = BeamTProfileElement(width=300, height=700, step_width_left=75, step_height_left=150)
    model.add_beam(beam, edges_beams[edge_index], 150)

# =============================================================================
# Make vault
# =============================================================================

barrel_model: tuple[list[Mesh], list[Frame]] = compas.json_load(Path(__file__).parent.parent.parent.parent / "data" / "barrel.json")

# =============================================================================
# Add vault blocks
# =============================================================================
for i in range(len(barrel_model["meshes"])):
    grid_block = BlockElement(shape=barrel_model["meshes"][i], is_support=barrel_model["meshes"][i].attributes["is_support"])
    T = Translation.from_vector([0, 0, 3800])
    grid_block.transformation = T
    model.add_element(grid_block)


# =============================================================================
# Process elements
# =============================================================================
elements = list(model.elements())
columns = [element for element in elements if isinstance(element, ColumnElement)]
beams = [element for element in elements if isinstance(element, BeamTProfileElement)]
blocks = [element for element in elements if isinstance(element, BlockElement)]

# =============================================================================
# Visualize
# =============================================================================

config = Config()
config.camera.target = [0, 1000, 1250]
config.camera.position = [0, -10000, 8125]
config.camera.near = 10
config.camera.far = 100000
config.camera.pandelta = 100
config.renderer.gridsize = (20000, 20, 20000, 20)

viewer = Viewer(config=config)

viewer.scene.add([e.modelgeometry for e in columns], show_faces=True, opacity=0.7, name="Columns", hide_coplanaredges=True)

viewer.scene.add([e.modelgeometry for e in beams], show_faces=True, name="Beams", hide_coplanaredges=True)

viewer.scene.add([e.modelgeometry for e in blocks], show_faces=True, name="Blocks", hide_coplanaredges=True)


viewer.show()
