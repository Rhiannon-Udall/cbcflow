import configparser
import copy
import glob
import json
import logging
import os
from functools import cached_property

import dateutil.parser as dp
from jsondiff import replace, diff
import jsonschema
import pygit2
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import get_all_schema_def_defaults, get_simple_schema_defaults
from .schema import get_schema
from .gracedb import fetch_gracedb_information
from .utils import get_dumpable_json_diff

logger = logging.getLogger(__name__)

# from .process import populate_defaults_if_necessary


class LocalLibraryDatabase(object):
    def __init__(
        self,
        library_path: str,
        schema: dict | None = None,
        default_data: dict | None = None,
    ):
        """A class to handle operations on the local library (git) database

        Parameters
        ==========
        library: str
            A path to the directory containing the metadata files
        """

        self.library = library_path
        self.metadata_dict = {}

        self.metadata_schema = schema
        if default_data is None:
            _, default_data = get_parser_and_default_data(self.metadata_schema)

        metadata_list = [
            MetaData.from_file(
                f, self.metadata_schema, default_data, local_library=self
            )
            for f in self.filelist
        ]
        for md in metadata_list:
            self.metadata_dict[md.sname] = md

    @property
    def filelist(self):
        """The list of cbc metadata jsons in this library"""
        return glob.glob(os.path.join(self.library, "*cbc-metadata.json"))

    @property
    def metadata_schema(self) -> dict:
        """The schema for the metadata jsons in this library"""
        return self._metadata_schema

    @metadata_schema.setter
    def metadata_schema(self, schema: dict | None = None):
        if schema is None:
            self._metadata_schema = get_schema()
        else:
            self._metadata_schema = schema

    def validate(self, data):
        jsonschema.validate(data, self.metadata_schema)

    @cached_property
    def _author_signature(self):
        gitconfig = os.path.expanduser("~/.gitconfig")
        config = configparser.ConfigParser()
        config.sections()
        config.read(gitconfig)
        name = config["user"]["name"]
        email = config["user"]["email"]
        return pygit2.Signature(name, email)

    @cached_property
    def library_config(self):
        """The configuration information for this library"""
        config = configparser.ConfigParser()
        config_file = os.path.join(self.library, "library.cfg")
        library_defaults = dict()
        library_defaults["Library Info"] = {"library-name": "CBC-Library"}
        library_defaults["Events"] = {
            "far-threshold": 1.2675e-7,
            "pastro-threshold": 0.5,
            "created-since": "2022-01-01",
            "snames-to-include": [],
            "snames-to-exclude": [],
        }
        library_defaults["Monitor"] = {"parent": "gracedb"}
        if os.path.exists(config_file):
            config.read(config_file)
            for section_key in config.sections():
                if section_key not in library_defaults.keys():
                    library_defaults[section_key] = dict()
                section = config[section_key]
                for key in section.keys():
                    library_defaults[section_key][key] = section[key]
        return library_defaults

    @property
    def index_file_path(self):
        """The file path to the library's index json"""
        library_name = self.library_config["Library Info"]["library-name"]
        index_file = os.path.join(self.library, f"{library_name}-index.json")
        return index_file

    @property
    def library_index_schema(self):
        """The schema being used for this library's index"""
        return get_schema(index_schema=True)

    def _initialize_library_git_repo(self):
        """Initialize the pygit repository object for this library"""
        if os.path.exists(os.path.join(self.library, ".git")) is False:
            raise ValueError(
                f"The library directory {self.library} is not a repository"
            )

        self.repo = pygit2.init_repository(self.library)

        try:
            self.ref = self.repo.head.name
        except pygit2.GitError:
            # If the git repo is empty
            raise ValueError(
                f"The git library directory {self.library} is empty ."
                "Please initialise with a commit"
            )

    @property
    def parents(self):
        return [self.repo.head.target]

    def read_index_file(self):
        """Fetch the info from the index json as it currently exists"""
        if os.path.exists(self.index_file_path):
            current_index_data = json.load(self.index_file_path)
            return current_index_data
        else:
            logger.info("No index file currently present")

    def generate_index_from_library(self):
        """Generate the index reflecting the current state of the library

        Returns
        =======
        dict:
            The new index contents, based on the contents of the library
        """
        # We need a starting date, and GW150914 seems appropriate
        current_most_recent = "2015-09-14 00:00:00"
        # Get a basic index
        new_index = get_simple_schema_defaults(self.library_index_schema)
        # Get the generic template for a Superevent index object
        superevent_default = get_all_schema_def_defaults(self.library_index_schema)[
            "Superevents"
        ]
        # Loop over all superevents included in the downselected library
        for sname, metadata in self.downselected_metadata_dict.items():
            # Fill out basic info
            superevent_meta = copy.deepcopy(superevent_default)
            superevent_meta["Sname"] = sname
            superevent_meta["LastUpdated"] = metadata.get_date_of_last_commit()
            new_index["Superevents"].append(superevent_meta)
            # Get the datetime of the most recent change
            if dp.parse(superevent_meta["LastUpdated"]) > dp.parse(current_most_recent):
                current_most_recent = superevent_meta["LastUpdated"]
        # Sort by Sname for readability
        new_index["Superevents"].sort(key=lambda x: x["Sname"])
        # Set the most recent change as the time of the library's most recent change
        new_index["LibraryStatus"]["LastUpdated"] = current_most_recent
        return new_index

    def check_for_index_update(self) -> dict:
        """Check if the index file will see any changes

        Returns
        =======
        dict
            The output of jsondiff between the current index file
            and the index generated presently
        """
        read_file_data = self.read_index_file()
        generate_data = self.generate_index_from_library()
        index_diff = diff(read_file_data, generate_data)
        if index_diff != {}:
            logger.info("Index data has changed since it was last written")
            string_rep_diff = get_dumpable_json_diff(index_diff)
            logger.info(json.dumps(string_rep_diff, indent=2))
        return index_diff

    def write_index_file(self):
        """Writes the new index to the library"""
        new_index_data = self.generate_index_from_library()
        with open(self.index_file_path, "w") as f:
            json.dump(new_index_data, f, indent=2)

    @cached_property
    def downselected_metadata_dict(self):
        """Get the snames of events which satisfy library inclusion criteria"""
        downselected_metadata_dict = dict()
        for sname, metadata in self.metadata_dict.items():
            if sname in self.library_config["Events"]["snames-to-include"]:
                downselected_metadata_dict[sname] = metadata
            elif sname in self.library_config["Events"]["snames-to-exclude"]:
                pass
            # TODO prepare for how this will work with the all-sky schema changes
            # This will include:
            # 1. adapting to G-eventwise values
            # 2. adding p-astro
            # 3. possibly adding p_nsbh, p_bns, b_bbh
            # 4. possibly adding SNR
            elif metadata.data["GraceDB"]["FAR"] <= float(
                self.library_config["Events"]["far-threshold"]
            ):
                downselected_metadata_dict[sname] = metadata
        return downselected_metadata_dict


