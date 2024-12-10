from compas.datastructures import Mesh
from compas.geometry import Transformation
from compas_grid.interactions import InteractionInterface


class InteractionInterfaceBooleanDifference(InteractionInterface):
    """Class for cutting one element by a plane.

    Notes
    -----

    Class does not have any attributes. It is used to cut the geometry of the element by a plane."""

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None) -> None:
        super(InteractionInterfaceBooleanDifference, self).__init__(name=name)

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
        geometry_cutter_copy: Mesh = geometry_cutter.copy()
        # slice_plane.translate([0.0, 0.0, 0.001])
        geometry_cutter_copy.transform(xform)  # transform plane to the object space (often WorldXY)

        # Perform split and capture debug information.
        mesh_cut: Mesh = None

        from compas_cgal.booleans import boolean_difference_mesh_mesh

        geometry_to_modify.unify_cycles()
        geometry_cutter_copy.unify_cycles()

        A = geometry_to_modify.to_vertices_and_faces(triangulated=True)
        B = geometry_cutter_copy.to_vertices_and_faces(triangulated=True)
        V, F = boolean_difference_mesh_mesh(A, B)
        mesh_cut = Mesh.from_vertices_and_faces(V, F)

        # try:
        #     from compas_cgal.booleans import mesh_boolean_difference

        #     A = geometry_to_modify.to_vertices_and_faces(triangulated=True)
        #     B = geometry_cutter_copy.to_vertices_and_faces(u=64, v=64, triangulated=True)
        #     V, F = mesh_boolean_difference(A, B)
        #     mesh_cut = Mesh.from_vertices_and_faces(V, F)
        # except Exception:
        #     print(
        #         """
        #             Error in in CGAL Mesh Boolean Difference.
        #             """
        #     )
        if mesh_cut:
            return mesh_cut
