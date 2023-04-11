Basics of Metadata
==================

Why Metadata
------------

The central purpose of ``CBCFlow`` is to provide a central database for the relevant information about all CBC analyses.
However, we do not want to store these data themselves, due to both size and usability constraints.
Instead, we store the metadata about these analyses which is important for downstream users and internal communication.
For example, we do not store the full configuration of a parameter estimation run, but we do store the path to where one may found it.
Similarly we store the recommendation from detector characterization for the minimum frequency to use in a given detector when analyzing a specific event, but we do not store the values used by each analysis directly.

What Does Metadata Look Like
----------------------------

Metadata takes the form of json files, governed by a schema.
In python terms, they are nested combinations of dictionaries and lists, with the lowest level elements being primitive objects like strings or numbers.
This structure is fixed ahead of time, so that, for example, the list of key words that may go into the parameter estimation section of the schema is immutable.
That structure can be read in :doc:`schema-visualization`, and in order to accommodate all the possible inputs, it is very complex. However, the structural elements which can go into it are more limited.
For guidance on how to understand it, check out :doc:`reading-the-schema`

How to Interact With Metadata
-----------------------------

In essentially all cases, interacting with metadata means one of two things: reading it or updating it.
If you only want to look at a single value for a field, it is likely easiest to read it in the GWOSC visualization :doc`gwosc`.
However, if you want to harvest data in bulk, you will likely want to do so via the python API, basic usage of which is detailed at :doc:`updating-metadata-with-the-python-api`


