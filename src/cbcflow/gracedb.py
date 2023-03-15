import logging
from datetime import datetime
from typing import Union

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

logger = logging.getLogger(__name__)


def fetch_gracedb_information(sname: str, service_url: Union[str, None] = None):
    """Get the standard GraceDB metadata contents for this superevent

    Parameters
    ==========
    sname : str
        The sname of the superevent to fetch.
    service_url : Union[str, None], optional
        The url for the GraceDB instance to access.
        If None is passed then this will use the configuration default.

    Returns
    =======
    dict
        An update dictionary to apply to the metadata, containing the GraceDB info.
    """
    if service_url is None:
        from .configuration import config_defaults

        service_url = config_defaults["gracedb_service_url"]
        logger.info("Using configuration default GraceDB service_url")
    logger.info(f"Using GraceDB service_url: {service_url}")

    data = dict(GraceDB=dict(Events=[]))

    with GraceDb(service_url=service_url) as gdb:
        try:
            # Get the json of metadata for the superevent
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            raise ValueError(f"Superevent {sname} not found on {service_url}")
        # We want the one best event per pipeline
        for pipeline, event in superevent["pipeline_preferred_events"].items():
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
            for label in event["Labels"]:
                if "GWTC" in label:
                    event_data["Label"] = label
            event_data["GPSTime"] = event["gpstime"]
            event_data["FAR"] = event["far"]
            event_data["NetworkSNR"] = event["extra_attributes"]["CoincInspiral"]["snr"]
            for ii, inspiral in event["extra_attributes"]["SingleInspiral"]:
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
                    pastro_data = gdb.files(gname, f"{pipeline}.p_astro.json").json()

                    event_data["Pastro"] = 1 - pastro_data["Terrestrial"]
                    event_data["Pbbh"] = pastro_data["BBH"]
                    event_data["Pbns"] = pastro_data["BNS"]
                    event_data["Pnsbh"] = pastro_data["NSBH"]
                except HTTPError:
                    logger.warning(
                        f"Was not able to get source classification for G-event {gname}"
                    )

                try:
                    # Some pipelines will provide source classification, others will no
                    embright_data = gdb.files(gname, "em_bright.json").json()
                    for key in embright_data:
                        if key == "HasNS":
                            event_data["HasNS"] = embright_data[key]
                        elif key == "HasRemnant":
                            event_data["HasRemnant"] = embright_data[key]
                        elif key == "HasMassGap":
                            event_data["HasMassGap"] = embright_data[key]
                except HTTPError:
                    logger.info(f"No em bright provided for G-event {gname}")

                try:
                    # All pipelines should provide these 3 files
                    file_links = gdb.files(gname, "").json()

                    event_data["XML"] = file_links["coinc.xml"]
                    event_data["SourceClassification"] = file_links[
                        f"{pipeline}.p_astro.json"
                    ]
                    event_data["Skymap"] = file_links["bayestar.multiorder.fits"]
                except HTTPError:
                    logger.warning(f"Could not fetch file links for G-event {gname}")

                # Add the final event data to the array
                data["GraceDB"]["Events"].append(event_data)

    data["GraceDB"]["LastUpdate"] = str(datetime.now())

    return data
