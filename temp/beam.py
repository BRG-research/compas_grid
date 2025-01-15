from compas_model.elements import BeamElement


class BeamStepElement(BeamElement):
    """A beam element with a step in the middle of the beam."""

    def __init__(self, width: float, depth: float, step_height: float, step_width: float):
        super().__init__(width, depth)
        self.step_height = step_height
        self.step_width = step_width
