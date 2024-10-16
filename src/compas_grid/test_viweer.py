from compas.geometry import Box
from compas_viewer import Viewer
from compas_viewer.components import Button

box = Box(1)

viewer = Viewer()

boxobj = viewer.scene.add(box)


def delete_box():
    if boxobj in viewer.scene.objects:
        viewer.scene.remove(boxobj)
        viewer.renderer.update()
        print(boxobj, "deleted from scene")
    else:
        print(boxobj, "is already deleted from scene")


viewer.ui.sidedock.show = True
viewer.ui.sidedock.add(Button(text="Delete Box", action=delete_box))
viewer.show()