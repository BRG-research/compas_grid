from compas_model.models import Model
from 

class GridModel(Model):
    """ Class representing a grid model of a multi-story building.
    
    Pseudo code for the user interface:
    lines_and_surfaces = {}
    model = GridModel.from_lines_and_surfaces(lines_and_surfaces)
    model.cut_interfaces()
    
    """
    
    def __init__(self, name=None):
        super(GridModel, self).__init__(name=name)
        self._cell_network = None
        self._cutter_interfaces = []
    
    @property
    def cell_network(self):
        return self._cell_network
    
    @property
    def cutter_interfaces(self):
        return self._cutter_interfaces
    
    @classmethod
    def from_lines_and_surfaces(cls, lines, surfaces):
        pass
    
    def add_cutter_interface(self, cutter_interface):
        self._cutter_interfaces.append(cutter_interface)
    
    def remove_cutter_interface(self, cutter_interface):
        self._cutter_interfaces.remove(cutter_interface)
    
    def clear_cutter_interfaces(self):
        self._cutter_interfaces = []
    
    def add_cell_network(self, cell_network):
        self._cell_network = cell_network
    
    def clear_cell_network(self):
        self._cell_network = None