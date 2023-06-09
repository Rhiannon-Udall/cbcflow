Building Blocks: Metadata and Libraries
=======================================

When writing scripts which use ``cbcflow``, you should expect to use two classes:
``cbcflow.metadata.MetaData`` and ``cbcflow.database.LocalLibraryDatabase``.
These describe the attributes and methods for a given event's metadata and the 
library of event metadata respectively.
This page will give an introduction to each in turn, while a more thorough tour
may be found in subsequent pages.

``MetaData``
------------

The most central building block in ``cbcflow`` is metadata. 
Loading this is surprisingly easy - for example:

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

.. collapsible:: The contents of S230409g

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

If you want to read a specific element in a ``MetaData`` object, it also works like you expect it to.
For example:

.. code-block::

    >>> metadata["GraceDB"]["Events"][2]
    {'State': 'preferred', 'UID': 'G991765', 'Pipeline': 'gstlal', 'GPSTime': 1365062495.091802, 'FAR': 2.900794989032493e-36,
    'NetworkSNR': 16.56542135029717, 'H1SNR': 12.060055, 'Mass1': 1.7551488, 'Mass2': 1.540255, 'Spin1z': 0.04640625, 'Spin2z': 0.04640625,
    'L1SNR': 10.567706, 'V1SNR': 4.1583471, 'Pastro': 1.0, 'Pbbh': 3.347659662210488e-57, 'Pbns': 1.0, 'Pnsbh': 5.433561263857133e-56,
    'HasNS': 1.0, 'HasRemnant': 1.0, 'HasMassGap': 0.0, 'XML': 'https://gracedb-playground.ligo.org/api/events/G991765/files/coinc.xml',
    'SourceClassification': 'https://gracedb-playground.ligo.org/api/events/G991765/files/gstlal.p_astro.json',
    'Skymap': 'https://gracedb-playground.ligo.org/api/events/G991765/files/bayestar.multiorder.fits'}

Note that since ``Events`` is a list (of dictionaries), this level of the hierarchy must be accessed by list index, *not* by the UID name.
This may be updated in the future, but for now is a necessary evil. 

If you want to write to the metadata, it is *strongly* recommended that you do so with the ``update`` method detailed in
:doc:`updating-metadata-with-the-python-api`, which will automatically handle merging the correct UIDs, validation against the schema,
and so on.

``LocalLibraryDatabase``
------------------------