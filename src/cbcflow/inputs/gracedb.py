"""Methods for interacting with gracedb"""
from datetime import datetime
from typing import Union, Tuple, Optional, Dict, TYPE_CHECKING, List

if TYPE_CHECKING:
    from ligo.gracedb.rest import GraceDb

from ..core.utils import setup_logger

logger = setup_logger(name=__name__)


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
    if gevent_data["offline"]:
        cbcflow_gevent_dict["SearchType"] = "offline"
    else:
        cbcflow_gevent_dict["SearchType"] = "low latency"
    cbcflow_gevent_dict["EarlyWarning"] = "EARLY_WARNING" in gevent_data["labels"]
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
    p_terrestrial = pastro_data.get("Terrestrial", None)
    if p_terrestrial is not None:
        cbcflow_gevent_dict["Pastro"] = 1 - p_terrestrial
    cbcflow_gevent_dict["Pbbh"] = pastro_data.get("BBH", None)
    cbcflow_gevent_dict["Pbns"] = pastro_data.get("BNS", None)
    cbcflow_gevent_dict["Pnsbh"] = pastro_data.get("NSBH", None)
    # Cleanup keys with no value
    cbcflow_gevent_dict = {
        k: v for k, v in cbcflow_gevent_dict.items() if v is not None
    }

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
    try:
        ifo_line = [line for line in trigger_file_lines if "ifo:" in line][0]
        # Split get the functional part of the ifos line, then split on spaces
        ifos = ifo_line.split(":")[1].strip().split()
    except Exception as e:
        ifos = []
        logger.warning(
            f"Attempt to determine ifos from trigger.txt gives exception: {e}"
        )
        logger.warning("This will prevent full use of cwb file contents")
    try:
        sSNR_line = [line for line in trigger_file_lines if "sSNR:" in line][0]
        # Get the functional part of the snrs line, then split on spaces and convert to floats
        snrs = [float(x) for x in sSNR_line.split(":")[1].strip().split()]
        # Loop to assign SNRs by IFO
        for ii, ifo in enumerate(ifos):
            cbcflow_gevent_dict[f"{ifo}SNR"] = snrs[ii]
    except Exception as e:
        logger.warning(
            f"Attempt to determine snrs from trigger.txt gives exception: {e}"
        )
        logger.warning("This will prevent full use of cwb file contents")
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
    if "SingleInspiral" not in gevent_data["extra_attributes"]:
        return cbcflow_gevent_dict
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

    # Cleanup keys with no value
    cbcflow_gevent_dict = {
        k: v for k, v in cbcflow_gevent_dict.items() if v is not None
    }

    return cbcflow_gevent_dict


def add_catalog_gevent_metadata(
    catalog_number: str, catalog_version: int, in_offline_table: bool
):
    """Add catalog specific information to the gevent metadata"""
    cbcflow_gevent_dict = dict()
    if not in_offline_table:
        cbcflow_gevent_dict["InOfflineCatalog"] = False
        return cbcflow_gevent_dict
    cbcflow_gevent_dict["CatalogNumber"] = catalog_number
    cbcflow_gevent_dict["CatalogVersion"] = catalog_version
    cbcflow_gevent_dict["InOfflineCatalog"] = True
    return cbcflow_gevent_dict


