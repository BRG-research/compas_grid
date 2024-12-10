
from enum import Enum
from compas.geometry import Point, Vector
from compas.datastructures import Mesh


###########################################################################################
# Generate rules.
# TODO generate rules from the local graph using v, e, f:
# v - points, first one is always the origin
# e - first find nearest edges, edges starts from v0 between points v0-v1, v0-v2 and so on
# f - faces between points v0-v1-v2-v3 and so on
# This local graph should be independent from any datastructure.
###########################################################################################

class CardinalDirections(int, Enum):
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
    def get_direction_combination(cls, direction1: 'CardinalDirections', direction2: 'CardinalDirections') -> 'CardinalDirections':
        """
        Get the direction combination of two directions.

        Parameters
        -------
        direction1 : CardinalDirections
            The first direction.
        direction2 : CardinalDirections
            The second direction.

        Returns
        -------
        CardinalDirections
            The direction combination.
        """
        direction_combinations: dict[tuple[int, int], 'CardinalDirections'] = {
            (CardinalDirections.NORTH, CardinalDirections.WEST): CardinalDirections.NORTH_WEST,
            (CardinalDirections.WEST, CardinalDirections.NORTH): CardinalDirections.NORTH_WEST,
            (CardinalDirections.WEST, CardinalDirections.SOUTH): CardinalDirections.SOUTH_WEST,
            (CardinalDirections.SOUTH, CardinalDirections.WEST): CardinalDirections.SOUTH_WEST,
            (CardinalDirections.SOUTH, CardinalDirections.EAST): CardinalDirections.SOUTH_EAST,
            (CardinalDirections.EAST, CardinalDirections.SOUTH): CardinalDirections.SOUTH_EAST,
            (CardinalDirections.NORTH,CardinalDirections.EAST): CardinalDirections.NORTH_EAST,
            (CardinalDirections.EAST, CardinalDirections.NORTH): CardinalDirections.NORTH_EAST,
        }
        return direction_combinations[(direction1, direction2)]


def closest_direction(
    vector: Vector,
    directions: dict[CardinalDirections, Vector] = {
        CardinalDirections.NORTH: Vector(0, 1, 0),
        CardinalDirections.EAST: Vector(1, 0, 0),
        CardinalDirections.SOUTH: Vector(0, -1, 0),
        CardinalDirections.WEST: Vector(-1, 0, 0),
    },
) -> CardinalDirections:
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
    CardinalDirections
        The closest cardinal direction.
    """
    # Unitize the given vector
    vector.unitize()

    # Compute dot products with cardinal direction vectors
    dot_products: dict[CardinalDirections, float] = {}
    for direction, unit_vector in directions.items():
        dot_product = vector.dot(unit_vector)
        dot_products[direction] = dot_product

    # Find the direction with the maximum dot product
    closest: CardinalDirections = max(dot_products, key=dot_products.get)
    return closest



v : dict[Point] = {
    7 : Point(0,0,0),
    5 : Point(-1,0,0),
    6 : Point(0,1,0),
    8 : Point(0,-1,0),
    2 : Point(1,0,0),
}

e : list[tuple[int, int]] = [
    # (7, 5),
    # (7, 6),
    (7, 8),
    (7, 2),
]

f : list[list[int]] = [
    # [5, 7, 6, 10],
    # [2, 7, 6, 10]
    [2, 7, 8, 10]
]

def generate_rules(v: dict[Point], e: list[tuple[int, int]], f: list[list[int]]) -> list[bool]:
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
    list
        The generated rules.
    """
    
    rules = [False, False, False, False, False, False, False, False]
    edge_directions : dict[tuple[int, int], CardinalDirections] = {}

    # Find the directions of the edges
    for edge in e:
        
        if not edge[0] in v:
            raise ValueError(f"Vertex {edge[0]} not found in the vertices.")
        if not edge[1] in v:
            raise ValueError(f"Vertex {edge[1]} not found in the vertices.")
        
        p0 = v[edge[0]]
        p1 = v[edge[1]]
        vector = p1 - p0
        direction = closest_direction(vector)
        rules[direction] = True
        
        # track direction for face edge search
        edge_directions[(edge[0], edge[1])] = direction
        edge_directions[(edge[1], edge[0])] = direction
        

    for face in f:
        face_edge_directions = []
        for i in range(len(face)):
            v0 = face[i]
            v1 = face[(i+1)%len(face)]
            
            if not (v0, v1) in edge_directions:
                continue
            
            face_edge_directions.append(edge_directions[(v0, v1)])
        
        # Face must have two directions
        if not len(face_edge_directions) == 2:
            raise ValueError(f"Face {face} does not share two edges.")
        
        face_direction : CardinalDirections = CardinalDirections.get_direction_combination(face_edge_directions[0], face_edge_directions[1])
        rules[face_direction] = True
            

    return rules

rules = generate_rules(v, e, f)


###########################################################################################
# Generate mesh based on the rules.
###########################################################################################

# Geomeetrical parameters of the column head.
_width, _depth, _height, _offset = 150, 150, 300, 210

vertices: list[Point] = [
    # Outer ring
    Point(_width, _depth+_offset, -_height) , # 0    
    Point(-_width, _depth+_offset, -_height), # 1
    Point(-_width-_offset, _depth, -_height), # 2
    Point(-_width-_offset, -_depth, -_height), # 3
    Point(-_width, -_depth-_offset, -_height), # 4 
    Point(_width, -_depth-_offset, -_height), # 5
    Point(_width+_offset, -_depth, -_height) , # 6
    Point(_width+_offset, _depth, -_height) , # 7
    # Inner quad
    Point(_width, _depth, -_height), # 8
    Point(-_width, _depth, -_height), # 9
    Point(-_width, -_depth, -_height), # 10
    Point(_width, -_depth, -_height), # 11
    # Top quad
    Point(_width, _depth, 0), # 12
    Point(-_width, _depth, 0), # 13
    Point(-_width, -_depth, 0), # 14
    Point(_width, -_depth, 0), # 15
]

# Check if two floor plate has two beams else plate cannot be connected to column head.
for i in range(4):
    if rules[i*2+1]:
        if not rules[i*2] or not rules[(i*2+2)%8]:
            rules[i*2+1] = False

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
from math import ceil, floor
for i in range(8):
    if rules[i]:
        continue
    
    if rules[(i-1)%8]:
        v0 = (i)%8
        inner_v = int(ceil(((i+0)%8)*0.5))%4 + 8
        v1 = inner_v
        v2 = inner_v+4
        faces.append([v0, v1, v2])
    
    if rules[(i+1)%8]:
        v0 = (i+1)%8
        inner_v = int(ceil(((i+1)%8)*0.5))%4 + 8
        v1 = inner_v
        v2 = inner_v+4
        faces.append([v0, v1, v2])   

# Inner quad vertical triangle faces
for i in range(4):
    if not rules[i*2]:
        v0 = i+8
        v1 = (i+1)%4+8
        v2 = v1+4
        v3 = v0+4
        faces.append([v0, v1, v2, v3])   

mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
mesh.remove_unused_vertices()



from compas_snippets.viewer_live import ViewerLive
viewer = ViewerLive()

for i, v in enumerate(vertices):
    point = v.copy()
    point.name = str(i)
    point.scale(0.001)
    viewer.add(point)
viewer.add(mesh.scaled(0.001))
viewer.serialize()
# viewer.run()
