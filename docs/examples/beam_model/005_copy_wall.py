from compas import json_load, json_dump
from pathlib import Path
from compas_viewer import Viewer
from compas_model.models import Model
from compas_grid.elements import PlateElement
from compas.geometry import Translation, Rotation
from math import pi

###############################################################################
# Beam
###############################################################################
model = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_004.json")

plate = None 
for element in model.elements():
    if isinstance(element, PlateElement):
        plate = element


###############################################################################
# Replace this with BeamModel that allows to copy elements and its childs.
# After the copy the group is added to the model.
# Step 1: - Find Specific Element with additional attribute of transformation.
# Step 2: - Copy it with childs and add to the model.
###############################################################################
plate_copy = plate.copy()
node = model.add_element(plate_copy)

for plate.treenode in plate.treenode.children:
        model.add_element(plate.treenode.element.copy(), node)
plate_copy.transformation = Translation.from_vector([0, 6, 0])


###############################################################################
# Serialize
###############################################################################
# json_dump(model, Path(__file__).parent.parent.parent.parent / "data" / "beam_model_004.json")

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)


viewer.show()
