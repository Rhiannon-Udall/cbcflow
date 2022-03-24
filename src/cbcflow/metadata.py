import copy
import json
import os

import jsondiff
import jsonschema


class MetaData(object):
    fname_suffix = "json"

    def __init__(self, sname, library, default_data=None, schema=None):
        """A object to store and interact with a metadata object

        Parameters
        ----------
        sname: str
            The GraceDB assigned SNAME of the event
        library: str
            A directory to store cached copies of the metadata
        default_data: dict
            A dictionary containing the defaults inferred from the schema
        schema: dict
            The loaded schema for validation
        """

        self.sname = sname
        self.library = library
        self.schema = schema
        self._loaded_data = None

        if os.path.exists(self.library_file):
            print("Found existing library file: loading")
            self.load_from_library()
        else:
            print("No library file: creating defaults")
            if default_data is None:
                self.data = {}
            else:
                self.validate(default_data)
                self.data = default_data

    @property
    def library(self):
        return self._library

    @library.setter
    def library(self, library):
        if os.path.exists(library) is False:
            os.mkdir(library)
        self._library = library

    @property
    def library_file(self):
        return os.path.join(self.library, self.sname + "." + self.fname_suffix)

    def load_from_library(self):
        with open(self.library_file, "r") as file:
            data = json.load(file)

        self.validate(data)
        self.data = data
        self._loaded_data = copy.deepcopy(data)

    def write_to_library(self):
        self.validate(self.data)
        self.print_diff()
        with open(self.library_file, "w") as file:
            json.dump(self.data, file, indent=2)

    def print_diff(self):
        if self._loaded_data is None:
            return

        diff = jsondiff.diff(self._loaded_data, self.data)
        if diff:
            print("Changes between loaded and current data:")
            print(diff)

    def pretty_print(self, data):
        print(json.dumps(data, indent=4))

    def validate(self, data):
        jsonschema.validate(data, self.schema)
