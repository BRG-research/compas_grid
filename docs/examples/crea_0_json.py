from compas import json_load
from compas_grid.grid_model import GridModel
from compas.geometry import Point, Scale, Frame, Line
from compas_viewer import Viewer
from compas_viewer.scene import ViewerSceneObject

viewer: Viewer = Viewer(show_grid=False)

# Rhino Geometry stored in a JSON file: 
# Columns
# Beams
# DoubleHeights
# Staircase
# References 
rhino_geometry = json_load('data/crea/crea.json')

for key, geometries in rhino_geometry.items():
    viewer_scene_object : ViewerSceneObject = viewer.scene.add(geometries)
    viewer_scene_object.name = key

# Create a GridModel
output = GridModel.from_spacings(
                                 [6000, 6000, 6000, 6000],
                                 [6000, 6000, 6000, 6000, 6000, 6000],
                                 [4725.884, 3800, 3800, 3800, 3800, 3800, 3800, 3800, 3800, 3800],
                                 
                                 ) # 6000*4, 6000*6, 3900*10, 4, 6, 10




# for idx, vertex in enumerate(output.vertices()):
#     viewer.scene.add(
#         Point(*output.vertex_coordinates(vertex)), 
#         name=str(idx) + " " + str(output.vertex_attributes(vertex)["uvw"]), 
#         # color=output.vertex_attribute(vertex, "color")[2]
#     )

# for edge in output.edges():
#     viewer.scene.add(
#         output.edge_line(edge),
#         # color=output.edge_attribute(edge, "color"),
#         linewidth=1,
#         name=str(output.edge_attributes(edge)["uvw"]),
#     )

# for face in output.faces():
#     viewer.scene.add(
#         output.face_polygon(face), 
#         # color=output.face_attribute(face, "color"), 
#         name=str(output.face_attributes(face)["uvw"])
#         )

# for cell in output.cells():
#     scale: Scale = Scale.from_factors([0.75, 0.75, 0.75], Frame(output.cell_center(cell), [1, 0, 0], [0, 1, 0]))
#     viewer.scene.add(output.cell_to_mesh(cell).transformed(scale), name=str(output.cell_attributes(cell)), color=output.cell_attribute(cell, "color")[2])

viewer.show()