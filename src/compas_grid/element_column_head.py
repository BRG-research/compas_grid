from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Polygon
from compas.geometry import Frame
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_model.elements import Element
from compas_model.elements import Feature
from typing import List
from typing import Optional
from typing import Dict
from typing import Any


class ColumnHeadFeature(Feature):
    pass


class ColumnHeadElement(Element):
    """Class representing a column head element.

    Parameters
    ----------
    mesh : :class:`compas.datastructures.Mesh`
        The base shape of the column head.
    frame : :class:`compas.geometry.Frame`, optional
        The frame of the column head.
    features : list[:class:`ColumnHead]
        Additional block features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`ColumnHeadFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = super(ColumnHeadElement, self).__data__
        data["shape"] = self.shape
        data["features"] = self.features
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ColumnHeadElement":
        return cls(
            mesh=data["shape"],
            features=data["features"],
        )

    def __init__(self, mesh: Mesh, frame: Frame = Frame.worldXY(), features: Optional[List[ColumnHeadFeature]] = None, name: Optional[str] = None):
        super(ColumnHeadElement, self).__init__(frame=frame, name=name)
        self.features: List[ColumnHeadFeature] = features or []
        self.shape: Mesh = mesh
        self.name = self.__class__.__name__

    @property
    def face_polygons(self) -> List[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self) -> Mesh:
        """Compute the shape of the column head.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        # This method is redundant unless more specific implementation is needed...
        return self.shape

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
    def from_box(
        cls, width: float = 0.4, depth: Optional[float] = None, height: Optional[float] = None, features: Optional[List[ColumnHeadFeature]] = None, name: str = "None"
    ) -> "ColumnHeadElement":
        """Create a column head element from a square section centered on XY frame.


        Parameters
        ----------
        width : float
            The width of the column head.
        depth : float, optional
            The depth of the column head.
        height : float, optional
            The height of the column head.
        features : list[:class:`ColumnHeadFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance.
        """

        box: Box = Box(xsize=width, ysize=depth, zsize=height, frame=Frame.worldXY())
        box.translate([0, 0, height * 0.5])
        mesh: Mesh = Mesh.from_vertices_and_faces(box.vertices, box.faces)

        column_head_element: ColumnHeadElement = cls(mesh=mesh, features=features, name=name)
        return column_head_element

    @classmethod
    def from_loft(
        cls, polygons: List[Polygon], top_holes: List[Polygon] = [], bottom_holes: List[Polygon] = [], features: Optional[List[ColumnHeadFeature]] = None, name: str = "None"
    ) -> "ColumnHeadElement":
        """Loft a list of polygons.
        When top and bottom holes are provided, inner loft is created too.

        Parameters
        ----------
        polygons : list[:class:`Polygon`]
            The list of polygons to loft.
        top_holes : list[:class:`Polygon`]
            The list of polygons to loft.
        bottom_holes : list[:class:`Polygon`]
            The list of polygons to loft.
        features : list[:class:`ColumnHeadFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance.
        """

        ########################################################################################
        #  Top and bottom polygons
        ########################################################################################
        from compas_cgal.triangulation import conforming_delaunay_triangulation

        # Mesh top and bottom polygons
        polygon_0 = polygons[0]
        polygon_1 = polygons[-1]

        v_0, f_0 = conforming_delaunay_triangulation(boundary=polygon_0, holes=top_holes)
        v_0 = v_0.tolist()
        f_0 = f_0.tolist()
        v_1, f_1 = [], []
        v_1.extend(polygon_1.points)
        for hole in bottom_holes:
            v_1.extend(hole.points)

        for f in f_0:
            face = [i + len(v_0) for i in f]
            face.reverse()
            f_1.append(face)

        # Mesh side polygons
        v, f = [], []
        v.extend(v_0)
        f.extend(f_0)
        v.extend(v_1)
        f.extend(f_1)

        ########################################################################################
        # Inner sides
        ########################################################################################

        n_top = len(v_0)
        n_boundary = len(polygon_0.points)
        n_hole_vertex = n_top - n_boundary
        for i in range(0, n_hole_vertex):
            face = [i + n_boundary, (i + 1) % n_hole_vertex + n_boundary, (i + 1) % n_hole_vertex + n_boundary + n_top, i + n_boundary + n_top]
            f.append(face)

        ########################################################################################
        # Outer sides
        ########################################################################################

        v_count = len(v)

        for i in range(1, len(polygons) - 1):
            v.extend(polygons[i].points)

        n = len(polygons[0].points)
        a = 0
        b = n_top * 2

        for j in range(n):
            f.append([j, (j + 1) % n, (j + 1) % n + b, j + b])

        for i in range(1, len(polygons) - 2):
            c = (i - 1) * n
            for j in range(n):
                f.append([v_count + c + j, v_count + c + (j + 1) % n, v_count + c + (j + 1) % n + n, v_count + c + j + n])

        # Side faces for the last polygon
        b = n_top
        c = (len(polygons) - 3) * n
        for j in range(n):
            f.append([v_count + c + j, v_count + c + (j + 1) % n, (j + 1) % n + b, j + b])

        ########################################################################################
        # Create Mesh
        ########################################################################################
        for face in f:
            face.reverse()
        mesh = Mesh.from_vertices_and_faces(v, f)

        ########################################################################################
        # Create Element
        ########################################################################################
        column_head_element: ColumnHeadElement = cls(mesh=mesh, features=features, name=name)
        return column_head_element


if __name__ == "__main__":
    from compas_viewer import Viewer

    column_head: ColumnHeadElement = ColumnHeadElement.from_box()
    column_head.copy()

    viewer: Viewer = Viewer()
    viewer.scene.add(column_head.shape)
    viewer.show()
