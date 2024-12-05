from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_grid.elements import ColumnSquareElement
from compas_grid.elements import ColumnHeadElement
from compas_grid.elements import BeamElement
from compas_grid.elements import PlateElement
from compas_grid.models import GridModel
from compas_grid import global_property


#######################################################################################################
# Geometry from Rhino.
#######################################################################################################
rhino_geometry: dict[str, list[any]] = json_load("data/crea/crea_4x4.json")
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

#######################################################################################################
# First create examples with the same type.
# Then try to see if you can pass the clas type.
#######################################################################################################

column: ColumnSquareElement = ColumnSquareElement(width=300, depth=300, height=1)  # Scaled 1D vertically
# column_head : ColumnHeadElement = ColumnHeadElement.from_column_head_cross_shape( v=None, e=None, f=None, width=150, depth=150, height=150, offset=210) # Recreated from axes
# beam : BeamElement = BeamElement.from_square_section(width=150, depth=150, height=1) # Scaled 1D vertically
# plate : PlateElement = PlateElement.from_polygon_and_thickness(Polygon([[-0.5, -0.5, 0], [-0.5, 0.5, 0], [0.5, 0.5, 0], [0.5, -0.5, 0]]), 200) # Scale 2D

#######################################################################################################
# Create the model.
# Compute geometry inetaractions.
#######################################################################################################

model: GridModel = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces, column=column)

local_transform = False
geometry_interfaced = []
for element in model.elements():
    geometry_interfaced.append(element.compute_interactions(local_transform))

#######################################################################################################
# Visualize the model.
#######################################################################################################
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()
    viewer_live.clear()

    for geometry in geometry_interfaced:
        viewer_live.add(geometry.scaled(0.001))

    for geo in global_property:
        viewer_live.add(geo.scaled(0.001))

    viewer_live.serialize()
    # viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
