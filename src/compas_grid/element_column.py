import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.geometry import Line
from compas.itertools import pairwise
from compas.geometry import Polygon, Frame
from compas_model.elements import Element
from compas_model.elements import Feature


class ColumnFeature(Feature):
    pass


class ColumnElement(Element):
    """Class representing a column elements using an axis and two polygons.
    Polygons are needed because the column can be inclined.

    Parameters
    ----------
    shape : :class:`compas.datastructures.Mesh`
        The base shape of the block.
    features : list[:class:`ColumnFeature`], optional
        Additional block features.
    is_support : bool, optional
        Flag indicating that the block is a support.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`ColumnFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(ColumnElement, self).__data__
        data["bottom"] = self._bottom
        data["top"] = self._top
        data["features"] = self.features
        return data

    def __init__(self, axis, bottom, top, features=None, frame=None, name=None):
        # type: (compas.geometry.Polygon, compas.geometry.Polygon, list[columnFeature] | None, compas.geometry.Frame | None, str | None) -> None

        super(ColumnElement, self).__init__(frame=frame, name=name)
        axis = axis or [0, 0, 1]
        self._bottom = bottom
        self._top = top
        self.shape = self.compute_shape()
        self.features = features or []  # type: list[columnFeature]

    @property
    def face_polygons(self):
        # type: () -> list[compas.geometry.Polygon]
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self):
        # type: () -> compas.datastructures.Mesh
        """Compute the shape of the column from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        offset = len(self._bottom)
        vertices = self._bottom.points + self._top.points  # type: ignore
        bottom = list(range(offset))
        top = [i + offset for i in bottom]
        faces = [bottom[::-1], top]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, b, d, c])
        mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_geometry(self, include_features=False):
        geometry = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self):
        # TODO: (TvM) make this a pluggable with default implementation in core and move import to top
        from compas.geometry import convex_hull_numpy

        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    @classmethod
    def from_square_section(cls, width:float=0.4,  depth:float=0.4,  height:float=3.0, features:Feature=None, frame:Frame=None, name:str="None"):
        """Create a column element from a square section.

        Parameters
        ----------
        width : float
            The width of the column.
        depth : float
            The depth of the column.
        height : float
            The height of the column.
        features : list[:class:`ColumnFeature`], optional
            Additional block features.
        frame : :class:`compas.geometry.Frame`, optional
            The coordinate frame of the block.
        name : str, optional
            The name of the element.

        Returns
        -------
        :class:`ColumnElement`

        """

        p0 = [-width*0.5, -depth*0.5, 0]
        p1 = [-width*0.5, depth*0.5, 0]
        p2 = [width*0.5, depth*0.5, 0]
        p3 = [width*0.5, -depth*0.5, 0]
        polygon = Polygon([p0, p1, p2, p3])
        axis = Line([0, 0, 0], [0, 0, height])
    
        normal = polygon.normal
        up = normal * (1.0 * height)
        top = polygon.copy()
        for point in top.points:
            point += up
        bottom = polygon.copy()
        
        column = cls(axis=axis, bottom=bottom, top=top, features=features, frame=frame, name=name)
        return column
    
    @classmethod
    def from_polygon(cls, axis, polygon_on_xy_plane, horizontal_frame = Frame):
        
        pass
        
        
    
 

if __name__ == "__main__":
    
    from compas_viewer import Viewer   
    column_square = ColumnElement.from_square_section()
    
    viewer = Viewer()
    viewer.scene.add(column.shape)
    viewer.show()
