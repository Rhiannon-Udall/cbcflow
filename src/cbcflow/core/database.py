"""Class objects for databases, and for providing supplemental database behavior"""
import configparser
import copy
import glob
import json
import os
import ast
from functools import cached_property
import sys
from pprint import pformat
from typing import Union, Dict, Type, TypeVar, Tuple, Optional, List, TYPE_CHECKING
from datetime import datetime

import dateutil.parser as dp
from jsondiff import diff
import fastjsonschema
import git
import tqdm

from .metadata import MetaData
from .metadata import logger as metadata_logger
from .parser import get_parser_and_default_data
from .process import (
    get_all_schema_def_defaults,
    get_simple_schema_defaults,
    process_update_json,
    process_merge_json,
)
from .schema import get_schema
from ..inputs.gracedb import fetch_gracedb_information
from ..inputs.pe_scraper import add_pe_information
from .utils import get_dumpable_json_diff, setup_logger, reset_root_handlers

logger = setup_logger(name=__name__)


class Labeller(object):
    """A generic parent class for labellers,
    which apply labels to the index entry
    for events based on the contents of the metadata"""

    def __init__(self, library: "LocalLibraryDatabase") -> None:
        """Setup the labeller

        Parameters
        ==========
        library : `LocalLibraryDatabase`
            A library object to access for index and metadata
        """
        self.library = library

    def label_event(self, event_metadata: "MetaData") -> list:
        """Generate index labels given an event's metadata.
        This is the workhorse of the labeller, and should be redefined by child classes

        Parameters
        ==========
        event_metadata : `cbcflow.metadata.MetaData`
            The metadata for a given event, to generate labels with

        Returns
        =======
        list
            The list of labels from the event metadata
        """
        return list()

    def populate_working_index_with_labels(self) -> None:
        """Loop over all events in the index, and apply labels to them based on their metadata"""
        for superevent in self.library.working_index["Superevents"]:
            sname = superevent["UID"]
            labels = self.label_event(self.library.metadata_dict[sname])
            superevent["Labels"] = labels


LabellerType = TypeVar("LabellerType", bound=Labeller)


class StandardLabeller(Labeller):
    """The default labeller. NOTE this is presently considered an example of barebones usage only!
    For ongoing development, please write an analogous Labeller, within the library's git CI."""

    def __init__(self, library: "LocalLibraryDatabase") -> None:
        """Setup the labeller

        Parameters
        ==========
        library : `LocalLibraryDatabase`
            A library object to access for index and metadata
        """
        super(StandardLabeller, self).__init__(library)

    def label_event(self, event_metadata: "MetaData") -> list:
        """Generate standard CBC library labels for this event

        Parameters
        ==========
        event_metadata : `cbcflow.metadata.MetaData`
            The metadata for a given event, to generate labels with

        Returns
        =======
        list
            The list of labels from the event metadata
        """
        # Get preferred event
        preferred_event = None
        for event in event_metadata.data["GraceDB"]["Events"]:
            if event["State"] == "preferred":
                preferred_event = event

        labels = []
        if preferred_event:
            # Add PE significance labels
            pe_high_significance_threshold = 1e-30
            pe_medium_significance_threshold = 1e-10
            if preferred_event["FAR"] < pe_high_significance_threshold:
                labels.append("PE::high-significance")

            elif preferred_event["FAR"] < pe_medium_significance_threshold:
                labels.append("PE::medium-significance")
            else:
                labels.append("PE::below-threshold")

            # Add PE status labels
            status = event_metadata.data["ParameterEstimation"]["Status"]
            labels.append(f"PE-status::{status}")

        return labels


