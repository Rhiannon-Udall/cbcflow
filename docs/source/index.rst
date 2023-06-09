Welcome to the cbcflow documentation!
=====================================

CBCFlow allows convenient and machine readable storage, communication, and retrieval of important metadata for CBC analyses of events. 
This project consists of three parts:

#. Metadata for superevents, stored in a standardized format
#. A Python API for interacting with that metadata
#. Integrated visualization tools

Important Links
---------------

When using ``cbcflow``, there are a lot of different links which may be important. 
For convenience, we note some here:

#. `The current (O4a) library <https://git.ligo.org/cbc/projects/cbc-workflow-o4a>`_

   #. `The issues page for that library, to track developments <https://git.ligo.org/cbc/projects/cbc-workflow-o4a/-/issues>`_

   #. The cluster copy of this library (read only) is at ``CIT:/home/cbc/cbcflow/O4a/cbc-workflow-o4a``

#. `The GWOSC visualization page for the library <https://gwosc-rl8.ligo.caltech.edu/eventapi/html/>`_

#. `The cbcflow development repository <https://git.ligo.org/cbc/projects/cbcflow>`_ 

   #. `The mattermost help channel <https://chat.ligo.org/landing#/ligo/channels/cbcflow-help>`_

This Documentation
------------------

These pages are meant to provide tutorials and examples for interacting with
and developing ``cbcflow``, as well as documenting the API. If you find anything
unclear or missing, please request improvements to the documentation 
`here <https://git.ligo.org/cbc/projects/cbcflow/-/issues/56>`_

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   configuration
   local-library-copy-setup
   what-is-metadata
   reading-the-schema
   command-line-general
   command-line-update
   
.. toctree::
   :maxdepth: 1
   :caption: Using CBCFlow's Python API

   python-api-basics
   python-api-update-metadata
   python-api-libraries

.. toctree::
   :maxdepth: 1
   :caption: Integrated Projects

   asimov
   gwosc

.. toctree::
   :maxdepth: 1
   :caption: Expert Usage

   development-setup
   library-setup-from-scratch
   monitor-usage
   library-indices
   library-index-labelling
   cbcflow-git-merging

.. toctree::
   :maxdepth: 1
   :caption: Schema Information:

   schema-visualization
   adding-to-the-schema

API
---

.. autosummary::
   :toctree: api
   :caption: API:
   :template: custom-module-template.rst
   :recursive:

    cbcflow
