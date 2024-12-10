from compas.datastructures import Mesh
from compas.geometry import Plane
from compas.geometry import Transformation
from compas_grid.interactions import InteractionInterface


class InteractionInterfaceCutter(InteractionInterface):
    """Class for cutting one element by a plane.

    Notes
    -----

    Class does not have any attributes. It is used to cut the geometry of the element by a plane."""

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None) -> None:
        super(InteractionInterfaceCutter, self).__init__(name=name)

    def compute_interaction(self, geometry_cutter: Mesh, geometry_to_modify: Mesh, xform: Transformation) -> Mesh:
        """Modify the geometry of the element.

        Geometry is modified in-place by slicing it with the plane of the interface.

        Parameters
        ----------
        geometry_cutter : Mesh
            The geometry of the element that cuts the other

        geometry_to_modify : Mesh
            The geometry of the element that is cut

        xform : Transformation
            Transformation of the geometry_cutter to the geometry_to_modify

        Returns
        -------
        Mesh
            The modified geometry of the element.
        """

        # First transform the plane to the 3D space.
        slice_plane: Plane = Plane.from_frame(geometry_cutter)
        # slice_plane.translate([0.0, 0.0, 0.001])
        slice_plane.transform(xform)  # transform plane to the object space (often WorldXY)

        # Perform split and capture debug information.
        split_meshes: list[any] = None

        try:
            split_meshes = geometry_to_modify.slice(slice_plane)  # Slice meshes and take the one opposite to the plane normal.
        except Exception:
            import compas_grid

            if compas_grid.debug:
                compas_grid.global_property.append(slice_plane)
                compas_grid.global_property.append(geometry_to_modify)
                print(
                    """
                    Class: InteractionInterfaceCutter\nSlicing is not successful.
                    Check the transformation of <InterfaceCutterElement> or <Mesh.slice()>.
                    Data-set is added to <compas_grid.global_property> for debugging."
                    """
                )
        if split_meshes:
            return split_meshes[0]
