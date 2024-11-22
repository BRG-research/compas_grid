from typing import Optional

import compas
import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.geometry import Vector
from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.materials import Material  # noqa: F401
from compas_model.models import Model  # noqa: F401
from compas_model.models.elementnode import ElementNode
from compas_model.models.groupnode import GroupNode
from compas_model.models.interactiongraph import InteractionGraph

from compas_grid import BeamElement
from compas_grid import CellNetwork
from compas_grid import ColumnElement
from compas_grid import ColumnHeadElement
from compas_grid import CutterInterface
from compas_grid import PlateElement


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

                    childnode = GroupNode(
                        name=childdata["name"],
                        attr=childdata["attributes"],
                    )
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

    def __init__(self, name: Optional[str] = None):
        super(GridModel, self).__init__(name=name)
        self._cell_network = None
        self._cutter_interfaces: list[CutterInterface] = []
        self.PRECISION = 3

    @classmethod
    def from_lines_and_surfaces(cls, column_and_beams: list[Line], floor_surfaces: list[Mesh], tolerance: int = 3) -> "GridModel":
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
        cell_network: CellNetwork = CellNetwork.from_lines_and_surfaces(column_and_beams, floor_surfaces, tolerance=tolerance)

        #######################################################################################################
        # Convert the CellNetwork to a GridModel.
        # Annotate ColumnHeadElement faces types, design of column head very specific including faces.
        # TODO:
        # Column head quadrants + frame.
        # ColumnHead class, based on the valency of the node you have cases:  corner, boundary, internal vertices.
        # Align column head with the overall frame system
        #######################################################################################################
        cell_network_columns: list[tuple[int, int]] = list(cell_network.edges_where({"is_column": True}))  # Order as in the model
        cell_network_beams: list[tuple[int, int]] = list(cell_network.edges_where({"is_beam": True}))  # Order as in the model
        cell_network_floors: list[int] = list(cell_network.faces_where({"is_floor": True}))  # Order as in the model

        model: Model = Model()
        columns = model.add_group("columns")
        column_heads = model.add_group("column_heads")
        beams = model.add_group("beams")
        floors = model.add_group("floors")

        column_head_to_vertex: dict[Element, int] = {}
        column_to_edge: dict[Element, tuple[int, int]] = {}
        beam_to_edge: dict[Element, tuple[int, int]] = {}

        width, depth, height, column_head_offset = 150, 150, 300, 210

        def add_column_head(edge):
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]

            # top rectangle
            polygon0: Polyline = Polyline(
                [
                    Point(-width, -depth, -height) + Vector(0, -column_head_offset, 0),
                    Point(width, -depth, -height) + Vector(0, -column_head_offset, 0),
                    Point(width, -depth, -height) + Vector(column_head_offset, 0, 0),
                    Point(width, depth, -height) + Vector(column_head_offset, 0, 0),
                    Point(width, depth, -height) + Vector(0, column_head_offset, 0),
                    Point(-width, depth, -height) + Vector(0, column_head_offset, 0),
                    Point(-width, depth, -height) + Vector(-column_head_offset, 0, 0),
                    Point(-width, -depth, -height) + Vector(-column_head_offset, 0, 0),
                ]
            )

            polygon1: Polyline = Polyline([Point(-width, -depth, 0), Point(width, -depth, 0), Point(width, depth, 0), Point(-width, depth, 0)])

            v: list[Point] = []
            f: list[list[int]] = []
            v.extend(polygon0.points)
            v.extend(polygon1.points)
            f.append([0, 1, 2, 3, 4, 5, 6, 7])
            f.append([3 + 8, 2 + 8, 1 + 8, 0 + 8])

            for i in range(4):
                f.append([i * 2, (i * 2 + 1) % 8, 8 + (i + 1) % 4, 8 + i])
                f.append([(i * 2 + 1) % 8, (i * 2 + 2) % 8, 8 + (i + 1) % 4])

            mesh: Mesh = Mesh.from_vertices_and_faces(v, f)

            element_column_head: ColumnHeadElement = ColumnHeadElement.from_mesh(mesh)
            # element_column_head: ColumnHeadElement = ColumnHeadElement.from_box(width=300, depth=300, height=300)
            element_column_head.frame = Frame(cell_network.vertex_point(column_head_vertex), [1, 0, 0], [0, 1, 0])
            model.add_element(element=element_column_head, parent=column_heads)

            column_head_to_vertex[column_head_vertex] = element_column_head

        def add_column(edge):
            axis: Line = cell_network.edge_line(edge)
            # column_head_vertex: int = edge[1]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                # column_head_vertex = edge[0]

            element_column: ColumnElement = ColumnElement.from_square_section(width=width * 2, depth=depth * 2, height=axis.length)
            element_column.frame = Frame(axis.start, [1, 0, 0], [0, 1, 0])
            model.add_element(element=element_column, parent=columns)

            column_to_edge[edge] = element_column

        def add_interaction_column_and_column_head(edge):
            axis: Line = cell_network.edge_line(edge)
            column_head_vertex: int = edge[1]
            column_base_vertex: int = edge[0]
            if axis[0][2] > axis[1][2]:
                axis = Line(axis[1], axis[0])
                column_head_vertex = edge[0]
                column_base_vertex = edge[1]

            if column_head_vertex in column_head_to_vertex:
                model.add_interaction(
                    column_head_to_vertex[column_head_vertex],
                    column_to_edge[edge],
                    interaction=CutterInterface(polygon=column_head_to_vertex[column_head_vertex].face_lowest, name="column_head_column_to_column"),
                )

            if column_base_vertex in column_head_to_vertex:
                model.add_interaction(
                    column_head_to_vertex[column_base_vertex],
                    column_to_edge[edge],
                    interaction=CutterInterface(polygon=column_head_to_vertex[column_base_vertex].face_highest, name="column_head_column_to_column"),
                )

        def add_beam(edge):
            axis: Line = cell_network.edge_line(edge)
            element: BeamElement = BeamElement.from_square_section(width=height, depth=depth * 2, height=axis.length)
            element.frame = Frame(axis.start, [0, 0, 1], Vector.cross(axis.direction, [0, 0, 1]))
            model.add_element(element=element, parent=beams)

            beam_to_edge[edge] = element

        def add_interaction_beam_and_column_head(edge):
            beam_element: BeamElement = beam_to_edge[edge]

            if edge[0] in column_head_to_vertex:
                column_head_element = column_head_to_vertex[edge[0]]
                model.add_interaction(
                    column_head_element,
                    beam_element,
                    interaction=CutterInterface(polygon=column_head_element.face_nearest(beam_element.obb.frame.point), name="column_head_and_beam"),
                )

            if edge[1] in column_head_to_vertex:
                column_head_element = column_head_to_vertex[edge[1]]
                model.add_interaction(
                    column_head_element,
                    beam_element,
                    interaction=CutterInterface(polygon=column_head_element.face_nearest(beam_element.obb.frame.point), name="column_head_and_beam"),
                )

        def add_floor(face):
            width, depth, thickness = 3000, 3000, 200
            polygon: Polygon = Polygon([[-width, -depth, -thickness], [-width, depth, -thickness], [width, depth, -thickness], [width, -depth, -thickness]])
            plate_element: PlateElement = PlateElement.from_polygon_and_thickness(polygon, thickness)
            plate_element.frame = Frame(cell_network.face_polygon(face).centroid, [1, 0, 0], [0, 1, 0])
            model.add_element(element=plate_element, parent=floors)

            for vertex in cell_network.face_vertices(face):
                if vertex in column_head_to_vertex:
                    column_head_element = column_head_to_vertex[vertex]

                    model.add_interaction(
                        column_head_to_vertex[vertex],
                        plate_element,
                        interaction=CutterInterface(polygon=column_head_element.face_nearest(plate_element.obb.frame.point), name="column_head_and_plate"),
                    )

        for edge in cell_network_columns:
            add_column_head(edge)

        for edge in cell_network_columns:
            add_column(edge)

        for edge in cell_network_columns:
            add_interaction_column_and_column_head(edge)

        for edge in cell_network_beams:
            add_beam(edge)

        for edge in cell_network_beams:
            add_interaction_beam_and_column_head(edge)

        for face in cell_network_floors:
            add_floor(face)

        return model

    def cut(self):
        # Add your cutting logic here
        pass