class LibraryParent(object):
    """A generic parent class for LibraryParent objects"""

    def __init__(self, source_path: str, library: "LocalLibraryDatabase") -> None:
        """Setup a LibraryParent object

        Parameters
        ==========
        source_path : str
            A path to the parent's source.
            This can be a GraceDB service URL, a git repo url,
            or the path to a git repo on the shared filesystem.
        library : `LocalLibraryDatabase`
            The library for which this is serving as a parent
        """
        self.source_path = source_path
        self.superevents_to_propagate = list()
        self.library = library
        logger.info(
            f"Parent of library {self.library} initialized with source path {self.source_path}"
        )

    def pull(self, sname: str) -> dict:
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

    def pull_library_updates(self, branch_name: Union[str, None] = None) -> None:
        """Propagates metadata in superevents_to_propagate into the library.
        Should be overwritten by the child class.

        Parameters
        ==========
        branch_name : str | None, optional
            The branch_name to write commits to, per `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`
        """
        return None

    def sync_library(self, branch_name: Union[str, None] = None) -> None:
        """A method for syncing the library, using the query specified in the library config.
        This should be overwritten by the child class.

        Parameters
        ==========
        branch_name : str | None, optional
            The branch_name to write commits to, per `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`"""
        return None


class GraceDbDatabase(LibraryParent):
    """The LibraryParent class to use when the parent is GraceDB"""

    def __init__(
        self,
        service_url: str,
        library: "LocalLibraryDatabase",
        cred: Union[Tuple[str, str], str, None] = None,
        pe_rota_token_path: Union[str, None] = None,
    ) -> None:
        """Setup the GraceDbDatabase that this library pairs to

        Parameters
        ==========
        service_url : str
            The http address for the gracedb instance that this library pairs to
        library : `LocalLibraryDatabase`
            The library for which this serves as a parent.
        cred : Union[Tuple[str, str], str, None]
            The credentials to pass when accessing gracedb
        pe_rota_token_path : str
            The path to the token to use when accessing the PE rota
        """
        super(GraceDbDatabase, self).__init__(source_path=service_url, library=library)
        self.cred = cred
        self.pe_rota_token = pe_rota_token_path

        # Do the setup of the standard query from the library config here
        self.event_config = self.library.library_config["Events"]

        # annying hack due to gracedb query bug
        import datetime
        from gwpy.time import to_gps

        start_gps = to_gps(self.event_config["earliest-library-datetime"])
        # to_gps understands 'now'
        end_gps = to_gps(self.event_config["latest-library-datetime"])

        now = datetime.datetime.utcnow()

        logger.info(f"Syncing with GraceDB at {now}")
        # make query and defaults, query
        self.library_query = f"gpstime: {start_gps} .. {end_gps} \
        FAR <= {self.event_config['far-threshold']}"
        logger.info(f"Constructed query {self.library_query} from library config")

    @property
    def cred(self) -> Union[Tuple[str, str], str, None]:
        """Information on the credentials to pass to GraceDb, per
        https://ligo-gracedb.readthedocs.io/en/latest/api.html#ligo.gracedb.rest.GraceDb
        """
        return self._cred

    @cred.setter
    def cred(self, input_cred: Union[Tuple[str, str], str, None]) -> None:
        self._cred = input_cred

    @property
    def pe_rota_token(self) -> Union[None, str]:
        """The token used to access the pe rota gitlab api"""
        return self._pe_rota_token

    @pe_rota_token.setter
    def pe_rota_token(self, path_name: str) -> None:
        if path_name is not None:
            with open(path_name, "r") as file:
                self._pe_rota_token = file.read().strip()
        else:
            self._pe_rota_token = None

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
        try:
            return fetch_gracedb_information(
                sname, service_url=self.source_path, cred=self.cred
            )
        except Exception:
            logger.warning(
                f"Failed with exception {Exception} to fetch gracedb information for {sname},\
                no update will be performed"
            )
            return None

    def query_superevents(self, query: Optional[str] = None) -> list:
        """Queries superevents in GraceDb, according to a given query

        Parameters
        ==========
        query : str
            a GraceDb query string to query for superevents
            see https://gracedb.ligo.org/documentation/queries.html.
            Defaults to the query constructed from the library config.

        Returns
        =======
        list
            The superevents which satisfy the query
        """
        from ligo.gracedb.rest import GraceDb

        if query is None:
            query = self.library_query

        queried_superevents = []
        with GraceDb(service_url=self.source_path, cred=self.cred) as gdb:
            superevent_iterator = gdb.superevents(query)
            for superevent in superevent_iterator:
                queried_superevents.append(superevent["superevent_id"])

        reset_root_handlers()

        return queried_superevents

    def pull_library_updates(self, branch_name: Union[str, None] = None) -> None:
        """Pulls updates from GraceDb and writes them to library, creates default data as required

        Parameters
        ==========
        branch_name : str, optional
            The name of the branch to write to, as passed to `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`
        """
        from ligo.gracedb.exceptions import HTTPError

        if not hasattr(self, "superevents_to_propagate"):
            logger.info(
                "This GraceDbDatabase instance has not assigned any superevents to propagate yet\
                 please do so before attempting to pull them."
            )
            return None
        for superevent_id in tqdm.tqdm(self.superevents_to_propagate):
            logger.info(f"Updating superevent {superevent_id}")
            if superevent_id in self.library.metadata_dict.keys():
                metadata = self.library.metadata_dict[superevent_id]
            else:
                metadata = MetaData(
                    superevent_id,
                    local_library=self.library,
                    schema=self.library.metadata_schema,
                    default_data=self.library.metadata_default_data,
                )
                assert (
                    len(self.library.metadata_default_data["Info"]["Notes"]) == 0
                ), "Something has gone horribly wrong and modified the defaults"
            updated_metadata = copy.deepcopy(metadata)

            # Note - we will *always* clear the g-events from an event before
            # starting the update loop, even though it's only strictly necessary
            # in catalog operations. This saves a lot of code duplication.
            # If something fails in the update loop then
            # The metadata won't be updated in total, so this should be safe
            # (the failure mode would be if Gracedb 'successfully' returned 0 events
            # In which case the issue would be something upstream)
            updated_metadata["GraceDB"]["Events"] = []

            # Pull information from GraceDB
            gdb_data = self.pull(superevent_id)
            for note in metadata["Info"]["Notes"]:
                # If a note already marks this as retracted don't add another
                if "retracted" in note.lower() and "Info" in gdb_data:
                    gdb_data.pop("Info")
                    break
            if gdb_data is not None:
                try:
                    updated_metadata.update(gdb_data)
                    metadata = updated_metadata
                except fastjsonschema.JsonSchemaValueException:
                    logger.warning(
                        f"For superevent {superevent_id}, GraceDB generated metadata failed validation\n\
                        No GraceDB information will be updated\n"
                    )

            try:
                # Pull information from PE
                add_pe_information(updated_metadata, superevent_id, self.pe_rota_token)
                metadata = updated_metadata
            except Exception as e:
                logger.warning(
                    f"Fatal error while scraping PE automatically for superevent {superevent_id}"
                )
                logger.warning("No PE information will be updated")
                logger.warning(f"The exception was {e}")

            changes = metadata.get_diff()
            if "GraceDB" in changes.keys() and len(changes.keys()) == 1:
                # This is a hack to make it not update if the only update would be "LastUpdate"
                # It may have to change in further schema versions
                if len(changes["GraceDB"].keys()) == 1:
                    continue

            logger.info(f"Updates to supervent {superevent_id}")
            string_rep_changes = get_dumpable_json_diff(changes)
            logger.info(json.dumps(string_rep_changes, indent=2))
            metadata.write_to_library(branch_name=branch_name)

    def sync_library(self, branch_name: Union[str, None] = None) -> None:
        """Attempts to sync library and GraceDb,
        pulling any new events and changes to GraceDB data.

        Parameters
        ==========
        branch_name : str | None, optional
            The branch_name to write commits to, per `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`
        """
        from ligo.gracedb.exceptions import HTTPError

        try:
            self.superevents_to_propagate = self.query_superevents(
                query=self.library_query
            )

            # TODO self.superevents_to_propogate should now include only catalog superevents satsifying the query
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
                logger.info(
                    f"Also querying superevent {superevent_id} which was in the library\
                \n but which did not meet query parameters"
                )

        # For special events which are called out by name, act accordingly
        specially_included_snames = ast.literal_eval(
            self.library.library_config["Events"]["snames-to-include"]
        )
        specially_excuded_snames = ast.literal_eval(
            self.library.library_config["Events"]["snames-to-exclude"]
        )

        self.superevents_to_propagate += specially_included_snames
        self.superevents_to_propagate = list(
            set(self.superevents_to_propagate) - set(specially_excuded_snames)
        )

        self.pull_library_updates(branch_name=branch_name)


