from typing import *
from compas import json_dump
from compas.colors import Color
from compas.colors import ColorMap
from compas.datastructures import VolMesh
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Scale
from compas_model.models import Model
from compas_viewer import Viewer
from compas import json_load
from compas.geometry import Box


class GridModel(Model):
    @classmethod
    def __from_data__(cls, data: dict) -> "GridModel":
        model: GridModel = super(GridModel, cls).__from_data__(data)
        # todo: implement the rest of data
        return model

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(GridModel, self).__init__()

    def __str__(self) -> str:
        return "GridModel"

    @staticmethod
    def sort_faces_by_axis(centers: List[Point], faces: List[int], axis_index: int) -> List[int]:
        return [x for _, x in sorted(zip(centers, faces), key=lambda pair: pair[0][axis_index])]

    @staticmethod
    def set_face_attributes(volmesh: VolMesh, face: int, axis: str, storey: int, color_func: Callable[[float], Color], nz: int) -> None:
        volmesh.face_attribute(face, "axis", axis)
        volmesh.face_attribute(face, "storey", str(storey))
        volmesh.face_attribute(face, "color", color_func(1 / (nz + 1) * storey))

        fv: List[int] = list(volmesh.face_vertices(face))
        fe: List[Tuple[int, int]] = [(fv[i], fv[(i + 1) % len(fv)]) for i in range(len(fv))]
        strips: Dict[str, float] = {axis: float("inf") for axis in ["x", "y", "z"] if axis != axis}

        for e in fe:
            edge_axis: str = volmesh.edge_attribute(e, "axis")
            strip: float = volmesh.edge_attribute(e, "strip")
            strips[edge_axis] = min(strip, strips[edge_axis])

        volmesh.face_attribute(face, "strip", strips)

    @classmethod
    def from_meshgrid(cls, dx: float = 8, dy: float = 8, dz: float = 3.5 * 7, nx: int = 5, ny: int = 3, nz: int = 10) -> List[VolMesh]:
        #######################################################################################################
        # 3D Grid, translate the grid to the center.
        # Vertex order
        # 2 5 8 11
        # 1 4 7 10
        # 0 3 6 9
        #######################################################################################################
        volmesh: VolMesh = VolMesh.from_meshgrid(dx, dy, dz, nx, ny, nz)
        volmesh.translate([dx * -0.5, dy * -0.5, 0])

        #######################################################################################################
        # Color map for display of UVW coordinates.
        #######################################################################################################
        cmap_red: ColorMap = ColorMap.from_two_colors(Color.from_hex("#ff0074"), Color.from_hex("#DDDDDD"), diverging=True)
        cmap_green: ColorMap = ColorMap.from_two_colors(Color.from_hex("#40B5AD"), Color.from_hex("#DDDDDD"))
        cmap_blue: ColorMap = ColorMap.from_two_colors(Color.from_hex("#0096FF"), Color.from_hex("#DDDDDD"))

        #######################################################################################################
        # Assign Node U, V, W identification to the vertices.
        #######################################################################################################

        vertex_list: List[int] = list(volmesh.vertices())
        number_of_vertices_xy: int = (nx + 1) * (ny + 1)
        for w in range(nz + 1):
            for u in range(nx + 1):
                for v in range(ny + 1):
                    vertex: int = vertex_list[v + u * (ny + 1) + number_of_vertices_xy * w]
                    volmesh.vertex_attribute(vertex, "uvw", [u, v, w])
                    volmesh.vertex_attribute(vertex, "color", [cmap_red(1 / (nx + 1) * u), cmap_green(1 / (ny + 1) * v), cmap_blue(1 / (nz + 1) * w)])

        #######################################################################################################
        # Assign Edge U, V, W identification to the edges.
        #######################################################################################################

        def set_edge_attributes(volmesh: VolMesh, e: Tuple[int, int], u: int, v: int, w: int, axis: int, color_func: Callable[[float], Color]) -> None:
            volmesh.edge_attribute(e, "uvw", [u, v, w])
            volmesh.edge_attribute(e, "axis", axis)
            volmesh.edge_attribute(e, "color", color_func(1 / [nx, ny, nz][axis] * [u, v, w][axis]))

        # Z-Axis
        for w in range(nz):
            for u in range(nx + 1):
                for v in range(ny + 1):
                    node: int = v + u * (ny + 1)
                    e: Tuple[int, int] = (vertex_list[node + number_of_vertices_xy * w], vertex_list[node + number_of_vertices_xy * (w + 1)])
                    set_edge_attributes(volmesh, e, u, v, w, 2, cmap_blue)

        # Y-Axis
        for w in range(nz + 1):
            for u in range(nx + 1):
                for v in range(ny):
                    e: Tuple[int, int] = (vertex_list[v + u * (ny + 1) + number_of_vertices_xy * w], vertex_list[v + u * (ny + 1) + 1 + number_of_vertices_xy * w])
                    set_edge_attributes(volmesh, e, u, v, w, 1, cmap_green)

        # X-Axis
        for w in range(nz + 1):
            for u in range(nx):
                for v in range(ny + 1):
                    e: Tuple[int, int] = (vertex_list[v + u * (ny + 1) + number_of_vertices_xy * w], vertex_list[v + u * (ny + 1) + ny + 1 + number_of_vertices_xy * w])
                    set_edge_attributes(volmesh, e, u, v, w, 0, cmap_red)

        #######################################################################################################
        # Assign Face U, V, W identification to the edges.
        # Cells and polygons have no topological grid ordering.
        # Sorting is done through geometrical sorting of polygon centers.:
        # 1. Z-Axis 0 and -1
        # 2. Y-Axis 0 and -1
        # 3. X-Axis 0 and -1
        #######################################################################################################

        cells: List[int] = list(volmesh.cells())
        cells_count_in_storey: int = nx * ny

        storey: int = -1
        for i in range(len(cells)):
            if i % cells_count_in_storey == 0:
                storey += 1

            # Get the center of each face and sort them by axis.
            centers: List[Point] = []
            for face in volmesh.cell_faces(cells[i]):
                centers.append(volmesh.face_center(face))

            # Sort the faces by axis.
            sorted_faces: List[int] = [x for _, x in sorted(zip(centers, volmesh.cell_faces(cells[i])), key=lambda pair: pair[0][2])]
            faces_z_axis: List[int] = [sorted_faces[0], sorted_faces[-1]]

            sorted_faces: List[int] = [x for _, x in sorted(zip(centers, volmesh.cell_faces(cells[i])), key=lambda pair: pair[0][0])]
            faces_y_axis: List[int] = [sorted_faces[0], sorted_faces[-1]]

            sorted_faces: List[int] = [x for _, x in sorted(zip(centers, volmesh.cell_faces(cells[i])), key=lambda pair: pair[0][1])]
            faces_x_axis: List[int] = [sorted_faces[0], sorted_faces[-1]]

            def set_face_attributes(volmesh: VolMesh, f: int, uvw: List[int], axis: int, color_func: Callable[[float], Color]) -> None:
                volmesh.face_attribute(f, "uvw", uvw)
                volmesh.face_attribute(f, "axis", axis)
                volmesh.face_attribute(f, "color", color_func(1 / [nx, ny, nz][axis] * uvw[axis]))

            for face in faces_z_axis:
                fv: List[int] = list(volmesh.face_vertices(face))
                min_vertex_id: int = min(fv)
                set_face_attributes(volmesh, face, volmesh.vertex_attribute(min_vertex_id, "uvw"), 2, cmap_blue)

            for face in faces_y_axis:
                fv: List[int] = list(volmesh.face_vertices(face))
                min_vertex_id: int = min(fv)
                set_face_attributes(volmesh, face, volmesh.vertex_attribute(min_vertex_id, "uvw"), 1, cmap_green)

            for face in faces_x_axis:
                fv: List[int] = list(volmesh.face_vertices(face))
                min_vertex_id: int = min(fv)
                set_face_attributes(volmesh, face, volmesh.vertex_attribute(min_vertex_id, "uvw"), 0, cmap_red)

        #######################################################################################################
        # Assign Cells U, V, W identification to the edges.
        # Cells are essentially like vertices.
        # Take the lowest coordinate in u,v,w from vertex and assign to cell.
        #######################################################################################################
        for cell in cells:
            cell_vertices: List[int] = list(volmesh.cell_vertices(cell))
            min_uvw: List[int] = [nx, ny, nz]
            for vertex in cell_vertices:
                uvw: List[int] = volmesh.vertex_attribute(vertex, "uvw")
                min_uvw = [min(uvw[i], min_uvw[i]) for i in range(3)]
            volmesh.cell_attribute(cell, "uvw", min_uvw)
            volmesh.cell_attribute(cell, "color", [cmap_red(1 / (nx) * min_uvw[0]), cmap_green(1 / (ny) * min_uvw[1]), cmap_blue(1 / (nz) * min_uvw[2])])

        return [volmesh]

    @classmethod
    def from_fan(
        cls,
        dx=6,
        dy=6,
        dz=3,
        column_width=0.4,
        column_depth=0.4,
        column_head_width=0.96,
        column_head_depth=0.96,
        column_head_height=0.475,
        plate_width=3,
        plate_depth=3,
        plate_height=0.04,
    ) -> None:
        # Create a model.
        model = Model()
        geometry = []

        # Create Main Frames
        frame_origin = Frame(Point(0, 0, 0), [1, 0, 0], [0, 1, 0], name="frame_origin")
        frame_column = Frame(Point(0, 0, 0), [1, 0, 0], [0, 1, 0], name="frame_column")
        frame_floor = Frame(Point(0, 0, dz), [1, 0, 0], [0, 1, 0], name="frame_floor")
        frame_panel = Frame(Point(0, 0, dz + column_head_height), [1, 0, 0], [0, 1, 0], name="frame_panel")
        frame_beam0 = Frame(Point(0, 0, dz + column_head_height), [0, 1, 0], [0, 0, 1], name="frame_beam0")
        frame_beam1 = Frame(Point(0, 0, dz + column_head_height), [-1, 0, 0], [0, 0, 1], name="frame_beam1")
        frame_beam_cut0 = Frame(Point(dx * 0.5, 0, dz + column_head_height), [0, 1, 0], [0, 0, 1], name="frame_beam_cut0")
        frame_beam_cut1 = Frame(Point(column_head_width * 0.5, 0, dz + column_head_height), [0, 1, 0], [0, 0, 1], name="frame_beam_cut1")
        frame_beam_cut2 = Frame(Point(0, dx * 0.5, dz + column_head_height), [1, 0, 0], [0, 0, 1], name="frame_beam_cut2")
        frame_beam_cut3 = Frame(Point(0, column_head_depth * 0.5, dz + column_head_height), [1, 0, 0], [0, 0, 1], name="frame_beam_cut3")

        # Number of interpolation steps
        num_steps = 12

        # Interpolated frames
        interpolated_frames_xform0 = []
        interpolated_frames0 = []
        interpolated_frames_xform1 = []
        interpolated_frames1 = []

        # Calculate the angle between the y-axes of the two frames

        angle = frame_beam0.zaxis.angle(frame_beam1.zaxis)

        # Interpolate the frames
        from compas.geometry import Rotation
        from compas.geometry import Transformation

        for i in range(num_steps + 1):
            t = i / num_steps
            rotation = Rotation.from_axis_and_angle(frame_beam0.yaxis, angle * t, point=frame_beam0.point)
            if i < num_steps + 0 - (int)(num_steps * 0.5):
                interpolated_frame = frame_beam0.transformed(rotation)
                interpolated_frames0.append(interpolated_frame)
                interpolated_frames_xform0.append(Transformation.from_frame(interpolated_frame))
            else:
                interpolated_frame = frame_beam0.transformed(rotation)
                interpolated_frames1.append(interpolated_frame)
                interpolated_frames_xform1.append(Transformation.from_frame(interpolated_frame))

        geometry.append(frame_column)
        geometry.append(frame_floor)
        geometry.append(frame_panel)
        geometry.append(frame_beam0)
        geometry.append(frame_beam1)
        geometry.append(frame_beam_cut0)
        geometry.append(frame_beam_cut1)
        geometry.append(frame_beam_cut2)
        geometry.append(frame_beam_cut3)
        # geometry.extend(interpolated_frames)

        # Create ColumnElements.
        from compas_grid.element_column import ColumnElement
        from compas.geometry import Translation
        from compas.geometry import Transformation

        column = ColumnElement.from_square_section(width=column_width, depth=column_depth, height=dz)

        T = [Transformation.from_frame(frame_column)]

        for i in T:
            model.add_element(column.transformed(i))

        # Create ColumnHeadElements.
        from compas_grid.element_column_head import ColumnHeadElement

        column_head = ColumnHeadElement.from_box(width=column_head_width, depth=column_head_depth, height=column_head_height)

        T = [Transformation.from_frame(frame_floor)]

        for i in T:
            model.add_element(column_head.transformed(i))

        # Create PlateElements.
        from compas_grid.element_plate import PlateElement

        plate = PlateElement.from_width_depth_thickness(dx * 0.5, dy * 0.5, thickness=plate_height)
        T = [Transformation.from_frame(frame_panel)]
        for i in T:
            model.add_element(plate.transformed(i))

        # Create BeamTaperedElements.
        from compas_grid.element_beam_tapered import BeamTaperedElement

        beam = BeamTaperedElement.from_cross_sections(width=plate_height, depth_0=0.5, depth_1=0.1, height=dx * 0.72)

        for idx, xform in enumerate(interpolated_frames_xform0):
            from compas.geometry import Transformation

            T = Transformation.from_frame_to_frame(interpolated_frames0[idx], frame_origin)
            temp0 = frame_beam_cut0.transformed(T)
            temp1 = frame_beam_cut1.transformed(T)
            b = beam.transformed(xform)

            g0, g1 = b.compute_top_and_bottom_polygons(temp0, temp1)
            geometry.append(temp0)
            geometry.append(temp1)
            b.shape = b.compute_shape()
            element_node = model.add_element(b)

        for idx, xform in enumerate(interpolated_frames_xform1):
            from compas.geometry import Transformation

            T = Transformation.from_frame_to_frame(interpolated_frames1[idx], frame_origin)
            temp0 = frame_beam_cut2.transformed(T)
            temp1 = frame_beam_cut3.transformed(T)
            b = beam.transformed(xform)

            g0, g1 = b.compute_top_and_bottom_polygons(temp0, temp1)
            geometry.append(temp0)
            geometry.append(temp1)
            b.shape = b.compute_shape()
            element_node = model.add_element(b)

        # Array of elements
        geo_to_array = []
        for e in model.elements():
            geo_to_array.append(e.compute_geometry().copy())
            geo_to_array[-1].name = e.name

        import math

        for i in range(4):
            T = Rotation.from_axis_and_angle([0, 0, 1], i * math.pi * 0.5, point=[dx * 0.0, dy * 0.0, 0])

            for g in geo_to_array:
                geometry.append(g.copy().transformed(T))

        # Serialize the geometry.+(column_head_depth-column_depth)*0.5

        # for e in model.elements():
        #     geometry.append(e.compute_geometry())
        from compas_grid.viewer import serialize

        serialize(geometry)


