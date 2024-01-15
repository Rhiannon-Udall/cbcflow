"""Methods for interacting with gracedb"""
from datetime import datetime
from typing import Union, Tuple, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ligo.gracedb.rest import GraceDb

from ..core.utils import setup_logger

logger = setup_logger()


def add_common_gevent_metadata(
    gevent_data: dict, preferred: bool = False
) -> Tuple[dict, dict]:
    """Adds metadata which should be common for *any* gevent.
    For example, gid, instruments, etc.

    Parameters
    ==========
    gevent_data : dict
        The json output of the query to gracedb for this event's metadata
    preferred : bool
        Whether this is the preferred gevent for the superevent.
        Determines whether certain event data should be set using this gevent.

    Returns
    =======
    dict
        Updates to the cbcflow gevent dict.
        This should satisfy structural requirements of `$defs-Events` in the schema
    dict
        Updates to the cbcflow sevent dict.
        This should satisfy structural requirements of `GraceDB` in the schema.
    """
    cbcflow_gevent_dict = dict()
    cbcflow_sevent_dict = dict()
    cbcflow_gevent_dict["UID"] = gevent_data["graceid"]
    cbcflow_gevent_dict["Pipeline"] = gevent_data["pipeline"]
    cbcflow_gevent_dict["GPSTime"] = gevent_data["gpstime"]
    cbcflow_gevent_dict["FAR"] = gevent_data["far"]
    if preferred:
        cbcflow_gevent_dict["State"] = "preferred"
        cbcflow_sevent_dict["Instruments"] = gevent_data["instruments"]
    else:
        cbcflow_gevent_dict["State"] = "neighbor"
    return cbcflow_gevent_dict, cbcflow_sevent_dict


def add_pastro_gevent_metadata(pastro_data: dict) -> dict:
    """Adds information from the pastro file to the gevent metadata

    Parameters
    =========
    pastro_data : dict
        JSON data read from the gracedb p_astro.json file

    Returns
    =======
    dict
        Updates to the cbcflow gevent metadata, for pastro info.
        This should satisfy structural requirements of `$defs-Events` in the schema
    """
    cbcflow_gevent_dict = dict()
    cbcflow_gevent_dict["Pastro"] = 1 - pastro_data["Terrestrial"]
    cbcflow_gevent_dict["Pbbh"] = pastro_data["BBH"]
    cbcflow_gevent_dict["Pbns"] = pastro_data["BNS"]
    cbcflow_gevent_dict["Pnsbh"] = pastro_data["NSBH"]

    return cbcflow_gevent_dict


def add_embright_gevent_metadata(
    embright_data: dict, pipeline_embright: bool = False
) -> dict:
    """Generate updates to a gevent object for embright metadata

    Parameters
    ==========
    embright_data : dict
        The data read from an em_bright.json file
    pipeline_embright : bool
        Whether the data is read from a {pipeline}.em_bright.json file or not.
        Determines which fields will be populated.

    Returns
    =======
    dict
        Updates to the cbcflow gevent metadata, for embright info.
        This should satisfy structural requirements of `$defs-Events` in the schema
    """
    if pipeline_embright:
        prefix = "Pipeline"
    else:
        prefix = ""

    cbcflow_gevent_dict = dict()
    cbcflow_gevent_dict[f"{prefix}HasNS"] = embright_data.get("HasNS", None)
    cbcflow_gevent_dict[f"{prefix}HasRemnant"] = embright_data.get("HasRemnant", None)
    cbcflow_gevent_dict[f"{prefix}HasMassGap"] = embright_data.get("HasMassGap", None)
    # Cleanup keys with no value
    cbcflow_gevent_dict = {
        k: v for k, v in cbcflow_gevent_dict.items() if v is not None
    }

    return cbcflow_gevent_dict


