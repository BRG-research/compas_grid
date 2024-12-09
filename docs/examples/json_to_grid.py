from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_grid import global_property
from compas_grid.elements import BeamElement
from compas_grid.elements import ColumnHeadCrossElement
from compas_grid.elements import ColumnSquareElement
from compas_grid.elements import CutterElement
from compas_grid.elements import PlateElement
from compas_grid.models import GridModel

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load("data/crea/crea_4x4.json")
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================

# Create Elements that will be used in the model.
column: ColumnSquareElement = ColumnSquareElement(width=300, depth=300)
column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
beam: BeamElement = BeamElement(width=300, depth=300)
plate: PlateElement = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
cutter: CutterElement = CutterElement()

# Create the Model.
model: GridModel = GridModel.from_lines_and_surfaces(
    columns_and_beams=lines, floor_surfaces=surfaces, column=column, column_head=column_head, beam=beam, plate=plate, cutter=cutter
)

# Compute interactions.
geometry_interfaced: list[Mesh] = []
for element in model.elements():
    geometry_interfaced.append(element.compute_interactions(False))

# =============================================================================
# Visualize the model.
# =============================================================================
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()
    viewer_live.clear()
    [viewer_live.add(geometry.scaled(0.001)) for geometry in geometry_interfaced]
    [viewer_live.add(geometry.scaled(0.001)) for geometry in global_property]
    viewer_live.serialize()
    # viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
