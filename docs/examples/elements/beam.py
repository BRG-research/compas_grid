from compas_viewer import Viewer
from compas_viewer.config import Config

from compas_grid.elements import BeamElement
from compas_grid.elements import BeamTProfileElement

beam_t: BeamTProfileElement = BeamTProfileElement(
    width=0.2,
    height=0.3,
    step_height_left=0.1,
    step_height_right=0.1,
    step_width_left=0.05,
    step_width_right=0.05,
    length=6,
)

beam = BeamElement(
    width=0.2,
    height=0.3,
    length=6,
)

config = Config()

viewer = Viewer(config=config)
viewer.scene.add(beam_t.elementgeometry)
viewer.scene.add(beam.elementgeometry)

viewer.show()
