from compas_model.models import Model
from compas.datastructures import Mesh
from compas_viewer import Viewer


class GridModel(Model):
    @classmethod
    def __from_data__(cls, data):
        model = super(GridModel, cls).__from_data__(data)
        # todo: implement the rest of data
        return model

    def __init__(self, *args, **kwargs):
        super(GridModel, self).__init__()

    def __str__(self):
        return "GridModel"

    @classmethod
    def from_divisions_and_dimensions(cls, dx, nx, dy, ny, dz, nz):
        # Grid interpolation. Start from simple.
        meshes = []
        for i in range(nz):
            mesh = Mesh.from_meshgrid(dx, nx, dy, ny)
            mesh.translate([dx * -0.5, dy * -0.5, dz * i])
            meshes.append(mesh)

        # Create building elements:
        # - columns
        # - walls
        # - beams
        # - slabs

        return meshes


if __name__ == "__main__":
    meshes = GridModel.from_divisions_and_dimensions(10, 3, 10, 3, 3.5, 3)
    viewer = Viewer(show_grid=True)
    obj = viewer.scene.add(meshes, show_points=True)
    viewer.show()
