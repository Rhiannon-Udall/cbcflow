import configparser
import copy
import json
import logging
import os
import sys

import jsondiff
import jsonschema
import pygit2

from .process import process_update_json

logger = logging.getLogger(__name__)


class MetaData(object):
    def __init__(self, sname, library, default_data, schema, no_git_library=False):
        """A object to store and interact with a metadata object

        Parameters
        ----------
        sname: str
            The GraceDB assigned SNAME of the event.
        library: str
            A directory to store cached copies of the metadata.
        default_data: dict
            A dictionary containing the defaults inferred from the schema. If
            no default_data is suggested, this should be an empty dictionary.
        schema: dict
            The loaded schema for validation.
        no_git_library: bool
            If False (default), treat the library as a git directory and add
            and commit changes on write.
        """

        self.sname = sname
        self.library = library
        self.schema = schema
        self.no_git_library = no_git_library
        self._loaded_data = None

        if self.library_file_exists:
            logger.info("Found existing library file: loading")
            self.load_from_library()
        else:
            logger.info("No library file: creating defaults")
            default_data["Sname"] = self.sname
            self.validate(default_data)
            self.data = default_data

    @staticmethod
    def from_file(filename, schema, default_data):
        library = os.path.dirname(filename)
        sname = os.path.basename(filename).split("-")[0]
        return MetaData(sname, library, default_data, schema)

    @property
    def library(self):
        return self._library

    @library.setter
    def library(self, library):
        if library is None:
            raise ValueError(
                "The library directory is NoneType. Please set the library path."
            )
        if os.path.exists(library) is False:
            os.mkdir(library)
        self._library = library

    @staticmethod
    def get_filename(sname):
        fname_suffix = "json"
        return sname + "-cbc-metadata" + "." + fname_suffix

    @property
    def filename(self):
        return self.get_filename(self.sname)

    @property
    def library_file(self):
        return os.path.join(self.library, self.filename)

    def update(self, update_dict, is_removal=False):
        new_metadata = copy.deepcopy(self)
        new_metadata.data = process_update_json(
            update_dict, new_metadata.data, self.schema, is_removal=is_removal
        )
        self.validate(new_metadata.data)
        self.data = new_metadata.data

    def load_from_library(self):
        with open(self.library_file, "r") as file:
            data = json.load(file)

        self.validate(data)
        self.data = data
        self._loaded_data = copy.deepcopy(data)

    def write_to_library(self, message: str | None = None):
        """
        Write loaded metadata back to library, and stage/commit if the library is a git repository

        Parameters
        ==========
        message : str | None
            If passed, this message will be used for the git commit instead of the default.
        """
        if self.is_updated is False:
            logger.info("No changes made, exiting")
            return

        self.validate(self.data)
        self.print_diff()
        logger.info(f"Writing file {self.library_file}")
        with open(self.library_file, "w") as file:
            json.dump(self.data, file, indent=2)
        if self.no_git_library is False:
            self.git_add_and_commit(message=message)

    def git_add_and_commit(self, message: str | None = None):
        """
        Perform the git operations add and commit

        Parameters
        ==========
        message : str | None
            If passed, this message will be used in the git commit, rather than the default.
        """
        if os.path.exists(os.path.join(self.library, ".git")) is False:
            raise ValueError(
                f"The library directory {self.library} is not a repository"
            )

        repo = pygit2.init_repository(self.library)

        try:
            ref = repo.head.name
        except pygit2.GitError:
            # If the git repo is empty
            raise ValueError(
                f"The git library directory {self.library} is empty ."
                "Please initialise with a commit"
            )

        parents = [repo.head.target]
        repo.index.add(self.filename)
        repo.index.write()
        author = self._get_author_signature()
        if message is None:
            message = f"Changes made to [{self.toplevel_diff}]"
            message += f"\ncmd line: {' '.join(sys.argv)}"
        tree = repo.index.write_tree()
        repo.create_commit(ref, author, author, message, tree, parents)

    def _get_author_signature(self):
        gitconfig = os.path.expanduser("~/.gitconfig")
        config = configparser.ConfigParser()
        config.sections()
        config.read(gitconfig)
        name = config["user"]["name"]
        email = config["user"]["email"]
        return pygit2.Signature(name, email)

    @property
    def is_updated(self):
        return self._loaded_data != self.data

    @property
    def library_file_exists(self):
        return os.path.exists(self.library_file)

    def get_diff(self):
        return jsondiff.diff(self._loaded_data, self.data)

    def print_diff(self):
        if self._loaded_data is None:
            return

        diff = self.get_diff()
        if diff:
            logger.info("Changes between loaded and current data:")
            logger.info(diff)

    @property
    def toplevel_diff(self):
        return ",".join([str(k) for k in self.get_diff().keys()])

    def pretty_print(self, data):
        logger.info(f"Metadata contents for {self.sname}:")
        logger.info(json.dumps(data, indent=4))

    def validate(self, data):
        jsonschema.validate(data, self.schema)
