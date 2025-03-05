from typing import Optional
from typing import Union

from compas_model.elements.element import Element
from compas_model.elements.element import Feature

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Transformation


class CutFeature(Feature):
    pass


class CutElement(Element):
    """Class representing a Cut of an element.

    Parameters
    ----------
    shape : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, optional
        The shape of the Cut.
    transformation : :class:`compas.geometry.Transformation`, optional
        The transformation applied to the Cut.
    features : list[:class:`compas_model.features.CutFeature`], optional
        The features of the Cut.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    center_line : :class:`compas.geometry.Line`
        The axis of the Cut.
    section : :class:`compas.geometry.Polygon`
        The section of the Cut.

    """

    @property
    def __data__(self) -> dict:
        return {
            "shape": self.shape,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        shape: Union[Mesh, Brep] = None,
        transformation: Optional[Transformation] = None,
        features: Optional[list[CutFeature]] = None,
        name: Optional[str] = None,
    ) -> "CutElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self._shape: Union[Mesh, Brep] = shape  # public property that can be changed any time

    @property
    def shape(self) -> Union[Mesh, Brep]:
        return self._shape

    @shape.setter
    def shape(self, shape: Union[Mesh, Brep]):
        self._shape = shape
        self._geometry = None

    def compute_elementgeometry(self) -> Mesh:
        """Compute the top and bottom polygons of the Cut.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The mesh of the Cut.
        """

        return self.shape

    def compute_aabb(self, inflate: Optional[bool] = None) -> Box:
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The axis-aligned bounding box.
        """

        box = self.modelgeometry.aabb()
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._aabb = box
        return box

    def compute_obb(self, inflate: Optional[bool] = None) -> Box:
        """Compute the oriented bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The oriented bounding box.
        """
        box = self.modelgeometry.oobb()
        if inflate and inflate != 1.0:
            box.xsize += inflate
            box.ysize += inflate
            box.zsize += inflate
        self._obb = box
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        return self.modelgeometry
