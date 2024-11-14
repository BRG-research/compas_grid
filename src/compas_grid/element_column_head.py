from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_model.elements import Element
from compas_model.elements import Feature


class ColumnHeadDirection(int, Enum):
    """
    Enumeration of directions where the number corresponds to the column head mesh face index.

    Attributes
    ----------
    NORTH : int
        Represents the first mesh face of the column_head.
    EAST : int
        Represents the second mesh face of the column_head.
    SOUTH : int
        Represents the third mesh face of the column_head.
    WEST : int
        Represents the fourth mesh face of the column_head.
    """

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


class ColumnHeadSquarePyramids:
    """Singleton class for creating column head meshes only once.
    Currently orthogonal column heads are supported.
    TODO: a separate class for non-orthogonal column heads.

    Parameters
    ----------
    _instance : ColumnHeadSquarePyramids
        The instance of the class.
    _meshes : dict
        A dictionary of meshes.
    _width : float
        The width of the column head.
    _depth : float
        The depth of the column head.
    _height : float
        The height of the column head.
    _offset : float
        The offset of the column head.

    Example
    -------
    # Class can be initialized multiple times, while meshes are built only once.
    column_head_mesh_factory: ColumnHeadSquarePyramids = ColumnHeadSquarePyramids()
    (column_head_mesh_factory.get_mesh(ColumnHeadDirection.NORTH, ColumnHeadDirection.WEST))
    """

    _instance = None
    _meshes = {}
    _width, _depth, _height, _offset = 150, 150, 300, 210

    def __new__(cls, width=150, depth=150, height=300, column_head_offset=210):
        if cls._instance is None:
            cls._instance = super(ColumnHeadSquarePyramids, cls).__new__(cls)
            cls._width = width
            cls._depth = depth
            cls._height = height
            cls._offset = column_head_offset
            cls._instance._initialize_meshes()
        return cls._instance

    def _create_mesh(self, faces: int) -> Mesh:
        """Create a column head mesh.

        Parameters
        ----------
        faces : int
            The number of faces of the column head.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The mesh of the column head.

        """
        width, depth, height = 1.0, 1.0, 1.0
        box = Box(Frame.worldXY(), width, depth, height)
        mesh = Mesh.from_vertices_and_faces(box.vertices, box.faces[:faces])
        return mesh

    def _get_key(self, start_direction: ColumnHeadDirection, end_direction: ColumnHeadDirection) -> str:
        """Generate a unique key using directions and axes.

        Attributes
        ----------
        start_direction : :class:`ColumnHeadDirection`
            The start direction of the quadrant.

        end_direction : :class:`ColumnHeadDirection`
            The end direction of the quadrant.

        Returns
        -------
        str
            The unique key.
        """
        return f"{start_direction.name}_{end_direction.name}"

    def _shift_right(self, my_list: list, n: int = 1) -> list:
        """
        Shift a list of points to the right by a specified number of positions.

        Parameters
        ----------
        points : list
            The list of points to shift.
        positions : int, optional
            The number of positions to shift the list. Default is 1.

        Returns
        -------
        list
            The shifted list of points.
        """
        if not my_list:
            return my_list
        n = n % len(my_list)  # Ensure positions is within the length of the list
        return my_list[-n:] + my_list[:-n]

    def _initialize_meshes(self) -> None:
        """Generate a quadrant mesh based on the start and end directions.

        Returns
        -------
        None
            No return value.
        """

        bottom_points_octagon: List[Point] = [
            Point(self._width, -self._depth, -self._height) + Vector(self._offset, 0, 0),
            Point(self._width, self._depth, -self._height) + Vector(self._offset, 0, 0),
            Point(self._width, self._depth, -self._height) + Vector(0, self._offset, 0),
            Point(-self._width, self._depth, -self._height) + Vector(0, self._offset, 0),
            Point(-self._width, self._depth, -self._height) + Vector(-self._offset, 0, 0),
            Point(-self._width, -self._depth, -self._height) + Vector(-self._offset, 0, 0),
            Point(-self._width, -self._depth, -self._height) + Vector(0, -self._offset, 0),
            Point(self._width, -self._depth, -self._height) + Vector(0, -self._offset, 0),
        ]

        top_points_rectangle: List[Point] = [
            Point(self._width, -self._depth, 0),
            Point(self._width, self._depth, 0),
            Point(-self._width, self._depth, 0),
            Point(-self._width, -self._depth, 0),
        ]

        for i in range(4):
            # Apply shift.
            bottom_points: List[Point] = self._shift_right(bottom_points_octagon, i * 2)
            top_points: List[Point] = self._shift_right(top_points_rectangle, i)

            # Generate keys for the 4, 3, 2, and 1 sided quadrants.
            key_4_quadrants = self._get_key(ColumnHeadDirection(i), ColumnHeadDirection((i + 3) % 4))  # N-E-S-W, E-S-W-N, S-W-N-E, W-N-E-S
            key_3_quadrants = self._get_key(ColumnHeadDirection(i), ColumnHeadDirection((i + 2) % 4))  # N-E-S, E-S-W, S-W-N, W-N-E
            key_2_quadrants = self._get_key(ColumnHeadDirection(i), ColumnHeadDirection((i + 1) % 4))  # N-E, E-S, S-W, W-N
            key_1_quadrants = self._get_key(ColumnHeadDirection(i), ColumnHeadDirection(i))  # N-N, E-E, S-S, W-W

            # Create the mesh for the 4-sided quadrant.
            v: list[Point] = []
            v.extend(bottom_points)
            v.extend(top_points)

            f: list[list[int]] = [
                [0, 8, 9, 1],
                [1, 9, 2],
                [2, 9, 10, 3],
                [3, 10, 4],
                [4, 10, 11, 5],
                [5, 11, 6],
                [6, 11, 8, 7],
                [7, 8, 0],
                [0, 1, 2, 3, 4, 5, 6, 7],
                [8, 11, 10, 9],
            ]

            mesh_4_quadrants: Mesh = Mesh.from_vertices_and_faces(v, f)

            # Create the mesh for the 3-sided quadrant.

            step: int = 6
            v.clear()
            v.extend(bottom_points[0:step])
            v.extend(top_points)

            f = [[0, 6, 7, 1], [1, 7, 2], [2, 7, 8, 3], [3, 8, 4], [4, 8, 9, 5], [5, 9, 6, 0], [0, 1, 2, 3, 4, 5], [6, 9, 8, 7]]

            mesh_3_quadrants: Mesh = Mesh.from_vertices_and_faces(v, f)

            # Create the mesh for the 2-sided quadrant.
            step: int = 4
            v.clear()
            v.extend(bottom_points[0:step])
            v.append(top_points[3] - Vector(0, 0, self._height))
            v.extend(top_points)

            f = [[0, 5, 6, 1], [1, 6, 2], [2, 6, 7, 3], [3, 7, 8, 4], [4, 8, 5, 0], [0, 1, 2, 3, 4], [5, 8, 7, 6]]

            mesh_2_quadrants: Mesh = Mesh.from_vertices_and_faces(v, f)

            # Create the mesh for the 1-sided quadrant.
            step: int = 2
            v.clear()
            v.extend(bottom_points[0:step])
            v.append(top_points[2] - Vector(0, 0, self._height))
            v.append(top_points[3] - Vector(0, 0, self._height))
            v.extend(top_points)

            f = [[0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0], [0, 1, 2, 3], [4, 7, 6, 5]]

            mesh_1_quadrants: Mesh = Mesh.from_vertices_and_faces(v, f)

            mesh_4_quadrants.name = key_4_quadrants
            mesh_3_quadrants.name = key_3_quadrants
            mesh_2_quadrants.name = key_2_quadrants
            mesh_1_quadrants.name = key_1_quadrants

            # Store the mesh in the factory.
            self._meshes[key_4_quadrants] = mesh_4_quadrants
            self._meshes[key_3_quadrants] = mesh_3_quadrants
            self._meshes[key_2_quadrants] = mesh_2_quadrants
            self._meshes[key_1_quadrants] = mesh_1_quadrants

    def get_mesh(self, start_direction: ColumnHeadDirection, end_direction: ColumnHeadDirection) -> Optional[Mesh]:
        """Get mesh by column head type.

        Parameters
        ----------
        start_direction : :class:`ColumnHeadDirection`
            The start direction of the quadrant.

        end_direction : :class:`ColumnHeadDirection`
            The end direction of the quadrant.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The mesh of the column head.
        """

        # If the order of the directions is not correct, swap them.
        start_direction_checked: ColumnHeadDirection = start_direction
        end_direction_checked: ColumnHeadDirection = end_direction

        if int(end_direction) < int(start_direction):
            start_direction_checked, end_direction_checked = end_direction, start_direction

        # Generate a unique key using directions and axes.
        name: str = self._get_key(start_direction_checked, end_direction_checked)

        # Get the mesh from the factory.
        if name not in self._meshes.keys():
            self._initialize_meshes()

        return self._meshes.get(name)

    def meshes_aligned(self) -> list[Mesh]:
        """Get all meshes aligned to the world XY plane for visualization purposes.

        Returns
        -------
        list[:class:`compas.datastructures.Mesh`]
            List of meshes aligned to the world XY plane.
        """

        meshes: List[Mesh] = []
        x_width = 0
        for _, value in self._meshes.items():
            x_width_local: float = abs(value.aabb().width)
            min_point: Point = value.aabb().points[0]
            mesh: Mesh = value.translated([-min_point[0], 0, 0])
            mesh.translate([x_width, 0, 0])
            x_width: float = x_width + x_width_local * 1.1
            meshes.append(mesh)

        return meshes


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

    @property
    def face_lowest(self) -> List[Polygon]:
        lowest_polygon: Polygon = self.face_polygons
        height: float = float("inf")
        for polygon in self.face_polygons:
            if polygon.centroid[2] < height:
                height = polygon.centroid[2]
                lowest_polygon = polygon
        return lowest_polygon

    @property
    def face_highest(self) -> List[Polygon]:
        highest_polygon: Polygon = self.face_polygons
        height: float = float("-inf")
        for polygon in self.face_polygons:
            if polygon.centroid[2] > height:
                height = polygon.centroid[2]
                highest_polygon = polygon
        return highest_polygon

    def face_nearest(self, point: List[float]) -> List[Polygon]:
        nearest_polygon: Polygon = self.face_polygons
        distance: float = float("inf")
        for polygon in self.face_polygons:
            if polygon.centroid.distance_to_point(point) < distance:
                distance = polygon.centroid.distance_to_point(point)
                nearest_polygon = polygon
        return nearest_polygon

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
        box.translate([0, 0, -height * 0.5])
        mesh: Mesh = Mesh.from_vertices_and_faces(box.vertices, box.faces)

        column_head_element: ColumnHeadElement = cls(mesh=mesh, features=features, name=name)
        return column_head_element

    @classmethod
    def from_mesh(cls, mesh: Mesh, features: Optional[List[ColumnHeadFeature]] = None, name: str = "None") -> "ColumnHeadElement":
        """Create a column head element from a mesh.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            The mesh of the column head.
        features : list[:class:`ColumnHeadFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance.
        """

        column_head_element: ColumnHeadElement = cls(mesh=mesh, features=features, name=name)
        return column_head_element

    @classmethod
    def from_loft(
        cls, polygons: List[Polygon], top_holes: List[Polygon] = [], bottom_holes: List[Polygon] = [], features: Optional[List[ColumnHeadFeature]] = None, name: str = "None"
    ) -> "ColumnHeadElement":
        """Loft a list of polygons.
        When top and bottom holes are provided, inner loft is created to itself.

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
        :class:`ColumnHeadElement`column_head_mesh_factory
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

    @classmethod
    def from_quadrant(
        cls,
        start_direction: ColumnHeadDirection,
        end_direction: ColumnHeadDirection,
        width=150,
        depth=150,
        height=300,
        offset=210,
        features: Optional[List[ColumnHeadFeature]] = None,
        name: str = "None",
    ) -> "ColumnHeadElement":
        """Create a column head element from a quadrant.

        Subtraction of the directions provides what type of mesh is generated:
        - HALF: 1 face
        - QUARTER: 2 faces
        - THREE_QUARTERS: 3 faces
        - FULL: 4 faces

        Parameters
        ----------
        start_direction : :class:`ColumnHeadDirection`
            The start direction of the quadrant.
        end_direction : :class:`ColumnHeadDirection`
            The end direction of the quadrant.
        width : float
            The width of the column head.
        depth : float
            The depth of the column head.
        features : list[:class:`ColumnHeadFeature`], optional
            Additional block features.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance

        Example
        -------
        start_direction = ColumnHeadDirection.NORTH
        end_direction = ColumnHeadDirection.EAST
        column_head_element = ColumnHeadElement.from_quadrant(start_direction, end_direction, width=1.0, depth=1.0)
        """
        column_head_mesh_factory: ColumnHeadSquarePyramids = ColumnHeadSquarePyramids(width=width, depth=depth, height=height, column_head_offset=offset)
        mesh: Mesh = column_head_mesh_factory.get_mesh(start_direction=start_direction, end_direction=end_direction)
        column_head_element: ColumnHeadElement = cls(mesh=mesh, features=features, name=name)
        return column_head_element


if __name__ == "__main__":
    column_head_mesh_factory: ColumnHeadSquarePyramids = ColumnHeadSquarePyramids()
    (column_head_mesh_factory.get_mesh(ColumnHeadDirection.NORTH, ColumnHeadDirection.WEST))

    from compas_viewer import Viewer

    viewer: Viewer = Viewer(show_grid=False)
    viewer.renderer.rendermode = "ghosted"
    viewer.renderer.view = "top"

    for mesh in column_head_mesh_factory.meshes_aligned():
        viewer.scene.add(mesh)
    # viewer.show()