def add_cwbtrigger_gevent_metadata(trigger_file_contents: str) -> dict:
    """Parse the contents of the trigger.txt file which cwb uploads.

    Parameters
    ==========
    trigger_file_contents : str
        The contents of the trigger file

    Returns
    =======
    dict
        Updates to the cbcflow gevent metadata, for cwb SNR info.
        This should satisfy structural requirements of `$defs-Events` in the schema
    """
    cbcflow_gevent_dict = dict()
    # CWB contents are in a text file rather than a json dict
    # We'll parse by making assumptions about those files:
    # 1. There exists one and only one line which looks like e.g. ifo:\tH1 L1\n
    # 2. There exists one and only one line which looks like e.g. sSNR:\txx.xxxxx yy.yyyyy
    # So we'll do string parsing to pull out those elements
    trigger_file_lines = str(trigger_file_contents).split("\\n")
    ifo_line = [line for line in trigger_file_lines if "ifo:" in line][0]
    sSNR_line = [line for line in trigger_file_lines if "sSNR:" in line][0]
    # Split get the functional part of the ifos line, then split on spaces
    ifos = ifo_line.split(" ")[1].strip().split()
    #  Get the functional part of the snrs line, then split on spaces and convert to floats
    snrs = [float(x) for x in sSNR_line.split(":")[1].strip().split()]
    # Loop to assign SNRs by IFO
    for ii, ifo in enumerate(ifos):
        cbcflow_gevent_dict[f"{ifo}SNR"] = snrs[ii]
    return cbcflow_gevent_dict


def add_singleinspiral_gevent_metadata(gevent_data: dict) -> dict:
    """Fetches information associated with the SingleInspiral table for matched filter searches

    Parameters
    ==========
    gevent_data : dict
        The json output of the query to gracedb for this event's metadata

    Returns
    =======
    dict
        Updates to the cbcflow gevent metadata, for matched filter pipeline info.
        This should satisfy structural requirements of `$defs-Events` in the schema
    """
    cbcflow_gevent_dict = dict()
    for ii, inspiral in enumerate(gevent_data["extra_attributes"]["SingleInspiral"]):
        ifo = inspiral["ifo"]
        snr_key = f"{ifo}SNR"
        cbcflow_gevent_dict[snr_key] = inspiral["snr"]
        if ii == 0:
            cbcflow_gevent_dict["Mass1"] = inspiral["mass1"]
            cbcflow_gevent_dict["Mass2"] = inspiral["mass2"]
            cbcflow_gevent_dict["Spin1z"] = inspiral["spin1z"]
            cbcflow_gevent_dict["Spin2z"] = inspiral["spin2z"]
        else:
            # The SingleInspirals should be the same template
            # If they aren't, that's pretty bad! so we put in
            # impossible placeholders. After discussion with reviewers,
            # we'll leave this in as a safeguard against confusion, but
            # these checks should be handled internally to gracedb already
            if (
                (cbcflow_gevent_dict["Mass1"] != inspiral["mass1"])
                or (cbcflow_gevent_dict["Mass2"] != inspiral["mass2"])
                or (cbcflow_gevent_dict["Spin1z"] != inspiral["spin1z"])
                or (cbcflow_gevent_dict["Spin2z"] != inspiral["spin2z"])
            ):

                logger.warning(
                    "Templates do not match!\
                            Assigning placeholder masses and spins"
                )
                cbcflow_gevent_dict["Mass1"] = -1
                cbcflow_gevent_dict["Mass2"] = -1
                cbcflow_gevent_dict["Spin1z"] = -1
                cbcflow_gevent_dict["Spin2z"] = -1

    return cbcflow_gevent_dict


def add_filelinks_gevent_metadata(links_data: dict, pipeline: str) -> dict:
    """Add metadata of file links to the gevent metadata

    Parameters
    ==========
    links_data : dict
        The data obtained by gdb.files(gid, "").json(), which is a dict of links
    pipeline : str
        Which pipeline to do this process for

    Returns
    =======
    dict
        Updates to the cbcflow gevent metadata, for file links info.
        This should satisfy structural requirements of `$defs-Events` in the schema
    """
    cbcflow_gevent_dict = dict()
    cbcflow_gevent_dict["SourceClassification"] = links_data.get(
        f"{pipeline.lower()}.p_astro.json", None
    )
    if pipeline == "cwb":
        cbcflow_gevent_dict["Skymap"] = links_data.get("cwb.multiorder.fits", None)
    else:
        cbcflow_gevent_dict["Skymap"] = links_data.get("bayestar.multiorder.fits", None)
        cbcflow_gevent_dict["XML"] = links_data.get("coinc.xml", None)

    return cbcflow_gevent_dict


