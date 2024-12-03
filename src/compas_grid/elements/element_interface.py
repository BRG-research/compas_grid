import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Transformation
from compas_grid.elements import BaseElement


class InterfaceElement(BaseElement):
    """Class representing a phyisical interface between two other elements.

    Parameters
    ----------
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the interface.

    Notes
    -----
    The shape of the interface is calculated automatically from the input polygon and thickness.
    The frame of the element is the frame of the polygon.

    """

    @property
    def __data__(self) -> dict:
        data = super(InterfaceElement, self).__data__
        return data

    def __init__(self, frame: Frame, name: str = None) -> None:
        super(InterfaceElement, self).__init__(frame=frame, name=name)

    def compute_shape(self) -> Mesh:
        raise NotImplementedError

    def compute_interface(
        self,
        geometries: list[any],
        xform: Transformation = None,
    ) -> None:
        return None
