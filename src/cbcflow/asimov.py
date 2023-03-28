import cbcflow
import logging
import os
import glob

from asimov.event import Event

logger = logging.getLogger(__name__)


class Collector:
    status_map = {
        "ready": "unstarted",
        "processing": "ongoing",
        "running": "ongoing",
        "stuck": "hold",
        "restart": "hold",
        "stopped": "cancelled",
        "finished": "complete",
        "uploaded": "complete",
    }

    def __init__(self, ledger):
        """
        Collect data from the asimov ledger and write it to a CBCFlow library.
        """
        hook_data = ledger.data["hooks"]["postmonitor"]["cbcflow"]
        self.library = hook_data["library location"]
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
            for analysis in event.productions:
                analysis_output = {}
                analysis_output["UID"] = analysis.name
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
                if "ini" in analysis.meta:
                    analysis_output["ConfigFile"] = {}
                    analysis_output["ConfigFile"]["Path"] = analysis.meta["ini"]
                analysis_output["Notes"] = [analysis.comment]
                if analysis.finished:
                    # Get the results
                    results = analysis.pipeline.collect_assets()
                    if str(analysis.pipeline).lower() == "bayeswave":
                        # If the pipeline is Bayeswave, we slot each psd into its designated spot
                        analysis_output["BayeswaveResults"] = {}
                        for ifo, psd in results["psds"].items():
                            analysis_output["BayeswaveResults"][f"{ifo}PSD"][
                                "Path"
                            ] = psd
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
                            analysis_output["ResultFile"]["Path"] = results["samples"][
                                0
                            ]
                        else:
                            # If greater than one, we will try to prefer the hdf5 results
                            hdf_results = [x for x in results["samples"] if "hdf5" in x]
                            if len(hdf_results) == 0:
                                # If there aren't any, this implies we have more than one result, and they are all jsons
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
                                analysis_output["ResultFile"]["Path"] = hdf_results[0]
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
                    else:
                        logger.warning(
                            f"Method to obtain result file for pipeline {str(analysis.pipeline)} is not implemented"
                        )

                if analysis.status == "uploaded":
                    # Next, try to get PESummary information
                    # I've guessed this form based on
                    # https://git.ligo.org/asimov/asimov/-/blob/review/asimov/pipelines/bilby.py#L428
                    # TODO is that correct?
                    pesummary_pages_dir = os.path.join(
                        event.pipeline.production.event.name,
                        event.pipeline.production.name,
                    )
                    sample_h5s = glob.glob(f"{pesummary_pages_dir}/pesummary/samples/")
                    if len(sample_h5s) == 1:
                        # If there is only one samples h5, we're good!
                        # This *should* be true, and it should normally be called "posterior_samples.h5"
                        # But this may not be universal?
                        analysis_output["PESummaryResultFile"] = {}
                        analysis_output["PESummaryResultFile"]["Path"] = sample_h5s[0]
                    else:
                        logger.warning(
                            "Could not uniquely determine location of PESummary result samples"
                        )
                    if pesummary_pages_dir.split("/")[2] == "public_html":
                        # This is the case where files are being written directly into public html
                        # First get the stuff that comes after public_html - this structure will stay the same
                        pesummary_pages_url_extension = "/".join(
                            pesummary_pages_dir.split("/")[3:]
                        )
                        # next get the user in ldas form
                        url_user = f"~{pesummary_pages_dir.split('/')}"
                        # Combine them
                        pesummary_pages_url_dir = f"https://ldas-jobs.ligo.caltech.edu/\
                            {url_user}/{pesummary_pages_url_extension}"
                        # If we've written a result file, infer its url
                        if "PESummaryResultFile" in analysis_output.keys():
                            # We want to get whatever the name we previously decided was
                            # This will only run if we did make that decision before, so we can use similar logic
                            analysis_output["PESummaryResultFile"][
                                "PublicHTML"
                            ] = f"{pesummary_pages_url_dir}/pesummary/samples/{sample_h5s[0].split('/')[-1]}"
                        # Infer the summary pages URL
                        analysis_output[
                            "PESummaryPageURL"
                        ] = f"{pesummary_pages_url_dir}/pesummary/home.html"

                pe.append(analysis_output)
                metadata.update(output)
                metadata.write_to_library(message="Analysis run update by asimov")


class Applicator:
    """Apply information from CBCFlow to an asimov event"""

    def __init__(self, ledger):
        hook_data = ledger.data["hooks"]["applicator"]["cbcflow"]
        self.ledger = ledger
        self.library = hook_data["library location"]

    def run(self, sid=None):

        metadata = cbcflow.get_superevent(sid, library=self.library)
        detchar = metadata.data["DetectorCharacterization"]
        grace = metadata.data["GraceDB"]
        ifos = detchar["RecommendedDetectors"]
        if len(ifos) == 0:
            ifos = grace["Instruments"].split(",")
        quality = {}
        max_f = quality["maximum frequency"] = {}
        min_f = quality["minimum frequency"] = {}

        for ifo in ifos:
            max_f[ifo] = detchar["RecommendedMaximumFrequency"]
            min_f[ifo] = detchar["RecommendedMinimumFrequency"]

        # Data settings
        data = {}
        channels = data["channels"] = {}
        if len(detchar["RecommendedChannels"]) > 0:
            for i, ifo in enumerate(ifos):
                channels[ifo] = detchar["RecommendedChannels"][i]
        data["segment length"] = detchar["RecommendedDuration"]

        # GraceDB Settings
        ligo = {}
        ligo["preferred event"] = grace["PreferredEvent"]
        ligo["sname"] = sid
        ligo["false alarm rate"] = grace["FAR"]

        output = {
            "name": metadata.data["Sname"],
            "quality": quality,
            "ligo": ligo,
            "data": data,
            "event time": grace["GPSTime"],
        }

        event = Event.from_dict(output)
        self.ledger.add_event(event)
