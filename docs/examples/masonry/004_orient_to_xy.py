from pathlib import Path

from compas_model.models import Model
from compas_viewer import Viewer

from compas import json_load
from compas_grid.elements import BlockElement

# =============================================================================
# Deserilize Model form JSON file.
# =============================================================================
model: Model = json_load(Path("data/model.json"))


viewer = Viewer()
for element in list(model.elements()):
    if isinstance(element, BlockElement):
        viewer.scene.add(element.elementgeometry.scaled(0.001), hide_coplanaredges=True)
        break
viewer.show()
