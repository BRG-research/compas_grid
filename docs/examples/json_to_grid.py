from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_grid.models.model_grid import GridModel
from compas_grid.elements import ColumnElement, BeamElement, PlateElement
import compas_grid

#######################################################################################################
# Geometry from Rhino.
#######################################################################################################
rhino_geometry: dict[str, list[any]] = json_load("data/crea/crea_4x4.json")
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

#######################################################################################################
# Create the model.
# Compute geometry inetaractions.
#######################################################################################################


model = GridModel.from_lines_and_surfaces(lines, surfaces)

geometry_interfaced = []
local_transform = False
for element in model.elements():
    geometry_interfaced.append(element.compute_interactions(local_transform=local_transform))

#######################################################################################################
# Visualize the model.
#######################################################################################################
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()
    viewer_live.clear()

    for geometry in geometry_interfaced:
        viewer_live.add(geometry.scaled(0.001))

    for geo in compas_grid.global_property:
        viewer_live.add(geo.scaled(0.001))

    viewer_live.serialize()
    # viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