class GraceDbDatabase(object):
    def __init__(self, service_url):
        """Setup the GraceDbDatabase that this library pairs to

        Parameters
        ==========
        service_url : str
            The http address for the gracedb instance that this library pairs to
        """
        self.service_url = service_url
        self.queried_superevents = dict()
        logger.info(f"Using GraceDB service_url: {service_url}")

    def pull(self, sname: str) -> dict:
        """Pull information on the superevent with this sname from GraceDB

        Parameters
        ==========
        sname : str
            The sname for the superevent in question

        Returns
        =======
        dict
            The GraceDB data for the superevent
        """
        return fetch_gracedb_information(sname, service_url=self.service_url)

    @property
    def queried_superevents(self) -> dict:
        """Superevents which have been queried from GraceDB by this object"""
        return self._queried_superevents

    @queried_superevents.setter
    def queried_superevents(self, newly_queried_superevents: dict) -> None:
        if not hasattr(self, "_queried_superevents"):
            self._queried_superevents = dict()
        self._queried_superevents.update(newly_queried_superevents)

    def query_superevents(self, query: str):
        """Queries superevents in GraceDb, according to a given query

        Parameters
        ==========
        query
            a GraceDb query string to query for superevents
            see https://gracedb.ligo.org/documentation/queries.html

        Returns
        =======
        self.queried_superevents
            The queried_superevents attribute updated with these queries.
            This is also modified in place.
        """
        with GraceDb(service_url=self.service_url) as gdb:
            superevent_iterator = gdb.superevents(query)
            for superevent in superevent_iterator:
                self.queried_superevents.update(
                    {superevent["superevent_id"]: superevent}
                )
        return self.queried_superevents

    def pull_updates_gracedb(
        self, library: LocalLibraryDatabase, no_git_library: bool = False
    ):
        """Pulls updates from GraceDb and writes them to library, creates default data as required

        Parameters:
        ===========
        library
            As in metadata.MetaData
        no_git_library
            As in metadata.MetaData
        """
        if hasattr(self, "queried_superevents"):
            schema = get_schema()
            _, default_data = get_parser_and_default_data(schema)
            for superevent_id, superevent in self.queried_superevents.items():
                database_data = self.pull(superevent_id)
                metadata = MetaData(
                    superevent_id,
                    local_library=library,
                    default_data=default_data,
                    schema=schema,
                    no_git_library=no_git_library,
                )
                metadata.update(database_data)
                try:
                    metadata.write_to_library()
                except jsonschema.exceptions.ValidationError:
                    logger.info(
                        "GraceDB metadata cannot be validated.\
                        Local metadata will not be updated\n"
                    )

        else:
            logger.info(
                "This GraceDbDatabase instance has not queried for superevents yet,\
                 please do so before attempting to pull them."
            )

    def sync_library_gracedb(
        self, local_library: LocalLibraryDatabase = None, local_library_path=None
    ):
        """Attempts to sync library and GraceDb,
        pulling any new events and changes to GraceDB data.

        Parameters:
        ===========
        library
            As in metadata.MetaData

        """
        # setup defaults
        schema = get_schema()
        if local_library is None:
            assert (
                local_library_path is not None
            ), "Must specify library object or path to library"
            local_library = LocalLibraryDatabase(local_library_path, schema)
        # monitor_config = local_library.library_config["Monitor"]
        event_config = local_library.library_config["Events"]

        # annying hack due to gracedb query bug
        import datetime

        now = datetime.datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        logging.info(f"Syncing with GraceDB at time UTC:{now_str}")
        # make query and defaults, query
        query = f"created: {event_config['created-since']} .. {now_str} \
        FAR <= {event_config['far-threshold']}"
        logger.info(f"Constructed query {query} from library config")
        _, default_data = get_parser_and_default_data(schema)
        self.query_superevents(query)

        logger.info(
            f"Querying based on library configuration returned {len(self.queried_superevents)} superevents"
        )
        # for superevents not in the query parameters, but already in the library
        for superevent_id in local_library.metadata_dict.keys():
            if superevent_id not in self.queried_superevents.keys():
                self.query_superevents(superevent_id)
                logging.info(
                    f"Also querying superevent {superevent_id} which was in the library\
                \n but which did not meet query parameters"
                )

        # loop over all superevents of interest
        for superevent_id, superevent in self.queried_superevents.items():
            gracedb_data = self.pull(superevent["superevent_id"])
            if superevent_id in local_library.metadata_dict.keys():
                local_data = local_library.metadata_dict[superevent_id]
            else:
                # if not in library make default
                logger.info(
                    f"Superevent {superevent_id} appeared in the GraceDB query,\n\
                            but was not present in the library, so defaults are being generated."
                )
                local_data = MetaData(
                    superevent_id,
                    local_library=local_library,
                    default_data=default_data,
                    schema=schema,
                )
            try:
                backup_data = copy.deepcopy(local_data.data)
                # if in gracedb, use the gracedb data
                local_data.update(gracedb_data)
                changes = local_data.get_diff()
                if replace in changes:
                    # This is a hack to make it not update if the only update would be "LastUpdate"
                    # It may have to change in further schema versions
                    logger.info(f"Updates to supervent {superevent_id}")
                    string_rep_changes = get_dumpable_json_diff(changes)
                    logger.info(json.dumps(string_rep_changes, indent=2))
                    local_data.write_to_library()
            except jsonschema.exceptions.ValidationError:
                logger.info(
                    f"For superevent {superevent_id}, GraceDB generated metadata failed validation\
                    Writing backup data (either default or pre-loaded) to library instead\n"
                )
                local_data.update(backup_data)
                local_data.write_to_library
