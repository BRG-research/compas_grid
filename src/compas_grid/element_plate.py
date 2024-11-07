from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.geometry import Polygon
from compas.geometry import Frame
from compas.geometry import Point
from compas.itertools import pairwise
from compas.geometry import Vector
from compas.geometry import Line
from typing import *
from compas_model.elements import Element
from compas_model.elements import Feature
from numpy.typing import NDArray
import numpy as np


class PlateFeature(Feature):
    pass


class PlateElement(Element):
    """Class representing a block element.

    Parameters
    ----------
    shape : :class:`compas.datastructures.Mesh`
        The base shape of the block.
    features : list[:class:`PlateFeature`], optional
        Additional block features.
    is_support : bool, optional
        Flag indicating that the block is a support.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`PlateFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(PlateElement, self).__data__
        data["bottom"] = self.bottom
        data["top"] = self.top
        data["features"] = self.features
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "PlateElement":
        return cls(
            bottom=data["bottom"],
            top=data["top"],
            features=data["features"],
        )

    def __init__(self, bottom: Polygon, top: Polygon, features: List[PlateFeature] = None, frame: Frame = None, name: str = None, shape: Mesh = None):
        super(PlateElement, self).__init__(frame=frame, name=name)
        self.bottom: Polygon = bottom
        self.top: Polygon = top
        self.shape: Mesh = shape if shape else self.compute_shape()
        self.features: List[Feature] = features or []  # type: list[PlateFeature]
        if not self.name:
            self.name = self.__class__.__name__

    @property
    def face_polygons(self) -> List[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self) -> Mesh:
        """Compute the shape of the plate from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        offset: int = len(self.bottom)
        vertices: List[Point] = self.bottom.points + self.top.points  # type: ignore
        bottom: List[int] = list(range(offset))
        top: List[int] = [i + offset for i in bottom]
        faces: List[List[int]] = [bottom[::-1], top]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, b, d, c])
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_geometry(self, include_features: bool = False) -> Mesh:
        geometry: Mesh = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate: float = 0.0) -> Box:
        points: List[Point] = self.geometry.vertices_attributes("xyz")
        box: Box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate: float = 0.0) -> Box:
        points: List[Point] = self.geometry.vertices_attributes("xyz")
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        from compas.geometry import convex_hull_numpy

        points: List[Point] = self.geometry.vertices_attributes("xyz")
        vertices: NDArray[np.intc]
        faces: NDArray[np.intc] = convex_hull_numpy(points)
        vertices: List[Point] = [points[index] for index in vertices]
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    @classmethod
    def from_polygon_and_thickness(cls, polygon: Polygon, thickness: float, features: List[Feature] = None, frame: Frame = None, name: str = None, shape=None) -> "PlateElement":
        """Create a plate element from a polygon and a thickness.

        Parameters
        ----------
        polygon : :class:`compas.geometry.Polygon`
            The base polygon of the plate.
        thickness : float
            The total offset thickness above and blow the polygon.

        Returns
        -------
        :class:`PlateElement`

        """
        normal: Vector = polygon.normal
        down: Vector = normal * (0.0 * thickness)
        up: Vector = normal * (1.0 * thickness)
        bottom: Polygon = polygon.copy()
        for point in bottom.points:
            point += down
        top: Polygon = polygon.copy()
        for point in top.points:
            point += up
        plate: PlateElement = cls(bottom, top, features=features, frame=frame, name=name, shape=shape)
        return plate

    @classmethod
    def from_width_depth_thickness(
        cls, width: float, depth: float, thickness: float, features: List[Feature] = None, frame: Frame = None, name: str = None, shape=None
    ) -> "PlateElement":
        """Create a plate element from a width, depth and thickness.

        Parameters
        ----------
        width : float
            The width of the plate.
        depth : float
            The depth of the plate.
        thickness : float
            The total offset thickness above and blow the polygon.

        Returns
        -------
        :class:`PlateElement`

        """
        polygon: Polygon = Polygon.from_rectangle(Point(0, 0, 0), width, depth)
        return cls.from_polygon_and_thickness(polygon, thickness, features=features, frame=frame, name=name, shape=shape)


if __name__ == "__main__":
    from compas.geometry import Polygon
    from compas.geometry import Frame
    from compas_viewer import Viewer

    polygon = Polygon([[0, 0, 0], [0, 10, 0], [10, 10, 0], [10, 0, 0]])
    frame = Frame.worldXY()
    plate = PlateElement.from_polygon_and_thickness(polygon, 0.1, frame=frame)
    plate.copy()

    viewer: Viewer = Viewer()
    viewer.scene.add(plate.shape)
    viewer.show()