def get_superevent_online_gevents(
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
    gevents_dict = superevent_data.get("pipeline_preferred_events", dict())
    gevents_dict = {v["graceid"]: v for v in gevents_dict.values()}
    preferred_event = superevent_data["preferred_event_data"]
    if len(gevents_dict) == 0:
        # Sometimes pipeline_preferred_events is not set correctly
        # This defaults to the data
        gevents_dict[preferred_event["graceid"]] = preferred_event

    return gevents_dict


def get_superevent_gwtc_gevents(
    gdb: "ligo.gracedb.rest.GraceDb", gevent_ids: List[str]
) -> Dict[str, dict]:
    """Gets the gevents associated with a superevent.

    Parameters
    ==========
    gdb : "ligo.gracedb.rest.GraceDb"
        An instance of the rest API, with gwtc functionality
    gevent_ids : List[str]
        The list of g-event ids to query

    Returns
    =======
    dict
        A dictionary of gevent data, with gid as the key.
    """
    gevents_dict = dict()

    for gevent_id in gevent_ids:
        gevents_dict[gevent_id] = gdb.event(gevent_id).json()

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
    catalog_mode: bool = False,
    catalog_number: Optional[str] = "4",
    catalog_version: Optional[int] = None,
    gevent_ids: List[str] = None,
    catalog_superevent_far: float = None,
    catalog_superevent_pastro: float = None,
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
    catalog_mode : bool = False
        Whether to get events from the catalog gracedb interface, or the online interface
    catalog_number : Optional[int] = 4
        The number of the catalog - defaults to 4 for GWTC-4
    catalog_version : Optional[int]
        The version of the catalog table from which data was queried.
        Note that even if it was queried as "latest" it should report the table version.
    gevent_ids : List[str]
        A list of the event ids which are relevant for a given superevent, when in catalog operation
    catalog_superevent_far : float
        The FAR associated with this superevent in the catalog table, if available
    catalog_superevent_pastro : float
        The probability of being of astrophysical origin associated with this superevent,
        as recorded in the catalog table, if available

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
        logger.info("Using default (production) GraceDB service_url")
        service_url = "https://gracedb.ligo.org/api/"

    with GraceDb(service_url=service_url, cred=cred) as gdb:
        try:
            # Get the json of metadata for the superevent
            superevent_data = gdb.superevent(sname).json()

            # TODO we only need preferred event from this, otherwise offload all querying to get_superevent_gevents
        except HTTPError:
            msg = f"Superevent {sname} not found on {service_url}.\n"
            msg += "Either it does not exist, or you may need to run ligo-proxy-init.\n"
            msg += "No updates will be made to this superevent accordingly."
            logger.error(msg)
            return full_update_dict

        preferred_event = superevent_data["preferred_event"]

        if not catalog_mode:
            gevents_data = get_superevent_online_gevents(superevent_data)
        else:
            gevents_data = get_superevent_gwtc_gevents(gdb=gdb, gevent_ids=gevent_ids)

        if catalog_mode and preferred_event not in gevents_data.keys():
            gevents_data[preferred_event] = gdb.event(preferred_event).json()

        file_data = get_superevent_file_data(gdb, gevents_data=gevents_data)

    full_update_dict["GraceDB"]["ADVOK"] = "ADVNO" not in superevent_data["labels"]

    # Add high level superevent catalog info
    if catalog_mode:
        if catalog_superevent_far is not None:
            full_update_dict["GraceDB"]["SupereventFAR"] = catalog_superevent_far
        if catalog_superevent_pastro is not None and catalog_superevent_pastro != {}:
            full_update_dict["GraceDB"]["SupereventPastro"] = (
                1 - catalog_superevent_pastro["Terrestrial"]
            )

    for gid, gevent_data in gevents_data.items():
        cbcflow_gevent_dict = dict()
        pipeline = gevent_data["pipeline"].lower().strip()
        is_preferred = preferred_event == gid

        # Do some checks to make sure we're only looking at events with valid information
        if pipeline not in ["spiir", "mbta", "gstlal", "pycbc", "cwb"]:
            continue
        elif pipeline == "cwb" and gevent_data["search"].lower() not in [
            "allsky",
            "bbh",
        ]:
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

        # Catalog specific additions:
        if catalog_mode:
            cbcflow_gevent_dict.update(
                add_catalog_gevent_metadata(
                    catalog_number, catalog_version, (gid in gevent_ids)
                )
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
            if "Skymap" in cbcflow_gevent_dict.keys():
                full_update_dict["Cosmology"][
                    "PreferredLowLatencySkymap"
                ] = cbcflow_gevent_dict["Skymap"]

        full_update_dict["GraceDB"]["Events"].append(cbcflow_gevent_dict)

    full_update_dict["GraceDB"]["LastUpdate"] = str(datetime.now())

    return full_update_dict
