from compas_viewer import Viewer
from compas_grid.elements import BeamElement
from compas_grid.elements import BeamProfileElement, BeamProfileFeature
from compas.geometry import Polygon, Polyline
from compas.geometry import Translation, Rotation
from compas_model.models import Model
from math import pi

###############################################################################
# Beam
###############################################################################
radius = 0.15
height0 = 0.1
height1 = 0.02
width = 0.1
polygon = Polygon(
    [
        [radius, 0, 0],
        [0, radius, 0],
        [-radius, 0, 0],
        [-radius, -height0, 0],
        [-radius+width, -height0, 0],
        [-radius+width, -height0-height1, 0],
        [radius-width, -height0-height1, 0],
        [radius-width, -height0, 0],
        [radius, -height0, 0],
    ]
)

circle = Polygon.from_sides_and_radius_xy(40, radius)
beam0 = BeamProfileElement(circle, shape=None)
beam0_t = BeamProfileFeature(polygon)
beam0.features.append(beam0_t)

radius = 0.15
height0 = 0.3
height1 = 0.02
width = 0.1
polygon = Polygon(
    [
        [radius, 0, 0],
        [0, radius, 0],
        [-radius, 0, 0],
        [-radius, -height0, 0],
        [radius, -height0, 0],
    ]
)

beam1 = BeamProfileElement(circle, shape=None)
beam1_t = BeamProfileFeature(polygon)
beam1.features.append(beam1_t)



###############################################################################
# Create a model.
###############################################################################
model = Model()

###############################################################################
# Array Beams in an alternating line.
###############################################################################



count : int = 10
for i in range(count):
    beam_i = beam0.copy()
    model.add_element(beam_i)
    T = Translation.from_vector([i*radius*2, 0, 0])
    beam_i.transformation = T

for i in range(count-1):
    beam_i = beam1.copy()
    model.add_element(beam_i)
    T1 = Translation.from_vector([i*radius*2, 0, 0])
    R = Rotation.from_axis_and_angle([0, 0, 1], pi)
    T0 = Translation.from_vector([-radius, -radius, 0])
    beam_i.transformation = T1 * R * T0


    # R = Rotation.from_axis_and_angle([0, 0, 1], pi) if i % 2 == 0 else Rotation.from_axis_and_angle([0, 0, 1], 0)
    # T = 
    # beam_i.transformation = T
    # if i % 2 == 0:
    #     R = Rotation.from_axis_and_angle([0, 0, 1], pi)
    #     beam_i.transformation = beam_i.transformation * R
    # # beam_i.transform(translation=[i*radius*2, 0, 0])
    # # beam_i.transform(rotation=[0, 0, 0.5 * i])



viewer = Viewer()
# viewer.scene.add(polygon)
# viewer.scene.add(Polygon.from_sides_and_radius_xy(20, radius))
# viewer.scene.add(beam_t.elementgeometry)
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)

viewer.show()