def get_superevent_gevents(
    superevent_data: dict,
) -> Dict[str, dict]:
    """Gets the gevents associated with a superevent.

    Parameters
    ==========
    superevent_data : dict
        The data from a call of gdb.superevent(sname).json()

    Returns
    =======
    dict
        A dictionary of gevent data, with gid as the key.
    """
    # NOTE: This will be one of the big changes once the catalog API is integrated!
    # Also NOTE: this is one of the few semantic changes: making the g-event the key instead of pipeline
    # This requires shifting things around, but is conceptually much clearer (it's an actual unique ID)
    gevents_dict = superevent_data.get("pipeline_preferred_events", dict())
    gevents_dict = {v["graceid"]: v for v in gevents_dict.values()}
    preferred_event = superevent_data["preferred_event_data"]
    if len(gevents_dict) == 0:
        # Sometimes pipeline_preferred_events is not set correctly
        # This defaults to the data
        gevents_dict[preferred_event["graceid"]] = preferred_event

    return gevents_dict


def load_data_file(
    gdb: "ligo.gracedb.rest.GraceDb", gid: str, file_name: str, json: bool = True
) -> dict:
    """Fetch data from a given GraceDB file, with error handling

    Parameters
    ==========
    gdb : ligo.gracedb.rest.GraceDb
        The GraceDB REST API instance to use for queries
    gid : str
        The gid of the relevant event
    file_name : str
        The name of the file to load
    json : bool
        Whether the file can be loaded as a json

    Returns
    =======
    dict
        The contents of the file, or an empty dictionary if there was an HTTPError
    """
    from ligo.gracedb.exceptions import HTTPError

    try:
        if json:
            contents = gdb.files(gid, file_name).json()
        else:
            contents = gdb.files(gid, file_name).read()
        return contents
    except HTTPError:
        return dict()


