from typing import List
from compas.geometry import Line
from compas.datastructures import Mesh
from compas.geometry import Vector
from compas.geometry import Point
from compas.tolerance import TOL
from compas_grid.element_column_head import ColumnHeadDirection


def closest_direction(
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


north = Vector(0, 1, 0)
east = Vector(1, 0, 0)
south = Vector(0, -1, 0)
west = Vector(-1, 0, 0)

print(closest_direction(north))  # ColumnHeadDirection.NORTH
print(closest_direction(east))  # ColumnHeadDirection.EAST
print(closest_direction(south))  # ColumnHeadDirection.SOUTH
print(closest_direction(west))  # ColumnHeadDirection.WEST
