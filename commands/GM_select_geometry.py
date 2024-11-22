def serialize_rhino_data(
    layer_names: list[str] = ["Model::Line::Segments", "Model::Mesh::Floor", "Model::Mesh::Facade", "Model::Mesh::Core"],
    path : str ="C:/brg/2_code/compas_grid/data/crea/crea_4x4.json",
) -> None:
    """Select lines and meshes from Rhino from layers.
    Layer names are added as attributes to each geometry object for further processing.
    If no layer name is provided, empty layers are created.
    NOTE: This method is a placeholder for the actual Rhino UI logic.

    Parameters
    ----------
    layer_names : list[str], optional

    """

    # Selection
    import Rhino
    from compas import json_dump
    from compas.datastructures import Mesh
    from compas.geometry import Line
    from compas.geometry import distance_point_point
    from compas_rhino.conversions import curve_to_compas_line
    from compas_rhino.conversions import mesh_to_compas
    from compas_rhino.layers import create_layers_from_path
    from compas_rhino.layers import find_objects_on_layer
    from compas_rhino.objects import find_object
    from System import Guid

    # Create layers if they do not exist.
    for layer_name in layer_names:
        create_layers_from_path(layer_name)

    # Conversions from Rhino GUID to compas objects.
    def select_lines(name):
        guids: list[Guid] = find_objects_on_layer(name)
        lines: list[Line] = []
        for guid in guids:
            obj: Rhino.DocObjects.CurveObject = find_object(guid)
            line: Line = curve_to_compas_line(obj.Geometry)
            lines.append(line)
        return lines

    def select_meshes(name):
        guids: list[Guid] = find_objects_on_layer(name)
        meshes: list[Rhino.Geometry.Mesh] = []
        for guid in guids:
            obj: Rhino.DocObjects.MeshObject = find_object(guid)
            mesh: Mesh = mesh_to_compas(obj.Geometry)
            v, f = mesh.to_vertices_and_faces()
            if len(v) == 4:
                if distance_point_point(v[0], v[3]) > distance_point_point(v[0], v[2]):
                    f = [[0, 1, 2, 3]]
                    v = [v[0], v[1], v[3], v[2]]
            mesh = Mesh.from_vertices_and_faces(v, f)
            meshes.append(mesh)
        return meshes

    serialization_dictionary: dict = {}
    for layer_name in layer_names:
        if "mesh" in layer_name.lower():
            serialization_dictionary[layer_name] = select_meshes(layer_name)
        elif "line" in layer_name.lower():
            serialization_dictionary[layer_name] = select_lines(layer_name)

    # scene = Scene()
    # scene.clear()
    # for mesh in serialization_dictionary["Mesh::Facade"]:
    #     v,f = mesh.to_vertices_and_faces()
    #     print(v)
    #     scene.add(mesh)
    #     break
    # scene.draw()

    # from compas import json_dump
    json_dump(serialization_dictionary, path)

path : str ="C:/brg/2_code/compas_grid/data/crea/crea_4_4.json"
serialize_rhino_data()