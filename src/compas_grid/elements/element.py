from typing import Optional
from typing import Union

from compas_model.elements import Element

import compas
import compas.datastructures  # noqa: F401
import compas.geometry
import compas_grid
import compas_grid.interactions
from compas.geometry import Transformation


class BaseElement(Element):
    """Base class for all elements in the model.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`, optional
        The complete geometry of the element.
    frame : None, default WorldXY
        The frame of the element.
    name : None
        The name of the element.

    Attributes
    ----------
    graph_node : int
        The identifier of the corresponding node in the interaction graph of the parent model.
    tree_node : :class:`compas.datastructures.TreeNode`
        The node in the hierarchical element tree of the parent model.
    frame : :class:`compas.geometry.Frame`
        The local coordinate frame of the element.
    geometry : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, readonly
        The geometry of the element, computed from the base shape.
    aabb : :class:`compas.geometry.Box`, readonly
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`, readonly
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, readonly
        The collision geometry of the element.
    inflate_aabb : float
        Scaling factor to inflate the AABB with..Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`, optional
        The complete geometry of the el
    inflate_obb : float
        Scaling factor to inflate the OBB with.

    """

    @property
    def __data__(self):
        # type: () -> dict
        # note that the material can/should not be added here,
        # because materials should be added by/in the context of a model
        # and becaue this would also require a custom "from_data" classmethod.
        return {
            "frame": self.frame,
            "transformation": self.transformation,
            "name": self.name,
        }

    def __init__(
        self,
        geometry: Optional[Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]] = None,
        frame: compas.geometry.Frame = None,
        transformation: compas.geometry.Transformation = None,
        name: str = None,
    ):
        super(Element, self).__init__(name=name)
        self.graph_node = None
        self.tree_node = None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = geometry
        self._frame = frame
        self._transformation = transformation
        self._worldtransformation = None
        self._material = None
        self.inflate_aabb = 0.0
        self.inflate_obb = 0.0

    @property
    def geometry_local(self):
        return self._geometry

    def compute_geometry(self) -> Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]:
        """Compute the geometry of the element.
        The geometry is transformed by the world transformation.

        Returns
        -------
        :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            Geometry.
        """

        return self.shape.transformed(self.worldtransformation)

    def compute_interactions(self, is_local=False) -> list[Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]]:
        """
        Interactions are applied by modifying Element V1 element by Element V0
        Short exaplanation: V0 -> V1.
        For example elemenet of v1 is cut by the element of v0.


        Parameters
        ----------
        is_local : bool, default False
            If True, the interactions are computed in the local coordinate system of the element.
            If False, the interactions are computed in the world coordinate system.

        Returns
        -------
        list[:class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`]
            The modified geometry of the element.
        """

        graph = self.tree_node.tree.model.graph
        elements = list(self.tree_node.tree.model.elements())
        geometry_to_modify: any = self.geometry.copy()

        xform: Transformation = self.compute_worldtransformation().inverse() if is_local else Transformation()
        geometry_to_modify.transform(xform)

        for neighbor in graph.neighbors(self.graph_node):
            edge: tuple[int, int] = (self.graph_node, neighbor) if graph.has_edge((self.graph_node, neighbor)) else (neighbor, self.graph_node)

            # Order is important! We use Graph edges as directed edges.
            # Meaning current element always modifies the other element, and never itself.
            # If start element is the graph start of edge we continue, because we start element must modify the other element.
            if edge[0] == self.graph_node:  # V0 is always an interface element, while V1 is the element to be modified, otherwise continue.
                continue

            for interaction in graph.edge_interactions(edge):
                if isinstance(interaction, compas_grid.interactions.InteractionInterface):
                    # elements[neighbor].compute_interaction(geometry, xform)

                    result = interaction.compute_interaction(elements[neighbor].geometry, geometry_to_modify, xform)
                    if result:
                        geometry_to_modify = result

        return geometry_to_modify
