from compas_viewer import Viewer
from compas_grid.elements import BeamProfileElement
from compas.geometry import Polygon

###############################################################################
# Beam
###############################################################################
radius = 0.15
circle = Polygon.from_sides_and_radius_xy(10, radius)
shape = None
features = []
beam = BeamProfileElement(circle, shape=None, features=features)

###############################################################################
# Vizualize
###############################################################################

viewer = Viewer()
viewer.scene.add(beam.elementgeometry, hide_coplanaredges=True)
viewer.show()
