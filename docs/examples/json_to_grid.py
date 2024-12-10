from compas_model.models import Model

import compas_grid
from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_grid.elements import BeamIProfileElement
from compas_grid.elements import BeamSquareElement
from compas_grid.elements import ColumnHeadCrossElement
from compas_grid.elements import ColumnRoundElement
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
column_square: ColumnSquareElement = ColumnSquareElement(width=300, depth=300)
column_round: ColumnRoundElement = ColumnRoundElement(radius=150, sides=24, height=300)
column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
beam_square: BeamSquareElement = BeamSquareElement(width=300, depth=300)
beam_i_profile: BeamIProfileElement = BeamIProfileElement(width=300, depth=300, thickness=50)
plate: PlateElement = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
cutter: CutterElement = CutterElement()
cutter_model: Model = CutterElement.cutter_element_model()  # A model with one screw.

# Create the Model.
# Default all elements are dirty.
model: GridModel = GridModel.from_lines_and_surfaces(
    columns_and_beams=lines, floor_surfaces=surfaces, column=column_round, column_head=column_head, beam=beam_i_profile, plate=plate, cutter=cutter, cutter_model=cutter_model
)

# Compute interactions.
# Since elements are dirty compute interactions.
geometry_interfaced: list[Mesh] = []
for element in model.elements():
    geometry_interfaced.append(element.compute_interactions(False))

# Change Model Elements.
# Change a column head to round, which will change the is_dirty flag to true.

# Recompute interactions model_geometry for elements with is_dirty flag.

# =============================================================================
# Visualize the model.
# =============================================================================
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()
    viewer_live.clear()
    [viewer_live.add(geometry.scaled(0.001)) for geometry in geometry_interfaced]
    [viewer_live.add(geometry.scaled(0.001)) for geometry in compas_grid.global_property]
    viewer_live.serialize()
    # viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
