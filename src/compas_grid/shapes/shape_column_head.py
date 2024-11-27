from enum import Enum

from compas.datastructures import Mesh
from compas.geometry import Point
from compas.geometry import Vector


class ColumnHeadDirection(int, Enum):
    """
    Enumeration of directions where the number corresponds to the column head mesh face index.

    Attributes
    ----------
    NORTH : int
        The north direction.
    NORTH_WEST : int
        The north-west direction.
    WEST : int
        The west direction.
    SOUTH_WEST : int
        The south-west direction.
    SOUTH : int
        The south direction.
    SOUTH_EAST : int
        The south-east direction.
    EAST : int
        The east direction.
    NORTH_EAST : int
        The north-east direction.
    """

    NORTH = 0
    NORTH_WEST = 1
    WEST = 2
    SOUTH_WEST = 3
    SOUTH = 4
    SOUTH_EAST = 5
    EAST = 6
    NORTH_EAST = 7

    @classmethod
    def get_direction_combination(cls, direction1: "ColumnHeadDirection", direction2: "ColumnHeadDirection") -> "ColumnHeadDirection":
        """
        Get the direction combination of two directions.

        Parameters
        -------
        direction1 : ColumnHeadDirection
            The first direction.
        direction2 : ColumnHeadDirection
            The second direction.

        Returns
        -------
        ColumnHeadDirection
            The direction combination.
        """
        direction_combinations: dict[tuple[int, int], "ColumnHeadDirection"] = {
            (ColumnHeadDirection.NORTH, ColumnHeadDirection.WEST): ColumnHeadDirection.NORTH_WEST,
            (ColumnHeadDirection.WEST, ColumnHeadDirection.NORTH): ColumnHeadDirection.NORTH_WEST,
            (ColumnHeadDirection.WEST, ColumnHeadDirection.SOUTH): ColumnHeadDirection.SOUTH_WEST,
            (ColumnHeadDirection.SOUTH, ColumnHeadDirection.WEST): ColumnHeadDirection.SOUTH_WEST,
            (ColumnHeadDirection.SOUTH, ColumnHeadDirection.EAST): ColumnHeadDirection.SOUTH_EAST,
            (ColumnHeadDirection.EAST, ColumnHeadDirection.SOUTH): ColumnHeadDirection.SOUTH_EAST,
            (ColumnHeadDirection.NORTH, ColumnHeadDirection.EAST): ColumnHeadDirection.NORTH_EAST,
            (ColumnHeadDirection.EAST, ColumnHeadDirection.NORTH): ColumnHeadDirection.NORTH_EAST,
        }
        return direction_combinations[(direction1, direction2)]


