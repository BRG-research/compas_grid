from compas import json_load, json_dump
from pathlib import Path
from compas_viewer import Viewer
from compas_model.models import Model
from compas.geometry import Translation, Rotation
from math import pi

###############################################################################
# Beam
###############################################################################
model0 = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_004.json")
model1 = model0.copy()


model1.transformation = Translation.from_vector([0, 6, 0])



###############################################################################
# Serialize
###############################################################################
# json_dump(model, Path(__file__).parent.parent.parent.parent / "data" / "beam_model_004.json")

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
for element in model0.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)
for element in model1.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)

viewer.show()
