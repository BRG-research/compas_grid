from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.materials import Material  # noqa: F401
from compas_model.models import Model  # noqa: F401
from compas_model.models.elementnode import ElementNode
from compas_model.models.interactiongraph import InteractionGraph

import compas
import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry.transformation import Transformation
from compas_grid.datastructures import CellNetwork
from compas_grid.elements import BeamElement
from compas_grid.elements import ColumnElement
from compas_grid.elements import ColumnHeadElement
from compas_grid.elements import InterfaceCutterElement
from compas_grid.elements import PlateElement
from compas_grid.interactions import InteractionInterface
from compas_grid.shapes import CardinalDirections
from compas_grid.shapes import CrossBlockShape


class GridModel(Model):
    """Class representing a grid model of a multi-story building.

    Pseudo code for the user interface:
    import compas
    from compas.scene import Scene
    from compas_grid.model import GridModel

    # Call Rhino UI.
    lines, surfaces : tuple(list[Line], list[Mesh]) = GridModel.rhino_ui()

    # Create the model.
    model = GridModel.from_lines_and_surfaces(lines, surfaces)
    model.cut()

    # Visualize the model.
    scene = Scene()
    scene.clear()
    scene.add(model)
    scene.draw()

    """

    all_geo = []

    @property
    def __data__(self):
        # in their data representation,
        # the element tree and the interaction graph
        # refer to model elements by their GUID, to avoid storing duplicate data representations of those elements
        # the elements are stored in a global list
        data = {
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(self.elements()),
            "materials": list(self.materials()),
            "element_material": {str(element.guid): str(element.material.guid) for element in self.elements() if element.material},
        }
        return data

    @classmethod
    def __from_data__(cls, data):
        model = cls()
        model._guid_material = {str(material.guid): material for material in data["materials"]}
        model._guid_element = {str(element.guid): element for element in data["elements"]}

        for e, m in data["element_material"].items():
            element = model._guid_element[e]
            material = model._guid_material[m]
            element._material = material

        def add(nodedata, parentnode):
            # type: (dict, GroupNode) -> None

            for childdata in nodedata["children"]:
                if "element" in childdata:
                    if "children" in childdata:
                        raise Exception("A node containing an element cannot have children.")

                    guid = childdata["element"]
                    element = model._guid_element[guid]
                    childnode = ElementNode(element=element)
                    parentnode.add(childnode)

                elif "children" in childdata:
                    if "element" in childdata:
                        raise Exception("A node containing other nodes cannot have an element.")

                    parentnode.add(childnode)
                    add(childdata, childnode)

                else:
                    raise Exception("A node without an element and without children is not supported.")

        # add all children of a node's data representation
        # in a "live" version of the node,
        # while converting the data representations of the children to "live" nodes as well
        # in this process, guid references to model elements are replaced by the actual elements
        add(data["tree"]["root"], model._tree.root)  # type: ignore

        # note that this overwrites the existing interaction graph
        # during the reconstruction process,
        # guid references to model elements are replaced by actual elements
        model._graph = InteractionGraph.__from_data__(data["graph"], model._guid_element)

        return model

    def __init__(self, name: str = None):
        super(GridModel, self).__init__(name=name)
        self._cell_network = None
        self.PRECISION = 3
        self.all_geo = []

    @classmethod
    def from_lines_and_surfaces(
        cls,
        column_and_beams: list[Line],
        floor_surfaces: list[Mesh],
        tolerance: int = 3,
    ) -> "GridModel":
        """Create a grid model from a list of Line and surfaces.
        You can extend user input to include facade and core surfaces.

        Parameters
        ----------
        column_and_beams : list[Line]
            List of lines representing the columns and beams.

        floor_surfaces : list[Mesh]
            List of surfaces representing the floors.

        tolerance : int, optional
            The tolerance of the model

        Returns
        -------
        GridModel
            The grid model.
        """
        model = cls()
        model.PRECISION = tolerance

        #######################################################################################################
        # Convert lines and surfaces to a CellNetwork.
        #######################################################################################################
        cell_network = CellNetwork.from_lines_and_surfaces(column_and_beams, floor_surfaces, tolerance=tolerance)

        #######################################################################################################
        # Convert the CellNetwork to a GridModel.
        #######################################################################################################
        cell_network_columns: list[tuple[int, int]] = list(cell_network.edges_where({"is_column": True}))  # Order as in the model
        cell_network_beams: list[tuple[int, int]] = list(cell_network.edges_where({"is_beam": True}))  # Order as in the model
        cell_network_floors: list[int] = list(cell_network.faces_where({"is_floor": True}))  # Order as in the model

        column_head_to_vertex: dict[Element, int] = {}
        column_to_edge: dict[Element, tuple[int, int]] = {}
        beam_to_edge: dict[Element, tuple[int, int]] = {}
        vertex_to_plates_and_faces: dict[int, list[tuple[Element, list[int]]]] = {}

        width, depth, height, column_head_offset = 150, 150, 300, 210

        def add_column_head(edge):
            # Get the top vertex of the column head and the axis of the column.
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]

            # Input for the ColumnHead class
            v: dict[int, Point] = {}
            e: list[tuple[int, int]] = []
            f: list[list[int]] = []

            v[column_head_vertex] = cell_network.vertex_point(column_head_vertex)

            for neighbor in cell_network.vertex_attribute(column_head_vertex, "neighbors"):
                e.append([column_head_vertex, neighbor])
                v[neighbor] = cell_network.vertex_point(neighbor)

            for floor in list(set(cell_network.vertex_faces(column_head_vertex))):
                if "is_floor" in cell_network.face_attributes(floor):
                    f.append(cell_network.face_vertices(floor))  # This would fail when faces would include vertical walls.

            # Create column head and it to the model.
            element_column_head: ColumnHeadElement = ColumnHeadElement.from_column_head_cross_shape(
                v,
                e,
                f,
                width=width,
                depth=depth,
                height=height,
                offset=column_head_offset,
            )

            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(cell_network.vertex_point(column_head_vertex)))
            # element_column_head.frame = Frame(cell_network.vertex_point(column_head_vertex), [1, 0, 0], [0, 1, 0])
            element_column_head.transformation = orientation

            # Add the column head element to the model.
            model.add_element(element=element_column_head)

            # Store the column head element in a dictionary.
            column_head_to_vertex[column_head_vertex] = element_column_head

        def add_column(edge):
            axis: Line = cell_network.edge_line(edge)
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])

            element_column: ColumnElement = ColumnElement.from_square_section(width=width * 2, depth=depth * 2, height=axis.length)
            # element_column.frame = Frame(axis.start, [1, 0, 0], [0, 1, 0])
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [1, 0, 0], [0, 1, 0]))
            element_column.transformation = orientation

            model.add_element(element=element_column)
            column_to_edge[edge] = element_column

        def add_beam(edge):
            axis: Line = cell_network.edge_line(edge)
            element: BeamElement = BeamElement.from_square_section(width=height, depth=depth * 2, height=axis.length)
            # element.frame = Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1]))
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1])))
            element.transformation = orientation
            model.add_element(element=element)
            beam_to_edge[edge] = element

        def add_floor(face, width=3000, depth=3000, thickness=200):
            polygon: Polygon = Polygon([[-width, -depth, -thickness], [-width, depth, -thickness], [width, depth, -thickness], [width, -depth, -thickness]])
            plate_element: PlateElement = PlateElement.from_polygon_and_thickness(polygon, thickness)
            # plate_element.frame = Frame(cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0])
            orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0]))
            plate_element.transformation = orientation
            model.add_element(element=plate_element)

            for vertex in cell_network.face_vertices(face):
                if vertex in vertex_to_plates_and_faces:
                    vertex_to_plates_and_faces[vertex].append((plate_element, cell_network.face_vertices(face)))
                else:
                    vertex_to_plates_and_faces[vertex] = [(plate_element, cell_network.face_vertices(face))]

        def add_interaction_column_and_column_head(edge):
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            column_base_vertex: int = edge[0]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]
                column_base_vertex = edge[1]

            if column_head_vertex in column_head_to_vertex:
                interface_cutter_element: InterfaceCutterElement = InterfaceCutterElement(500)
                polygon = column_head_to_vertex[column_head_vertex].geometry.face_polygon(0)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                polygon_frame = Frame(polygon_frame.point, polygon_frame.xaxis, -polygon_frame.yaxis)
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, column_to_edge[edge], InteractionInterface())
                # model.add_interaction(interface_cutter_element, column_head_to_vertex[column_head_vertex], InteractionInterface())
                model.add_interaction(column_head_to_vertex[column_head_vertex], column_to_edge[edge], interaction=Interaction())

                # model.add_interaction(
                #     column_head_to_vertex[column_head_vertex],
                #     column_to_edge[edge],
                #     interaction=CutterInterface(polygon=column_head_to_vertex[column_head_vertex].geometry.face_polygon(0), name="column_head_column_to_column"),
                # )

            if column_base_vertex in column_head_to_vertex:
                interface_cutter_element: InterfaceCutterElement = InterfaceCutterElement(500)

                polygon = column_head_to_vertex[column_base_vertex].geometry.face_polygon(1)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                # polygon_frame = Frame(polygon_frame.point, polygon_frame.xaxis, -polygon_frame.yaxis)
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                model.add_interaction(interface_cutter_element, column_to_edge[edge], InteractionInterface())
                # model.add_interaction(interface_cutter_element, column_head_to_vertex[column_base_vertex], InteractionInterface())
                model.add_interaction(column_head_to_vertex[column_base_vertex], column_to_edge[edge], interaction=Interaction())
                # model.add_interaction(
                #     column_head_to_vertex[column_base_vertex],
                #     column_to_edge[edge],
                #     interaction=CutterInterface(polygon=column_head_to_vertex[column_base_vertex].geometry.face_polygon(1), name="column_head_column_to_column"),
                # )

        def add_interaction_beam_and_column_head(edge):
            beam_element: BeamElement = beam_to_edge[edge]

            if edge[0] in column_head_to_vertex:
                column_head_element = column_head_to_vertex[edge[0]]
                direction: CardinalDirections = CrossBlockShape.closest_direction(cell_network.vertex_point(edge[1]) - cell_network.vertex_point(edge[0]))
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction}))[0])

                interface_cutter_element: InterfaceCutterElement = InterfaceCutterElement(500)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                # model.add_interaction(interface_cutter_element, column_head_element, InteractionInterface())
                model.add_interaction(interface_cutter_element, beam_element, InteractionInterface())
                model.add_interaction(column_head_element, beam_element, interaction=Interaction())

                # model.add_interaction(
                #     column_head_element,
                #     beam_element,
                #     interaction=CutterInterface(polygon=polygon, name="column_head_and_beam"),
                # )

            if edge[1] in column_head_to_vertex:
                column_head_element = column_head_to_vertex[edge[1]]
                direction: CardinalDirections = CrossBlockShape.closest_direction(cell_network.vertex_point(edge[0]) - cell_network.vertex_point(edge[1]))
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction}))[0])

                interface_cutter_element: InterfaceCutterElement = InterfaceCutterElement(500)
                polygon_frame: Frame = Frame(polygon.centroid, polygon[1] - polygon[0], polygon[2] - polygon[1])
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon_frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                # model.add_interaction(interface_cutter_element, column_head_element, InteractionInterface())
                model.add_interaction(interface_cutter_element, beam_element, InteractionInterface())
                model.add_interaction(column_head_element, beam_element, interaction=Interaction())

                # model.add_interaction(
                #     column_head_element,
                #     beam_element,
                #     interaction=CutterInterface(polygon=polygon, name="column_head_and_beam"),
                # )

        def add_interaction_floor_and_column_head(vertex, plates_and_faces):
            if vertex not in column_head_to_vertex:
                return

            column_head_element = column_head_to_vertex[vertex]

            for plate_element, face in plates_and_faces:
                i: int = face.index(vertex)
                prev: int = (i - 1) % len(face)
                next: int = (i + 1) % len(face)
                v0 = face[i]
                v0_prev = face[prev]
                v0_next = face[next]
                direction0: CardinalDirections = CrossBlockShape.closest_direction(cell_network.vertex_point(v0_prev) - cell_network.vertex_point(v0))
                direction1: CardinalDirections = CrossBlockShape.closest_direction(cell_network.vertex_point(v0_next) - cell_network.vertex_point(v0))
                direction_angled: CardinalDirections = CardinalDirections.get_direction_combination(direction0, direction1)
                polygon: Polygon = column_head_element.geometry.face_polygon(list(column_head_element.geometry.faces_where(conditions={"direction": direction_angled}))[0])

                interface_cutter_element: InterfaceCutterElement = InterfaceCutterElement(500)
                orientation: Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), polygon.frame)
                interface_cutter_element.transformation = orientation

                model.add_element(element=interface_cutter_element)
                # model.add_interaction(interface_cutter_element, column_head_element, InteractionInterface())
                model.add_interaction(interface_cutter_element, plate_element, InteractionInterface())
                model.add_interaction(
                    column_head_element,
                    plate_element,
                    interaction=Interaction(),
                )

                # model.add_interaction(
                #     column_head_element,
                #     plate_element,
                #     interaction=CutterInterface(polygon=polygon, name="column_head_and_plate"),
                # )

        # Elements
        for edge in cell_network_columns:
            add_column_head(edge)

        for edge in cell_network_columns:
            add_column(edge)

        for edge in cell_network_beams:
            add_beam(edge)

        for face in cell_network_floors:
            add_floor(face, width=3000 - width, depth=3000 - depth, thickness=200)

        # Interactions
        for edge in cell_network_columns:
            add_interaction_column_and_column_head(edge)

        for edge in cell_network_beams:
            add_interaction_beam_and_column_head(edge)

        for vertex, plates_and_faces in vertex_to_plates_and_faces.items():
            add_interaction_floor_and_column_head(vertex, plates_and_faces)

        return model

    def add_column_head_interactions(
        self,
    ):
        pass
