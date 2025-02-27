from typing import TYPE_CHECKING
from typing import Optional

from compas_model.elements.element import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import bounding_box
from compas.geometry import intersection_line_plane
from compas.geometry import oriented_bounding_box

if TYPE_CHECKING:
    from compas_model.elements import BeamElement


class CableFeature(Feature):
    pass


class CableElement(Element):
    """Class representing a Cable element with a round section.

    Parameters
    ----------
    radius : float
        Radius of the Cable.
    sides : int
        Number of sides of the Cable's polygonal section.
    length : float
        Length of the Cable.
    is_support : bool
        Flag indicating if the Cable is a support.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the Cable.
    features : Optional[list[:class:`compas_model.features.CableFeature`]]
        Features of the Cable.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    radius : float
        Radius of the Cable.
    sides : int
        Number of sides of the Cable's polygonal section.
    length : float
        length of the Cable.
    is_support : bool
        Flag indicating if the Cable is a support.
    axis : :class:`compas.geometry.Line`
        Line axis of the Cable.
    section : :class:`compas.geometry.Polygon`
        Section polygon of the Cable.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the Cable.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the Cable.
    transformation : :class:`compas.geometry.Transformation`
        Transformation applied to the Cable.
    features : list[:class:`compas_model.features.CableFeature`]
        Features of the Cable.
    name : str
        The name of the Cable.
    """

    @property
    def __data__(self) -> dict:
        return {
            "radius": self.radius,
            "sides": self.sides,
            "length": self.length,
            "is_support": self.is_support,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        radius: float = 0.4,
        sides: int = 24,
        length: float = 3.0,
        is_support: bool = False,
        transformation: Optional[Transformation] = None,
        features: Optional[list[CableFeature]] = None,
        name: Optional[str] = None,
    ) -> "CableElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.radius = radius
        self.sides = sides
        self._length = length
        self.axis: Line = Line([0, 0, 0], [0, 0, self._length])
        self.section: Polygon = Polygon.from_sides_and_radius_xy(sides, radius)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.modelgeometry.face_polygon(face) for face in self.modelgeometry.faces()]  # type: ignore

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length
        self.axis: Line = Line([0, 0, 0], [0, 0, self._length])
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    def compute_top_and_bottom_polygons(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the Cable.

        Returns
        -------
        tuple[:class:`compas.geometry.Polygon`, :class:`compas.geometry.Polygon`]
        """

        plane0: Plane = Plane(self.axis.start, self.axis.direction)
        plane1: Plane = Plane(self.axis.end, self.axis.direction)
        points0: list[list[float]] = []
        points1: list[list[float]] = []
        for i in range(len(self.section.points)):
            line: Line = Line(self.section.points[i], self.section.points[i] + self.axis.vector)
            result0: Optional[list[float]] = intersection_line_plane(line, plane0)
            result1: Optional[list[float]] = intersection_line_plane(line, plane1)
            if not result0 or not result1:
                raise ValueError("The line does not intersect the plane")
            points0.append(result0)
            points1.append(result1)
        return Polygon(points0), Polygon(points1)

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the Cable from the given polygons.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        from compas.geometry import Point
        from compas.itertools import pairwise

        offset: int = len(self.polygon_bottom)
        vertices: list[Point] = self.polygon_bottom.points + self.polygon_top.points  # type: ignore
        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        faces: list[list[int]] = [bottom[::-1], top]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, b, d, c])
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_aabb(self, inflate: Optional[bool] = None) -> Box:
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
        points: list[list[float]] = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(bounding_box(points))
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        return box

    def compute_obb(self, inflate: Optional[bool] = None) -> Box:
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
        points: list[list[float]] = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        if inflate and inflate != 1.0:
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

        points: list[list[float]] = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance : float
            The distance to extend the beam.
        """
        self.length = self.length + distance * 2
        xform: Transformation = Translation.from_vector([0, 0, -distance])
        self.transformation = self.transformation * xform

    def add_modifier(self, target_element: Element, type: str = ""):
        """Computes the contact interaction of the geometry of the elements that is used in the model's add_contact method.

        Returns
        -------
        :class:`compas_model.interactions.BooleanModifier`
            The ContactInteraction that is applied to the neighboring element. One pair can have one or multiple variants.
        target_element : Element
            The target element to compute the contact interaction.
        type : str, optional
            The type of contact interaction, if different contact are possible between the two elements.

        """
        # Traverse up to the class one before the Element class.add()
        # Create a function name based on the target_element class name.
        parent_class = target_element.__class__
        while parent_class.__bases__[0] != Element:
            parent_class = parent_class.__bases__[0]

        parent_class_name = parent_class.__name__.lower().replace("element", "")
        method_name = f"_add_modifier_with_{parent_class_name}"
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Unsupported target element type: {type(target_element)}")

        return method(target_element, type)

    def _add_modifier_with_beam(self, target_element: "BeamElement", type: str):
        # Scenario:
        # A cable applies boolean difference with a block geometry.
        return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))

    def compute_point(self) -> Point:
        return Point(*self.aabb.frame.point)

    # =============================================================================
    # Constructors
    # =============================================================================
