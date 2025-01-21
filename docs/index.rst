********************************************************************************
compas_grid
********************************************************************************

.. rst-class:: lead

.. figure:: /_images/compas_grid.jpg
   :figclass: figure
   :class: figure-img img-fluid


COMPAS Grid is a model for multi-storey buildings, providing a comprehensive library of elements and a model based on the CellNetwork class from COMPAS. This package streamlines the creation and analysis of complex building structures by utilizing user input such as lines representing structural elements and meshes representing floors. From this input, an underlying Graph is created and transformed into a CellNetwork object, which forms the backbone of the structural model. The CellNetwork is then encapsulated within a GridModel, offering a flexible and robust representation of the building's structure. This approach allows for automatic generation and positioning of structural elements like beams, columns, slabs, and column heads based on the graph's connectivity. COMPAS Grid features include customizable elements, topological analysis capabilities, seamless integration with the COMPAS ecosystem, extensibility for adding new element types or analysis methods, and interoperability with various CAD and BIM software.


Table of Contents
=================

.. toctree::
   :maxdepth: 3
   :titlesonly:

   Introduction <self>
   installation
   tutorial
   examples
   api
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
