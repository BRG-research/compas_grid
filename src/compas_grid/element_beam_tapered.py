from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Frame
from compas.geometry import Vector
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import intersection_line_plane
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise
from compas_model.elements import Element
from compas_model.elements import Feature
from typing import List
from typing import Optional
from typing import Dict
from typing import Any
from typing import Tuple


class BeamTaperedFeature(Feature):
    pass


class BeamTaperedElement(Element):
    """Class representing a beam element.

    Parameters
    ----------
    axis : :class:`compas.geometry.Line`
        The axis of the beam.
    section_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the beam.
    section_top : :class:`compas.geometry.Polygon`
        The top polygon of the beam.
    frame_bottom : :class:`compas.geometry.Frame`, optional
        The frame of the bottom polygon.
    frame_top : :class:`compas.geometry.Frame`, optional
        The frame of the top polygon.
    features : list[:class:`BeamTaperedFeature`], optional
        Additional block features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`BeamTaperedFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(BeamTaperedElement, self).__data__
        data["axis"] = self.axis.__data__
        data["section_bottom"] = self.section_bottom
        data["section_top"] = self.section_top
        data["frame_bottom"] = self.frame_top
        data["frame_top"] = self.frame_top
        data["features"] = self.features
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "BeamTaperedElement":
        return cls(
            axis=Line(data["axis"]["start"], data["axis"]["end"]),
            section_bottom=data["section_bottom"],
            section_top=data["section_top"],
            frame_bottom=data["frame"],
            frame_top=data["frame_top"],
            features=data["features"],
        )

    def __init__(
        self,
        axis: Line,
        section_bottom: Polygon,
        section_top: Polygon,
        frame_bottom: Optional[Frame] = Frame.worldXY(),  # if beams are inclined, the shape is cut by the inclined plane
        frame_top: Optional[Frame] = None,  # if beams are inclined, the shape is cut by the inclined plane
        features: Optional[List[BeamTaperedFeature]] = None,
        name: Optional[str] = None,
    ):
        super(BeamTaperedElement, self).__init__(frame=frame_bottom, name=name)

        if len(section_bottom) != len(section_top):
            raise ValueError("The number of points in the bottom and top polygons must be the same")

        self.section_bottom: Polygon = section_bottom
        self.section_top: Polygon = section_top
        self.axis: Line = axis or Line(section_bottom[0], section_top[0])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.features: List[BeamTaperedFeature] = features or []
        self.section_bottom, self.section_top = self.compute_top_and_bottom_polygons()
        self.shape: Mesh = self.compute_shape()
        self.name = self.__class__.__name__

    @property
    def face_polygons(self) -> List[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def recompute(self):
        self.section_bottom, self.section_top = self.compute_top_and_bottom_polygons()
        self.shape: Mesh = self.compute_shape()

    def compute_top_and_bottom_polygons(self, frame_cut0: Frame = None, frame_cut1: Frame = None) -> Tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the beam.

        Returns
        -------
        Tuple[:class:`compas.geometry.Polygon`, :class:`compas.geometry.Polygon`]
        """

        plane0: Plane = Plane.from_frame(frame_cut0) if frame_cut0 else Plane.from_frame(self.frame)
        plane1: Plane = Plane.from_frame(frame_cut1) if frame_cut1 else Plane.from_frame(self.frame_top)

        points0: List[List[float]] = []
        points1: List[List[float]] = []
        for i in range(len(self.section_bottom.points)):
            line: Line = Line(self.section_bottom.points[i], self.section_top.points[i])
            result0: Optional[List[float]] = intersection_line_plane(line, plane0)
            result1: Optional[List[float]] = intersection_line_plane(line, plane1)
            if not result0 or not result1:
                raise ValueError("The line does not intersect the plane")
            points0.append(result0)
            points1.append(result1)
        self.section_bottom = Polygon(points0)
        self.section_top = Polygon(points1)
        return self.section_bottom, self.section_top

    def compute_shape(self) -> Mesh:
        """Compute the shape of the beam from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """

        offset: int = len(self.section_bottom.points)
        vertices: List[Point] = self.section_bottom.points + self.section_top.points  # type: ignore
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
    def from_cross_sections(
        cls,
        width: float = 0.1,
        depth_0: float = 0.4,
        depth_1: float = 0.2,
        height: float = 3.0,
        offset: float = 0.0,
        frame_bottom: Optional[Plane] = Frame.worldXY(),
        frame_top: Optional[Plane] = None,
        features: Optional[List[BeamTaperedFeature]] = None,
        name: str = "None",
    ) -> "BeamTaperedElement":
        """
        Create a beam element from two cross sections centered on XY frame.

        Parameters
        ----------
        width : float, optional
            The width of the beam.
        depth_0 : float, optional
            The depth of the beam at the bottom.
        depth_1 : float, optional
            The depth of the beam at the top.
        height : float, optional
            The height of the beam.
        frame_bottom : :class:`compas.geometry.Plane`, optional
            The frame of the bottom polygon.
        frame_top : :class:`compas.geometry.Plane`, optional
            The frame of the top polygon.
        features : list[:class:`BeamFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`BeamTaperedElement`


        """

        t0 = 0
        t1 = 1 - t0
        offset = (depth_1 - depth_0) * 0.5

        p00: List[float] = [width * 0.5, -depth_0 * 0.5, 0]
        p01: List[float] = [width * 0.5, depth_0 * 0.5, 0]
        p02: List[float] = [-width * 0.5, depth_0 * 0.5, 0]
        p03: List[float] = [-width * 0.5, -depth_0 * 0.5, 0]
        polygon_0: Polygon = Polygon([p00, p01, p02, p03])

        p10: List[float] = [width * 0.5, -depth_1 * 0.5 - offset, height]
        p11: List[float] = [width * 0.5, depth_1 * 0.5 - offset, height]
        p12: List[float] = [-width * 0.5, depth_1 * 0.5 - offset, height]
        p13: List[float] = [-width * 0.5, -depth_1 * 0.5 - offset, height]
        polygon_1: Polygon = Polygon([p10, p11, p12, p13])

        # recenter
        polygon_1.translate([-width * 0.0, depth_0 * -0.5, 0])
        polygon_0.translate([-width * 0.0, depth_0 * -0.5, 0])

        axis: Line = Line(Point(0, 0, 0), Point(0, 0, height))

        beam: BeamTaperedElement = cls(axis=axis, section_bottom=polygon_0, section_top=polygon_1, frame_bottom=frame_bottom, frame_top=frame_top, features=features, name=name)
        return beam


if __name__ == "__main__":
    from compas_viewer import Viewer

    beam: BeamTaperedElement = BeamTaperedElement.from_cross_sections(
        frame_bottom=Frame(Point(0, 0, 0), Vector(1, 0, 0), Vector(0, 1, 0)), frame_top=Frame(Point(0, 0, 2.0), Vector(1, 0, 0), Vector(0, 1, 0))
    )
    viewer: Viewer = Viewer()
    viewer.scene.add(beam.shape)
    viewer.show()
