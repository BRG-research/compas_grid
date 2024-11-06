from compas import json_load
from compas_grid.grid_model import GridModel
from compas.geometry import Point, Scale, Frame, Line

# Rhino Geometry stored in a JSON file: 
# Columns
# Beams
# DoubleHeights
# Staircase
# References 
rhino_geometry = json_load('data/crea/crea.json')

# Create a GridModel
output = GridModel.from_spacings(
                                 [6000, 6000, 6000, 6000],
                                 [6000, 6000, 6000, 6000, 6000, 6000],
                                 [4725.884, 3800, 3800, 3800, 3800, 3800, 3800, 3800, 3800, 3800],
                                 
                                 ) # 6000*4, 6000*6, 3900*10, 4, 6, 10


temp = []
# for idx, vertex in enumerate(output.vertices()):
#     temp.append(Point(*output.vertex_coordinates(vertex)),
#                 # name=str(idx) + " " + str(output.vertex_attributes(vertex)),
#                 # color=output.vertex_attribute(vertex, "color")[2]
#                 )

# for edge in output.edges():
#     temp.append(
#         output.edge_line(edge),
#         # color=output.edge_attribute(edge, "color"),
#         # linewidth=output.edge_attribute(edge, "axis") * 2 + 3,
#         # name=str(output.edge_attributes(edge)
#         ),

for face in output.faces():
    temp.append(
        output.face_polygon(face), 
        # color=output.face_attribute(face, "color"), 
        # name=str(output.face_attributes(face))
        )

# for cell in output.cells():
#     scale: Scale = Scale.from_factors([0.75, 0.75, 0.75], Frame(output.cell_center(cell), [1, 0, 0], [0, 1, 0]))
#     temp.append(
#         output.cell_to_mesh(cell).transformed(scale), 
#         # name=str(output.cell_attributes(cell)), 
#         # color=output.cell_attribute(cell, "color")[2]
#         )



# ViewerLive
try:
    from compas_snippets.viewer_live import ViewerLive
    # ViewerLive.run()
    ViewerLive.clear()
    for key, geometries in rhino_geometry.items():
        ViewerLive.extend(geometries)
    ViewerLive.extend(temp)
    ViewerLive.serialize()
except ImportError:
    print("compas_snippets.viewer_live is not available. Skipping viewer execution.")