Python Metadata Interface
=========================

Reading Metadata
----------------

One of the most common interactions we may have with ``cbcflow`` metadata is to read it programmatically.
To do this, we start by loading in metadata for usage.
Prototypically, this may be done with: 

.. code-block::

    >>> import cbcflow

    >>> metadata = cbcflow.get_superevent("S230409lg")
    INFO:cbcflow.schema:Using schema file /home/rhiannon.udall/.conda/envs/cbcflow_development/lib/python3.10/site-packages/cbcflow/schema/cbc-meta-data-v2.schema

If a specific library argument is not passed, then the default library will be used (see :doc:`configuration`), 
as has occurred in this example. 
To pass a specific library, one may add the keyword argument ``library=/a/path/to/a/library``.

If the library already contains metadata for the superevent described by ``sname``,
then that metadata will be loaded.
Otherwise, this superevent will start with default data.

To see what our metadata looks like, we can use the ``pretty_print()`` method:

.. code-block::

    >>> metadata.pretty_print()
    INFO:cbcflow.metadata:Metadata contents for S230409lg:
    INFO:cbcflow.metadata:{
        "Sname": "S230409lg",
        "Info": {
            "Labels": [],
            "SchemaVersion": "v2",
            "Notes": []
        },
        "Publications": {
            "Papers": []
        },
        "GraceDB": {
            "Events": [
                {
                    "State": "neighbor",
                    "UID": "G991768",
                    "Pipeline": "pycbc",
                    "GPSTime": 1365062495.063965,
                    "FAR": 2.223779464140237e-06,
                    "NetworkSNR": 16.22064184905374,
                    "V1SNR": 4.3057876,
                    "Mass1": 2.0122149,
                    "Mass2": 1.3525492,
                    "Spin1z": 0.23247161,
                    "Spin2z": -0.21646233,
                    "H1SNR": 11.750094,
                    "L1SNR": 10.320111,
                    "Pastro": 0.005880358839495448,
                    "Pbbh": 0.0,
                    "Pbns": 0.005880358839495448,
                    "Pnsbh": 0.0,
                    "HasNS": 1.0,
                    "HasRemnant": 1.0,
                    "HasMassGap": 0.0,
                    "PipelineHasMassGap": 0.0,
                    "XML": "https://gracedb-playground.ligo.org/api/events/G991768/files/coinc.xml",
                    "SourceClassification": "https://gracedb-playground.ligo.org/api/events/G991768/files/pycbc.p_astro.json",
                    "Skymap": "https://gracedb-playground.ligo.org/api/events/G991768/files/bayestar.multiorder.fits"
                },
                {
                    "State": "neighbor",
                    "UID": "G991767",
                    "Pipeline": "MBTA",
                    "GPSTime": 1365062495.074961,
                    "FAR": 1.501446e-09,
                    "NetworkSNR": 15.872046,
                    "V1SNR": 2.175341,
                    "Mass1": 2.76463,
                    "Mass2": 1.026004,
                    "Spin1z": 0.262998,
                    "Spin2z": 0.0,
                    "H1SNR": 12.018019,
                    "L1SNR": 10.13691,
                    "Pastro": 1.0,
                    "Pbbh": 0.0,
                    "Pbns": 0.924042,
                    "Pnsbh": 0.075958,
                    "HasNS": 1.0,
                    "HasRemnant": 1.0,
                    "HasMassGap": 0.0,
                    "XML": "https://gracedb-playground.ligo.org/api/events/G991767/files/coinc.xml",
                    "SourceClassification": "https://gracedb-playground.ligo.org/api/events/G991767/files/mbta.p_astro.json",
                    "Skymap": "https://gracedb-playground.ligo.org/api/events/G991767/files/bayestar.multiorder.fits"
                },
                {
                    "State": "preferred",
                    "UID": "G991765",
                    "Pipeline": "gstlal",
                    "GPSTime": 1365062495.091802,
                    "FAR": 2.900794989032493e-36,
                    "NetworkSNR": 16.56542135029717,
                    "H1SNR": 12.060055,
                    "Mass1": 1.7551488,
                    "Mass2": 1.540255,
                    "Spin1z": 0.04640625,
                    "Spin2z": 0.04640625,
                    "L1SNR": 10.567706,
                    "V1SNR": 4.1583471,
                    "Pastro": 1.0,
                    "Pbbh": 3.347659662210488e-57,
                    "Pbns": 1.0,
                    "Pnsbh": 5.433561263857133e-56,
                    "HasNS": 1.0,
                    "HasRemnant": 1.0,
                    "HasMassGap": 0.0,
                    "XML": "https://gracedb-playground.ligo.org/api/events/G991765/files/coinc.xml",
                    "SourceClassification": "https://gracedb-playground.ligo.org/api/events/G991765/files/gstlal.p_astro.json",
                    "Skymap": "https://gracedb-playground.ligo.org/api/events/G991765/files/bayestar.multiorder.fits"
                },
                {
                    "State": "neighbor",
                    "UID": "G991763",
                    "Pipeline": "spiir",
                    "GPSTime": 1365062495.087402,
                    "FAR": 2.197285962424614e-27,
                    "NetworkSNR": 16.38410099714992,
                    "H1SNR": 12.11474,
                    "Mass1": 2.1702261,
                    "Mass2": 1.2627214,
                    "Spin1z": 0.10948601,
                    "Spin2z": 0.042859491,
                    "L1SNR": 10.236156,
                    "V1SNR": 4.1101012,
                    "Pastro": 1.0,
                    "Pbbh": 0.0,
                    "Pbns": 1.0,
                    "Pnsbh": 0.0,
                    "HasNS": 1.0,
                    "HasRemnant": 1.0,
                    "HasMassGap": 0.0,
                    "XML": "https://gracedb-playground.ligo.org/api/events/G991763/files/coinc.xml",
                    "SourceClassification": "https://gracedb-playground.ligo.org/api/events/G991763/files/spiir.p_astro.json",
                    "Skymap": "https://gracedb-playground.ligo.org/api/events/G991763/files/bayestar.multiorder.fits"
                }
            ],
            "Instruments": "H1,L1,V1",
            "LastUpdate": "2023-04-11 18:27:52.777929"
        },
        "ExtremeMatter": {
            "Analyses": []
        },
        "Cosmology": {
            "Counterparts": [],
            "CosmologyRunsUsingThisSuperevent": [],
            "Notes": [],
            "PreferredLowLatencySkymap": "https://gracedb-playground.ligo.org/api/events/G991765/files/bayestar.multiorder.fits"
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
            "SafeLowerMassRatio": 0.05,
            "Notes": []
        },
        "Lensing": {
            "Analyses": []
        },
        "TestingGR": {
            "BHMAnalyses": [],
            "EchoesCWBAnalyses": [],
            "FTIAnalyses": [],
            "IMRCTAnalyses": [],
            "LOSAAnalyses": [],
            "MDRAnalyses": [],
            "ModeledEchoesAnalyses": [],
            "PCATGRAnalyses": [],
            "POLAnalyses": [],
            "PSEOBRDAnalyses": [],
            "PYRINGAnalyses": [],
            "QNMRationalFilterAnalyses": [],
            "ResidualsAnalyses": [],
            "SIMAnalyses": [],
            "SMAAnalyses": [],
            "SSBAnalyses": [],
            "TIGERAnalyses": [],
            "UnmodeledEchoesAnalyses": [],
            "Notes": []
        },
        "DetectorCharacterization": {
            "Analysts": [],
            "Reviewers": [],
            "ParticipatingDetectors": [],
            "Status": "unstarted",
            "RecommendedDetectors": [],
            "RecommendedDuration": 4.0,
            "DQRResults": [],
            "Notes": []
        }
    }

Since this event has already been initialized from gracedb, we can see a lot of gracedb information already.

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
