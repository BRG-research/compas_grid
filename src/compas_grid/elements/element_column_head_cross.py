from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_grid.elements import BaseElement
from compas_grid.shapes import CrossBlockShape


class ColumnHeadCrossElement(BaseElement):
    """Create a column head element from a quadrant.

    Subtraction of the directions provides what type of mesh is generated:
    - HALF: 1 face
    - QUARTER: 2 faces
    - THREE_QUARTERS: 3 faces
    - FULL: 4 faces

    Parameters
    ----------
    v : dict[int, Point]
        The points, first one is always the origin.
    e : list[tuple[int, int]]
        Edges starts from v0 between points v0-v1, v0-v2 and so on.
    f : list[list[int]]
        Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.
    width : float
        The width of the column head.
    depth : float
        The depth of the column head.
    height : float
        The height of the column head.
    offset : float
        The offset of the column head.

    Returns
    -------
    :class:`ColumnHeadCrossElement`
        Column head instance

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.

    Example
    -------

    width: float = 150
    depth: float = 150
    height: float = 300
    offset: float = 210
    v: dict[int, Point] = {
        7: Point(0, 0, 0),
        5: Point(-1, 0, 0),
        6: Point(0, 1, 0),
        8: Point(0, -1, 0),
        2: Point(1, 0, 0),
    }

    e: list[tuple[int, int]] = [
        (7, 5),
        (7, 6),
        (7, 8),
        (7, 2),
    ]

    f: list[list[int]] = [[5, 7, 6, 10]]
    column_head_cross = ColumnHeadCrossElement(v=v, e=e, f=f, width=width, depth=depth, height=height, offset=offset)


    """

    @property
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(ColumnHeadCrossElement, self).__data__
        data["v"] = self.v
        data["e"] = self.e
        data["f"] = self.f
        data["width"] = self.width
        data["depth"] = self.depth
        data["height"] = self.height
        data["offset"] = self.offset
        return data

    @classmethod
    def __from_data__(cls, data: dict[str, any]) -> "ColumnHeadCrossElement":
        return cls(data["v"], data["e"], data["f"], data["width"], data["depth"], data["height"], data["offset"], data["name"])

    def __init__(
        self,
        v: dict[int, Point] = {
            7: Point(0, 0, 0),
            5: Point(-1, 0, 0),
            6: Point(0, 1, 0),
            8: Point(0, -1, 0),
            2: Point(1, 0, 0),
        },
        e: list[tuple[int, int]] = [
            (7, 5),
            (7, 6),
            (7, 8),
            (7, 2),
        ],
        f: list[list[int]] = [[5, 7, 6, 10]],
        width=150,
        depth=150,
        height=300,
        offset=210,
        name: str = "None",
    ) -> "ColumnHeadCrossElement":
        super(ColumnHeadCrossElement, self).__init__(frame=Frame.worldXY(), name=name)
        self.v = v
        self.e = e
        self.f = f
        self.width = width
        self.depth = depth
        self.height = height
        self.offset = offset
        column_head_cross_shape: CrossBlockShape = CrossBlockShape(v, e, f, width, depth, height, offset)
        self.shape: Mesh = column_head_cross_shape.mesh.copy()  # Copy because the meshes are created only once.
        self.name = self.__class__.__name__ if name is None or name == "None" else name

    @property
    def face_polygons(self) -> list[Polygon]:
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
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
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
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
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

        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    def rebuild(
        self,
        v: list[Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
    ) -> "ColumnHeadCrossElement":
        """Rebuild the column with a new height.

        Parameters
        ----------
        v : dict[int, Point]
            The points, first one is always the origin.
        e : list[tuple[int, int]]
            Edges starts from v0 between points v0-v1, v0-v2 and so on.
        f : list[list[int]]
            Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.

        Returns
        -------
        :class:`ColumnHeadCrossElement`
            The new column head cross element.
        """
        return ColumnHeadCrossElement(v=v, e=e, f=f, width=self.width, depth=self.depth, height=self.height, offset=self.offset, name=self.name)
