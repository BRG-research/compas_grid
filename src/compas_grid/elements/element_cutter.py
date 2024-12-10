from compas_model.models import Model

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas_grid.elements import BaseElement


class CutterElement(BaseElement):
    """Class representing a phyisical interface between two other elements.

    Parameters
    ----------
    size : float, optional
        The size of the interface.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the interface.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.geometry.Frame`
        The base shape of the interface.

    Notes
    -----
    The shape is a frame. Size can be used for visualization purposes.

    """

    @property
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(CutterElement, self).__data__
        data["size"] = self.size
        data["frame"] = self.frame
        data["name"] = self.name
        return data

    @classmethod
    def __from_data__(cls, data: dict[str, any]) -> "CutterElement":
        return cls(
            size=data["size"],
            frame=data["frame"],
            name=data["name"],
        )

    def __init__(self, size=500, frame=None, name=None) -> None:
        frame = frame or Frame.worldXY()
        super(CutterElement, self).__init__(frame=frame, name=name)
        self.size = 500
        self.shape = self.compute_shape()

    def compute_shape(self) -> Mesh:
        return Frame.worldXY()

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_aabb(self, inflate=0.0) -> Box:
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0) -> Box:
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        from compas.geometry import convex_hull_numpy

        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # def compute_interaction(self, geometry: Mesh, xform: Transformation) -> None:
    #     """Modify the geometry of the element.
    #     Geometry is modified in-place by slicing it with the plane of the interface."""

    #     # First transform the plane to the 3D space.
    #     slice_plane: Plane = Plane.from_frame(self.frame).transformed(self.compute_worldtransformation())
    #     slice_plane.transform(xform)  # transform plane to the object space (often WorldXY)
    #     split_meshes: list[any] = None

    #     try:
    #         split_meshes = geometry.slice(slice_plane)  # Slice meshes and take the one opposite to the plane normal.
    #     except Exception:
    #         # print("Error in slice")
    #         import compas_grid

    #         compas_grid.global_property.append(slice_plane)
    #         compas_grid.global_property.append(geometry)
    #         # from compas import json_dump
    #         # json_dump([geometries[0], slice_plane], "error.json")
    #     if split_meshes:
    #         geometry = split_meshes[0]

    @classmethod
    def cutter_element_model(self) -> Model:
        """Create a model from the column head cross element and screws.

        Returns
        -------
        :class:`compas_model.models.Model`
            The model of the column head cross element.
        """

        from compas_grid.elements import ScrewElement

        cutter: CutterElement = CutterElement()
        screw: ScrewElement = ScrewElement(radius=20, length=200)
        model: Model = Model(name="CutterElementModel")
        parent = model.add_element(cutter.copy())
        model.add_element(screw.copy(), parent=parent)

        return model
