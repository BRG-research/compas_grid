from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise
from compas_model.elements import Element
from compas_model.elements import Feature
from typing import List
from typing import Optional
from typing import Dict
from typing import Any


class CableFeature(Feature):
    pass


class CableElement(Element):
    """Class representing a cable element.

    Parameters
    ----------
    axis : :class:`compas.geometry.Line`
        The axis of the beam.
    radius : :class:`float`
        The radius of the cable.
    frame : :class:`compas.geometry.Frame`, optional
        The frame of the cable.
    features : list[:class:`CableFeature`], optional
        Additional block features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`CableElement`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(CableElement, self).__data__
        data["axis"] = self.axis
        data["radius"] = self.radius
        data["features"] = self.features
        return data

    def __init__(
        self,
        axis: Line,
        radius: float,
        sides: Optional[float] = 6,
        frame: Optional[Frame] = Frame.worldXY(),  # if beams are inclined, the shape is cut by the inclined plane
        features: Optional[List[CableFeature]] = None,
        name: Optional[str] = None,
    ):
        super(CableElement, self).__init__(frame=frame, name=name)
        self.axis: Line = axis or Line([0, 0, 0], [0, 0, 1])
        self.radius: float = radius
        self.section: Polygon = Polygon.from_sides_and_radius_xy(sides, self.radius)
        self.features: List[CableFeature] = features or []
        self.shape: Mesh = self.compute_shape()

    def compute_shape(self) -> Mesh:
        """Compute the shape of the beam from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """

        offset: int = len(self.section.points)
        vertices: List[Point] = self.section.points
        for i in range(0, len(self.section.points)):
            vertices.append(self.section.points[i] + self.axis.vector)
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
        """Compute the geometry of the element.
        The geometry is transformed by the world transformation.

        Parameters
        ----------
        include_features : bool, optional
            Flag indicating whether to include features in the geometry.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            Geometry with applied features.
        """

        geometry: Mesh = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate: float = 0.0) -> Box:
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The axis-aligned bounding box.
        """
        points: List[List[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate: float = 0.0) -> Box:
        """Compute the oriented bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The oriented bounding box.
        """
        points: List[List[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        from compas.geometry import convex_hull_numpy

        points: List[List[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    @classmethod
    def from_length_and_radius(
        cls,
        length: float = 10,
        radius: float = 0.02,
        features: Optional[List[CableFeature]] = None,
        name: str = "None",
    ) -> "CableElement":
        """Create a beam element from a square section centered on XY frame.

        Parameters
        ----------
        length : float
            The length of the cable.
        radius : float
            The radius of the cable.
        features : list[:class:`CableFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`CableElement`

        """

        axis: Line = Line([0, 0, 0], [0, 0, length])
        beam: CableElement = cls(axis=axis, radius=radius, features=features, name=name)
        return beam


if __name__ == "__main__":
    from compas_viewer import Viewer

    cable: CableElement = CableElement.from_length_and_radius()
    viewer: Viewer = Viewer()
    viewer.scene.add(cable.shape)
    viewer.show()
