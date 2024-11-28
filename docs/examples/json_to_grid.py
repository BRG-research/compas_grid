from compas.geometry import Line
from compas.datastructures import Mesh
from compas import json_load
from compas_snippets.viewer_live import ViewerLive
from compas_grid.model import GridModel


#######################################################################################################
# Geometry from Rhino.
#######################################################################################################
rhino_geometry: dict[str, list[any]] = json_load("data/crea/crea_4x4.json")
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

#######################################################################################################
# Create the model.
#######################################################################################################
model = GridModel.from_lines_and_surfaces(lines, surfaces)
model.cut()

#######################################################################################################
# Visualize the model.
#######################################################################################################
viewer_live = ViewerLive()

for element in model.elements():
    geometry = element.geometry
    geometry.name = element.name
    viewer_live.add(geometry.scaled(0.001))

for geo in model.all_geo:
    viewer_live.add(geo.scaled(0.001))

viewer_live.serialize()
# viewer_live.run()
