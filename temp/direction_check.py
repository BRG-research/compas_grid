from typing import List
from compas.geometry import Line
from compas.datastructures import Mesh
from compas.geometry import Vector
from compas.geometry import Point
from compas.tolerance import TOL
from compas_grid.element_column_head import CardinalDirections


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


north = Vector(0, 1, 0)
east = Vector(1, 0, 0)
south = Vector(0, -1, 0)
west = Vector(-1, 0, 0)

print(closest_direction(north))  # CardinalDirections.NORTH
print(closest_direction(east))  # CardinalDirections.EAST
print(closest_direction(south))  # CardinalDirections.SOUTH
print(closest_direction(west))  # CardinalDirections.WEST
