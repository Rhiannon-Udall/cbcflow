Welcome to the cbcflow documentation!
=====================================

CBCFlow allows convenient and machine readable storage, communication, and retrieval of important metadata for CBC analyses of events. 
Getting started covers the topics that typical users should know for interacting with a CBCFlow library.
Expert usage includes further topics, such as the configuration of libraries and operation of monitors.
Schema information describes how to understand the schema, and gives a breakdown of the various elements.
Finally, we provide autobuilt API documentation. 

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   configuration
   local-library-copy-setup
   what-is-metadata
   reading-the-schema
   updating-metadata-from-the-command-line
   updating-metadata-with-the-python-api
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
