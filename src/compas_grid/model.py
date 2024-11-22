from typing import Optional

import compas
import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401
from compas_model.materials import Material  # noqa: F401
from compas_model.models import Model  # noqa: F401
from compas_model.models.elementnode import ElementNode
from compas_model.models.groupnode import GroupNode
from compas_model.models.interactiongraph import InteractionGraph

from compas_grid import CutterInterface


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
    def from_lines_and_surfaces(cls, line: list[Line], surfaces: list[Mesh], tolerance: int = 3) -> "GridModel":
        """Create a grid model from a list of Line and surfaces.

        If a line has no attribute starting with "is" e.g.: is_beam, is_column, is_facade, is_stairs, is_etc
        They are geometrically sorted by z-coordinate and added to CellNetwork with coordinates with is_beam or is_column.
        Other attributes are kept in the CellNetwork but they are nowhere used in the model.

        Parameters
        ----------
        line : list[Line]
            List of lines representing the columns.

        surfaces : list[Mesh]
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

        return model

    def cut(self):
        # Add your cutting logic here
        pass
