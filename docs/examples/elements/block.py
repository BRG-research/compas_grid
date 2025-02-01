from compas_viewer import Viewer

from compas_grid.elements import BlockElement
from compas.geometry import Box
from compas_model.models import Model

block = BlockElement.from_box(Box(1))

model = Model()
model.add_element(block)
print(block.aabb)

viewer = Viewer()
viewer.scene.add(block.elementgeometry)
viewer.show()
