from compas_viewer import Viewer
from compas_grid.elements import CableElement

cable = CableElement()

viewer = Viewer()
viewer.scene.add(cable.elementgeometry)
viewer.scene.add(cable.axis)

viewer.show()
