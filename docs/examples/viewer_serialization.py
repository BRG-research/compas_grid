from typing import *
from compas import json_dump
from compas.geometry import Box


if __name__ == "__main__":
    
    box0 = Box(1)
    json_dump([box0], "geometry_list.json")
    json_dump(True, "has_update.json")
