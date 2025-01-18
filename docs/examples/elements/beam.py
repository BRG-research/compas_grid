from compas_viewer import Viewer
from compas_viewer.config import Config

from compas.tolerance import TOL
from compas_grid.elements import BeamArcElement
from compas_grid.elements import BeamTProfileElement

beam: BeamTProfileElement = BeamTProfileElement(
    width=0.2,
    height=0.3,
    step_height_left=0.1,
    step_height_right=0.1,
    step_width_left=0.05,
    step_width_right=0.05,
    length=6,
)

beam_arc : BeamArcElement = BeamArcElement()

# TOL.lineardeflection = 1000

config = Config()

# config.camera.target = [0, 0.1, 0]
# config.camera.position = [0, -0.2, 7]
# config.camera.near = 0.1
# config.camera.far = 10

viewer = Viewer(config=config)
viewer.scene.add(beam.elementgeometry)
viewer.scene.add(beam_arc.elementgeometry)


viewer.show()
