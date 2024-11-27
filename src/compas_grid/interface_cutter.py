from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import Transformation
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
            "polygon": self.polygon,
            "name": self.name,
        }

    def __init__(self, polygon=None, name=None):
        super(CutterInterface, self).__init__(name=name)

        self._frame = polygon.frame
        self._polygon = polygon

    @property
    def frame(self):
        return self._frame

    @property
    def polygon(self):
        return self._polygon

    # Temporary method to display the frame of the interface
    def frame_polygon(self, size=500):
        polygon: Polygon = Polygon.from_rectangle([-size * 0.5, -size * 0.5, 0], size, size)
        polygon.transform(Transformation.from_frame_to_frame(Frame.worldXY(), self._frame))
        return polygon

    def cut(self):
        pass
