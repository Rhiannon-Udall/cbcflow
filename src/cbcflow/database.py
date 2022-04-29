import json
import logging

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData
from .parser import get_parser_and_default_data
from .schema import get_schema

logger = logging.getLogger(__name__)


class GraceDbDatabase(object):
    def __init__(self, service_url):
        self.service_url = service_url

    def pull(self, sname):
        fname = MetaData.get_filename(sname)
        try:
            with GraceDb(service_url=self.service_url) as gdb:
                return json.loads(gdb.files(sname, fname).data)
        except HTTPError:
            logger.info(
                f"No metadata stored on GraceDb ({self.service_url}) for {sname}"
            )
            return {}

    def push(self, metadata):
        logger.info(
            f"Pushing changes for {metadata.sname} to Gracedb ({self.service_url})"
        )
        message = "Updating cbc-meta"
        with GraceDb(service_url=self.service_url) as gdb:
            gdb.writeLog(
                object_id=metadata.sname,
                message=message,
                filename=metadata.library_file,
            )

    def query_superevents(self, query):
        with GraceDb(service_url=self.service_url) as gdb:
            superevent_iterator = gdb.superevents(query)
            self.superevents = [superevent for superevent in superevent_iterator]

    def pull_updates_gracedb(self, library, no_git_library=False):
        if hasattr(self, "superevents"):
            schema = get_schema()
            _, default_data = get_parser_and_default_data(schema)
            for superevent in self.superevents:
                database_data = self.pull(superevent["superevent_id"])
                metadata = MetaData(
                    superevent["superevent_id"],
                    library,
                    default_data=default_data,
                    schema=schema,
                    no_git_library=no_git_library,
                )
                metadata.data.update(database_data)
                metadata.write_to_library()
        else:
            logger.info(
                "This GraceDbDatabase instance has not queried for superevents yet,\
                 please do so before attempting to pull them."
            )
