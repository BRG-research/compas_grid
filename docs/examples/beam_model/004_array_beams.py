from compas import json_load, json_dump
from pathlib import Path
from compas_viewer import Viewer
from compas.geometry import Polygon
from compas_model.models import Model
from compas_grid.elements import PlateElement
from compas.geometry import Translation, Rotation
from math import pi

###############################################################################
# Beam
###############################################################################
beam0 = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_001.json")
beam1 = json_load(Path(__file__).parent.parent.parent.parent / "data" / "beam_model_002.json")

###############################################################################
# Create a model.
###############################################################################
model = Model()

###############################################################################
# Create a plate.
###############################################################################
polygon = Polygon([[0, 0.25, 0], [6, 0.25, 0], [6, 0.25, 3], [0, 0.25, 3]])
thickness = 0.4
plate = PlateElement(polygon, thickness)
plane_node = model.add_element(plate)

###############################################################################
# Array Beams in an alternating line.
###############################################################################

length = 6
radius = 0.15
count : int = int(length/(radius*2)+1)


for i in range(count):
    beam_i = beam0.copy()
    model.add_element(beam_i, plane_node)
    T = Translation.from_vector([i*radius*2, 0, 0])
    beam_i.transformation = T

for i in range(count-1):
    beam_i = beam1.copy()
    model.add_element(beam_i, plane_node)
    T1 = Translation.from_vector([i*radius*2, 0, 0])
    R = Rotation.from_axis_and_angle([0, 0, 1], pi)
    T0 = Translation.from_vector([-radius, -radius, 0])
    beam_i.transformation = T1 * R * T0

###############################################################################
# Serialize
###############################################################################
json_dump(model, Path(__file__).parent.parent.parent.parent / "data" / "beam_model_004.json")

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)

viewer.show()
