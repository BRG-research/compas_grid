from __future__ import print_function

import os
from .element_beam import BeamElement
from .element_column_head import ColumnHeadElement
from .element_column import ColumnElement
from .element_plate import PlateElement
from .interface_cutter import CutterInterface
from .model import GridModel

__author__ = ["Petras Vestartas"]
__copyright__ = "Petras Vestartas"
__license__ = "MIT License"
__email__ = "petrasvestartas@gmail.com"
__version__ = "0.1.0"

HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

__all__ = [
    "HOME",
    "DATA",
    "DOCS",
    "TEMP",
    "BeamElement",
    "ColumnHeadElement",
    "CardinalDirections",
    "ColumnElement",
    "PlateElement",
    "GridModel",
    "CutterInterface",
]
