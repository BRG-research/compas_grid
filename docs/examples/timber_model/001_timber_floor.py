from math import radians
from pathlib import Path

from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Rotation
from compas.geometry import Translation
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import add_vectors
from compas.geometry import angle_vectors
from compas.geometry import subtract_vectors
from compas.geometry import transform_points
from compas.geometry import translate_points
from compas.geometry.transformation import Transformation
from compas.tolerance import TOL
from compas_grid.elements import BeamSquareElement
from compas_grid.elements import BeamArcElement
from compas_grid.elements import BeamVProfileElement
from compas_grid.elements import BlockElement
from compas_grid.elements import CableElement
from compas_grid.elements import ColumnSquareElement
from compas_grid.elements import PlateElement
from compas_model.models import ElementNode
from compas_grid.elements import ColumnHeadCrossElement
from compas_grid.models import GridModel

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/timber_frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]


# =============================================================================
# Model
# =============================================================================
model = Model()
print(lines)
print(surfaces)
grid_model : GridModel = GridModel.from_lines_and_surfaces(lines, surfaces)

# =============================================================================
# Add Column on a CellNetwork Edge
# Add ColumnHead on a CellNetwork Edge
# Add Beams on a CellNetwork Edge
# Add Plates on a CellNetwork Face
# =============================================================================
edges_columns = list(grid_model.cell_network.edges_where({"is_column": True}))  # Order as in the model
edges_beams = list(grid_model.cell_network.edges_where({"is_beam": True}))  # Order as in the model
faces_floors = list(grid_model.cell_network.faces_where({"is_floor": True}))  # Order as in the model

# for i, edge in enumerate(edges_columns):
#     column: ColumnSquareElement = ColumnSquareElement(width=200, depth=200)
#     grid_model.add_column(column, edge)


# for edge in edges_columns:
#    column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
#    grid_model.add_column_head(column_head, edge)
#    break



# Add Four Columns and Their ColumnHeads
for edge in edges_columns:
    column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=100, depth=100, height=400, offset=400)
    grid_model.add_column_head(column_head, edge)

for edge in edges_columns:
    column_square: ColumnSquareElement = ColumnSquareElement(width=200, depth=200)
    grid_model.add_column(column_square, edge)

# Add Four Beams
beam_nodes : list[ElementNode] = []
for i, edge in enumerate(edges_beams):
    if i < 4:
        beam: BeamArcElement = BeamArcElement(200, [400,400,200,200,400,400], [0, 500, 3000-60, 3000+60, 6000-500, 6000])
        beam.transformation = Translation.from_vector([0, 0, -200])
        grid_model.add_beam(beam, edge)
    else:
        beam: BeamVProfileElement = BeamVProfileElement(width0=120, width1=60, depth=200, length=lines[i].length)
        #beam: BeamSquareElement = BeamSquareElement(width=80, depth=200, length=lines[i].length)
        beam.transformation = Translation.from_vector([0, 0, -100])
        grid_model.add_beam(beam, edge)
        if i == 4:
            beam.extend_two_sides(-100,-100)
        else:
            beam.extend_two_sides(-100,-30)

# Add Slab
width = 2870
polygon : Polygon = Polygon([
    [0, 0, 0],
    [width, 0, 0],
    [width, width, 0],
    [0, width, 0],

    ])
plate : PlateElement = PlateElement(polygon, 400)

plate.transformation = Translation.from_vector([30, 30, 3800])
grid_model.add_element(plate)

# # Add Hinges
# beam_nodes : list[ElementNode] = []
# for i in range(8, 11):













# =============================================================================
# Vizualize
# =============================================================================
TOL.lineardeflection = 100
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
for element in list(grid_model.elements()):
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=False)
viewer.show()
