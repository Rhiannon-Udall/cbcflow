"""Functionality for information which flows from Asimov into cbcflow"""
import cbcflow
import os
import glob

from asimov import config, logger


class Collector:
    status_map = {
        "ready": "unstarted",
        "processing": "running",
        "running": "running",
        "stuck": "running",
        "restart": "running",
        "stopped": "cancelled",
        "finished": "running",
        "uploaded": "complete",
    }

    supported_pipelines = ["bayeswave", "bilby", "rift"]

    def __init__(self, ledger):
        """
        Collect data from the asimov ledger and write it to a CBCFlow library.
        """
        hook_data = ledger.data["hooks"]["postmonitor"]["cbcflow"]
        self.library = cbcflow.core.database.LocalLibraryDatabase(
            hook_data["library location"]
        )
        self.library.git_pull_from_remote(automated=True)
        self.schema_section = hook_data["schema section"]
        self.ledger = ledger

    def run(self):
        """
        Run the hook.
        """

        for event in self.ledger.get_event():
            # Do setup for the event
            output = {}
            output[self.schema_section] = {}
            pe = output[self.schema_section]["Results"] = []
            metadata = cbcflow.get_superevent(
                event.meta["ligo"]["sname"], library=self.library
            )

            # Get the metadata that already exists for reference
            metadata_pe_results = metadata["ParameterEstimation"]["Results"]
            metadata_pe_results_uids = cbcflow.core.utils.get_uids_from_object_array(
                metadata_pe_results
            )
            for analysis in event.productions:
                if str(analysis.pipeline).lower() in self.supported_pipelines:
                    analysis_output = {}
                    analysis_output["UID"] = analysis.name

                    if analysis.name in metadata_pe_results_uids:
                        corresponding_analysis = metadata_pe_results[
                            metadata_pe_results_uids.index(analysis.name)
                        ]
                    else:
                        corresponding_analysis = None

                    analysis_output["InferenceSoftware"] = str(analysis.pipeline)
                    if analysis.status.lower() in self.status_map.keys():
                        analysis_output["RunStatus"] = self.status_map[
                            analysis.status.lower()
                        ]
                    if "waveform" in analysis.meta:
                        if "approximant" in analysis.meta["waveform"]:
                            analysis_output["WaveformApproximant"] = str(
                                analysis.meta["waveform"]["approximant"]
                            )

                    try:
                        ini = analysis.pipeline.production.event.repository.find_prods(
                            analysis.pipeline.production.name,
                            analysis.pipeline.category,
                        )[0]
                        analysis_output["ConfigFile"] = {}
                        analysis_output["ConfigFile"]["Path"] = ini
                    except IndexError:
                        logger.warning("Could not find ini file for this analysis")

                    analysis_output["Notes"] = []

                    if analysis.comment is not None:
                        # We only want to add the comment to the notes if it doesn't already exist
                        if corresponding_analysis is None:
                            analysis_output["Notes"].append(analysis.comment)
                        elif analysis.comment not in corresponding_analysis["Notes"]:
                            analysis_output["Notes"].append(analysis.comment)

                    if analysis.review.status:
                        if analysis.review.status.lower() == "approved":
                            analysis_output["ReviewStatus"] = "pass"
                        elif analysis.review.status.lower() == "rejected":
                            analysis_output["ReviewStatus"] = "fail"
                        elif analysis.review.status.lower() == "deprecated":
                            analysis_output["Deprecated"] = True
                        messages = sorted(
                            analysis.review.messages, key=lambda k: k.timestamp
                        )
                        if len(messages) > 0:
                            if corresponding_analysis is None:
                                analysis_output["Notes"].append(
                                    f"{messages[0].timestamp:%Y-%m-%d}: {messages[0].message}"
                                )
                            elif (
                                f"{messages[0].timestamp:%Y-%m-%d}: {messages[0].message}"
                                in corresponding_analysis["Notes"]
                            ):
                                analysis_output["Notes"].append(
                                    f"{messages[0].timestamp:%Y-%m-%d}: {messages[0].message}"
                                )

                    if analysis.finished:
                        # Get the results
                        results = analysis.pipeline.collect_assets()

                        if str(analysis.pipeline).lower() == "bayeswave":
                            # If the pipeline is Bayeswave, we slot each psd into its designated spot
                            analysis_output["BayeswaveResults"] = {}

                            for ifo, psd in results["psds"].items():
                                analysis_output["BayeswaveResults"][f"{ifo}PSD"] = {
                                    "Path": psd
                                }

                            if analysis_output["BayeswaveResults"] == {}:
                                # Cleanup if we fail to write any results
                                analysis_output.pop("BayeswaveResults")
                        elif str(analysis.pipeline).lower() == "bilby":
                            # If it's bilby, we need to parse out which of possibly multiple merge results we want
                            analysis_output["ResultFile"] = {}
                            if len(results["samples"]) == 0:
                                logger.warning(
                                    "Could not get samples from Bilby analysis, even though run is nominally finished!"
                                )
                            elif len(results["samples"]) == 1:
                                # If there's only one easy enough
                                analysis_output["ResultFile"]["Path"] = results[
                                    "samples"
                                ][0]
                            else:
                                # If greater than one, we will try to prefer the hdf5 results
                                hdf_results = [
                                    x
                                    for x in results["samples"]
                                    if "hdf5" in x or "h5" in x
                                ]
                                if len(hdf_results) == 0:
                                    # If there aren't any, this implies we have more than one result,
                                    # and they are all jsons
                                    # This is a bad situation, because it implies CBCFlow
                                    # does not have the requisite fields to handle the analysis outputs.
                                    logger.warning(
                                        "No hdf5 results were found, but more than one json result is present -\
                                                skipping since we can't choose!"
                                    )
                                    analysis_output["ResultFile"]["Path"] = results[
                                        "samples"
                                    ][0]
                                elif len(hdf_results) == 1:
                                    # If there's only one hdf5, then we can proceed smoothly
                                    analysis_output["ResultFile"]["Path"] = hdf_results[
                                        0
                                    ]
                                elif len(hdf_results) > 1:
                                    # This is the same issue as described above, just with all hdf5s instead
                                    logger.warning(
                                        "Multiple merge_result hdf5s returned from Bilby analysis -\
                                                skipping since we can't choose!"
                                    )
                                # This has treated the case of >1 json and only 1 hdf5 as being fine
                                # Maybe it should throw a warning for this too?
                                if analysis_output["ResultFile"] == {}:
                                    # Cleanup if we fail to get any results
                                    analysis_output.pop("ResultFile")
                        elif str(analysis.pipeline).lower() == "rift":
                            # RIFT should only ever return one result file - extrinsic_posterior_samples.dat
                            results = analysis.pipeline.collect_assets()
                            if len(results) == 1:
                                analysis_output["ResultFile"] = {}
                                analysis_output["ResultFile"]["Path"] = results[0]
                            else:
                                logger.warning(
                                    "Could not get results from RIFT run - to many or too few outputs"
                                )

                    if analysis.status == "uploaded":
                        # Next, try to get PESummary information
                        pesummary_pages_dir = os.path.join(
                            config.get("general", "webroot"),
                            analysis.event.name,
                            analysis.name,
                            "pesummary",
                        )
                        sample_h5s = glob.glob(f"{pesummary_pages_dir}/samples/*.h5")
                        if len(sample_h5s) == 1:
                            # If there is only one samples h5, we're good!
                            # This *should* be true, and it should normally be called "posterior_samples.h5"
                            # But this may not be universal?
                            analysis_output["PESummaryResultFile"] = {}
                            analysis_output["PESummaryResultFile"]["Path"] = sample_h5s[
                                0
                            ]
                        else:
                            logger.warning(
                                "Could not uniquely determine location of PESummary result samples"
                            )
                        if "public_html" in pesummary_pages_dir.split("/"):
                            # Currently, we do the bit of trying to guess the URL ourselves
                            # In the future there may be an asimov config value for this
                            pesummary_pages_url_dir = (
                                cbcflow.core.utils.get_url_from_public_html_dir(
                                    pesummary_pages_dir
                                )
                            )
                            # If we've written a result file, infer its url
                            if "PESummaryResultFile" in analysis_output.keys():
                                # We want to get whatever the name we previously decided was
                                # This will only run if we did make that decision before, so we can use similar logic
                                analysis_output["PESummaryResultFile"][
                                    "PublicHTML"
                                ] = f"{pesummary_pages_url_dir}/samples/{sample_h5s[0].split('/')[-1]}"
                            # Infer the summary pages URL
                            analysis_output[
                                "PESummaryPageURL"
                            ] = f"{pesummary_pages_url_dir}/home.html"

                    pe.append(analysis_output)
                    metadata.update(output)
                    # Note that Asimov *should* write to main, unlike most other processes
                    metadata.write_to_library(
                        message="Analysis run update by asimov", branch_name="main"
                    )
                else:
                    logger.info(
                        f"Pipeline {analysis.pipeline} is not supported by cbcflow"
                    )
                    logger.info(
                        "If this is a mistake, please contact the cbcflow developers to add support."
                    )
        self.library.git_push_to_remote()
