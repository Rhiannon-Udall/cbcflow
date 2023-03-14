Welcome to the cbcflow documentation!
=====================================

CBCFlow allows convenient and machine readable storage, communication, and retrieval of important metadata for CBC analyses of events. 
Basic usage goes over how to interact with CBCFlow as a user, as well as a schematic of its place within the operations of the CBC group.
The metadata that may be stored is encoded in the schema; see below for how to interact with this schema, and what fields are currently present.
Finally, we lay out future development goals (also reflected in the git issues), as well as plans for integration with outside software. 

.. automodule:: cbcflow
    :members:

.. toctree::
   :maxdepth: 1
   :caption: Basic Usage

   installation
   command-line-usage
   usage-for-scripting
   libraries

.. toctree::
   :maxdepth: 1
   :caption: Schema Information:

   metadata
   schema-visualization
   
.. toctree::
   :maxdepth: 1
   :caption: Planning and Integration

   actionitems
   gwosc
   asimov
