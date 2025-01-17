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
from compas.geometry import Vector
from compas.geometry import add_vectors
from compas.geometry import angle_vectors
from compas.geometry import subtract_vectors
from compas.geometry import transform_points
from compas.geometry import translate_points
from compas.geometry.transformation import Transformation
from compas.tolerance import TOL
from compas_grid.elements import BeamTProfileElement
from compas_grid.elements import BlockElement
from compas_grid.elements import CableElement
from compas_grid.elements import ColumnSquareElement

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]

# =============================================================================
# Model
# =============================================================================
model = Model()

# Add columns
for i in range(0, 4):
    column: ColumnSquareElement = ColumnSquareElement(300, 300, lines[i].length)
    column.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(lines[i].start))
    model.add_element(column)


# Add two beams
for i in range(4, len(lines) - 2):
    beam: BeamTProfileElement = BeamTProfileElement(width=300, height=700, step_width_left=75, step_height_left=150, length=lines[i].length)
    target_frame: Frame = Frame(lines[i].start, Vector.Zaxis().cross(lines[i].vector), Vector.Zaxis())
    beam.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame) * Translation.from_vector([0, beam.height * 0.5, 0])
    beam.extend(150)
    model.add_element(beam)

# Add two cables
for i in range(6, len(lines)):
    cable: CableElement = CableElement(length=lines[i].length, radius=10)
    target_frame: Frame = Frame(lines[i].start, Vector.Zaxis().cross(lines[i].vector), Vector.Zaxis())
    cable.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame) * Translation.from_vector([0, beam.height * 0.1, 0])
    cable.extend(200)
    model.add_element(cable)




