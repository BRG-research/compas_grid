from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_grid.elements import BaseElement
from compas_grid.shapes import CrossBlockShape


class ColumnHeadElement(BaseElement):
    """Class representing a column head element.

    Parameters
    ----------
    mesh : :class:`compas.datastructures.Mesh`
        The base shape of the column head.
    frame : :class:`compas.geometry.Frame`, optional
        The frame of the column head.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(ColumnHeadElement, self).__data__
        data["shape"] = self.shape
        return data

    @classmethod
    def __from_data__(cls, data: dict[str, any]) -> "ColumnHeadElement":
        return cls(
            mesh=data["shape"],
        )

    def __init__(self, mesh: Mesh, frame: Frame = Frame.worldXY(), name: str = None):
        super(ColumnHeadElement, self).__init__(frame=frame, name=name)
        self.type = None
        self.shape: Mesh = mesh
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

    @classmethod
    def from_box(cls, width: float = 0.4, depth: float = None, height: float = None, name: str = "None") -> "ColumnHeadElement":
        """Create a column head element from a square section centered on XY frame.


        Parameters
        ----------
        width : float
            The width of the column head.
        depth : float, optional
            The depth of the column head.
        height : float, optional
            The height of the column head.
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

        column_head_element: ColumnHeadElement = cls(mesh=mesh, name=name)
        return column_head_element

    @classmethod
    def from_mesh(cls, mesh: Mesh, name: str = "None") -> "ColumnHeadElement":
        """Create a column head element from a mesh.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            The mesh of the column head.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance.
        """

        column_head_element: ColumnHeadElement = cls(mesh=mesh, name=name)
        return column_head_element

    @classmethod
    def from_column_head_cross_shape(
        cls,
        v: list[Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
        width=150,
        depth=150,
        height=300,
        offset=210,
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
        start_direction : :class:`CardinalDirections`
            The start direction of the quadrant.
        end_direction : :class:`CardinalDirections`
            The end direction of the quadrant.
        width : float
            The width of the column head.
        depth : float
            The depth of the column head.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnHeadElement`
            Column head instance

        Example
        -------
        start_direction = CardinalDirections.NORTH
        end_direction = CardinalDirections.EAST
        column_head_element = ColumnHeadElement.from_quadrant(start_direction, end_direction, width=1.0, depth=1.0)
        """
        column_head_cross_shape: CrossBlockShape = CrossBlockShape(v, e, f, width, depth, height, offset)
        mesh: Mesh = column_head_cross_shape.mesh.copy()  # Copy because the meshes are created only once.
        column_head_element: ColumnHeadElement = cls(mesh=mesh, name=name)
        return column_head_element