if __name__ == "__main__":
    GridModel.from_fan()

# def add_objects_to_scene(viewer: Any, output: Any) -> None:
#     if isinstance(output, list):
#         for item in output:
#             add_objects_to_scene(viewer, item)
#     else:
#         if isinstance(output, VolMesh):
#             for idx, vertex in enumerate(output.vertices()):
#                 viewer.scene.add(
#                     Point(*output.vertex_coordinates(vertex)), name=str(idx) + " " + str(output.vertex_attributes(vertex)), color=output.vertex_attribute(vertex, "color")[2]
#                 )

#             for edge in output.edges():
#                 viewer.scene.add(
#                     output.edge_line(edge),
#                     color=output.edge_attribute(edge, "color"),
#                     linewidth=output.edge_attribute(edge, "axis") * 2 + 3,
#                     name=str(output.edge_attributes(edge)),
#                 )

#             for face in output.faces():
#                 viewer.scene.add(output.face_polygon(face), color=output.face_attribute(face, "color"), name=str(output.face_attributes(face)))

#             for cell in output.cells():
#                 scale: Scale = Scale.from_factors([0.75, 0.75, 0.75], Frame(output.cell_center(cell), [1, 0, 0], [0, 1, 0]))
#                 viewer.scene.add(output.cell_to_mesh(cell).transformed(scale), name=str(output.cell_attributes(cell)), color=output.cell_attribute(cell, "color")[2])

#         else:
#             viewer.scene.add(output)

# objects = []
# viewer: Viewer = Viewer(show_grid=False)
# counter: int = 0


# if __name__ == "__main__":
#     viewer.config.renderer.show_grid = False
#     output = GridModel.from_meshgrid()
#     json_dump(output, "grid.json")
#     add_objects_to_scene(viewer, output)
#     # boxobj = viewer.scene.add(Box(1))

#     # @viewer.on(interval=1000)
#     # def reload(frame):

#     #     # make objects global
#     #     global viewer
#     #     global boxobj

#     #     # read objects from
#     #     if boxobj in viewer.scene.objects:
#     #         viewer.scene.remove(boxobj)
#     #         viewer.renderer.update()
#     #         print(boxobj, "deleted from scene")

#     #     boxobj = viewer.scene.add(Box(1))
#     #     boxobj.init()

#     #     viewer.renderer.update()

#     #     # update renderer
#     #     viewer.ui.init()
#     #     print(viewer.scene.objects)

#     viewer.show()