def from_barrel_vault(
    span: float = 6.0,
    length: float = 6.0,
    thickness: float = 0.25,
    rise: float = 0.6,
    vou_span: int = 9,
    vou_length: int = 6,
    zero_is_centerline_or_lowestpoint: bool = False,
) -> list[BlockElement]:
    """
    Creates block elements from the barrel vault geometry.

    Parameters
    ----------
    span : float
        span of the vault
    length : float
        length of the vault perpendicular to the span
    thickness : float
        thickness of the vault
    rise : float
        rise of the vault from 0.0 to middle axis of the vault thickness
    vou_span : int
        number of voussoirs in the span direction
    vou_length : int
        number of voussoirs in the length direction
    zero_is_centerline_or_lowestpoint : bool
        if True, the lowest point of the vault is at the center line of the arch, otherwise the center line of the vault is lowest mesh z-coordinate.

    Returns
    -------
    list[:class:`compas.datastructures.Mesh`]
    A list of meshes representing the geometry of the barrel vault.
    """
    radius: float = rise / 2 + span**2 / (8 * rise)
    top: list[float] = [0, 0, rise]
    left: list[float] = [-span / 2, 0, 0]
    center: list[float] = [0.0, 0.0, rise - radius]
    vector: list[float] = subtract_vectors(left, center)
    springing: float = angle_vectors(vector, [-1.0, 0.0, 0.0])
    sector: float = radians(180) - 2 * springing
    angle: float = sector / vou_span

    a: list[float] = [0, -length / 2, rise - (thickness / 2)]
    d: list[float] = add_vectors(top, [0, -length / 2, (thickness / 2)])

    R: Rotation = Rotation.from_axis_and_angle([0, 1.0, 0], 0.5 * sector, center)
    bottom: list[list[float]] = transform_points([a, d], R)
    brick_pts: list[list[list[float]]] = []
    for i in range(vou_span + 1):
        R_angle: Rotation = Rotation.from_axis_and_angle([0, 1.0, 0], -angle * i, center)
        points: list[list[float]] = transform_points(bottom, R_angle)
        brick_pts.append(points)

    depth: float = length / vou_length
    grouped_data: list[list[float]] = [pair[0] + pair[1] for pair in zip(brick_pts, brick_pts[1:])]

    meshes: list[Mesh] = []
    for i in range(vou_length):
        for l, group in enumerate(grouped_data):  # noqa: E741
            is_support: bool = l == 0 or l == (len(grouped_data) - 1)
            if l % 2 == 0:
                point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
                point_list: list[list[float]] = [
                    [group[0][0], group[0][1] + (depth * i), group[0][2]],
                    [group[1][0], group[1][1] + (depth * i), group[1][2]],
                    [group[2][0], group[2][1] + (depth * i), group[2][2]],
                    [group[3][0], group[3][1] + (depth * i), group[3][2]],
                ]
                p_t: list[list[float]] = translate_points(point_l, [0, depth * (i + 1), 0])
                vertices: list[list[float]] = point_list + p_t
                faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                mesh.attributes["is_support"] = is_support
                meshes.append(mesh)
            else:
                point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
                points_base: list[list[float]] = translate_points(point_l, [0, depth / 2, 0])
                points_b_t: list[list[float]] = translate_points(points_base, [0, depth * i, 0])
                points_t: list[list[float]] = translate_points(points_base, [0, depth * (i + 1), 0])
                vertices: list[list[float]] = points_b_t + points_t
                if i != vou_length - 1:
                    faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                    mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                    mesh.attributes["is_support"] = is_support
                    meshes.append(mesh)

    for l, group in enumerate(grouped_data):  # noqa: E741
        is_support: bool = l == 0 or l == (len(grouped_data) - 1)
        if l % 2 != 0:
            point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
            p_t: list[list[float]] = translate_points(point_l, [0, depth / 2, 0])
            vertices: list[list[float]] = point_l + p_t
            faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
            mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
            mesh.attributes["is_support"] = is_support
            meshes.append(mesh)

            point_f: list[list[float]] = translate_points(point_l, [0, length, 0])
            p_f: list[list[float]] = translate_points(point_f, [0, -depth / 2, 0])
            vertices: list[list[float]] = p_f + point_f
            faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
            mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
            mesh.attributes["is_support"] = is_support
            meshes.append(mesh)

    # Find the lowest z-coordinate and move all the block to zero.
    if not zero_is_centerline_or_lowestpoint:
        min_z: float = min([min(mesh.vertex_coordinates(key)[2] for key in mesh.vertices()) for mesh in meshes])
        for mesh in meshes:
            mesh.translate([0, 0, -min_z])


    # Translate blocks to xy frame and create blockmodel.
    blocks = []

    for mesh in meshes:
        origin: Point = mesh.face_polygon(5).frame.point
        xform: Transformation = Transformation.from_frame_to_frame(
            Frame(origin, mesh.vertex_point(0) - mesh.vertex_point(2), mesh.vertex_point(4) - mesh.vertex_point(2)), Frame.worldXY()
        )
        mesh_xy: Mesh = mesh.transformed(xform)

        brep : Brep = Brep.from_polygons(mesh_xy.to_polygons())

        block: BlockElement = BlockElement(shape=brep, is_support=mesh_xy.attributes["is_support"])
        block.transformation = xform.inverse()
        blocks.append(block)

    return blocks

# Add blocks, by moving them by the height of the first column.
block_elements: list[BlockElement] = from_barrel_vault(span=6000, length=6000, thickness=250, rise=600, vou_span=5, vou_length=5)

for block in block_elements:
    block.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame([0, 0, lines[0].end[2]])) * block.transformation
    model.add_element(block)


# Add Interactions
# for element in list(model.elements()):
#     if isinstance(element, BeamTProfileElement):
#         for block in block_elements:
#             model.add_modifier(element, block)  # beam -> cuts -> block

# for element in list(model.elements()):
#     if isinstance(element, CableElement):
#         for beam in list(model.elements()):
#             if isinstance(beam, BeamTProfileElement):
#                 model.add_modifier(element, beam)  # cable -> cuts -> beam

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
for element in list(model.elements()):
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=False)
viewer.show()
