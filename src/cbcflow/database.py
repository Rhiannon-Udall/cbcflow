import configparser
import copy
import glob
import json
import logging
import os
from functools import cached_property

import dateutil.parser as dp
import jsondiff
import jsonschema
import pygit2
from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import get_all_schema_def_defaults, get_simple_schema_defaults
from .schema import get_schema

logger = logging.getLogger(__name__)

# from .process import populate_defaults_if_necessary


class GraceDbDatabase(object):
    def __init__(self, service_url):
        """Setup the GraceDbDatabase that this library pairs to

        Parameters
        ==========
        service_url : str
            The http address for the gracedb instance that this library pairs to
        """
        self.service_url = service_url
        logger.info(f"Using GraceDB service_url: {service_url}")
        self.superevents = dict()

    def pull(self, sname):
        """Pull information on the superevent with this sname from GraceDB

        Parameters
        ==========
        sname : str
            The sname for the superevent in question
        """
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
        """Push the newly update metadata to GraceDB - deprecated by changes in backend infrastructure

        Parameters
        ==========
        metadata : cbcflow.metadata.MetaData
            The metadata object to push back to GraceDB
        """
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
        """Queries superevents in GraceDb, according to a given query

        Parameters
        ==========
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
        """Pulls updates from GraceDb and writes them to library, creates default data as required

        Parameters:
        ===========
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

    def push_updates_gracedb(self, library):
        """Pushes contents of the library to GraceDb

        Parameters
        ==========
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
        """Attempts to sync library and GraceDb, conflict resolution presently favors gracedb

        Parameters:
        ===========
        library
            As in metadata.MetaData
        """
        # setup defaults
        schema = get_schema()
        local_library = LocalLibraryDatabase(library, schema)
        # monitor_config = local_library.library_config["Monitor"]
        event_config = local_library.library_config["Events"]

        # annying hack due to gracedb query bug
        import datetime

        now = datetime.datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        logging.info(f"Syncing with GraceDB at time {now_str}")
        # make query and defaults, query
        query = f"created: {event_config['created-since']} .. {now_str} \
        FAR <= {event_config['far-threshold']}"
        logger.info(f"Constructed query {query} from library config")
        _, default_data = get_parser_and_default_data(schema)
        self.query_superevents(query)
        from pprint import pformat

        logger.info("Querying based on library configuration returned superevents:")
        logger.info(pformat(self.query_superevents))
        # for superevents not in the query parameters, but already in the library
        for superevent_id in local_library.metadata_dict.keys():
            if superevent_id not in self.superevents.keys():
                self.query_superevents(superevent_id)
                logging.info(
                    f"Also querying superevent {superevent_id} which was in the library\
                \n but which did not meet query parameters"
                )

        # loop over all superevents of interest
        for superevent_id, superevent in self.superevents.items():
            gracedb_data = self.pull(superevent["superevent_id"])
            if superevent_id not in self.superevents.items():
                # if not in library make default
                local_default = MetaData(
                    superevent_id,
                    local_library=local_library,
                    default_data=default_data,
                    schema=schema,
                )
                if gracedb_data == {}:
                    # if not in gracedb use default, write and push
                    local_default.write_to_library()
                    self.push(local_default)
                    logger.info(
                        f"The superevent {superevent_id} had no data in the library or gracedb,\
                    \n and so defaults were generated and added to both repositories."
                    )
                else:
                    try:
                        backup_default = copy.deepcopy(local_default)
                        # if in gracedb, use the gracedb data
                        local_default.update(gracedb_data)
                        local_default.write_to_library()
                        logger.info(
                            f"The superevent {superevent_id} was present in gracedb but not in the library,\
                            \n and so was added to the library using gracedb data"
                        )
                    except jsonschema.exceptions.ValidationError:
                        logger.info(
                            f"For superevent {superevent_id}, metadata was present in gracedb, but failed validation\n\
                            Writing default data to library instead\n\
                            If important information from GraceDB must be added, do so manually\n"
                        )
                        backup_default.write_to_library()


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
        return self.repo.head.target

    def read_index_file(self):
        """Fetch the info from the index json as it currently exists"""
        if os.path.exists(self.index_file_path):
            current_index_data = json.load(self.index_file_path)
            return current_index_data
        else:
            logger.info("No index file currently present")

    def generate_index_from_library(self):
        """Generate the index reflecting the current state of the library"""
        current_most_recent = "2015-09-14 09:50:45"
        new_index = get_simple_schema_defaults(self.library_index_schema)
        superevent_default = get_all_schema_def_defaults(self.library_index_schema)[
            "Superevents"
        ]
        for sname, metadata in self.downselected_metadata_dict.items():
            superevent_meta = copy.deepcopy(superevent_default)
            superevent_meta["Sname"] = sname
            superevent_meta["LastUpdated"] = metadata.get_date_of_last_commit()
            new_index["Superevents"].append(superevent_meta)
            if dp.parse(superevent_meta["LastUpdated"]) > dp.parse(current_most_recent):
                current_most_recent = superevent_meta["LastUpdated"]
        new_index["LibraryStatus"]["LastUpdated"] = current_most_recent
        return new_index

    def check_for_index_update(self):
        """Check if the index file will see any changes"""
        read_file_data = self.read_index_file()
        generate_data = self.generate_index_from_library()
        diff = jsondiff.diff(read_file_data, generate_data)
        if diff != {}:
            logger.info("Index data has changed since it was last written")
            logger.info(json.dump(diff, indent=2))
        return diff

    def write_index_file(self):
        """Writes the new index to the"""
        new_index_data = self.generate_index_from_library()
        with open(self.index_file_path, "w") as f:
            json.dump(new_index_data, f, indent=2)

    @cached_property
    def downselected_metadata_dict(self):
        """Get the snames of events which satisfy library inclusion criteria"""
        downselected_metadata_dict = dict()
        for sname, metadata in self.metadata_dict:
            if sname in self.library_config["snames-to-include"]:
                self.downselected_metadata_dict[sname] = metadata
            elif sname in self.library_config["snames-to-exclude"]:
                pass
            # TODO prepare for how this will work with the all-sky schema changes
            # This will include:
            # 1. adapting to G-eventwise values
            # 2. adding p-astro
            # 3. possibly adding p_nsbh, p_bns, b_bbh
            # 4. possibly adding SNR
            elif metadata["GraceDB"]["FAR"] <= self.library_config["far-threshold"]:
                self.downselected_metadata_dict[sname] = metadata
        return downselected_metadata_dict
