from compas_model.interactions import Interaction


class CutterInterface(Interaction):
    """Class representing a interface by a frame, to cut shapes of the model.


    Parameters
    ----------
    frame
    name

    Attributes
    ----------
    frame : :class:`compas.geometry.Frame`
        The frame of the interface.
    name : str, optional
        The name of the interface.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "points": self.points,
            "frame": self.frame,
            "name": self.name,
        }

    def __init__(self, frame, name=None):
        super(CutterInterface, self).__init__(name=name)

        self._frame = frame

    @property
    def frame(self):
        return self._frame
