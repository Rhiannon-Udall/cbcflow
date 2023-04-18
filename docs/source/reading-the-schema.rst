How To Read The Schema
======================

In order to use ``cbcflow`` effectively, it is critical to understand how to read the schema. 
This will go over how to do so, using a simple example schema.
It will also discuss the core building blocks of the schema, and some details of how to interact with them.
This page assumes you have already read :doc:`what-is-metadata` - 
if you haven't done so yet it is strongly advised that you read that first.

Important Concepts
------------------

Nested Structure
^^^^^^^^^^^^^^^^

Json files are useful due to hierarchical structure, with heterogeneous data types. 
The prototypical example is simple: just a dictionary with various key words corresponding to values, with those values being primitive objects (strings or numbers).
From the example in :doc:`what-is-metadata`, this is something like

.. code-block::

    "PublicationInformation":{
        "Title": "Babylon",
        "Author": "Joan Oates"
    }

We can make that one more step complicated by making some values arrays of primitive objects, such as:

.. code-block::

    "PublicationInformation":{
        "Title": "Babylon",
        "Author": "Joan Oates",
        "CopyrightYears": [1979, 1986]
    }

Furthermore, we can have dictionaries within dictionaries, building up to:

.. code-block::

    "PublicationInformation":{
        "Title": "Babylon",
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
For an example of how this works in practice, we can look back at our example metadata:

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

We see that "Topics" contains multiple dictionaries, and each has a "UID" to identify it, as well as some extra information.
If we wanted, we could nest these further, for example giving each "Topic" a field that is an array of objects, and so on.

Linked Files
^^^^^^^^^^^^

There's one special concept which exists only in ``cbcflow`` meta-data: linked files.
These are files which exist in the cluster - importantly, they consist not only of a path, but also other information.
What's special about them is how they are populated: when updating, you need only specify a valid path within the cluster you are on: ``cbcflow`` takes care of the rest.
Optionally, you may also point to a url for convenience, but these are not required.

Dissecting an Example Schema
----------------------------

Now, lets look at the schema which describes the above example metadata.

.. raw:: html
    :file: example_mini_schema/schema_doc.html

Each element can be expanded to learn more about it.
If it's a leaf node in the schema's tree, then you'll get information about the values.
If it branches out, you will also see more collapsible elements, and so on in turn.
For objects in arrays such as "Topics", you can learn about the properties of that object template.

The Real Schema
---------------

Now that we understand how to read the schema, we can proceed to updating metadata.
For this, you will want to have a copy of the true schema open - you can find this at :doc:`schema-visualization`.