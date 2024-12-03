from compas import json_load
from compas.datastructures import Mesh
from compas_viewer import Viewer

mesh_and_plane = json_load("/home/petras/brg/2_code/compas_grid/data/crea/error.json")
mesh_and_plane[1].translate([-0.001, 0.001, 0])

# print(mesh_and_plane[0].slice(mesh_and_plane[1]))


viewer = Viewer()
# viewer.scene.add(mesh_and_plane[0].scaled(0.001))
# viewer.scene.add(mesh_and_plane[1].scaled(0.001))
viewer.scene.add(mesh_and_plane[0].slice(mesh_and_plane[1])[0].scaled(0.001))

viewer.show()
