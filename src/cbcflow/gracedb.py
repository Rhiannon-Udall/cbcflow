import logging
from datetime import datetime

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

logger = logging.getLogger(__name__)


def fetch_gracedb_information(sname, service_url):
    logger.info(f"Using GraceDB service_url: {service_url}")
    with GraceDb(service_url=service_url) as gdb:
        try:
            superevent = gdb.superevent(sname).json()
        except HTTPError:
            raise ValueError("Superevent {sname} not found on {service_url}")
        try:
            gname = superevent["preferred_event"]
            event = gdb.event(gname).json()
        except HTTPError:
            raise ValueError("Event {sname} not found on {service_url}")

    data = dict(
        gracedb=dict(
            preferred_event=superevent["preferred_event"],
            far=event["far"],
            gpstime=event["gpstime"],
            instruments=event["instruments"],
            last_update=str(datetime.now()),
        )
    )
    return data