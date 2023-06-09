Building Blocks: Metadata and Libraries
=======================================

When writing scripts which use ``cbcflow``, you should expect to use two classes:
``cbcflow.metadata.MetaData`` and ``cbcflow.database.LocalLibraryDatabase``.
These describe the attributes and methods for a given event's metadata and the 
library of event metadata respectively.
This page will give an introduction to each in turn, while a more thorough tour
may be found in subsequent pages.

``MetaData``
----------

The most central building block in ``cbcflow`` is metadata. 
Loading this is surprisingly easy for example:

.. code-block::

    >>> import cbcflow

    >>> metadata = cbcflow.get_superevent("S230409lg")
    INFO:cbcflow.schema:Using schema file /home/rhiannon.udall/.conda/envs/cbcflow_development/lib/python3.10/site-packages/cbcflow/schema/cbc-meta-data-v2.schema
