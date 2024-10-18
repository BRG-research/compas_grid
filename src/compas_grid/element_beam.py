from compas.datastructures import Mesh
from compas.geometry import Box, Line, Polygon, Frame, Vector, Plane
from compas.geometry import intersection_line_plane
from compas.geometry import bounding_box, oriented_bounding_box
from compas.geometry import cross_vectors
from compas.itertools import pairwise
from compas.geometry import boolean_intersection_mesh_mesh, boolean_difference_mesh_mesh
from compas_model.elements import Element, Feature
from typing import List, Optional, Dict, Any, Union, Tuple


class BeamFeature(Feature):
    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(BeamFeature, self).__data__
        return data

    def __init__(self, name: Optional[str] = None):
        super(BeamFeature, self).__init__()


class BeamFeatureOutlineCut(BeamFeature):
    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(BeamFeatureOutlineCut, self).__data__
        data["polygon"] = self.polygon
        data["depth"] = self.depth
        data["intersection_or_difference"] = self.intersection_or_difference
        data["shape"] = self.shape
        return data

    def __init__(self, polygon: Polygon, depth: float, intersection_or_difference: bool = True, name: Optional[str] = None):
        super(BeamFeatureOutlineCut, self).__init__()
        self.polygon: Polygon = polygon
        self.depth: float = depth
        self.intersection_or_difference: bool = intersection_or_difference
        self.shape: Mesh = self.compute_shape()

    def average_normal(self) -> Vector:
        """
        Compute the average normal of a Polygon.

        Returns
        -------
        compas.geometry.Vector
            The average normal vector.
        """
        n = len(self.polygon.points)
        normal = Vector(0, 0, 0)

        for i in range(n):
            num = (i - 1 + n) % n
            item1 = (i + 1 + n) % n
            point3d = self.polygon[num]
            point3d1 = self.polygon[item1]
            item2 = self.polygon[i]
            normal += cross_vectors(Vector.from_start_end(point3d, item2), Vector.from_start_end(item2, point3d1))

        normal.unitize()

        return normal

    def compute_shape(self) -> Mesh:
        """Compute the shape of the feature, it will be used to for Boolean Intersection.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """

        offset: int = len(self.polygon)
        polygon_top = self.polygon.translated(self.average_normal() * self.depth)
        vertices: List[Union[List[float], Any]] = self.polygon.points + polygon_top.points  # type: ignore
        bottom: List[int] = list(range(offset))
        top: List[int] = [i + offset for i in bottom]
        faces: List[List[int]] = [bottom[::-1], top]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, b, d, c])
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    def apply(self, shape: Mesh) -> Mesh:
        """Extrude the outline and make boolean intersection with the shape.

        Parameters
        ----------
        shape : :class:`compas.datastructures.Mesh`
            The shape to be cut.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The shape after the cut.
        """
        shape.unify_cycles()
        self.shape.unify_cycles()
        v0, f0 = shape.to_vertices_and_faces(True)
        v1, f1 = self.shape.to_vertices_and_faces(True)

        if self.intersection_or_difference:
            mesh = Mesh.from_vertices_and_faces(*boolean_intersection_mesh_mesh((v0, f0), (v1, f1)))
            mesh.name = "intersection"
            return mesh
        else:
            mesh = Mesh.from_vertices_and_faces(*boolean_difference_mesh_mesh((v0, f0), (v1, f1)))
            mesh.name = "difference"
            return mesh


