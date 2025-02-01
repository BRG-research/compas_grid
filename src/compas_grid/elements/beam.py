from typing import Optional
from typing import Union

from compas_model.elements.element import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Modifier
from compas_model.interactions import SlicerModifier

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import intersection_line_plane
from compas.geometry import is_point_in_polygon_xy
from compas.geometry import mirror_points_line
from compas_grid.elements import BlockElement


class BeamFeature(Feature):
    pass


class BeamElement(Element):
    """Class representing a beam element with a square section, constructed from the WorldXY Frame.
    The beam is defined in its local frame, where the length corresponds to the Z-Axis, the height to the Y-Axis, and the width to the X-Axis.
    By default, the local frame is set to WorldXY frame.

    Parameters
    ----------
    width : float
        The width of the beam.
    height : float
        The height of the beam.
    length : float
        The length of the beam.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the beam.
    features : Optional[list[:class:`compas_model.features.BeamFeature`]]
        Features of the beam.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    box : :class:`compas.geometry.Box`
        The box geometry of the beam.
    width : float
        The width of the beam.
    height : float
        The height of the beam.
    length : float
        The length of the beam.
    center_line : :class:`compas.geometry.Line`
        Line axis of the beam.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.box.xsize,
            "height": self.box.ysize,
            "length": self.box.zsize,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.1,
        height: float = 0.2,
        length: float = 3.0,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamElement":
        super().__init__(transformation=transformation, features=features, name=name)
        self._box = Box.from_width_height_depth(width, length, height)
        self._box.frame = Frame(point=[0, 0, self._box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def box(self) -> Box:
        return self._box

    @property
    def width(self) -> float:
        return self.box.xsize

    @width.setter
    def width(self, width: float):
        self.box.xsize = width

    @property
    def height(self) -> float:
        return self.box.ysize

    @height.setter
    def height(self, height: float):
        self.box.ysize = height

    @property
    def length(self) -> float:
        return self.box.zsize

    @length.setter
    def length(self, length: float):
        self.box.zsize = length
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.box.height])

    def compute_elementgeometry(self) -> Mesh:
        """Compute the mesh shape from a box.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        return self.box.to_mesh()

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance : float
            The distance to extend the beam.
        """

        self.box.zsize = self.length + distance * 2
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2 - distance], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

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

        box = self.box.transformed(self.modeltransformation)
        box = Box.from_bounding_box(box.points)
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._aabb = box
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
        box = self.box.transformed(self.modeltransformation)
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._obb = box
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        return self.modelgeometry.to_mesh()

    def compute_point(self) -> Point:
        """Compute the reference point of the beam from the centroid of its geometry.

        Returns
        -------
        :class:`compas.geometry.Point`

        """
        return Point(*self.modelgeometry.centroid())

    # =============================================================================
    # Modifier methods (WIP)
    # =============================================================================

    def _add_modifier_with_beam(self, target_element: "BeamElement", type: str) -> Union["BooleanModifier", None]:
        # Scenario:
        # A cable applies boolean difference with a block geometry.
        return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))

    def _add_modifier_with_block(self, target_element: "BlockElement", type: str) -> Union["BooleanModifier", None]:
        # Scenario:
        # A beam with a profile applies boolean difference with a block geometry.
        if target_element.is_support:
            return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))
        else:
            return None

    def _create_slicer_modifier(self, target_element: "BeamElement") -> Modifier:
        # This method performs mesh-ray intersection for detecting the slicing plane.
        mesh = self.elementgeometry.transformed(self.modeltransformation)
        center_line: Line = target_element.center_line.transformed(target_element.modeltransformation)

        p0 = center_line.start
        p1 = center_line.end

        closest_distance_to_end_point = float("inf")
        closest_face = 0
        for face in self.elementgeometry.faces():
            polygon = mesh.face_polygon(face)
            frame = polygon.frame
            result = intersection_line_plane(center_line, Plane.from_frame(frame))
            if result:
                point = Point(*result)
                xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                point = point.transformed(xform)
                polygon = polygon.transformed(xform)
                if is_point_in_polygon_xy(point, polygon):
                    d = max(p0.distance_to_point(point), p1.distance_to_point(point))
                    if d < closest_distance_to_end_point:
                        closest_distance_to_end_point = d
                        closest_face = face

        plane = Plane.from_frame(mesh.face_polygon(closest_face).frame)
        plane = Plane(plane.point, -plane.normal)
        return SlicerModifier(plane)


class BeamTProfileElement(BeamElement):
    """Class representing a beam element with I profile.

    Parameters
    ----------
    width : float, optional
        The width of the beam.
    height : float, optional
        The height of the beam.
    step_width_left : float, optional
        The step width on the left side of the beam.
    step_height_left : float, optional
        The step height on the left side of the beam.
    length : float, optional
        The length of the beam.
    inverted : bool, optional
        Flag indicating if the beam section is inverted as upside down letter T.
    step_width_right : float, optional
        The step width on the right side of the beam, if None then the left side step width is used.
    step_height_right : float, optional
        The step height on the right side of the beam, if None then the left side step height is used.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    axis : :class:`compas.geometry.Line`
        The axis of the beam.
    section : :class:`compas.geometry.Polygon`
        The section of the beam.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the beam.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the beam.
    transformation : :class:`compas.geometry.Transformation`
        The transformation applied to the beam.

    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "step_width_left": self.step_width_left,
            "step_height_left": self.step_height_left,
            "length": self.length,
            "inverted": self.inverted,
            "step_height_right": self.step_height_right,
            "step_width_right": self.step_width_right,
            "is_support": self.is_support,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.1,
        height: float = 0.2,
        step_width_left: float = 0.02,
        step_height_left: float = 0.02,
        length: float = 3.0,
        inverted: bool = False,
        step_height_right: Optional[float] = None,
        step_width_right: Optional[float] = None,
        is_support: bool = False,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamTProfileElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = abs(width)
        self.height: float = abs(height)
        self.step_width_left: float = abs(step_width_left)
        self.step_width_right: float = abs(step_width_right) if step_width_right is not None else step_width_left
        self.step_height_left: float = abs(step_height_left)
        self.step_height_right: float = abs(step_height_right) if step_height_right is not None else step_height_left
        self.inverted: bool = inverted
        self._length: float = abs(length)

        self.step_width_left = min(self.step_width_left, width * 0.5 * 0.999)
        self.step_width_right = min(self.step_width_right, width * 0.5 * 0.999)
        self.step_height_left = min(self.step_height_left, height)
        self.step_height_right = min(self.step_height_right, height)

        self.points: list[float] = [
            [self.width * 0.5, -self.height * 0.5, 0],
            [-self.width * 0.5, -self.height * 0.5, 0],
            [-self.width * 0.5, -self.height * 0.5 + self.step_height_left, 0],
            [-self.width * 0.5 + self.step_width_left, -self.height * 0.5 + self.step_height_left, 0],
            [-self.width * 0.5 + self.step_width_left, self.height * 0.5, 0],
            [self.width * 0.5 - self.step_width_right, self.height * 0.5, 0],
            [self.width * 0.5 - self.step_width_right, -self.height * 0.5 + self.step_height_right, 0],
            [self.width * 0.5, -self.height * 0.5 + self.step_height_right, 0],
        ]

        if inverted:
            mirror_line: Line = Line([0, 0, 0], [1, 0, 0])
            self.points = mirror_points_line(self.points, mirror_line)

        # Create the polygon of the T profile
        self.section: Polygon = Polygon(self.points)
        self.axis: Line = Line([0, 0, 0], [0, 0, length])

    def compute_elementgeometry(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the beam.

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
        polygon0 = Polygon(points0)
        polygon1 = Polygon(points1)

        from compas.geometry import earclip_polygon
        from compas.itertools import pairwise

        offset: int = len(polygon0)
        vertices: list[Point] = polygon0.points + polygon1.points  # type: ignore

        triangles: list[list[int]] = earclip_polygon(Polygon(polygon0.points))
        top_faces: list[list[int]] = []
        bottom_faces: list[list[int]] = []
        for i in range(len(triangles)):
            triangle_top: list[int] = []
            triangle_bottom: list[int] = []
            for j in range(3):
                triangle_top.append(triangles[i][j] + offset)
                triangle_bottom.append(triangles[i][j])
            triangle_bottom.reverse()
            top_faces.append(triangle_top)
            bottom_faces.append(triangle_bottom)
        faces: list[list[int]] = bottom_faces + top_faces

        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([c, d, b, a])
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length

        self.section = Polygon(list(self.points))

        self.axis = Line([0, 0, 0], [0, 0, length])
        self.compute_elementgeometry()

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
        self.compute_elementgeometry()

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

        box = self.modelgeometry.aabb()
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._aabb = box
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
        box = self.modelgeometry.oobb()
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._obb = box
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        return self.modelgeometry

    # =============================================================================
    # Constructors
    # =============================================================================
