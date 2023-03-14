from __future__ import annotations

import copy
import json
import logging
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Union

import jsondiff

from .process import process_update_json

if TYPE_CHECKING:
    from .database import LocalLibraryDatabase

logger = logging.getLogger(__name__)


class MetaData(object):
    def __init__(
        self,
        sname: str,
        local_library: Union["LocalLibraryDatabase", None] = None,
        local_library_path: Union[str, None] = None,
        schema: Union[dict, None] = None,
        default_data: Union[dict, None] = None,
        no_git_library: bool = False,
    ) -> None:
        """A object to store and interact with a metadata object

        Parameters
        ----------
        sname: str
            The GraceDB assigned SNAME of the event.
        local_library : cbcflow.database.LocalLibraryDatabase, optional
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

        if self.library_file_exists:
            logger.info("Found existing library file: loading")
            self.load_from_library()
        else:
            logger.info("No library file: creating defaults")
            default_data["Sname"] = self.sname
            self.library.validate(default_data)
            self.data = default_data

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
        MetaData
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
    def library_file(self) -> None:
        """The full metadata's file path, found in its corresponding library"""
        return os.path.join(self.library.library, self.filename)

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
        new_metadata = copy.deepcopy(self)
        new_metadata.data = process_update_json(
            update_dict,
            new_metadata.data,
            self.library._metadata_schema,
            is_removal=is_removal,
        )
        self.library.validate(new_metadata.data)
        self.data = new_metadata.data

    def load_from_library(self):
        """Load metadata from a library"""
        with open(self.library_file, "r") as file:
            data = json.load(file)

        self.library.validate(data)
        self.data = data
        self._loaded_data = copy.deepcopy(data)

    def write_to_library(self, message: Union[str, None] = None) -> None:
        """
        Write loaded metadata back to library, and stage/commit if the library is a git repository

        Parameters
        ==========
        message : str | None, optional
            If passed, this message will be used for the git commit instead of the default.
        """
        if self.is_updated is False:
            logger.info("No changes made, exiting")
            return

        self.library.validate(self.data)
        self.print_diff()
        logger.info(f"Writing file {self.library_file}")
        with open(self.library_file, "w") as file:
            json.dump(self.data, file, indent=2)
        if self.no_git_library is False:
            self.git_add_and_commit(message=message)

    def git_add_and_commit(self, message: Union[str, None] = None):
        """
        Perform the git operations add and commit

        Parameters
        ==========
        message : str | None
            If passed, this message will be used in the git commit, rather than the default.
        """
        if not hasattr(self.library, "repo"):
            self.library._initialize_library_git_repo()

        self.library.repo.index.add(self.filename)
        self.library.repo.index.write()
        author = self.library._author_signature
        if message is None:
            message = f"Changes made to [{self.toplevel_diff}]"
            message += f"\ncmd line: {' '.join(sys.argv)}"
        tree = self.library.repo.index.write_tree()
        self.library.repo.create_commit(
            self.library.ref, author, author, message, tree, self.library.parents
        )

    @property
    def is_updated(self):
        """Has the library been updated since it was loaded"""
        return self._loaded_data != self.data

    @property
    def library_file_exists(self):
        """Does a file for this superevent exist in this library"""
        return os.path.exists(self.library_file)

    def get_diff(self):
        """Give the difference between the loaded data and the updated data

        Returns
        =======
        dict
            The output of a json diff between the loaded data and the current data
        """
        return jsondiff.diff(self._loaded_data, self.data)

    def print_diff(self):
        """Cleanly print the output of get_diff"""
        if self._loaded_data is None:
            return

        diff = self.get_diff()
        if diff:
            logger.info("Changes between loaded and current data:")
            logger.info(diff)

    @property
    def toplevel_diff(self):
        """Get a clean string representation of the output of get_diff"""
        return ",".join([str(k) for k in self.get_diff().keys()])

    def pretty_print(self):
        """Prettily print the contents of the data"""
        logger.info(f"Metadata contents for {self.sname}:")
        logger.info(json.dumps(self.data, indent=4))

    def get_date_of_last_commit(self):
        """Get the date of the last commit including the metadata file for sname

        Parameters
        ==========
        sname : str
            The sname corresponding to the superevent whose metadata we are checking.

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
