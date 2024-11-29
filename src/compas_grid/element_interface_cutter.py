from compas_model.elements import Element
from compas_model.elements import Feature

import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box


class InterfaceCutterFeature(Feature):
    pass


class InterfaceCutterElement(Element):
    """Class representing a phyisical interface between two other elements.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        A polygon that represents the outline of the interface.
    thickness : float
        The thickness of the interface.
    features : list[:class:`InterfaceFeature`], optional
        Additional interface features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the interface.
    features : list[:class:`BlockFeature`]
        A list of additional interface features.

    Notes
    -----
    The shape of the interface is calculated automatically from the input polygon and thickness.
    The frame of the element is the frame of the polygon.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(InterfaceCutterElement, self).__data__
        return data

    def __init__(self, size=500, features=None, frame=None, name=None):
        frame = frame or Frame.worldXY()
        super(InterfaceCutterElement, self).__init__(frame=frame, name=name)
        self.size = size
        self.shape = self.compute_shape()
        self.features = features or []  # type: list[InterfaceCutterFeature]

    def compute_shape(self):
        # type: () -> compas.datastructures.Mesh
        polygon: Polygon = Polygon.from_rectangle([-self.size * 0.5, -self.size * 0.5, 0], self.size, self.size)
        mesh = Mesh.from_polygons([polygon])
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_geometry(self, include_features=False):
        geometry = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self):
        from compas.geometry import convex_hull_numpy

        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)
