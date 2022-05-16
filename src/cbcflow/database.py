import configparser
import glob
import json
import logging
import os

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData
from .parser import get_parser_and_default_data
from .schema import get_schema

logger = logging.getLogger(__name__)


class GraceDbDatabase(object):
    def __init__(self, service_url):
        self.service_url = service_url
        self.superevents = dict()

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
            a GraceDb query string to query for superevents
            see https://gracedb.ligo.org/documentation/queries.html
        """
        with GraceDb(service_url=self.service_url) as gdb:
            superevent_iterator = gdb.superevents(query)
            for superevent in superevent_iterator:
                self.superevents.update({superevent["superevent_id"]: superevent})
        return self.superevents

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
            for superevent_id, superevent in self.superevents.items():
                database_data = self.pull(superevent_id)
                metadata = MetaData(
                    superevent_id,
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
            for superevent_id, superevent in self.superevents.items():
                metadata = MetaData(
                    superevent_id,
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
        Attempts to sync library and GraceDb, conflict resolution presently favors gracedb

        Parameters:
        ------------
        library
            As in metadata.MetaData
        """
        # setup defaults
        schema = get_schema()
        local_library = LocalLibraryDatabase(library, schema)
        monitor_config = local_library.library_config["Monitor"]

        # annying hack due to gracedb query bug
        import datetime

        now = datetime.datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H-%M-%S")

        # make query and defaults, query
        query = f"created: {monitor_config['created-since']} .. {now_str} \
        FAR <= {monitor_config['far-threshold']}"
        _, default_data = get_parser_and_default_data(schema)
        self.query_superevents(query)

        # for superevents not in the query parameters, but already in the library
        for superevent_id in local_library.metadata_dict.keys():
            if superevent_id not in self.superevents.keys():
                self.query_superevents(superevent_id)

        # loop over all superevents of interest
        for superevent_id, superevent in self.superevents.items():
            gracedb_data = self.pull(superevent["superevent_id"])
            if superevent_id in local_library.metadata_dict.keys():
                # gracedb as source of truth - if in library update
                local_metadata = local_library.metadata_dict[superevent_id]
                local_metadata.update(gracedb_data)
                local_metadata.write_to_library()
            else:
                # if not in library make default
                local_default = MetaData(
                    superevent_id,
                    library,
                    default_data=default_data,
                    schema=schema,
                )
                if gracedb_data == {}:
                    # if not in gracedb use default, write and push
                    local_default.write_to_library()
                    self.push(local_default)
                else:
                    # if in gracedb, use the gracedb data
                    local_default.update(gracedb_data)
                    local_default.write_to_library()


class LocalLibraryDatabase(object):
    def __init__(self, library, schema, default_data=None):
        """A class to handle operations on the local library (git) database

        Parameters
        ----------
        library: str
            A path to the directory containing the metadata files
        """

        self.library = library
        self.metadata_dict = {}

        if default_data is None:
            default_data = {}

        metadata_list = [
            MetaData.from_file(f, schema, default_data) for f in self.filelist
        ]
        for md in metadata_list:
            self.metadata_dict[md.sname] = md

    @property
    def filelist(self):
        return glob.glob(os.path.join(self.library, "*cbc-metadata.json"))

    @property
    def library_config(self):
        config = configparser.ConfigParser()
        config_file = os.path.join(self.library, "library.cfg")
        library_defaults = dict()
        library_defaults["monitor"] = {
            "far-threshold": 1.2675e-7,
            "created-since": "2022-01-01",
        }
        if os.path.exists(config_file):
            config.read(config_file)
            for section_key in config.sections():
                if section_key not in library_defaults.keys():
                    library_defaults[section_key] = dict()
                section = config[section_key]
                for key in section.keys():
                    library_defaults[section_key][key] = section[key]
        return library_defaults
