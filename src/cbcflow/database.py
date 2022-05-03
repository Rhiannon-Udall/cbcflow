import copy
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
        """
        Queries superevents in GraceDb, according to a given query

        Parameters
        ------------
        query
            a GraceDb query string to query for superevents with
            see https://gracedb.ligo.org/documentation/queries.html
        """
        with GraceDb(service_url=self.service_url) as gdb:
            superevent_iterator = gdb.superevents(query)
            self.superevents = [superevent for superevent in superevent_iterator]

    def pull_updates_gracedb(self, library, no_git_library=False):
        """
        Pulls updates from GraceDb and writes them to library, creates default data as required

        Parameters:
        ------------
        library
            As in metadata.MetaData
        no_git_library
            As in metadata.MetaData
        """
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

    def push_updates_gracedb(self, library):
        """
        Pushes contents of the library to GraceDb

        Parameters
        ------------
        library
            As in metadata.MetaData
        """
        if hasattr(self, "superevents"):
            schema = get_schema()
            _, default_data = get_parser_and_default_data(schema)
            for superevent in self.superevents:
                metadata = MetaData(
                    superevent["superevent_id"],
                    library,
                    default_data=default_data,
                    schema=schema,
                )
                metadata.load_from_library()
                self.push(metadata)
        else:
            logger.info(
                "This GraceDbDatabase instance has not queried for superevents yet,\
                 please do so before attempting to push them."
            )

    def sync_library_gracedb(self, library):
        """
        Attempts to sync library and GraceDb, conflict resolution presently favors library

        Parameters:
        ------------
        library
            As in metadata.MetaData
        """
        if hasattr(self, "superevents"):
            schema = get_schema()
            _, default_data = get_parser_and_default_data(schema)
            for superevent in self.superevents:
                local_metadata_original = MetaData(
                    superevent["superevent_id"],
                    library,
                    default_data=default_data,
                    schema=schema,
                )
                gracedb_data_original = self.pull(superevent["superevent_id"])
                gracedb_data_update = copy.deepcopy(gracedb_data_original)
                local_metadata_update = copy.deepcopy(local_metadata_original)

                local_metadata_update.data.update(gracedb_data_original)
                gracedb_data_update.update(local_metadata_original.data)

                # 4 cases are considered
                # case 1 - GraceDb has no metadata
                # then push from library, creating default if necessary
                # case 2 - GraceDb has metadata but the library does not
                # then create defaults and update them with GraceDb metadata
                # case 3 - Both GraceDb and the library have metadata, and they agree
                # then do nothing
                # case 4 - GraceDb and the library have metadata, and they disagree
                # then push the library's metadata to GraceDb
                if gracedb_data_update != gracedb_data_original:
                    # GraceDb has been changed, implying case 1 or 4
                    self.push(local_metadata_original)
                elif local_metadata_update.data != local_metadata_original.data:
                    # GraceDb hasn't changed but the local has, implying case 2
                    local_metadata_update.write_to_library()
                else:
                    # neither has been changed, implying case 3
                    pass

        else:
            logger.info(
                "This GraceDbDatabase instance has not queried for superevents yet,\
                 please do so before attempting to sync."
            )