class CatalogGraceDbDatabase(GraceDbDatabase):
    def __init__(
        self,
        service_url: str,
        library: "LocalLibraryDatabase",
        cred: Tuple[str, str] | str | None = None,
        pe_rota_token_path: str | None = None,
    ) -> None:
        super().__init__(service_url, library, cred, pe_rota_token_path)
        self.catalog_number = library.library_config["Catalog"]["number"]
        self.catalog_query_version = library.library_config["Catalog"]["version"]

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
        try:
            return fetch_gracedb_information(
                sname,
                service_url=self.source_path,
                cred=self.cred,
                catalog_mode=True,
                catalog_number=self.catalog_number,
                catalog_version=self.catalog_table_version,
                gevent_ids=[
                    x for x in self.catalog_superevents[sname]["pipelines"].values()
                ],
                catalog_superevent_far=self.catalog_superevents[sname]["far"],
                catalog_superevent_pastro=self.catalog_superevents[sname]["pastro"],
            )
        except Exception as exception:
            logger.warning(
                f"Failed with exception:\n\
                {exception}\n\
                to fetch gracedb information for {sname},\
                no update will be performed"
            )
            return None

    @property
    def catalog_superevents(self) -> Dict[str, List[str]]:
        """A map of superevents to catalog gevents for superevents which are in the catalog"""
        return self._catalog_superevents

    @catalog_superevents.setter
    def catalog_superevents(self, catalog_superevents: Dict[str, List[str]]) -> None:
        self._catalog_superevents = catalog_superevents

    @property
    def catalog_query_version(self) -> Union[str, int]:
        """The version of the catalog table to query - either a number or "latest" """
        return self._catalog_query_version

    @catalog_query_version.setter
    def catalog_query_version(self, catalog_query_version: Union[str, int]):
        self._catalog_query_version = catalog_query_version

    @property
    def catalog_table_version(self) -> int:
        """The version of the gwtc catalog table which was obtained from the query."""
        return self._catalog_table_version

    @catalog_table_version.setter
    def catalog_table_version(self, catalog_table_version: int):
        self._catalog_table_version = catalog_table_version

    def query_superevents(self, query: Optional[str] = None) -> list:
        """Query for superevents in the catalog

        Parameters
        ==========
        query : Optional[str]
            This parameter is included for API compatibililty, but is ignored for Catalog operations
        """
        from ligo.gracedb.rest import GraceDb

        if query is None:
            query = self.library_query

        # standard query structure: "gpstime: {start_gps} .. {end_gps} \
        # FAR <= {self.event_config['far-threshold']}"
        # so split() then take 2 indexes further
        far_threshold = float(query.split()[query.split().index("FAR") + 2])

        with GraceDb(service_url=self.source_path, cred=self.cred) as gdb:
            gwtc_table = gdb.gwtc_get(
                number=self.catalog_number, version=self.catalog_query_version
            ).json()
            catalog_superevents_map = gwtc_table["gwtc_superevents"]
            catalog_superevents = {
                k: v
                for k, v in catalog_superevents_map.items()
                if v.get("far", 1) is not None and v.get("far", 1) <= far_threshold
            }
            self.catalog_table_version = gwtc_table["version"]

        reset_root_handlers()

        self.catalog_superevents = catalog_superevents
        return [k for k in catalog_superevents.keys()]


