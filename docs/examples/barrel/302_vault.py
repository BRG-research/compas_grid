from pathlib import Path

import compas
from compas.geometry import Brep
from compas.geometry import Translation
from compas.geometry import Frame
from compas.datastructures import Mesh
from compas.tolerance import TOL
from compas_grid.elements import BeamProfileElement
from compas_grid.elements import BlockElement
from compas_grid.elements import ColumnElement
from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# Load Model
# =============================================================================

model: Model = compas.json_load(Path(__file__).parent.parent.parent.parent / "data" / "model.json")

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
# Preprocess
# =============================================================================

TOL.lineardeflection = 1
TOL.angulardeflection = 1


elements = list(model.elements())
beams = [element for element in elements if isinstance(element, BeamProfileElement)]
columns = [element for element in elements if isinstance(element, ColumnElement)]

blocks = []
points = []
for element in elements:
    points.append(element.aabb.frame.point)
    if isinstance(element, BlockElement):
        brep = Brep.from_mesh(element.modelgeometry)
        brep.simplify(lineardeflection=TOL.lineardeflection, angulardeflection=TOL.angulardeflection)
        blocks.append(brep)

# =============================================================================
# Export
# =============================================================================

compas.json_dump(model, Path(__file__).parent.parent.parent.parent / "data" / "model_with_interactions.json")

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

viewer.scene.add(points)

viewer.scene.add(
    [Brep.from_mesh(e.modelgeometry) for e in columns],
    show_faces=True,
    opacity=0.7,
    name="Columns",
)

viewer.scene.add(
    [Brep.from_mesh(e.modelgeometry) for e in beams],
    show_faces=False,
    name="Beams",
)

viewer.scene.add(
    [e for e in blocks],
    show_faces=False,
    name="Blocks",
)

viewer.show()
