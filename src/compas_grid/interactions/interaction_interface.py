from compas_model.interactions import Interaction


class InteractionInterface(Interaction):
    def __init__(self, name=None) -> None:
        super(InteractionInterface, self).__init__(name=name)
