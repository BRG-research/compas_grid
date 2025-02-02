from compas import json_load
from pathlib import Path
from compas_viewer import Viewer
from compas_model.models import Model

###############################################################################
# Beam
###############################################################################
beam0 = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_001.json")
beam1 = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_002.json")


###############################################################################
# Create a model.
###############################################################################
model = Model()
model.add_element(beam0)
model.add_element(beam1)

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)

viewer.show()
