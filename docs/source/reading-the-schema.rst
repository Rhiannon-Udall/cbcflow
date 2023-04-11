How To Read The Schema
======================

In order to use ``cbcflow`` effectively, it is critical to understand how to read the schema. 

Important Concepts
------------------

Nested Structure
^^^^^^^^^^^^^^^^

Json files are useful due to hierarchical structure, with heterogeneous data types. 
The prototypical example is simple: just a dictionary with various key words corresponding to values, with those values being primitive objects (strings or numbers).
From the example in :doc:`what-is-metadata`, this is something like

.. code-block::

    "PublicationInformation":{
        "Author": "Joan Oates",
    }

We can make that one more step complicated by making some values arrays of primitive objects, such as:

.. code-block::

    "PublicationInformation":{
        "Author": "Joan Oates",
        "CopyrightYears": [1979, 1986],
    }

Furthermore, we can have dictionaries within dictionaries, building up to:

.. code-block::

    "PublicationInformation":{
        "Author": "Joan Oates",
        "CopyrightYears": [1979, 1986],
        "PublisherInfo": {
            "Name" : "Thames and Hudson",
            "City" : "London, UK" 
        }
    }

It's pretty straightforward to see how these parts fit together:
just have nested dictionaries forming trees with as much depth as you want, and put primitive objects or arrays of primitive objects at the leaf nodes.

Objects in Arrays
^^^^^^^^^^^^^^^^^

The nested structure is suitable for many situations.
Sometimes, though, we will have repeated objects which share structure but have different values.
For this, we want to be able to put objects into arrays, but we need some way to track them correctly so we can edit them later.
This is where the id of a "UID" comes in - a unique identifier which tells you which object you are modifying. 
Whenever you want to modify an object within an array in ``cbcflow``, you *must* specify a UID. 
If the object doesn't exist yet, this will create it, and if it does exist this will tell ``cbcflow`` the path to follow.
Furthermore, in ``cbcflow``, unique IDs will *always* be designated as "UID", even when they may have a more intuitive meaning (e.g. the IFO name).
This is a restriction on the methods by which ``cbcflow`` updates jsons, but it is also convenient: if you see "UID" in an object, you know it *must* be this sort of templated object, living in an array.
For an example of how this works in practice, we can look back at our example schema:

.. code-block::

    "Content":{
        "Summary" : "The history of Babylonia",
        "Topics" : [
            {
                "UID":"Old Babylon",
                "YearsRelevant": "c. 1900 BCE - 1600 BCE",
                "Language": "Akkadian"
            },
            {
                "UID": "Neo-Babylon",
                "YearsRelevant": "c. 626 BCE - 539 BCE",
                "Language": "Aramaic"
            }
        ]
    }


Dissecting an Example Schema
----------------------------

Now, lets look at the schema which describes the above example metadata.

.. raw:: html
    :file: example_mini_schema/schema_doc.html