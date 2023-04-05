import configparser
import copy
import glob
import json
import logging
import os
from functools import cached_property
import sys
from pprint import pformat
from typing import Union, Dict

import dateutil.parser as dp
from jsondiff import diff
import jsonschema
import pygit2
from ligo.gracedb.rest import GraceDb
from ligo.gracedb.exceptions import HTTPError
from gwpy.time import to_gps

from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import get_all_schema_def_defaults, get_simple_schema_defaults
from .schema import get_schema
from .gracedb import fetch_gracedb_information
from .utils import get_dumpable_json_diff

logger = logging.getLogger(__name__)


class LocalLibraryDatabase(object):
    def __init__(
        self,
        library_path: str,
        schema: Union[dict, None] = None,
        default_data: Union[dict, None] = None,
    ):
        """A class to handle operations on the local library (git) database

        Parameters
        ==========
        library: str
            A path to the directory containing the metadata files
        """

        self.library = library_path
        self.metadata_schema = schema

        self.metadata_dict = dict()

        logger.debug(
            f"Library initialized with {len(self.filelist)} superevents stored"
        )

    ############################################################################
    ############################################################################
    ####                     Metadata and Configuration                     ####
    ############################################################################
    ############################################################################

    @property
    def library_parent(self) -> "LibraryParent":
        """The parent to this library"""
        return self._library_parent

    def initialize_parent(self, source_path=None):
        """Get the LibraryParent object which will act as parent to this library

        Parameters
        ==========
        source_path
            The path (GraceDB url, git url, or filesystem path) to the parent source
        """
        if source_path is None:
            source_path = self.library_config["Monitor"]["parent"]
            logger.info(
                f"Initializing parent from configuration, with source path {source_path}"
            )
        if "https://gracedb" in source_path:
            self._library_parent = GraceDbDatabase(
                service_url=source_path, library=self
            )
        elif os.path.exists(source_path):
            # This will be the branch for pulling from a git repo in the local filesystem
            pass
        elif "https" in source_path:
            # This will be the branch for pulling from a non-local git repo on e.g. gitlab
            pass
        else:
            raise ValueError(
                f"Could not obtain source information from path {source_path}"
            )

    @property
    def filelist(self):
        """The list of cbc metadata jsons in this library"""
        return glob.glob(os.path.join(self.library, "*cbc-metadata.json"))

    @property
    def superevents_in_library(self):
        """Get a list of superevent names which are present in the library"""
        superevent_names = [x.split("/")[-1].split("-")[0] for x in self.filelist]
        return superevent_names

    @property
    def metadata_schema(self) -> dict:
        """The schema for the metadata jsons in this library"""
        return self._metadata_schema

    @metadata_schema.setter
    def metadata_schema(self, schema: Union[dict, None] = None):
        if schema is None:
            self._metadata_schema = get_schema()
        else:
            self._metadata_schema = schema

    @cached_property
    def metadata_default_data(self) -> dict:
        """The default data for a metadata object with this library's schema"""
        _, default_data = get_parser_and_default_data(self.metadata_schema)
        return default_data

    @property
    def metadata_dict(self) -> dict:
        """A dictionary of the metadata loaded for a library"""
        return self._metadata_dict

    @metadata_dict.setter
    def metadata_dict(self, new_dict) -> None:
        self._metadata_dict = new_dict

    def load_library_metadata_dict(self) -> None:
        """Load all of the metadata in a given library"""
        metadata_dict = dict()
        metadata_list = [
            MetaData.from_file(
                f, self.metadata_schema, self.metadata_default_data, local_library=self
            )
            for f in self.filelist
        ]
        for md in metadata_list:
            metadata_dict[md.sname] = md
        self.metadata_dict.update(metadata_dict)

    @property
    def downselected_metadata_dict(self) -> Dict[str, MetaData]:
        """Get the snames of events which satisfy library inclusion criteria"""
        downselected_metadata_dict = dict()
        self.load_library_metadata_dict()
        for sname, metadata in self.metadata_dict.items():
            library_created_earliest = to_gps(
                self.library_config["Events"]["created-since"]
            )
            library_created_latest = to_gps(
                self.library_config["Events"]["created-before"]
            )
            for event in metadata.data["GraceDB"]["Events"]:
                if event["State"] == "preferred":
                    preferred_far = event["FAR"]
                    preferred_time = to_gps(event["GPSTime"])
            if sname in self.library_config["Events"]["snames-to-include"]:
                downselected_metadata_dict[sname] = metadata
            elif sname in self.library_config["Events"]["snames-to-exclude"]:
                pass
            elif (
                preferred_time < library_created_earliest
                or preferred_time > library_created_latest
            ):
                continue
            # Right now we *only* check date, FAR threshold, and specific inclusion
            elif preferred_far <= float(self.library_config["Events"]["far-threshold"]):
                downselected_metadata_dict[sname] = metadata
        return downselected_metadata_dict

    def validate(self, data):
        try:
            jsonschema.validate(data, self.metadata_schema)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(e.message)
        except jsonschema.SchemaError as e:
            raise jsonschema.SchemaError(e.message)

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
            "created-before": "now",
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

    ############################################################################
    ############################################################################
    ####                Git Related Functions and Properties                ####
    ############################################################################
    ############################################################################

    @property
    def is_git_repository(self) -> bool:
        """Whether this library is a git repository"""
        return os.path.exists(os.path.join(self.library, ".git"))

    def _initialize_library_git_repo(self):
        """Initialize the pygit repository object for this library"""
        if not self.is_git_repository:
            raise ValueError(
                f"The library directory {self.library} is not a repository,\
                so you can't initialize pygit information for it."
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
    def git_parents(self):
        """The parents (in the git sense) for the repository"""
        if hasattr(self, "repo"):
            return [self.repo.head.target]
        else:
            try:
                self._initialize_library_git_repo()
            except ValueError:
                raise AttributeError(
                    "Cannot get git parents for this repo, since it is not a git repo!"
                )

    def git_add_and_commit(
        self, filename, message: Union[str, None] = None, sname: Union[str, None] = None
    ):
        """
        Perform the git operations add and commit

        Parameters
        ==========
        filename : str
            The path to the file to commit
        message : str, optional
            If passed, this message will be used in the git commit, rather than the default.
        sname : str, optional
            The sname of the metadata, if a metadata file is what is being committed.
            Used for generating a default commit message.
        """
        if not hasattr(self, "repo"):
            # If necessary, initialize git information for this library
            self._initialize_library_git_repo()

        # Add the file to the index
        self.repo.index.add(filename)
        self.repo.index.write()
        author = self._author_signature
        if message is None:
            # If no message is given, make a default
            if sname is not None:
                # The case where the file being committed is a metadata file
                if sname in self.metadata_dict:
                    # If we are updating an extant bit of metadata
                    metadata = self.metadata_dict[sname]
                    message = f"Changes made to [{metadata.toplevel_diff}]\n"
                else:
                    # If we are creating a new metadata file
                    message = f"Committing metadata for new superevent {sname}"
            message += f"cmd line: {' '.join(sys.argv)}"
        # Write the index to the working tree
        tree = self.repo.index.write_tree()
        # Commit the tree
        self.repo.create_commit(
            self.ref, author, author, message, tree, self.git_parents
        )

    @cached_property
    def _author_signature(self):
        gitconfig = os.path.expanduser("~/.gitconfig")
        config = configparser.ConfigParser()
        config.sections()
        config.read(gitconfig)
        name = config["user"]["name"]
        email = config["user"]["email"]
        return pygit2.Signature(name, email)

    ############################################################################
    ############################################################################
    ####               Index Related Functions and Properties               ####
    ############################################################################
    ############################################################################

    @property
    def index_file_name(self) -> str:
        """The name of the index file, given the library name"""
        library_name = self.library_config["Library Info"]["library-name"]
        index_file_name = f"{library_name}-index.json"
        return index_file_name

    @property
    def index_file_path(self) -> str:
        """The file path to the library's index json"""
        index_file = os.path.join(self.library, self.index_file_name)
        return index_file

    @property
    def library_index_schema(self):
        """The schema being used for this library's index"""
        return get_schema(index_schema=True, args=["--schema-version", "v1"])

    @cached_property
    def index_from_file(self) -> dict:
        """Fetch the info from the index json as it currently exists"""
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, "r") as f:
                    current_index_data = json.load(f)
                jsonschema.validate(current_index_data, self.library_index_schema)
                return current_index_data
            except jsonschema.ValidationError:
                logger.warning("Present index data failed validation!")
                return dict()
        else:
            logger.info("No index file currently present")
            return dict()

    @cached_property
    def generated_index(self) -> dict:
        """The index generated to reflect the current state of the library

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
            superevent_meta["LastUpdated"] = metadata.get_date_last_modified()
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
        index_diff = diff(self.index_from_file, self.generated_index)
        if index_diff != {}:
            logger.info("Index data has changed since it was last written")
            string_rep_diff = get_dumpable_json_diff(index_diff)
            logger.info(json.dumps(string_rep_diff, indent=2))
        return index_diff

    def write_index_file(self):
        """Writes the new index to the library"""
        index_delta = self.check_for_index_update()
        if index_delta != dict():
            with open(self.index_file_path, "w") as f:
                json.dump(self.generated_index, f, indent=2)
            if self.is_git_repository:
                self.git_add_and_commit(
                    filename=self.index_file_name,
                    message=f"Updating index with changes:\n\
                        {pformat(get_dumpable_json_diff(index_delta))}",
                )


class LibraryParent(object):
    def __init__(self, source_path: str, library: LocalLibraryDatabase) -> None:
        """Setup a LibraryParent object

        Parameters
        ==========
        source_path : str
            A path to the parent's source.
            This can be a GraceDB service URL, a git repo url,
            or the path to a git repo on the shared filesystem.
        """
        self.source_path = source_path
        self.superevents_to_propagate = dict()
        self.library = library
        logger.info(
            f"Parent of library {self.library} initialized with source path {self.source_path}"
        )

    def pull(self, sname: str) -> dict():
        """A method for pulling superevent metadata from this parent source.
        Child classes should overwrite this method.

        Parameters
        ==========
        sname : str
            The superevent sname

        Returns
        =======
        dict
            A dict containing pulled information about the superevent
        """
        return dict()

    @property
    def superevents_to_propagate(self) -> list:
        """Superevents which should be propagated from this parent"""
        return self._superevents_to_propagate

    @superevents_to_propagate.setter
    def superevents_to_propagate(self, new_superevents: list) -> None:
        if not hasattr(self, "_superevents_to_propagage"):
            self._superevents_to_propagate = list()
        self._superevents_to_propagate += new_superevents

    def query_superevents(self, query: str) -> list:
        """A method for fetching new superevents according to some query
        This should be overwritten by child classes

        Parameters
        ==========
        query : str
            A query for a collection of superevents (which may be empty or have only one element)

        Returns
        =======
        list
            The collection of superevents (represented by their sname) satisfying the query
        """
        return list()

    def pull_library_updates(self) -> None:
        """Propagates metadata in superevents_to_propagate into the library.
        Should be overwritten by the child class.
        """
        return None

    def sync_library(self) -> None:
        """A method for syncing the library, using the query specified in the library config.
        This should be overwritten by the child class."""
        return None


class GraceDbDatabase(LibraryParent):
    def __init__(self, service_url: str, library: LocalLibraryDatabase) -> None:
        """Setup the GraceDbDatabase that this library pairs to

        Parameters
        ==========
        service_url : str
            The http address for the gracedb instance that this library pairs to
        """
        super(GraceDbDatabase, self).__init__(source_path=service_url, library=library)

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
        return fetch_gracedb_information(sname, service_url=self.source_path)

    def query_superevents(self, query: str) -> list:
        """Queries superevents in GraceDb, according to a given query

        Parameters
        ==========
        query : str
            a GraceDb query string to query for superevents
            see https://gracedb.ligo.org/documentation/queries.html

        Returns
        =======
        list
            The superevents which satisfy the query
        """
        queried_superevents = []
        with GraceDb(service_url=self.source_path) as gdb:
            superevent_iterator = gdb.superevents(query)
            for superevent in superevent_iterator:
                queried_superevents.append(superevent["superevent_id"])
        return queried_superevents

    def pull_library_updates(self) -> None:
        """Pulls updates from GraceDb and writes them to library, creates default data as required"""
        if hasattr(self, "superevents_to_propagate"):
            for superevent_id in self.superevents_to_propagate:
                if superevent_id in self.library.metadata_dict.keys():
                    metadata = self.library.metadata_dict[superevent_id]
                else:
                    metadata = MetaData(
                        superevent_id,
                        local_library=self.library,
                        schema=self.library.metadata_schema,
                        default_data=self.library.metadata_default_data,
                    )
                try:
                    backup_data = copy.deepcopy(metadata.data)
                    database_data = self.pull(superevent_id)
                    metadata.update(database_data)
                    changes = metadata.get_diff()
                    if "GraceDB" in changes.keys() and len(changes.keys()) == 1:
                        if len(changes["GraceDB"].keys()) == 1:
                            continue
                        # This is a hack to make it not update if the only update would be "LastUpdate"
                        # It may have to change in further schema versions
                    logger.info(f"Updates to supervent {superevent_id}")
                    string_rep_changes = get_dumpable_json_diff(changes)
                    logger.info(json.dumps(string_rep_changes, indent=2))
                    metadata.write_to_library()
                except jsonschema.exceptions.ValidationError:
                    logger.warning(
                        f"For superevent {superevent_id}, GraceDB generated metadata failed validation\
                        Writing backup data (either default or pre-loaded) to library instead\n"
                    )
                    metadata.update(backup_data)
                    metadata.write_to_library()
                except HTTPError:
                    logger.warning(
                        f"For superevent {superevent_id}, failed to obtain data from GraceDB\
                        Writing backup data (either default or pre-loaded) to library instead\n"
                    )
                    metadata.update(backup_data)
                    metadata.write_to_library()
        else:
            logger.info(
                "This GraceDbDatabase instance has not assigned any superevents to propagate yet\
                 please do so before attempting to pull them."
            )

    def sync_library(self) -> None:
        """Attempts to sync library and GraceDb,
        pulling any new events and changes to GraceDB data.

        Parameters:
        ===========
        library
            As in metadata.MetaData

        """
        # setup defaults
        # monitor_config = local_library.library_config["Monitor"]
        event_config = self.library.library_config["Events"]

        # annying hack due to gracedb query bug
        import datetime

        if event_config["created-before"] == "now":
            now = datetime.datetime.utcnow()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            now_str = event_config["created-before"]

        logging.info(f"Syncing with GraceDB at time UTC:{now_str}")
        # make query and defaults, query
        query = f"created: {event_config['created-since']} .. {now_str} \
        FAR <= {event_config['far-threshold']}"
        logger.info(f"Constructed query {query} from library config")
        try:
            self.superevents_to_propagate = self.query_superevents(query)
        except HTTPError:
            self.superevents_to_propagate = []
            logger.warning(
                "Query to GraceDB for superevents unsuccessful \
                           - falling back on superevents already in library only"
            )

        logger.info(
            f"Querying based on library configuration returned {len(self.superevents_to_propagate)} superevents"
        )
        # for superevents not in the query parameters, but already in the library
        for superevent_id in self.library.metadata_dict.keys():
            if superevent_id not in self.superevents_to_propagate:
                self.superevents_to_propagate.append(superevent_id)
                logging.info(
                    f"Also querying superevent {superevent_id} which was in the library\
                \n but which did not meet query parameters"
                )

        self.pull_library_updates()
