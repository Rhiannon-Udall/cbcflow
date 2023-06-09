Updating Metadata in ``cbcflow``
================================

Updating From GraceDB
---------------------

When interacting with the central CBC library or it's derivatives
(which are directly or indirectly kept up to date with GraceDB)
GraceDB information should be automatically kept up to date.
To see what this might look like, we can do:

.. code-block::

    >>> metadata_pull_manually = cbcflow.get_superevent("S230410cb")
    INFO:cbcflow.schema:Using schema file /home/rhiannon.udall/.conda/envs/cbcflow_development/lib/python3.10/site-packages/cbcflow/schema/cbc-meta-data-v2.schema
    INFO:cbcflow.metadata:No library file: creating defaults
    >>> gracedb_info = cbcflow.gracedb.fetch_gracedb_information("S230410cb")
    INFO:cbcflow.gracedb:Using configuration default GraceDB service_url
    INFO:cbcflow.gracedb:No pipeline em bright provided for G-event G995755
    INFO:cbcflow.gracedb:Could not load event data for G995752 because it was from the pipeline
                                cwb which is not supported
    INFO:cbcflow.gracedb:No pipeline em bright provided for G-event G995750
    INFO:cbcflow.gracedb:No pipeline em bright provided for G-event G995747
    >>> metadata_pull_manually.update(gracedb_info)

The command ``gracedb.fetch_gracedb_information`` pulls information from gracedb, while ``update`` updates the metadata with this new information. 
Note that this event was pulled from playground data (https://gracedb-playground.ligo.org/api/),
as set in the test ``~/.cbcflow.cfg`` in use.

Updating Metadata
-----------------

Now that metadata has been loaded, we may edit it.
We can borrow an example from :doc:`command-line-usage`, by defining our update json: 

.. code-block:: 

    >>> update_add_json = {"ParameterEstimation":{
            "Results":[
                {
                "UID":"Tutorial1",
                "WaveformApproximant": "MyAwesomeWaveform",
                "ResultFile":{
                    "Path" : "/home/rhiannon.udall/meta-data/testing_libraries/cbcflow-tutorial-library/example_linking_file.txt"
                    }
                }
            ]
            }
        }
    >>> metadata.update(update_add_json)

Then the ParameterEstimation section should now look like:

.. collapsible:: ParameterEstimation After Updates

    .. code-block::
        
        ...
            "ParameterEstimation": {
                "Analysts": [],
                "Reviewers": [],
                "Status": "unstarted",
                "Results": [
                    {
                        "ReviewStatus": "unstarted",
                        "Deprecated": false,
                        "Publications": [],
                        "Notes": [],
                        "UID": "Tutorial1",
                        "WaveformApproximant": "MyAwesomeWaveform",
                        "ResultFile": {
                            "Path": "CIT:/home/rhiannon.udall/meta-data/testing_libraries/cbcflow-tutorial-library/example_linking_file.txt",
                            "MD5Sum": "5b24b3bea9381f64fa7cce695507bba7",
                            "DateLastModified": "2023/04/11 18:27:11"
                        }
                    }
                ],
                "SafeSamplingRate": 4096.0,
                "SafeLowerMassRatio": 0.05,
                "Notes": []
            },
        ...

Writing Our Changes to the File
-------------------------------

Once we are happy with our changes to the metadata, we can write it back to the library:

.. code-block::

    >>> metadata.write_to_library(message="A git commit message")
    INFO:cbcflow.metadata:Super event: S230331h, GPSTime=1364258362.641068, chirp_mass=1.25
    INFO:cbcflow.metadata:Writing file /home/rhiannon.udall/meta-data/testing_libraries/ru-cbcflow-test-library/S230331h-cbc-metadata.json

If the library is a git repository (and our example implicitly is - this is flagged when making the MetaData object, and is default True),
then writing to it will also automatically commit the changes. If no commit message is given then a default message will be used. 
