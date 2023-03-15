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
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            raise ValueError(f"Superevent {sname} not found on {service_url}")
        for gname in superevent["events"]:
            try:
                event = gdb.event(gname).json()
                event_data = dict()
                if gname == superevent["preferred_event"]:
                    data["GraceDB"]["Instruments"] = event["instruments"]
                    event_data["State"] = "preferred"
                else:
                    event_data["State"] = "neighbor"
                event_data["UID"] = gname
                event_data["Pipeline"] = event["pipeline"]
                # @Dimitri this grabs all labels - should we target one in particular?
                event_data["Label"] = str(event["labels"])
                event_data["GPSTime"] = event["gpstime"]
                event_data["FAR"] = event["far"]
                event_data["NetworkSNR"] = event["extra_attributes"]["CoincInspiral"][
                    "snr"
                ]
                for inspiral in event["extra_attributes"]["SingleInspiral"]:
                    ifo = inspiral["ifo"]
                    snr_key = f"{ifo}SNR"
                    event_data[snr_key] = inspiral["snr"]
                event_data["Mass1"] = inspiral["mass1"]
                event_data["Mass2"] = inspiral["mass2"]
                event_data["Spin1z"] = inspiral["spin1z"]
                event_data["Spin2z"] = inspiral["spin2z"]
                # More eventwise stuff should go here

            except HTTPError:
                raise ValueError(f"Event {sname} not found on {service_url}")

    data["GraceDB"]["LastUpdate"] = str(datetime.now())

    # data = dict(
    #     GraceDB=dict(
    #         PreferredEvent=superevent["preferred_event"],
    #         FAR=event["far"],
    #         GPSTime=event["gpstime"],
    #         Instruments=event["instruments"],
    #         LastUpdate=str(datetime.now()),
    #     )
    # )
    return data
