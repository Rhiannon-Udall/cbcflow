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
    with GraceDb(service_url=service_url) as gdb:
        try:
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            raise ValueError(f"Superevent {sname} not found on {service_url}")
        try:
            gname = superevent["preferred_event"]
            event = gdb.event(gname).json()
        except HTTPError:
            raise ValueError(f"Event {sname} not found on {service_url}")

    data = dict(
        GraceDB=dict(
            PreferredEvent=superevent["preferred_event"],
            FAR=event["far"],
            GPSTime=event["gpstime"],
            Instruments=event["instruments"],
            LastUpdate=str(datetime.now()),
        )
    )
    return data
