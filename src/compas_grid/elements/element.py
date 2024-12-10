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

        self._geometry_element: any = None  # Unchanged element geometry in local element frame.
        self._geometry_model: any = None  # Geometry with applied interactions and transformations.
        self._geometry_world: any = None  # Geometry in the world coordinate system.

        self._is_dirty: bool = True

    # ==========================================================================
    # Geometry types: geometry of an element, model, world.
    # ==========================================================================
    @property
    def geometry_element(self):
        if not self._geometry_element:
            self._geometry_element = self.compute_geometry_element()

    @property
    def is_dirty(self):
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value):
        self._is_dirty = value

        if value:
            elements = list(self.tree_node.tree.model.elements())
            for neighbor in self.tree_node.tree.model.graph.neighbors(self.graph_node):
                elements[neighbor].is_dirty = value

    @property
    def geometry_model(self):
        if not self._geometry_model or self.is_dirty:
            self._geometry_model = self.compute_geometry_model()

    @property
    def geometry_world(self):
        if not self._geometry_world:
            self._geometry_world = self.compute_geometry_world()

    def compute_geometry_element(self) -> Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]:
        """Compute the geometry of the element in the local coordinate system.

        Returns
        -------
        :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            Geometry.
        """

        pass

    def compute_geometry_model(self) -> Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]:
        """Compute the geometry of the element in the global model coordinate system with applied interactions.
        The model coordinate system is defined by the model frame.

        Returns
        -------
        :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            Geometry.
        """

        graph = self.tree_node.tree.model.graph
        elements = list(self.tree_node.tree.model.elements())
        geometry_to_modify: any = self.geometry.transformed(self.worldtransformation)

        # xform: Transformation = self.compute_worldtransformation().inverse() if local_transform else Transformation()
        xform: Transformation = Transformation()
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

    def compute_geometry_world(self) -> Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]:
        """Compute the geometry of the element in the world coordinate system.
        We transform geometry from the model frame to WorldXY frame.

        Returns
        -------
        :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            Geometry.
        """
        geometry_world: any = self.geometry_model.copy()
        xform: Transformation = Transformation.from_frame_to_frame(self.tree_node.tree.model.frame, compas.geometry.Frame.WorldXY())
        return geometry_world.transformed(xform)

    def compute_interactions(self, local_transform=False) -> list[Union[compas.geometry.Shape, compas.geometry.Brep, compas.datastructures.Mesh]]:
        """
        Interactions are applied by modifying Element V1 element by Element V0
        Short exaplanation: V0 -> V1.
        For example elemenet of v1 is cut by the element of v0.


        Parameters
        ----------
        local_transform : bool, default False
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

        xform: Transformation = self.compute_worldtransformation().inverse() if local_transform else Transformation()
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

    # def rebuild(self, parameter: any):
    #     """Rebuild the element."""
    #     pass
