from compas_model.interactions import Interaction

from compas.datastructures import Mesh
from compas.geometry import Transformation


class InteractionInterface(Interaction):
    def __init__(self, name=None) -> None:
        super(InteractionInterface, self).__init__(name=name)

    def compute_interaction(self, geometry_cutter: Mesh, geometry_to_modify: Mesh, xform: Transformation) -> None:
        """Modify geometry by another geometry."""
        pass
