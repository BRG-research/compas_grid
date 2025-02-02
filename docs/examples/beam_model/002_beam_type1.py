from compas import json_dump
from pathlib import Path
from compas_viewer import Viewer
from compas_grid.elements import BeamProfileElement, BeamProfileFeature
from compas.geometry import Polygon

###############################################################################
# Beam
###############################################################################
radius = 0.15
circle = Polygon.from_sides_and_radius_xy(10, radius)
shape = None
features = []

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

feature = BeamProfileFeature(polygon)
features.append(feature)

beam = BeamProfileElement(circle, shape=None, features=features)

###############################################################################
# Serialize
###############################################################################
json_dump(beam, Path(__file__).parent.parent.parent.parent / "data" / "beam_model_002.json")

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
viewer.scene.add(beam.elementgeometry, hide_coplanaredges=True)
viewer.show()