class BeamElement(Element):
    """Class representing a beam elements using an axis and two polygons.
    Polygons are needed because the beam can be inclined.

    Parameters
    ----------
    axis : :class:`compas.geometry.Vector`
        The axis of the beam.
    section : :class:`compas.geometry.Polygon`
        The section of the beam.
    frame_bottom : :class:`compas.geometry.Frame`, optional
        The frame of the bottom polygon.
    frame_top : :class:`compas.geometry.Frame`, optional
        The frame of the top polygon.
    features : list[:class:`BeamFeature`], optional
        Additional block features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the beam.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the beam.
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`BeamFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(BeamElement, self).__data__
        data["axis"] = self.axis
        data["section"] = self.section
        data["frame_bottom"] = self._frame
        data["frame_top"] = self._frame_top
        data["features"] = self.features
        return data

    def __init__(
        self,
        axis: Vector,
        section: Polygon,
        frame_bottom: Optional[Frame] = Frame.worldXY(),  # if beams are inclined, the shape is cut by the inclined plane
        frame_top: Optional[Frame] = None,  # if beams are inclined, the shape is cut by the inclined plane
        features: Optional[List[BeamFeature]] = None,
        name: Optional[str] = None,
    ):
        super(BeamElement, self).__init__(frame=frame_bottom, name=name)
        self.axis: Vector = axis or Vector(1, 0, 0)
        self.section: Polygon = section
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis, self.frame.xaxis, self.frame.yaxis)
        self.features: List[BeamFeature] = features or []
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()
        self.shape: Mesh = self.compute_shape()

    @property
    def face_polygons(self) -> List[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_top_and_bottom_polygons(self) -> Tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the beam.

        Returns
        -------
        Tuple[:class:`compas.geometry.Polygon`, :class:`compas.geometry.Polygon`]
        """

        plane0: Plane = Plane.from_frame(self.frame)
        plane1: Plane = Plane.from_frame(self.frame_top)
        points0: List[List[float]] = []
        points1: List[List[float]] = []
        for i in range(len(self.section.points)):
            line: Line = Line(self.section.points[i], self.section.points[i] + self.axis)
            result0: Optional[List[float]] = intersection_line_plane(line, plane0)
            result1: Optional[List[float]] = intersection_line_plane(line, plane1)
            if not result0 or not result1:
                raise ValueError("The line does not intersect the plane")
            points0.append(result0)
            points1.append(result1)
        return Polygon(points0), Polygon(points1)

    def compute_shape(self) -> Mesh:
        """Compute the shape of the beam from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """

        offset: int = len(self.polygon_bottom)
        vertices: List[Union[List[float], Any]] = self.polygon_bottom.points + self.polygon_top.points  # type: ignore
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
        # geometry.transform(self.worldtransformation)
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
    def from_square_section(
        cls,
        width: float = 0.1,
        depth: float = 0.2,
        height: float = 3.0,
        frame_bottom: Optional[Plane] = Frame.worldXY(),
        frame_top: Optional[Plane] = None,
        features: Optional[List[BeamFeature]] = None,
        name: str = "None",
    ) -> "BeamElement":
        """Create a beam element from a square section centered on XY frame.

        Parameters
        ----------
        width : float, optional
            The width of the beam.
        depth : float, optional
            The depth of the beam.
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
        :class:`BeamElement`

        """

        p3: List[float] = [-width * 0.5, -depth * 0.5, 0]
        p2: List[float] = [-width * 0.5, depth * 0.5, 0]
        p1: List[float] = [width * 0.5, depth * 0.5, 0]
        p0: List[float] = [width * 0.5, -depth * 0.5, 0]
        polygon: Polygon = Polygon([p0, p1, p2, p3])
        axis: Vector = Vector(0, 0, height)

        beam: BeamElement = cls(axis=axis, section=polygon, frame_bottom=frame_bottom, frame_top=frame_top, features=features, name=name)
        return beam


if __name__ == "__main__":
    from compas_viewer import Viewer

    depth: float = 0.013333

    tol: float = 0.001
    outline_cut_shape: Polygon = Polygon(
        [
            [-0.01, depth * 0.5 + tol * 1, 1.0],
            [-0.07, depth * 0.5 + tol * 1, 0.01],
            [0.07, depth * 0.5 + tol * 1, 0.01],
            [0.07, depth * 0.5 + tol * 1, 1.0],
        ]
    )

    beam_feature: BeamFeatureOutlineCut = BeamFeatureOutlineCut(outline_cut_shape, depth + tol * 2)
    beam: BeamElement = BeamElement.from_square_section(width=0.15, depth=depth, height=1.2, features=[beam_feature])
    viewer: Viewer = Viewer()
    viewer.scene.add(beam.shape)
    viewer.scene.add(beam_feature.shape)
    viewer.scene.add(beam.compute_geometry(True))
    viewer.show()
