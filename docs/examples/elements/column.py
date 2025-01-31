from compas_viewer import Viewer

from compas_grid.elements import ColumnElement

column = ColumnElement()


viewer = Viewer()
viewer.scene.add(column.elementgeometry)
viewer.scene.add(column.center_line)

viewer.show()
