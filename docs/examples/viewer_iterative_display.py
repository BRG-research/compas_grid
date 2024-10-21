from typing import *
from compas_viewer import Viewer
from compas import json_load, json_dump
from compas.geometry import Box


viewer: Viewer = Viewer(show_grid=False)


if __name__ == "__main__":
    viewer.config.renderer.show_grid = False
    viewer.config.window.width = 2560
    viewer.config.window.height = 1600

    boxobj = viewer.scene.add(Box(1))

    @viewer.on(interval=1000)
    def reload(frame):

        # make objects global
        global viewer
        global boxobj
        
        if json_load("docs/examples/has_update.json") == "false":
            return
        

        json_dump("false", "docs/examples/has_update.json")

        # read objects from
        for obj in viewer.scene.objects:
            viewer.scene.remove(obj)
        viewer.renderer.update()
        print(obj, "deleted from scene")
        
        print("reading from geometry_list.json")
        new_geometry = json_load("docs/examples/geometry_list.json")
        for geo in new_geometry:
            new_object = viewer.scene.add(geo)
            new_object.init()
        

        viewer.renderer.update()

        # update renderer
        viewer.ui.init()
        print(viewer.scene.objects)

    viewer.show()