class LocalLibraryDatabase(object):
    """An object reflecting the contents of a local library, and offering methods to interact with it"""

    def __init__(
        self,
        library_path: str,
        schema: Union[dict, None] = None,
        default_data: Union[dict, None] = None,
    ) -> None:
        """A class to handle operations on the local library (git) database

        Parameters
        ==========
        library: str
            A path to the directory containing the metadata files
        """

        self.library = library_path
        self.metadata_schema = schema
        self.validator = fastjsonschema.compile(copy.deepcopy(self.metadata_schema))
        self.index_validator = fastjsonschema.compile(
            copy.deepcopy(self.library_index_schema)
        )

        self.metadata_dict = dict()
        self.working_index = dict()
        self.remote_has_merge_conflict = False

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

    def initialize_parent(self, source_path=None) -> None:
        """Get the LibraryParent object which will act as parent to this library

        Parameters
        ==========
        source_path
            The path (GraceDB url, git url, or filesystem path) to the parent source
        """
        if source_path is None:
            source_path = self.library_config["Monitor"]["gracedb-service-url"]
            logger.debug(
                f"Initializing parent from configuration, with source path {source_path}"
            )
        if "https://gracedb" in source_path:
            if self.library_config["Monitor"]["cred"] is not None:
                import re

                if self.library_config["Monitor"]["cred"].lower() == "none":
                    # If it's just the string None
                    logger.debug("Using default credentials")
                    cred = None
                elif re.match(r"\(.,.\)", self.library_config["Monitor"]["cred"]):
                    import ast

                    logger.debug("Using cred/key pair given")
                    cred = ast.literal_eval(self.library_config["Monitor"]["cred"])
                else:
                    logger.debug("Using path to credential proxy file")
                    cred = self.library_config["Monitor"]["cred"]
            else:
                logger.debug("Using default credentials")
                cred = None
            if self.library_config["Monitor"]["pe_rota_token"] is not None:
                if self.library_config["Monitor"]["pe_rota_token"].lower() != "none":
                    pe_rota_token_path = self.library_config["Monitor"]["pe_rota_token"]
                else:
                    pe_rota_token_path = None
            else:
                pe_rota_token_path = None
            if self.library_config["Monitor"]["parent"] == "gracedb":
                self._library_parent = GraceDbDatabase(
                    service_url=source_path,
                    library=self,
                    cred=cred,
                    pe_rota_token_path=pe_rota_token_path,
                )
            elif self.library_config["Monitor"]["parent"] == "gwtc-gracedb":
                self._library_parent = CatalogGraceDbDatabase(
                    service_url=source_path,
                    library=self,
                    cred=cred,
                    pe_rota_token_path=pe_rota_token_path,
                )
            else:
                raise ValueError(
                    f"{self.library_config['Monitor']['parent']} is not a valid parent"
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
        return self._library_parent

    @property
    def filelist(self) -> list:
        """The list of cbc metadata jsons in this library"""
        return glob.glob(os.path.join(self.library, "*cbc-metadata.json"))

    @property
    def superevents_in_library(self) -> list:
        """Get a list of superevent names which are present in the library"""
        superevent_names = [x.split("/")[-1].split("-")[0] for x in self.filelist]
        return superevent_names

    @property
    def metadata_schema(self) -> dict:
        """The schema for the metadata jsons in this library"""
        return self._metadata_schema

    @metadata_schema.setter
    def metadata_schema(self, schema: Union[dict, None] = None) -> None:
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

    @cached_property
    def downselected_metadata_keys(self) -> Dict[str, MetaData]:
        """The keys of the downselected metadata
        stored to allow updating metadata without recomputing inclusion"""
        from gwpy.time import to_gps

        self._downselected_metadata_has_been_computed = True

        downselected_metadata_keys = list()
        if self.metadata_dict.keys() != self.superevents_in_library:
            self.load_library_metadata_dict()
        for sname, metadata in self.metadata_dict.items():
            earliest_library_datetime = to_gps(
                self.library_config["Events"]["earliest-library-datetime"]
            )
            latest_library_datetime = to_gps(
                self.library_config["Events"]["latest-library-datetime"]
            )
            preferred_far = 1
            preferred_time = 0
            for event in metadata.data["GraceDB"]["Events"]:
                if event["State"] == "preferred":
                    preferred_far = event["FAR"]
                    preferred_time = to_gps(event["GPSTime"])
            if preferred_far == 1 or preferred_time == 0:
                logger.warning(
                    f"No preferred event was identified for superevent {sname}: something is seriously wrong!\n\
                        Accordingly, this event will not be included in downselected_metadata_dict"
                )
                continue
            if sname in self.library_config["Events"]["snames-to-include"]:
                downselected_metadata_keys.append(sname)
            elif sname in self.library_config["Events"]["snames-to-exclude"]:
                pass
            elif (
                preferred_time < earliest_library_datetime
                or preferred_time > latest_library_datetime
            ):
                continue
            # Right now we *only* check date, FAR threshold, and specific inclusion
            elif preferred_far <= float(self.library_config["Events"]["far-threshold"]):
                downselected_metadata_keys.append(sname)
        return downselected_metadata_keys

    @property
    def downselected_metadata_dict(self) -> dict:
        """The metadata of events that satisfy library inclusion criteria, labelled by sname"""
        if not hasattr(self, "downselected_metadata_keys"):
            self.downselected_metadata_keys
        return {
            sname: metadata
            for sname, metadata in self.metadata_dict.items()
            if sname in self.downselected_metadata_keys
        }

    def validate(self, data) -> None:
        """Check that data satisfies the metadata schema

        Parameters
        ==========
        data : dict
            The data to validate
        """

        try:
            self.validator(data, self.metadata_schema)
        except fastjsonschema.JsonSchemaValueException as e:
            raise fastjsonschema.JsonSchemaValueException(e.message)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise fastjsonschema.JsonSchemaDefinitionException(e.message)

    @cached_property
    def library_config(self) -> dict:
        """The configuration information for this library"""
        config = configparser.ConfigParser()
        config_file = os.path.join(self.library, "library.cfg")
        library_defaults = dict()
        library_defaults["Library Info"] = {"library-name": "CBC-Library"}
        library_defaults["Events"] = {
            "far-threshold": 1.2675e-7,
            "earliest-library-datetime": "2022-01-01",
            "latest-library-datetime": "now",
            "snames-to-include": [],
            "snames-to-exclude": [],
        }
        library_defaults["Monitor"] = {
            "parent": "gracedb",
            "gracedb-service-url": "https://gracedb.ligo.org/api/",
            "cred": None,
            "pe_rota_token": None,
        }
        library_defaults["Catalog"] = {"number": "4", "version": "latest"}
        if os.path.exists(config_file):
            config.read(config_file)
            for section_key in config.sections():
                if section_key not in library_defaults.keys():
                    library_defaults[section_key] = dict()
                section = config[section_key]
                if (
                    "created-since" in section.keys()
                    and "earliest-library-datetime" not in section.keys()
                ):
                    # NOTE: this will be deprecated in time, but for now allow backwards compatibility with
                    # older library configuration files
                    section["earliest-library-datetime"] = section["created-since"]
                if (
                    "created-before" in section.keys()
                    and "latest-library-datetime" not in section.keys()
                ):
                    # As above
                    section["latest-library-datetime"] = section["created-before"]
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

    def _initialize_library_git_repo(self) -> None:
        """Initialize the pygit repository object for this library"""
        if not self.is_git_repository:
            raise ValueError(
                f"The library directory {self.library} is not a repository,\
                so you can't initialize pygit information for it."
            )

        self.repo = git.Repo(self.library)

    def git_add_and_commit(
        self,
        filename,
        message: Union[str, None] = None,
        sname: Union[str, None] = None,
        branch_name: Union[str, None] = None,
    ) -> None:
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
        branch_name: str, optional
            The name of the branch to which the commit will be written:
            If not passed, then:
                - If the current branch is main, a new branch name will be formulaically generated
                - If the current branch is not main, then the current branch will be used
            If passed as "main", then the main branch will be written to explicitly
            If passed as a string other than main, then that branch will be created if necessary, and checked out.
        """
        if not hasattr(self, "repo"):
            # If necessary, initialize git information for this library
            self._initialize_library_git_repo()

        if message is None:
            # If no message is given, make a default
            if sname is not None:
                # The case where the file being committed is a metadata file
                if sname in self.metadata_dict:
                    # If we are updating an extant bit of metadata
                    metadata = self.metadata_dict[sname]
                    diff = metadata.toplevel_diff
                    if "New file" in diff:
                        message = f"New file created for {metadata.sname}\n"
                    else:
                        message = f"Changes made to {metadata.toplevel_diff} for {metadata.sname}\n"
                else:
                    # If we are creating a new metadata file
                    message = f"Committing metadata for new superevent {sname}"
            if sys.argv is not [""]:
                if message is None:
                    message = ""
                message += f"cmd line: {' '.join(sys.argv)}"
            if message is None:
                message = "No information provided about this commit, and could not infer from context"

        if branch_name is None:
            if self.repo.active_branch == self.repo.heads["main"]:
                # If we are currently on main, we want to checkout a new branch
                logger.debug(
                    "Branch main is currently checked out, and no new branch title was passed"
                )
                user_name = (
                    self.repo.config_reader()
                    .get_value("user", "name")
                    .replace(" ", "-")
                )
                date = datetime.today().strftime("%Y-%m-%d")
                generated_branch_name = f"{user_name}-{date}"
                self.git_checkout_new_branch(generated_branch_name)
            else:
                # Otherwise, we can stay on our current branch
                pass
        else:
            if branch_name == "main":
                # The case where we are forcing the commit onto main
                logger.debug("Commit explicitly made to main")
            self.git_checkout_new_branch(branch_name)

        self.repo.git.add(filename)
        self.repo.git.commit("-m", message)
        logger.debug(f"Wrote commit {self.repo.active_branch.commit}")

    def git_merge_metadata_jsons(
        self, our_file: str, their_file: str, most_recent_common_ancestor_file: str
    ) -> None:
        """Merge metadata jsons in a manner which preserves meaning

        Parameters
        ==========
        our_file : str
            The file in the base (current)
        their_file : str
            The file from head (changes being applied)
        most_recent_common_ancestor_file : str
            The file from the MRCA (last commit shared by head and base)
        """
        # `cbcflow.process.process_merge_json handles the logic for us`
        # We just need to load in files here
        try:
            with open(most_recent_common_ancestor_file, "r") as file:
                mrca_json = json.load(file)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                f"Could not read head with error {e}, proceeding as if it's empty"
            )
            mrca_json = {}
        try:
            with open(our_file, "r") as file:
                head_json = json.load(file)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                f"Could not read head with error {e}, proceeding as if it's empty"
            )
            head_json = copy.deepcopy(mrca_json)
        try:
            with open(their_file, "r") as file:
                base_json = json.load(file)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                f"Could not read base with error {e}, proceeding as if it's empty"
            )
            base_json = copy.deepcopy(mrca_json)

        # Now get the merged json and the return status
        merge_json, return_status = process_merge_json(
            base_json=base_json,
            head_json=head_json,
            mrca_json=mrca_json,
            schema=self.metadata_schema,
        )

        # Base is where changes should be written
        with open(our_file, "w") as file:
            json.dump(merge_json, file, indent=2)

        # Return status tracks whether there are merge conflicts
        # 0 is good
        # 1 is conflicts
        return return_status

    def git_push_to_remote(self) -> None:
        """Push changes made to the library to the tracking remote"""
        if not hasattr(self, "repo"):
            self._initialize_library_git_repo()
        self.repo.git.push()

    def git_pull_from_remote(self, automated=False) -> None:
        """Pull from remote using our special logic"""
        if not hasattr(self, "repo"):
            self._initialize_library_git_repo()
        try:
            self.repo.git.fetch("origin")
            self.repo.git.merge("origin/main", "main")
        except Exception as e:
            logger.warning("Pull failed:")
            logger.warning(e)
            if automated:
                logger.info("Automated mode prioritizes continued json validity")
                self.remote_has_merge_conflict = True
                logger.info("Resetting to pre-merge state")
                self.repo.git.reset("--merge")

    def git_checkout_new_branch(
        self, branch_name: str, remote_to_track: str = "origin"
    ) -> None:
        """Checkout a branch, creating it if necessary

        Parameters
        ==========
        branch_name : str
            The title of the branch to create
        remote_to_track : str
            If a new branch is being created, such that we want to track a remote, this designates
            the remote which the tracking branch should be pushed to
        """
        # If necessary initialize the repo
        if not hasattr(self, "repo"):
            self._initialize_library_git_repo()
        # https://gitpython.readthedocs.io/en/stable/tutorial.html
        if branch_name not in self.repo.heads:
            # If necessary create a new branch with title branch_name
            logger.info(f"Creating branch {branch_name}")
            self.repo.create_head(branch_name)
        if self.repo.active_branch != self.repo.heads[branch_name]:
            # If necessary check out the branch with title branch_name
            logger.info(f"Checking out branch {branch_name}")
            self.repo.heads[branch_name].checkout()
        if self.repo.active_branch.tracking_branch() is None:
            logger.info(
                f"Pushing to tracked remote branch {remote_to_track}/{branch_name}"
            )
            self.repo.git.push("-u", remote_to_track, branch_name)

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
    def library_index_schema(self) -> dict:
        """The schema being used for this library's index"""
        return get_schema(index_schema=True, version="v1")

    @cached_property
    def index_from_file(self) -> dict:
        """Fetch the info from the index json as it currently exists"""
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, "r") as f:
                    current_index_data = json.load(f)
                self.index_validator(current_index_data, self.library_index_schema)
                return current_index_data
            except fastjsonschema.JsonSchemaValueException:
                logger.warning("Present index data failed validation!")
                return dict()
        else:
            logger.info("No index file currently present")
            return dict()

    @property
    def working_index(self) -> dict:
        """The working index for the library,
        probably generated from current metadata,
        potentially modified afterwards"""

        return self._working_index

    @working_index.setter
    def working_index(self, input_dict) -> None:
        self._working_index = input_dict

    def generate_index_from_metadata(self) -> dict:
        """Generate the index reflect the current state of the library

        Returns
        =======
        dict
            The new index contents, based on the contents of the library
        """
        self.load_library_metadata_dict()
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
            superevent_meta["UID"] = sname
            superevent_meta["LastUpdated"] = metadata.get_date_last_modified()
            new_index["Superevents"].append(superevent_meta)
            # Get the datetime of the most recent change
            if dp.parse(superevent_meta["LastUpdated"]) > dp.parse(current_most_recent):
                current_most_recent = superevent_meta["LastUpdated"]
        # Sort by Sname for readability
        new_index["Superevents"].sort(key=lambda x: x["UID"])
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
        if self.working_index == dict():
            self.working_index = self.generate_index_from_metadata()
        index_diff = diff(self.index_from_file, self.working_index)
        if index_diff != {}:
            logger.debug("Index data has changed since it was last written")
            string_rep_diff = get_dumpable_json_diff(index_diff)
            logger.debug(json.dumps(string_rep_diff, indent=2))
        return index_diff

    def set_working_index_with_updates_to_file_index(self) -> None:
        """Sometimes, we want to *update* the index instead of overwrite it.
        This sets the working index to do just that.
        Note:
        - This will not remove events even if they are no longer satisfy index requirements
        - If the working index has labels already set, this will concatenate those to the
        labels in the file index, rather than overwriting, which may be undesirable"""
        # Generate the working index from
        if self.working_index == dict():
            self.working_index = self.generate_index_from_metadata()
        # Do a copy in case of python scope shenanigans
        working_index_copy = copy.deepcopy(self.working_index)
        # Use update methods to apply the update
        self.working_index = process_update_json(
            working_index_copy,
            self.index_from_file,
            self.library_index_schema,
        )

    def write_index_file(self, branch_name: Union[str, None] = None) -> None:
        """Writes the new index to the library

        Parameters
        ==========
        branch_name: str | None, optional
            The branch name, as passed to `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`.
        """
        index_delta = self.check_for_index_update()
        if index_delta != dict():
            with open(self.index_file_path, "w") as f:
                json.dump(self.working_index, f, indent=2)
            if self.is_git_repository:
                self.git_add_and_commit(
                    filename=self.index_file_name,
                    message=f"Updating index with changes:\n\
                        {pformat(get_dumpable_json_diff(index_delta))}",
                    branch_name=branch_name,
                )

    def label_index_file(
        self, labeller_class: Type[LabellerType] = StandardLabeller
    ) -> None:
        """Apply labels to the working index file"""
        if self.working_index == dict():
            self.working_index = self.generate_index_from_metadata()

        labeller_instance = labeller_class(self)
        labeller_instance.populate_working_index_with_labels()
