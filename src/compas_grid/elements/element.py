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

    # ==========================================================================
    # Methods
    # ==========================================================================
    def compute_geometry(self) -> any:
        """Compute the geometry of the element.
        The geometry is transformed by the world transformation.

        Returns
        -------
        :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            Geometry.
        """

        geometry: any = self.shape
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_interfaces(self, is_object_frame=False) -> list[any]:
        """Add or cut or modify the current element by the neighbor element.
        Even though the underlying model graph in undirected, default_edge_attributes are still stored (u, v) order.
        If the U is current element we exclude it from the modification."""

        graph = self.tree_node.tree.model.graph
        elements = list(self.tree_node.tree.model.elements())
        geometries: list[any] = [self.geometry.copy()]

        xform: Transformation = self.compute_worldtransformation().inverse() if is_object_frame else Transformation()
        geometries[0].transform(xform)

        for neighbor in graph.neighbors(self.graph_node):
            edge: tuple[int, int] = (self.graph_node, neighbor) if graph.has_edge((self.graph_node, neighbor)) else (neighbor, self.graph_node)

            # If the U is current element we exclude it from the modification.
            # This gives clear order of interaction application from the smallest leaf to the root.

            if edge[0] == self.graph_node:
                continue

            # TODO: This is a temporary solution to consider only one InterfaceElement at a time. But interface elements can have a hierarchy too.

            for interaction in graph.edge_interactions(edge):
                if isinstance(interaction, compas_grid.interactions.InteractionInterface):
                    elements[neighbor].compute_interface(geometries, xform)

        return geometries

    # def compute_geometry_local(self):
    #     """Compute the interfaces of the element in local object space."""

    #     geometries: list[any] = self.compute_geometry()
    #     xform: Transformation = self.compute_worldtransformation().inverse()

    #     for geometry in geometries:
    #         geometry.transform(xform)

    #     return geometries
