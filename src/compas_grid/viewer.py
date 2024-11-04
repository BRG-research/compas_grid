from typing import *
from compas import json_dump


def serialize(geometry: Any):
    json_dump(geometry, "docs/examples/geometry_list.json")
    json_dump(True, "docs/examples/has_update.json")


if __name__ == "__main__":
    serialize([])
