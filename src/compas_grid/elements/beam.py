from typing import Optional
from typing import Union

from compas_model.elements.element import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Modifier
from compas_model.interactions import SlicerModifier

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Scale
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import bounding_box
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


class BeamProfileElement(BeamElement):
    """Class representing a beam element with I profile.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The section of the beam.
    length : float, optional
        The length of the beam.
    is_support : bool, optional
        Flag indicating if the beam is a support.
    transformation : :class:`compas.geometry.Transformation`, optional
        The transformation applied to the beam.
    features : list[:class:`compas_model.features.BeamFeature`], optional
        The features of the beam.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    center_line : :class:`compas.geometry.Line`
        The axis of the beam.
    section : :class:`compas.geometry.Polygon`
        The section of the beam.

    """

    @property
    def __data__(self) -> dict:
        return {
            "polygon": self.section,
            "length": self.length,
            "is_support": self.is_support,
            "shape": self.shape,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        polygon: Polygon,
        length: float = 3.0,
        is_support: bool = False,
        shape: Optional[Mesh] = None,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamProfileElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support
        self._length: float = abs(length)
        self.section: Polygon = polygon
        self._shape: Optional[Mesh] = shape  # public property that can be changed any time
        box = Box.from_points(bounding_box(polygon.points))
        self.width = box.xsize
        self.height = box.ysize

    @property
    def shape(self) -> Mesh:
        return self._shape

    @shape.setter
    def shape(self, shape: Mesh):
        self._shape = shape
        self._geometry = None

    def _loft(self, polygon: Polygon) -> Mesh:
        plane0: Plane = Plane(self.center_line.start, self.center_line.direction)
        plane1: Plane = Plane(self.center_line.end, self.center_line.direction)
        points0: list[list[float]] = []
        points1: list[list[float]] = []
        for i in range(len(polygon.points)):
            line: Line = Line(polygon.points[i], polygon.points[i] + self.center_line.vector)
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
            # Create bottom faces with original winding
            bottom_faces.append(triangles[i])
            # Create top faces with consistent winding and offset
            top_face = [triangles[i][0] + offset, triangles[i][2] + offset, triangles[i][1] + offset]
            top_faces.append(top_face)

        faces: list[list[int]] = bottom_faces + top_faces

        # Create side faces with consistent winding
        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, c, d, b])  # Changed winding order for side faces
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    def compute_elementgeometry(self) -> Mesh:
        """Compute the top and bottom polygons of the beam.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The mesh of the beam.
        """

        if self.features:
            shape = self.shape if self.shape else self._loft(self.section)
            mid_point: Point = self.center_line.midpoint
            cut_meshes: list[Mesh] = []
            for feature in self.features:
                if isinstance(feature, BeamFeature):
                    cut_mesh: Mesh = self._loft(feature.section)
                    frame = Frame(mid_point, [1, 0, 0], [0, 1, 0])
                    cut_mesh.transform(Scale.from_factors([1, 1, 2], frame))
                    cut_meshes.append(cut_mesh)

            from compas.geometry import boolean_intersection_mesh_mesh

            for cut_mesh in cut_meshes:
                A = shape.to_vertices_and_faces(triangulated=True)
                B = cut_mesh.to_vertices_and_faces(triangulated=True)

                V, F = boolean_intersection_mesh_mesh(A, B)
                shape: Mesh = Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else shape

            return shape

        else:
            mesh: Mesh = self._loft(self.section)
            return mesh

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length
        self.compute_elementgeometry()

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.length])

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
        box = self.modelgeometry.obb()
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

    @classmethod
    def from_t_profile(
        cls,  # type: ignore
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
    ) -> None:
        """Create a T profile beam element.

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
        """

        _width: float = abs(width)
        _height: float = abs(height)
        _step_width_left: float = abs(step_width_left)
        _step_width_right: float = abs(step_width_right) if step_width_right is not None else step_width_left
        _step_height_left: float = abs(step_height_left)
        _step_height_right: float = abs(step_height_right) if step_height_right is not None else step_height_left

        _step_width_left = min(_step_width_left, width * 0.5 * 0.999)
        _step_width_right = min(_step_width_right, width * 0.5 * 0.999)
        _step_height_left = min(_step_height_left, height)
        _step_height_right = min(_step_height_right, height)

        polygon = Polygon(
            [
                [_width * 0.5, -_height * 0.5, 0],
                [-_width * 0.5, -_height * 0.5, 0],
                [-_width * 0.5, -_height * 0.5 + _step_height_left, 0],
                [-_width * 0.5 + _step_width_left, -_height * 0.5 + _step_height_left, 0],
                [-_width * 0.5 + _step_width_left, _height * 0.5, 0],
                [_width * 0.5 - _step_width_right, _height * 0.5, 0],
                [_width * 0.5 - _step_width_right, -_height * 0.5 + _step_height_right, 0],
                [_width * 0.5, -_height * 0.5 + _step_height_right, 0],
            ]
        )

        if inverted:
            mirror_line: Line = Line([0, 0, 0], [1, 0, 0])
            polygon = Polygon(mirror_points_line(polygon.points, mirror_line))

        return cls(polygon, abs(length), is_support, transformation, features, name)

    # @classmethod
    # def from_v_profile(
    #     radius : float = 0.0,
    #     height0 : float = 0.0,
    #     hright1 : float = 0.0,
    #     wdith : float = 3.0,
    #     is_support: bool = False,
    #     transformation: Optional[Transformation] = None,
    #     features: Optional[list[BeamFeature]] = None,
    #     name: Optional[str] = None,) -> None:
    #     """Create a V profile beam element."""

    # pass


class BeamShapeElement(BeamElement):
    """Class representing a beam element with I profile.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The section of the beam.
    length : float, optional
        The length of the beam.
    is_support : bool, optional
        Flag indicating if the beam is a support.
    transformation : :class:`compas.geometry.Transformation`, optional
        The transformation applied to the beam.
    features : list[:class:`compas_model.features.BeamFeature`], optional
        The features of the beam.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    center_line : :class:`compas.geometry.Line`
        The axis of the beam.
    section : :class:`compas.geometry.Polygon`
        The section of the beam.

    """

    @property
    def __data__(self) -> dict:
        return {
            "shape": self.shape,
            "length": self.length,
            "is_support": self.is_support,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        shape: Union[Mesh, Brep] = None,
        length: float = 3.0,
        is_support: bool = False,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamProfileElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self._shape: Union[Mesh, Brep] = shape  # public property that can be changed any time
        self._length: float = abs(length)
        self.is_support: bool = is_support
        self._sticky_frame = shape.face_polygon(0).frame

    @property
    def shape(self) -> Union[Mesh, Brep]:
        return self._shape

    @shape.setter
    def shape(self, shape: Union[Mesh, Brep]):
        self._shape = shape
        self._geometry = None

    @property
    def sticky_frame(self) -> Frame:
        return self._sticky_frame

    def compute_elementgeometry(self) -> Mesh:
        """Compute the top and bottom polygons of the beam.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The mesh of the beam.
        """

        return self.shape

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length
        self.section = Polygon(list(self.points))
        self.compute_elementgeometry()

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.length])

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
