"""Class object for core metadata"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Union

import jsondiff

from .process import process_update_json
from .utils import get_date_last_modified
from .parser import get_parser_and_default_data
from .schema import get_schema
from .utils import setup_logger

if TYPE_CHECKING:
    from .database import LocalLibraryDatabase

logger = setup_logger()


class MetaData(object):
    """The core object for superevent level metadata, connecting to stored json information"""

    def __init__(
        self,
        sname: str,
        local_library: Union["LocalLibraryDatabase", None] = None,
        local_library_path: Union[str, None] = None,
        schema: Union[dict, None] = None,
        default_data: Union[dict, None] = None,
        no_git_library: bool = False,
    ) -> None:
        """Setup the code level representation of the metadata

        Parameters
        ----------
        sname: str
            The GraceDB assigned SNAME of the event.
        local_library :`cbcflow.database.LocalLibraryDatabase`, optional
            A directory to store cached copies of the metadata.
        local_library_path : str, optional
            The path
        default_data: dict, optional
            A dictionary containing the defaults inferred from the schema. If
            no default_data is suggested, this should be an empty dictionary.
        schema: dict, optional
            The loaded schema for validation.
        no_git_library: bool, default=False
            If False (default), treat the library as a git directory and add
            and commit changes on write.
        """

        self.sname = sname
        if local_library is not None:
            self.library = local_library
        elif local_library_path is not None:
            from cbcflow.database import LocalLibraryDatabase

            self.library = LocalLibraryDatabase(
                local_library_path, schema=schema, default_data=default_data
            )
        else:
            raise ValueError("One of local_library or local_library_path must be given")
        self.no_git_library = no_git_library
        self._loaded_data = None

        if schema is None:
            schema = get_schema()
        if default_data is None:
            _, default_data = get_parser_and_default_data(schema=schema)

        logger.debug(f"Loading metadata object for superevent {self.sname}")

        if self.library_file_exists:
            logger.debug("Found existing library file: loading")
            self.load_from_library()
        else:
            logger.info("No library file: creating defaults")
            default_data["Sname"] = self.sname
            self.library.validate(default_data)
            self.data = default_data

        self.library.metadata_dict[sname] = self

    ############################################################################
    ############################################################################
    ####                  System Properties and Operations                  ####
    ############################################################################
    ############################################################################

    @property
    def data(self) -> dict:
        """The MetaData object's actual data dict"""
        return self._data

    @data.setter
    def data(self, new_dict: dict) -> None:
        self._data = new_dict

    @property
    def library(self) -> "LocalLibraryDatabase":
        """The library this metadata is attached to"""
        return self._library

    @library.setter
    def library(self, library: "LocalLibraryDatabase") -> None:
        """The library this metadata is attached to

        Parameters
        ==========
        library : `cbcflow.database.LocalLibraryDatabase`
            The library to which this metadata will be connected.
        """
        self._library = library

    @staticmethod
    def get_filename(sname: str) -> str:
        """Get the standard file name given an sname

        Parameters
        ==========
        sname : str
            The superevent's sname string

        Returns
        =======
        str
            The corresponding standard file name
        """
        fname_suffix = "json"
        return sname + "-cbc-metadata" + "." + fname_suffix

    @property
    def filename(self) -> str:
        """The file name associated with this metadata object"""
        return self.get_filename(self.sname)

    @property
    def library_file(self) -> str:
        """The full metadata's file path, found in its corresponding library"""
        return os.path.join(self.library.library, self.filename)

    @property
    def library_file_exists(self) -> bool:
        """Does a file for this superevent exist in this library"""
        return os.path.exists(self.library_file)

    def get_date_of_last_commit(self) -> str:
        """Get the date of the last commit including the metadata file for sname

        Returns
        =======
        str
            The date and time last modified in iso standard (yyyy-MM-dd hh:mm:ss)
        """
        # What this function seeks to do is bizarrely difficult with pygit
        # So I will just use subprocess instead.
        # However, this remains as a mechanism by which one would start the process
        # if not hasattr(self.library, "repo"):
        #     self.library._initialize_library_git_repo()

        cwd = os.getcwd()
        os.chdir(self.library.library)
        date, time = str(
            subprocess.check_output(
                ["git", "log", "-1", "--date=iso", "--format=%cd", self.library_file]
            )
        ).split(" ")[:-1]
        datetime = date.strip("b'") + " " + time
        os.chdir(cwd)
        return datetime

    def get_date_last_modified(self) -> str:
        """Get the datetime of the last modification of this file *on this filesystem*

        Returns
        =======
        str
            The date and time last modified in iso standard (yyyy-MM-dd hh:mm:ss)
        """
        return get_date_last_modified(self.library_file)

    ############################################################################
    ############################################################################
    ####                   Read Write and Update Methods                    ####
    ############################################################################
    ############################################################################

    @staticmethod
    def from_file(
        filename: str,
        schema: Union[dict, None] = None,
        default_data: Union[dict, None] = None,
        local_library: Union["LocalLibraryDatabase", None] = None,
    ) -> MetaData:
        """Load a metadata object given a file path

        Parameters
        ==========
        filename : str
            The path to the file to load from
        schema : dict | None, optional
            If passed, the schema to use for the file, if None then use the configuration default
        default_data : dict | None, optional
            If passed, use this default data for loading the schema, if None then use the default for the schema
        local_library : `cbcflow.database.LocalLibrayDatabase`, optional
            If passed, load the MetaData with this backend library.
            If None, it will load the library using the file path.

        Returns
        =======
        `MetaData`
            The metadata object for this file\
        """
        sname = os.path.basename(filename).split("-")[0]
        if local_library is None:
            local_library_path = os.path.dirname(filename)
            return MetaData(
                sname,
                default_data=default_data,
                schema=schema,
                local_library_path=local_library_path,
            )
        else:
            return MetaData(
                sname,
                default_data=default_data,
                schema=schema,
                local_library=local_library,
            )

    def update(self, update_dict: dict, is_removal: bool = False) -> None:
        """Update the metadata with new elements

        Parameters
        ==========
        update_dict : dict
            The dictionary containing instructions to update with
        is_removal : bool, optional
            If true, this dictionary will treat all primitive list elements (i.e. not objects)
            as something to be removed, rather than added. Use sparingly.
        """
        import jsonschema

        new_metadata_data = copy.deepcopy(self.data)
        new_metadata_data = process_update_json(
            update_dict,
            new_metadata_data,
            self.library._metadata_schema,
            is_removal=is_removal,
        )
        try:
            self.library.validate(new_metadata_data)
        except jsonschema.ValidationError as e:
            logger.warning("Failed to validate")
            logger.warning(f"Changes are {jsondiff.diff(new_metadata_data, self.data)}")
            raise jsonschema.ValidationError(e.message)
        self.data = new_metadata_data

    def load_from_library(self) -> None:
        """Load metadata from a library"""
        with open(self.library_file, "r") as file:
            data = json.load(file)

        self.library.validate(data)
        self.data = data
        self._loaded_data = copy.deepcopy(data)

    def write_to_library(
        self,
        message: Union[str, None] = None,
        check_changes: bool = False,
        branch_name: Union[str, None] = None,
    ) -> None:
        """
        Write loaded metadata back to library, and stage/commit if the library is a git repository

        Parameters
        ==========
        message : str | None, optional
            If passed, this message will be used for the git commit instead of the default.
        check_changes : bool | True, False
            If true, ask the user to confirm the changes before changing the information on disk.
        branch_name: str | None, optional
            The branch name, as passed to `cbcflow.database.LocalLibraryDatabase.git_add_and_commit`.
            See that function for documentation.
        """
        if self.is_updated is False:
            logger.info("No changes made, exiting")
            return

        self.library.validate(self.data)
        self.print_summary()
        self.print_diff()

        if check_changes:
            commit_changes = self.confirm_changes()
        else:
            commit_changes = True

        if commit_changes:
            logger.info(f"Writing file {self.library_file}")
            with open(self.library_file, "w") as file:
                json.dump(self.data, file, indent=2)
            if self.no_git_library is False:
                self.library.git_add_and_commit(
                    filename=self.filename,
                    message=message,
                    sname=self.sname,
                    branch_name=branch_name,
                )
        else:
            logger.info(f"No changes made to {self.library_file}")

    def confirm_changes(self) -> bool:
        """Get input from the user that draft changes should be adopted

        Returns
        =======
        bool
            Whether the changes should be adopted
        """
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
        prompt = " [y/n] "

        question = "Are the proposed changes as you expect?"
        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if choice in valid:
                return valid[choice]
            else:
                sys.stdout.write(
                    "Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n"
                )

    ############################################################################
    ############################################################################
    ####                Status Updates and Printing Methods                 ####
    ############################################################################
    ############################################################################

    @property
    def is_updated(self) -> bool:
        """Has the library been updated since it was loaded"""
        return self._loaded_data != self.data

    def get_diff(self) -> dict:
        """Give the difference between the loaded data and the updated data

        Returns
        =======
        dict
            The output of a json diff between the loaded data and the current data
        """
        return jsondiff.diff(self._loaded_data, self.data)

    def print_summary(self) -> None:
        """Print a short summary of the event"""
        gdb = self.data["GraceDB"]
        events = gdb["Events"]

        # If no GraceDB events available fall back to None defaults
        GPSTime = None
        chirp_mass = None

        # Find the preferred event GPSTime and chirp mass
        for event in events:
            if event["State"] == "preferred":
                GPSTime = event["GPSTime"]
                m1, m2 = event["Mass1"], event["Mass2"]
                chirp_mass = round((m1 * m2) ** (3 / 5) / (m1 + m2) ** (1 / 5), 2)

        # Print the message
        logger.info(
            f"Super event: {self.sname}, GPSTime={GPSTime}, chirp_mass={chirp_mass}"
        )

    def print_diff(self) -> None:
        """Cleanly print the output of get_diff"""
        if self._loaded_data is None:
            return

        diff = self.get_diff()
        if diff:
            logger.info("Changes between loaded and current data:")
            logger.info(diff)

    @property
    def toplevel_diff(self) -> str:
        """A clean string representation of the output of get_diff"""
        diff_keys = [k for k in self.get_diff().keys()]
        if len(diff_keys) == 1 and list(diff_keys)[0] == jsondiff.replace:
            return "New file"
        else:
            return ",".join([str(k) for k in diff_keys])

    def pretty_print(self) -> None:
        """Prettily print the contents of the data"""
        logger.info(f"Metadata contents for {self.sname}:")
        logger.info(json.dumps(self.data, indent=4))
