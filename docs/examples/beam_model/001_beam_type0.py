from pathlib import Path
from compas_viewer import Viewer
from compas_grid.elements import BeamProfileElement, BeamProfileFeature
from compas.geometry import Polygon
from compas import json_dump

###############################################################################
# Beam
###############################################################################
radius = 0.15
circle = Polygon.from_sides_and_radius_xy(10, radius)
shape = None
features = []

height = 0.3
width = 0.1
polygon = Polygon(
    [
        [radius, 0, 0],
        [0, radius, 0],
        [-radius, 0, 0],
        [-radius, -height, 0],
        [radius, -height, 0],
    ]
)

feature = BeamProfileFeature(polygon)
features.append(feature)

beam = BeamProfileElement(circle, shape=None, features=features)

###############################################################################
# Serialize
###############################################################################
json_dump(beam, Path(__file__).parent.parent.parent.parent / "data" / "beam_model_001.json")

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
viewer.scene.add(beam.elementgeometry, hide_coplanaredges=True)
viewer.show()