class ColumnHeadShape:
    """Generate Column Head shapes based on vertex and edge and face adjacency.
    The class is singleton, considering the dimension of the column head is fixed and created once.

    Parameters
    ----------
    width : float
        The width of the column head.
    depth : float
        The depth of the column head.
    height : float
        The height of the column head.
    offset : float
        The offset of the column head.
    v : dict[int, Point]
        The points, first one is always the origin.
    e : list[tuple[int, int]]
        Edges starts from v0 between points v0-v1, v0-v2 and so on.
    f : list[list[int]]
        Faces between points v0-v1-v2-v3 and so on. If face vertices forms already given edges. Triangle mesh face is formed.


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

    columnHeadShape: ColumnHeadShape = ColumnHeadShape(v, e, f, width, depth, height, offset)
    mesh = columnHeadShape.mesh.scaled(0.001)

    """

    _instance = None
    _generated_meshes = {}
    _last_mesh = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ColumnHeadShape, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        v: dict[int, Point],
        e: list[tuple[int, int]],
        f: list[list[int]],
        width: float = 150,
        depth: float = 150,
        height: float = 300,
        offset: float = 210,
    ):
        if not hasattr(self, "_initialized"):
            self._width = width
            self._depth = depth
            self._height = height
            self._offset = offset
        rules = self._generate_rules(v, e, f)
        self._generated_meshes[rules] = self._generate_mesh(rules)
        self._last_mesh = self._generated_meshes[rules]
        self._initialized = True

    def _closest_direction(
        self,
        vector: Vector,
        directions: dict[ColumnHeadDirection, Vector] = {
            ColumnHeadDirection.NORTH: Vector(0, 1, 0),
            ColumnHeadDirection.EAST: Vector(1, 0, 0),
            ColumnHeadDirection.SOUTH: Vector(0, -1, 0),
            ColumnHeadDirection.WEST: Vector(-1, 0, 0),
        },
    ) -> ColumnHeadDirection:
        """
        Find the closest cardinal direction for a given vector.

        Parameters
        -------
        vector : Vector
            The vector to compare.

        directions : dict
            A dictionary of cardinal directions and their corresponding unit vectors.

        Returns
        -------
        ColumnHeadDirection
            The closest cardinal direction.
        """
        # Unitize the given vector
        vector.unitize()

        # Compute dot products with cardinal direction vectors
        dot_products: dict[ColumnHeadDirection, float] = {}
        for direction, unit_vector in directions.items():
            dot_product = vector.dot(unit_vector)
            dot_products[direction] = dot_product

        # Find the direction with the maximum dot product
        closest: ColumnHeadDirection = max(dot_products, key=dot_products.get)
        return closest

    def _generate_rules(self, v: dict[Point], e: list[tuple[int, int]], f: list[list[int]]) -> list[bool]:
        """
        Generate rules for generating the mesh of the column head.
        ATTENTION: edge first vertex is considered the column head origin, otherwise direction are flipped.

        Parameters
        -------
        v : dict
            The points, first one is always the origin.
        e : list
            First find nearest edges, edges starts from v0 between points v0-v1, v0-v2 and so on.
        f : list
            Faces between points v0-v1-v2-v3 and so on.

        Returns
        -------
        tuple
            The generated rules.
        """

        rules = [False, False, False, False, False, False, False, False]
        edge_directions: dict[tuple[int, int], ColumnHeadDirection] = {}

        # Find the directions of the edges
        for edge in e:
            if edge[0] not in v:
                raise ValueError(f"Vertex {edge[0]} not found in the vertices.")
            if edge[1] not in v:
                raise ValueError(f"Vertex {edge[1]} not found in the vertices.")

            p0 = v[edge[0]]
            p1 = v[edge[1]]
            vector = p1 - p0
            direction = self._closest_direction(vector)
            rules[direction] = True

            # track direction for face edge search
            edge_directions[(edge[0], edge[1])] = direction
            edge_directions[(edge[1], edge[0])] = direction

        for face in f:
            face_edge_directions = []
            for i in range(len(face)):
                v0 = face[i]
                v1 = face[(i + 1) % len(face)]

                if (v0, v1) not in edge_directions:
                    continue

                face_edge_directions.append(edge_directions[(v0, v1)])

            # Face must have two directions
            if not len(face_edge_directions) == 2:
                raise ValueError(f"Face {face} does not share two edges.")

            face_direction: ColumnHeadDirection = ColumnHeadDirection.get_direction_combination(face_edge_directions[0], face_edge_directions[1])
            rules[face_direction] = True

        return tuple(rules)

    def _generate_mesh(self, rules: tuple[bool]) -> Mesh:
        """
        Generate mesh based on the rules.

        Parameters
        ----------

        rules : tuple
            The generated rules that corresponds to world direction using ColumnHeadDirection enumerator.

        Returns
        -------
        Mesh
            The column head generated mesh.

        """

        if rules in self._generated_meshes:
            return self._generated_meshes[rules]

        ###########################################################################################
        # Generate mesh based on the rules.
        ###########################################################################################

        vertices: list[Point] = [
            # Outer ring
            Point(self._width, self._depth + self._offset, -self._height),  # 0
            Point(-self._width, self._depth + self._offset, -self._height),  # 1
            Point(-self._width - self._offset, self._depth, -self._height),  # 2
            Point(-self._width - self._offset, -self._depth, -self._height),  # 3
            Point(-self._width, -self._depth - self._offset, -self._height),  # 4
            Point(self._width, -self._depth - self._offset, -self._height),  # 5
            Point(self._width + self._offset, -self._depth, -self._height),  # 6
            Point(self._width + self._offset, self._depth, -self._height),  # 7
            # Inner quad
            Point(self._width, self._depth, -self._height),  # 8
            Point(-self._width, self._depth, -self._height),  # 9
            Point(-self._width, -self._depth, -self._height),  # 10
            Point(self._width, -self._depth, -self._height),  # 11
            # Top quad
            Point(self._width, self._depth, 0),  # 12
            Point(-self._width, self._depth, 0),  # 13
            Point(-self._width, -self._depth, 0),  # 14
            Point(self._width, -self._depth, 0),  # 15
        ]

        # Check if two floor plate has two beams else plate cannot be connected to column head.
        for i in range(4):
            if rules[i * 2 + 1]:
                if not rules[i * 2] or not rules[(i * 2 + 2) % 8]:
                    rules[i * 2 + 1] = False

        faces = [
            [8, 9, 10, 11],
            [12, 13, 14, 15],
        ]

        if rules[0]:
            faces.append([0, 1, 9, 8])
            faces.append([0, 1, 13, 12])

        if rules[1]:
            faces.append([1, 2, 9])
            faces.append([1, 2, 13])

        if rules[2]:
            faces.append([2, 3, 10, 9])
            faces.append([2, 3, 14, 13])

        if rules[3]:
            faces.append([3, 4, 10])
            faces.append([3, 4, 14])

        if rules[4]:
            faces.append([4, 5, 11, 10])
            faces.append([4, 5, 15, 14])

        if rules[5]:
            faces.append([5, 6, 11])
            faces.append([5, 6, 15])

        if rules[6]:
            faces.append([6, 7, 8, 11])
            faces.append([6, 7, 12, 15])

        if rules[7]:
            faces.append([7, 0, 8])
            faces.append([7, 0, 12])

        # Outer ring vertical triangle faces
        from math import ceil

        for i in range(8):
            if rules[i]:
                continue

            if rules[(i - 1) % 8]:
                v0 = (i) % 8
                inner_v = int(ceil(((i + 0) % 8) * 0.5)) % 4 + 8
                v1 = inner_v
                v2 = inner_v + 4
                faces.append([v0, v1, v2])

            if rules[(i + 1) % 8]:
                v0 = (i + 1) % 8
                inner_v = int(ceil(((i + 1) % 8) * 0.5)) % 4 + 8
                v1 = inner_v
                v2 = inner_v + 4
                faces.append([v0, v1, v2])

        # Inner quad vertical triangle faces
        for i in range(4):
            if not rules[i * 2]:
                v0 = i + 8
                v1 = (i + 1) % 4 + 8
                v2 = v1 + 4
                v3 = v0 + 4
                faces.append([v0, v1, v2, v3])

        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        mesh.remove_unused_vertices()
        return mesh

    @property
    def mesh(self):
        return self._last_mesh


if __name__ == "__main__":
    from compas_snippets.viewer_live import ViewerLive

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

    viewer = ViewerLive()

    columnHeadShape: ColumnHeadShape = ColumnHeadShape(v, e, f, width, depth, height, offset)
    print(columnHeadShape._generated_meshes)
    viewer.add(columnHeadShape.mesh.scaled(0.001))

    columnHeadShape: ColumnHeadShape = ColumnHeadShape(v, e, [], width, depth, height, offset)
    print(columnHeadShape._generated_meshes)
    viewer.add(columnHeadShape.mesh.scaled(0.001))

    viewer.serialize()
    # viewer.run()
