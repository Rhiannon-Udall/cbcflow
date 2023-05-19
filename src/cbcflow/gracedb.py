"""Methods for interacting with gracedb"""
from datetime import datetime
from typing import Union, Tuple

from .utils import setup_logger

logger = setup_logger()


def fetch_gracedb_information(
    sname: str,
    service_url: Union[str, None] = None,
    cred: Union[Tuple[str, str], str, None] = None,
) -> dict:
    """Get the standard GraceDB metadata contents for this superevent

    Parameters
    ==========
    sname : str
        The sname of the superevent to fetch.
    service_url : Union[str, None], optional
        The url for the GraceDB instance to access.
        If None is passed then this will use the configuration default.
    cred : Union[Tuple[str, str], str, None]
        Per https://ligo-gracedb.readthedocs.io/en/latest/api.html#ligo.gracedb.rest.GraceDb, information on credentials
        to use in authentication.

    Returns
    =======
    dict
        An update dictionary to apply to the metadata, containing the GraceDB info.
    """
    from ligo.gracedb.rest import GraceDb
    from ligo.gracedb.exceptions import HTTPError

    if service_url is None:
        from .configuration import config_defaults

        service_url = config_defaults["gracedb_service_url"]
        logger.info("Using configuration default GraceDB service_url")

    data = dict(GraceDB=dict(Events=[]), Cosmology=dict())

    with GraceDb(service_url=service_url, cred=cred) as gdb:
        try:
            # Get the json of metadata for the superevent
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            msg = f"Superevent {sname} not found on {service_url}. "
            msg += "Either it does not exist, or you may need to run ligo-proxy-init."
            raise ValueError(msg)
        # We want the one best event per pipeline
        event_dict = superevent["pipeline_preferred_events"]
        preferred_event = superevent["preferred_event_data"]
        if len(event_dict) == 0:
            event_dict[preferred_event["pipeline"]] = preferred_event

        for pipeline, event in superevent["pipeline_preferred_events"].items():
            if pipeline.lower().strip() in ["spiir", "mbta", "gstlal", "pycbc"]:
                try:
                    event_data = dict()
                    # Get the
                    gname = event["graceid"]
                    # Get the preferred event across pipelines
                    if gname == superevent["preferred_event"]:
                        data["GraceDB"]["Instruments"] = event["instruments"]
                        event_data["State"] = "preferred"
                    else:
                        event_data["State"] = "neighbor"
                    event_data["UID"] = gname
                    event_data["Pipeline"] = pipeline
                    # We specifically want the label that conveys whether this is
                    # an offline or online result (or which offline)
                    for label in event["labels"]:
                        if "GWTC" in label:
                            event_data["Label"] = label
                    event_data["GPSTime"] = event["gpstime"]
                    event_data["FAR"] = event["far"]
                    event_data["NetworkSNR"] = event["extra_attributes"][
                        "CoincInspiral"
                    ]["snr"]
                    for ii, inspiral in enumerate(
                        event["extra_attributes"]["SingleInspiral"]
                    ):
                        ifo = inspiral["ifo"]
                        snr_key = f"{ifo}SNR"
                        event_data[snr_key] = inspiral["snr"]
                        if ii == 0:
                            event_data["Mass1"] = inspiral["mass1"]
                            event_data["Mass2"] = inspiral["mass2"]
                            event_data["Spin1z"] = inspiral["spin1z"]
                            event_data["Spin2z"] = inspiral["spin2z"]
                        else:
                            # The SingleInspirals should be the same template
                            # If they aren't, that's pretty bad! so we put in
                            # impossible placeholders
                            if (
                                (event_data["Mass1"] != inspiral["mass1"])
                                or (event_data["Mass2"] != inspiral["mass2"])
                                or (event_data["Spin1z"] != inspiral["spin1z"])
                                or (event_data["Spin2z"] != inspiral["spin2z"])
                            ):

                                logger.warning(
                                    "Templates do not match!\
                                            Assigning placeholder masses and spins"
                                )
                                event_data["Mass1"] = -1
                                event_data["Mass2"] = -1
                                event_data["Spin1z"] = -1
                                event_data["Spin2z"] = -1

                    try:
                        # All pipelines should provide source classification
                        pastro_data = gdb.files(
                            gname, f"{pipeline.lower()}.p_astro.json"
                        ).json()

                        event_data["Pastro"] = 1 - pastro_data["Terrestrial"]
                        event_data["Pbbh"] = pastro_data["BBH"]
                        event_data["Pbns"] = pastro_data["BNS"]
                        event_data["Pnsbh"] = pastro_data["NSBH"]
                    except HTTPError:
                        logger.warning(
                            f"Was not able to get source classification for G-event {gname}"
                        )

                    try:
                        # Here we get information from the general em_bright file
                        embright_data = gdb.files(gname, "em_bright.json").json()
                        for key in embright_data:
                            if key == "HasNS":
                                event_data["HasNS"] = embright_data[key]
                            elif key == "HasRemnant":
                                event_data["HasRemnant"] = embright_data[key]
                            elif key == "HasMassGap":
                                event_data["HasMassGap"] = embright_data[key]
                    except HTTPError:
                        logger.debug(f"No em bright provided for G-event {gname}")

                    try:
                        # Some pipelines will provide source classification, others will not
                        # This is that information where available
                        embright_data = gdb.files(
                            gname, f"{pipeline.lower()}.em_bright.json"
                        ).json()
                        for key in embright_data:
                            if key == "HasNS":
                                event_data["PipelineHasNS"] = embright_data[key]
                            elif key == "HasRemnant":
                                event_data["PipelineHasRemnant"] = embright_data[key]
                            elif key == "HasMassGap":
                                event_data["PipelineHasMassGap"] = embright_data[key]
                    except HTTPError:
                        logger.debug(
                            f"No pipeline em bright provided for G-event {gname}"
                        )

                    try:
                        # All pipelines should provide these 3 files
                        file_links = gdb.files(gname, "").json()

                        event_data["XML"] = file_links["coinc.xml"]
                        event_data["SourceClassification"] = file_links[
                            f"{pipeline.lower()}.p_astro.json"
                        ]
                        event_data["Skymap"] = file_links["bayestar.multiorder.fits"]
                        # If this is the preferred event,
                        # Populate the cosmology low latency skymap with this skymap
                        # NOTE: this means that users *cannot* override this definition, since
                        # the monitor will automatically rewrite it this way each time
                        if event_data["State"] == "preferred":
                            data["Cosmology"]["PreferredLowLatencySkymap"] = file_links[
                                "bayestar.multiorder.fits"
                            ]
                    except HTTPError:
                        logger.warning(
                            f"Could not fetch file links for G-event {gname}"
                        )
                    except KeyError:
                        logger.warning(
                            f"Some or all file links were missing for G-event {gname}"
                        )

                    # Add the final event data to the array
                    data["GraceDB"]["Events"].append(event_data)
                except KeyError as err:
                    logger.info(f"Failed with key error {err}")
                    if "graceid" in event.keys():
                        logger.warning(
                            f"Failed to load data for event {event['graceid']}"
                        )
                    else:
                        logger.warning(
                            f"Failed to load an event for superevent {sname},\
                                    and could not return the event's id"
                        )
            elif pipeline.lower().strip() == "cwb" and event["search"].lower() == "bbh":
                # Catch the pipeline cwb in the group cbc
                try:
                    event_data = dict()
                    # Get the
                    gname = event["graceid"]
                    # Get the preferred event across pipelines
                    if gname == superevent["preferred_event"]:
                        data["GraceDB"]["Instruments"] = event["instruments"]
                        event_data["State"] = "preferred"
                    else:
                        event_data["State"] = "neighbor"
                    event_data["UID"] = gname
                    event_data["Pipeline"] = pipeline
                    # We specifically want the label that conveys whether this is
                    # an offline or online result (or which offline)
                    for label in event["labels"]:
                        if "GWTC" in label:
                            event_data["Label"] = label
                    event_data["GPSTime"] = event["gpstime"]
                    event_data["FAR"] = event["far"]
                    event_data["NetworkSNR"] = event["extra_attributes"]["MultiBurst"][
                        "snr"
                    ]
                    try:
                        # All pipelines should provide source classification
                        pastro_data = gdb.files(
                            gname, f"{pipeline.lower()}.p_astro.json"
                        ).json()

                        event_data["Pastro"] = 1 - pastro_data["Terrestrial"]
                        event_data["Pbbh"] = pastro_data["BBH"]
                        event_data["Pbns"] = pastro_data["BNS"]
                        event_data["Pnsbh"] = pastro_data["NSBH"]
                    except HTTPError:
                        logger.warning(
                            f"Was not able to get source classification for G-event {gname}"
                        )

                    try:
                        # Get the trigger file
                        trigger_file = gdb.files(gname, "trigger.txt").read()
                        # Parse lines by string hacking
                        # 'ifo:' and 'sSNR:' are unique hopefully?
                        trigger_file_lines = str(trigger_file).split("\\n")
                        ifo_line = [
                            line for line in trigger_file_lines if "ifo:" in line
                        ][0]
                        sSNR_line = [
                            line for line in trigger_file_lines if "sSNR:" in line
                        ][0]
                        # More string hacking to get ifos
                        ifos = ifo_line.split("")[1].strip().split()
                        # More string hacking to get sSNRs
                        snrs = [
                            float(x) for x in sSNR_line.split(":")[1].strip().split()
                        ]
                        # Loop to assign SNRs by IFO
                        for ii, ifo in ifos.enumerate():
                            event_data[f"{ifo}SNR"] = snrs[ii]
                    except HTTPError:
                        logger.warning(
                            f"Was not able to access trigger.txt for G-event {gname}"
                        )

                    try:
                        file_links = gdb.files(gname, "").json()
                        event_data["Skymap"] = file_links["cwb.multiorder.fits"]
                        event_data["SourceClassification"] = file_links[
                            f"{pipeline.lower()}.p_astro.json"
                        ]
                    except HTTPError:
                        logger.warning(
                            f"Could not fetch file links for G-event {gname}"
                        )

                    # Add the final event data to the array
                    data["GraceDB"]["Events"].append(event_data)

                except KeyError as err:
                    logger.warning(f"Failed with key error {err}")
                    if "graceid" in event.keys():
                        logger.warning(
                            f"Failed to load data for event {event['graceid']}"
                        )
                    else:
                        logger.warning(
                            f"Failed to load an event for superevent {sname},\
                                    and could not return the event's id"
                        )
            else:
                logger.debug(
                    f"Could not load event data for {event['graceid']} because it was from the pipeline\n\
                            {pipeline.lower().strip()} which is not supported"
                )

    data["GraceDB"]["LastUpdate"] = str(datetime.now())

    return data
