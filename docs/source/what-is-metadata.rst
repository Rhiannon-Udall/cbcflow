Basics of Metadata
==================

This page covers the basics of metadata: what it is, how to read it, and pointers to the pages that show how to interact with it. 
If you're new to ``cbcflow``, this is the place to start!

Why Metadata
------------

The central purpose of ``cbcflow`` is to provide a central database for the relevant information about all CBC analyses.
However, we do not want to store these data themselves, due to both size and usability constraints.
Instead, we store the metadata about these analyses which is important for downstream users and internal communication.
For example, we do not store the full configuration of a parameter estimation run, but we do store the path to where one may found it.
Similarly we store the recommendation from detector characterization for the minimum frequency to use in a given detector when analyzing a specific event, but we do not store the values used by each analysis directly.

What Does Metadata Look Like
----------------------------

Metadata takes the form of json files, governed by a schema.
In python terms, they are nested combinations of dictionaries and lists, with the lowest level elements being primitive objects like strings or numbers.
For example, say I am trying to describe a book in terms of some useful metadata:

.. code-block::

    {
        "PublicationInformation":{
            "Author": "Joan Oates",
            "Title":"Babylon"
            "CopyrightYears": [1979, 1986],
            "PublisherInfo": {
                "Name" : "Thames and Hudson",
                "City" : "London, UK" 
            }
        },
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
    }

Here we have two pieces of information about a book: publication information and content.
The publication information includes some natural elements like the title, author, the publisher, and years of publication.
The content include a "Summary" field, as well as a "Topics" array that contains a number of "Topic" objects, each with a unique ID ("UID") and some information.

This structure is fixed ahead of time, so for example the keys in "PublisherInfo", the type of "CopyrightYears", and the template for "Topic" objects are all fixed.
For guidance on how to read and understand these structures, check out :doc:`reading-the-schema`, which establishes an example schema corresponding to our example metadata here. 
For actual CBC metadata, that structure can be read in :doc:`schema-visualization`, and in order to accommodate all the possible inputs, it is very complex.
However, the structural elements which can go into it are more limited, and once these basic building blocks are understood one may infer the meaning of each field.

How to Interact With Metadata
-----------------------------

In essentially all cases, interacting with metadata means one of two things: reading it or updating it.
If you only want to look at a single value for a field, it is likely easiest to read it in :doc:`gwosc`.
However, if you want to harvest data in bulk, you will likely want to do so via the python API, basic usage of which is detailed at :doc:`updating-metadata-with-the-python-api`.

To update the metadata, you similarly have a couple options. 
If you wish to manually change the data, ``cbcflow`` provides command line options, with details at :doc:`updating-metadata-from-the-command-line`.
If you wish to change the data programmatically with ``python``, basics can be found at :doc:`updating-metadata-with-the-python-api`, and the details of the api are found at :doc:`api/cbcflow`

Where Do You Find Real Metadata?
--------------------------------

In ``cbcflow`` itself, metadata is stored in libraries, which are git repositories containing metadata jsons, along with a bit of scaffolding.
More detail on various aspects of libraries can be found in the expert usage section, specifically :doc:`library-setup` and :doc:`library-indices`.
For now though, let's assume that there already exists a library, and you just want to modify it. 
You first want to make a fork of the library, and clone the fork: the central CBC library will be protected, so only automated users can push directly.
Everyone else should update their forks, then submit and MR which will be approved by an expert user.
Once you have a clone of your fork, make sure you have gotten ``cbcflow`` configured according to the instructions in :doc:`configuration`, then you can proceed onwards to being updating metadata!


