from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_grid.model import GridModel
from compas_grid import BeamElement

#######################################################################################################
# Geometry from Rhino.
#######################################################################################################
rhino_geometry: dict[str, list[any]] = json_load("data/crea/crea_4x4_ground.json")
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

#######################################################################################################
# Create the model.
#######################################################################################################
model = GridModel.from_lines_and_surfaces(lines, surfaces)
# model.cut()


element = list(model.elements())[0]
# print(element)
# print(element.tree_node)
# print(type(element.tree_node.tree))
# print(element.tree_node.tree.model)
#######################################################################################################
# Visualize the model.
#######################################################################################################
try:
    from compas_snippets.viewer_live import ViewerLive

    viewer_live = ViewerLive()

    for element in model.elements():
        # if isinstance(element, BeamElement):
        #     element.apply_interactions()
        # geometry = element.geometry

        geometry = element.geometry
        geometries = element.compute_geometry_world()

        if geometries:
            for geo in geometries:
                geo.scale(0.001)
            # for geometry in geometries:
            print(len(geometries))
            viewer_live.add(geometries)

    for geo in model.all_geo:
        viewer_live.add(geo.scaled(0.001))
    #

    #     geometry.name = element.name
    #     viewer_live.add(geometry.scaled(0.001))

    # for geo in model.all_geo:
    #     viewer_live.add(geo.scaled(0.001))

    viewer_live.serialize()
    # viewer_live.run()
except ImportError:
    print("Could not import ViewerLive. Please install compas_snippets to visualize the model from https://github.com/petrasvestartas/compas_snippets")
