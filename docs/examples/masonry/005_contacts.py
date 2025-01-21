from pathlib import Path

from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

from compas import json_load
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Translation
from compas.geometry import Vector
from compas.geometry.transformation import Transformation
from compas_grid.elements import BeamTProfileElement
from compas_grid.elements import BeamVProfileElement  # noqa: F401
from compas_grid.elements import BlockElement
from compas_grid.elements import CableElement
from compas_grid.elements import ColumnSquareElement

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry = json_load(Path("data/frame.json"))
lines = rhino_geometry["lines"]
barrel_vault = json_load(Path("data/barrel_vault.json"))

# =============================================================================
# Model
# =============================================================================
model = Model()

# =============================================================================
# Add Elements
# =============================================================================

# Add columns
for i in range(0, 4):
    column = ColumnSquareElement(300, 300, lines[i].length)
    column.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(lines[i].start))
    model.add_element(column)

# Add beams
beams = []
for i in range(4, len(lines) - 2):
    beam = BeamTProfileElement(width=300, height=700, step_width_left=75, step_height_left=150, length=lines[i].length)
    point = lines[i].start
    xaxis = Vector.Zaxis().cross(lines[i].vector)
    yaxis = Vector.Zaxis()
    target_frame = Frame(point, xaxis, yaxis)
    X = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame)
    T = Translation.from_vector([0, beam.height * 0.5, 0])
    beam.transformation = X * T
    beam.extend(150)
    model.add_element(beam)
    beams.append(beam)

# Add cables
cables = []
for i in range(6, len(lines)):
    cable = CableElement(length=lines[i].length, radius=20)
    point = lines[i].start
    xaxis = Vector.Zaxis().cross(lines[i].vector)
    yaxis = Vector.Zaxis()
    target_frame = Frame(point, xaxis, yaxis)
    X = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame)
    T = Translation.from_vector([0, beam.height * 0.1, 0])
    cable.transformation = X * T
    cable.extend(200)
    model.add_element(cable)
    cables.append(cable)

# Add barrel vault blocks
blocks = []
for i in range(len(barrel_vault["meshes"])):
    mesh = barrel_vault["meshes"][i]
    frame = barrel_vault["frames"][i]
    mesh.transform(Transformation.from_frame_to_frame(frame, Frame.worldXY()))
    block = BlockElement(shape=mesh, is_support=mesh.attributes["is_support"])
    block.transformation = Translation.from_vector([0, 0, 3800]) * Transformation.from_frame_to_frame(Frame.worldXY(), frame)
    model.add_element(block)
    blocks.append(block)

# =============================================================================
# Add Interactions
# =============================================================================
for beam in beams:
    for block in blocks:
        model.add_interaction(beam, block)
        model.add_modifier(beam, block)  # beam -> cuts -> block

# =============================================================================
# Compute Contacts
# =============================================================================
model.compute_contacts(tolerance=1, minimum_area=1, k=8)

# =============================================================================
# Visualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer = Viewer()

lines = []
for element in list(model.elements()):
    for line in element.modelgeometry.to_lines():
        lines.append(Line(Point(*line[0]), Point(*line[1])))
viewer.scene.add(lines)

for edge in model.graph.edges():
    if model.graph.edge_attribute(edge, "contacts"):
        for contact in model.graph.edge_attribute(edge, "contacts"):
            viewer.scene.add(contact.mesh, facecolor=(0, 255, 0), hide_coplanaredges=True)

viewer.show()
