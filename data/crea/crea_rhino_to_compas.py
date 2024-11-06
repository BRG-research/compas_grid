#! python3
import compas
from compas import json_dump
from compas.scene import Scene
import compas_rhino.objects
import compas_rhino.conversions
from System import Guid
import Rhino
from compas.geometry import Line
from compas.geometry import Polyline
from typing import *

def select_lines(name):
    guids : List[Guid] = compas_rhino.layers.find_objects_on_layer(name)
    lines : List[Line] = []
    for guid in guids:
        obj : Rhino.DocObjects.CurveObject = compas_rhino.objects.find_object(guid)
        line : Line = compas_rhino.conversions.curve_to_compas_line(obj.Geometry)
        lines.append(line)
    return lines

def select_polylines(name):
    guids : List[Guid] = compas_rhino.layers.find_objects_on_layer(name)
    polylines : List[Polyline] = []
    for guid in guids:
        obj : Rhino.DocObjects.CurveObject = compas_rhino.objects.find_object(guid)
        if (not isinstance(obj.Geometry, Rhino.Geometry.PolylineCurve)):
            continue
        polyline : Polyline = compas_rhino.conversions.curve_to_compas_polyline(obj.Geometry)
        polylines.append(polyline)
    return polylines

columns : List[Line] = select_lines("Columns")
beams : List[Line] = select_lines("Beams")
double_heights : List[Line] = select_lines("DoubleHeights")
staircase : List[Polyline] = select_polylines("Staircase")
references : List[Polyline] = select_polylines("References")
raster : List[Polyline] = select_polylines("Raster")

serialization_dictionary : Dict = {}
serialization_dictionary["Columns"] = columns
serialization_dictionary["Beams"] = beams
serialization_dictionary["DoubleHeights"] = double_heights
serialization_dictionary["Staircase"] = staircase
serialization_dictionary["References"] = references
serialization_dictionary["Raster"] = raster

json_dump(serialization_dictionary, "C:/brg/2_code/compas_grid/data/crea/crea.json")