def get_superevent_file_data(
    gdb: "ligo.gracedb.rest.GraceDb", gevents_data: dict
) -> Dict[str, Dict[str, Union[Dict, str]]]:
    """Load in the contents of various files.

    Parameters
    ==========
    gdb : ligo.gracedb.rest.GraceDb
        The GraceDB REST API instance to use for queries
    gevent_data : dict
        The data about gevents, to inform which files to query

    Returns
    =======
    Dict[str, Dict[str, Dict]]
        A dictionary of gevent:files where
        files is a dictionary of name:data
        and data is a dictionary from the file which was read in (if it was a json)
        and raw string content eitherwise.
    """
    files_dict = dict()
    for gid, data in gevents_data.items():
        pipeline = gevents_data[gid]["pipeline"]
        files_dict[gid] = dict()
        # Passing no file name gives a dictionary of links instead
        files_dict[gid]["links"] = load_data_file(gdb, gid, "")
        files_dict[gid]["pastro_data"] = load_data_file(
            gdb, gid, f"{pipeline.lower()}.p_astro.json"
        )
        if pipeline.lower() == "cwb":
            files_dict[gid]["trigger"] = load_data_file(
                gdb, gid, "trigger.txt", json=False
            )
        else:
            files_dict[gid]["embright_data"] = load_data_file(
                gdb, gid, "em_bright.json"
            )
            files_dict[gid]["pipeline_embright_data"] = load_data_file(
                gdb, gid, f"{pipeline.lower()}.em_bright.json"
            )

    return files_dict


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

    full_update_dict = dict(
        GraceDB=dict(Events=[]), Cosmology=dict(), Info=dict(Notes=[])
    )

    if service_url is None:
        from ..core.configuration import config_defaults

        service_url = config_defaults["gracedb_service_url"]
        logger.info("Using configuration default GraceDB service_url")

    with GraceDb(service_url=service_url, cred=cred) as gdb:
        try:
            # Get the json of metadata for the superevent
            superevent_data = gdb.superevent(sname).json()
        except HTTPError:
            msg = f"Superevent {sname} not found on {service_url}.\n"
            msg += "Either it does not exist, or you may need to run ligo-proxy-init.\n"
            msg += "No updates will be made to this superevent accordingly."
            logger.ERROR(msg)
            return full_update_dict

        gevents_data = get_superevent_gevents(superevent_data)
        file_data = get_superevent_file_data(gdb, gevents_data=gevents_data)

    preferred_event = superevent_data["preferred_event"]

    if "ADVNO" in superevent_data["labels"]:
        # If ADVNO is here that means this event is retracted
        full_update_dict["Info"]["Notes"].append("Retracted: ADVNO applied in GraceDB")

    for gid, gevent_data in gevents_data.items():
        cbcflow_gevent_dict = dict()
        pipeline = gevent_data["pipeline"].lower().strip()
        is_preferred = preferred_event == gid

        # Do some checks to make sure we're only looking at events with valid information
        if pipeline not in ["spiir", "mbta", "gstlal", "pycbc", "cwb"]:
            continue
        elif pipeline == "cwb" and gevent_data["search"].lower() != "bbh":
            continue

        # Add common information for superevent and event
        common_gevent_update, common_sevent_update = add_common_gevent_metadata(
            gevent_data, preferred=is_preferred
        )
        full_update_dict["GraceDB"].update(common_sevent_update)
        cbcflow_gevent_dict.update(common_gevent_update)

        # Other universal info
        cbcflow_gevent_dict.update(
            add_filelinks_gevent_metadata(file_data[gid]["links"], pipeline)
        )
        cbcflow_gevent_dict.update(
            add_pastro_gevent_metadata(file_data[gid]["pastro_data"])
        )

        # Pipeline dependent changes
        if pipeline == "cwb":
            cbcflow_gevent_dict.update(
                add_cwbtrigger_gevent_metadata(file_data[gid]["trigger"])
            )
            cbcflow_gevent_dict["NetworkSNR"] = gevent_data["extra_attributes"][
                "MultiBurst"
            ]["snr"]
        else:
            cbcflow_gevent_dict.update(
                add_embright_gevent_metadata(file_data[gid]["embright_data"])
            )
            cbcflow_gevent_dict.update(
                add_embright_gevent_metadata(
                    file_data[gid]["pipeline_embright_data"], pipeline_embright=True
                )
            )
            cbcflow_gevent_dict.update(add_singleinspiral_gevent_metadata(gevent_data))
            cbcflow_gevent_dict["NetworkSNR"] = gevent_data["extra_attributes"][
                "CoincInspiral"
            ]["snr"]

        if is_preferred and pipeline != "cwb":
            # NOTE: This restriction on cwb is not necessary
            # but I am including it for now to replicate the behavior of the previous function
            # We can easily remove it and get valid (more complete) data
            # Though this only applies when the preferred event is a cwb trigger
            full_update_dict["Cosmology"][
                "PreferredLowLatencySkymap"
            ] = cbcflow_gevent_dict["Skymap"]

        full_update_dict["GraceDB"]["Events"].append(cbcflow_gevent_dict)

    full_update_dict["GraceDB"]["LastUpdate"] = str(datetime.now())

    return full_update_dict


def old_fetch_gracedb_information(
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
        from ..core.configuration import config_defaults

        service_url = config_defaults["gracedb_service_url"]
        logger.info("Using configuration default GraceDB service_url")

    data = dict(GraceDB=dict(Events=[]), Cosmology=dict(), Info=dict(Notes=[]))

    with GraceDb(service_url=service_url, cred=cred) as gdb:
        try:
            # Get the json of metadata for the superevent
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            msg = f"Superevent {sname} not found on {service_url}. "
            msg += "Either it does not exist, or you may need to run ligo-proxy-init."
            raise ValueError(msg)
        # We want the one best event per pipeline
        event_dict = superevent.get("pipeline_preferred_events", dict())
        preferred_event = superevent["preferred_event_data"]
        if "ADVNO" in superevent["labels"]:
            # If ADVNO is here that means this event is retracted
            data["Info"]["Notes"].append("Retracted: ADVNO applied in GraceDB")
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
                        ifos = ifo_line.split(" ")[1].strip().split()
                        # More string hacking to get sSNRs
                        snrs = [
                            float(x) for x in sSNR_line.split(":")[1].strip().split()
                        ]
                        # Loop to assign SNRs by IFO
                        for ii, ifo in enumerate(ifos):
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
