Python Metadata Interface
=========================

Core Usage
----------

In addition to the :doc:`command-line-usage`, python scripts may conveniently edit metadata. 
To do this, we start by loading in metadata for usage.
Prototypically, this may be done with: 

.. code-block::

    import cbcflow

    metadata = cbcflow.get_superevent("S190521g", library=/path/to/a/library)

If the library already contains metadata for the superevent described by ``sname``, then that metadata will be loaded.
Otherwise, this superevent will start with default data. 
Notably, this default data *does not* include the GraceDB information
- updating the superevent with this information requires specifically fetching that data from GraceDB.
However, when interacting with the central CBC library or it's derivatives
(which are directly or indirectly kept up to date with GraceDB)
this should not be an issue. 

If a specific library argument is not passed, then the default library will be used (see :doc:`configuration`). 

Now that metadata has been loaded, we may edit it.
We can borrow an example from :doc:`command-line-usage`, by defining our update json: 

.. code-block:: 

    update_add_json = {
        "ParameterEstimation":{
            "Status":"ongoing",
            "Analysts":["Albert Einstein"]
        }
    }

This may then be applied to the MetaData object with that object's ``update`` method:

.. code-block:: 

    metadata.update(update_add_json)

Producing the equivalent result to the example before.
Similar to before, if one wants to remove an array element, one should construct a negative image JSON:

.. code-block::

    update_remove_json = {
        "ParameterEstimation":{
            "Reviewers":["Kip Thorne"]
        }
    }

and then apply it in removal mode:

.. code-block::

    metadata.update(update_remove_json, is_removal=True)

The same examples from before also work to arbitrary complexity.
For example, the last yaml update method would be rendered as:

.. code-block::

    update_add_json_2 = {
        "TestingGR":{
            "IMRCTAnalyses":[
                {
                    "UID":"IMRCT1",
                    "SafeLowerMassRatio":2,
                    "Results":[
                        {
                            "UID":"ProdF1",
                            "WaveformApproximant":"IMRPhenomXPHM"
                        },
                        {
                            "UID":"ProdF2",
                            "WaveformApproximant":"SEOBNRv4PHM"
                        }
                    ]
                },
                {
                    "UID":"IMRCT2",
                    "SafeLowerMassRatio":3,
                    "Results":[
                        {
                            "UID":"ProdF1",
                            "WaveformApproximant":"SEOBNRv4PHM"
                        },
                        {
                            "UID":"ProdF2",
                            "WaveformApproximant":"IMRPhenomXPHM"
                        }
                    ]
                }
            ]
        }
    }

These do get rather complicated to construct, and it is strongly recommended that when rendering them one should use the ``json.dumps`` method with an indent of at least 2.
However, for automated scripts this should be substantially easier to interact with. 

Once we are happy with our changes to the metadata, we can write it back to the library:

.. code-block::

    metadata.write_to_library(message="A git commit message")

If the library is a git repository (and our example implicitly is - this is flagged when making the MetaData object, and is default True),
then writing to it will also automatically commit the changes. If no commit message is given then a default message will be used. 
