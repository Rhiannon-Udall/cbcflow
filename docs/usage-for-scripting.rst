Python Metadata Interface
=========================

Core Usage
----------

In addition to the :doc:`command-line-usage`, python scripts may conveniently edit metadata. 
To do this, we start by loading in metadata for usage.
Prototypically, this may be done with: 

.. code-block::

    >>> import cbcflow
    >>> import json

    >>> metadata = cbcflow.get_superevent("S190521q")
    INFO:cbcflow.schema:Using schema file /home/rhiannon.udall/meta-data/meta-data/src/cbcflow/schema/cbc-meta-data-v1.schema
    INFO:cbcflow.metadata:Found existing library file: loading
    INFO:cbcflow.metadata:Found existing library file: loading
    INFO:cbcflow.metadata:Found existing library file: loading
    INFO:cbcflow.metadata:Found existing library file: loading
    INFO:cbcflow.metadata:No library file: creating defaults

If a specific library argument is not passed, then the default library will be used (see :doc:`configuration`), 
as has occurred in this example. 
To pass a specific library, one may add the keyword argument ``library=/a/path/to/a/library``.

If the library already contains metadata for the superevent described by ``sname``,
then that metadata will be loaded.
Otherwise, this superevent will start with default data.
We can see that for this library we are creating defaults for this supervent,
since it has not been previously initialized.
To see what these defaults look like, we can do:

.. code-block::

    >>> metadata.pretty_print()
    INFO:cbcflow.metadata:Metadata contents for S190521q:
    INFO:cbcflow.metadata:{
        "Sname": "S190521q",
        "Info": {
            "Labels": [],
            "Notes": []
        },
        "Publications": {
            "Papers": []
        },
        "GraceDB": {},
        "ExtremeMatter": {
            "Analyses": []
        },
        "Cosmology": {
            "Counterparts": []
        },
        "RatesAndPopulations": {
            "RnPRunsUsingThisSuperevent": []
        },
        "ParameterEstimation": {
            "Analysts": [],
            "Reviewers": [],
            "Status": "unstarted",
            "Results": [],
            "SafeSamplingRate": 4096.0,
            "Notes": []
        },
        "Lensing": {
            "Analyses": []
        },
        "TestingGR": {
            "IMRCTAnalyses": [],
            "SSBAnalyses": [],
            "MDRAnalyses": [],
            "PSEOBRDAnalyses": [],
            "FTIAnalyses": [],
            "SIMAnalyses": []
        },
        "DetectorCharacterization": {
            "Analysts": [],
            "Reviewers": [],
            "Detectors": [],
            "Status": "unstarted",
            "RecommendedDetectors": [],
            "RecommendedMinimumFrequency": 20.0,
            "RecommendedMaximumFrequency": 2048.0,
            "RecommendedDuration": 4.0,
            "Results": [],
            "RecommendedChannels": [],
            "Notes": []
        }
    }

Notably, this default data *does not* include the GraceDB information
- updating the superevent with this information requires specifically fetching that data from GraceDB.
However, when interacting with the central CBC library or it's derivatives
(which are directly or indirectly kept up to date with GraceDB)
this should not be an issue. 
However, if we want to add GraceDB data manually, we can do:
.. code-block::

    >>> gracedb_info = cbcflow.gracedb.fetch_gracedb_information("S190521q")
    INFO:cbcflow.gracedb:Using configuration default GraceDB service_url
    INFO:cbcflow.gracedb:Using GraceDB service_url: https://gracedb.ligo.org/api/
    >>> metadata.update(gracedb_info)

The first command fetches the data in question from GraceDB,
while the second updates the metadata with this new information. 

Then the GraceDB data entry now looks like:

.. code-block::

    ...
       "GraceDB": {
            "PreferredEvent": "G333655",
            "FAR": 0.00027038072585128,
            "GPSTime": 1242457621.830566,
            "Instruments": "H1,L1",
            "LastUpdate": "2023-02-27 15:08:21.085697"
        },
    ...

As one may see, this is not a significant event, hence why you've never heard of it before!
The LastUpdate element reflects not the date of the GraceDB entry's last update, but rather the last time at which
this GraceDB entry of the metadata was updated. 

Now that metadata has been loaded, we may edit it.
We can borrow an example from :doc:`command-line-usage`, by defining our update json: 

.. code-block:: 

    >>> update_add_json = {
        "ParameterEstimation":{
            "Status":"ongoing",
            "Analysts":["Albert Einstein"],
            "Reviewers":["Kip Thorne", "Karl Schwarzschild"]
        }
    }
    >>> metadata.update(update_add_json)

Then the ParameterEstimation section should now look like:

.. code-block::
    
    ...
        "ParameterEstimation": {
            "Analysts": [
            "Albert Einstein"
            ],
            "Reviewers": [
            "Kip Thorne",
            "Karl Schwarzschild"
            ],
            "Status": "ongoing",
            "Results": [],
            "SafeSamplingRate": 4096.0,
            "Notes": []
        },
    ...

Similar to before, if one wants to remove an array element, one should construct a negative image JSON:

.. code-block::

    >>> update_remove_json = {
        "ParameterEstimation":{
            "Reviewers":["Kip Thorne"]
        }
    }

and then apply it in removal mode:

.. code-block::

    metadata.update(update_remove_json, is_removal=True)

So that ParameterEstimation now looks like:

.. code-block::

    ...
        "ParameterEstimation": {
            "Analysts": [
            "Albert Einstein"
            ],
            "Reviewers": [
            "Karl Schwarzschild"
            ],
            "Status": "ongoing",
            "Results": [],
            "SafeSamplingRate": 4096.0,
            "Notes": []
        },
    ...

The same examples from before also work to arbitrary complexity.
For example, the last yaml update method would be rendered as:

.. code-block::

    >>> update_add_json_2 = {
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

   >>> metadata.write_to_library(message="A git commit message")
   INFO:cbcflow.metadata:Writing file /home/rhiannon.udall/meta-data/testing_libraries/cbcflow-gwosc-integration-testbed-library/S190521q-cbc-metadata.json

If the library is a git repository (and our example implicitly is - this is flagged when making the MetaData object, and is default True),
then writing to it will also automatically commit the changes. If no commit message is given then a default message will be used. 
