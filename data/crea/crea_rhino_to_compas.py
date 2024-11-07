#! python3
import Rhino
from compas import json_dump
from compas.scene import Scene
from compas_rhino.layers import find_objects_on_layer
from compas_rhino.objects import find_object
from compas_rhino.conversions import curve_to_compas_line
from compas_rhino.conversions import curve_to_compas_polyline
from compas_rhino.conversions import mesh_to_compas
from compas.geometry import distance_point_point
from compas.geometry import Line
from compas.geometry import Polyline
from compas.geometry import Transformation
from compas.datastructures import Mesh
from System import Guid
from typing import *


def select_lines(name):
    guids : List[Guid] = find_objects_on_layer(name)
    lines : List[Line] = []
    for guid in guids:
        obj : Rhino.DocObjects.CurveObject = find_object(guid)
        line : Line = curve_to_compas_line(obj.Geometry)
        lines.append(line)
    return lines

def select_polylines(name):
    guids : List[Guid] = find_objects_on_layer(name)
    polylines : List[Polyline] = []
    for guid in guids:
        obj : Rhino.DocObjects.CurveObject = find_object(guid)
        if (not isinstance(obj.Geometry, Rhino.Geometry.PolylineCurve)):
            continue
        polyline : Polyline = curve_to_compas_polyline(obj.Geometry)
        polylines.append(polyline)
    return polylines

def select_meshes(name):
    guids : List[Guid] = find_objects_on_layer(name)
    meshes : List[Rhino.Geometry.Mesh] = []
    for guid in guids:
        obj : Rhino.DocObjects.MeshObject = find_object(guid)
        mesh : Mesh = mesh_to_compas(obj.Geometry)
        v, f = mesh.to_vertices_and_faces()
        if (len(v) == 4):
            if distance_point_point(v[0], v[3]) > distance_point_point(v[0], v[2]):
                f = [[0,1,2,3]]
                v = [v[0], v[1], v[3], v[2]]
        mesh = Mesh.from_vertices_and_faces(v, f)
        meshes.append(mesh)
    return meshes

serialization_dictionary : Dict = {}
serialization_dictionary["Line::Column"] = select_lines("Line::Column")
serialization_dictionary["Line::Beam"] = select_lines("Line::Beam")
serialization_dictionary["Mesh::Floor"] = select_meshes("Mesh::Floor")
serialization_dictionary["Mesh::Facade"] = select_meshes("Mesh::Facade")
serialization_dictionary["Mesh::Core"] = select_meshes("Mesh::Core")

# scene = Scene()
# scene.clear()
# for mesh in serialization_dictionary["Mesh::Facade"]:
#     v,f = mesh.to_vertices_and_faces()
#     print(v)
#     scene.add(mesh)
#     break
# scene.draw()

# from compas import json_dump
json_dump(serialization_dictionary, "C:/brg/2_code/compas_grid/data/crea/crea.json")
