import os
import shutil
import unittest

from cbcflow.metadata import MetaData
from cbcflow.parser import get_parser_and_default_data
from cbcflow.schema import get_schema


class TestMetaData(unittest.TestCase):
    def clean_up(self):
        if os.path.exists(self.test_library_directory):
            shutil.rmtree(self.test_library_directory)

    def setUp(self):
        self.test_library_directory = "test_library"
        self.test_sname = "S190425z"
        self.schema = get_schema()
        _, default_data = get_parser_and_default_data(self.schema)
        self.default_data = default_data
        self.default_data["Sname"] = self.test_sname
        self.default_metadata_kwargs = dict(
            schema=self.schema, default_data=self.default_data, no_git_library=True
        )
        self.clean_up()

    def tearDown(self):
        self.clean_up()

    def test_empty_metadata_sname(self):
        metadata = MetaData(
            self.test_sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        assert metadata.sname == self.test_sname

    def test_empty_metadata_library(self):
        metadata = MetaData(
            self.test_sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        assert metadata.library == self.test_library_directory

    def test_empty_metadata_library_print(self):
        metadata = MetaData(
            self.test_sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        metadata.pretty_print(metadata.data)

    def test_metadata_from_file(self):
        # Write a metadata file to test
        tgt = "tests/cbc-meta-data-example.json"
        sname = "S220331b"
        os.makedirs(self.test_library_directory)
        shutil.copy(
            tgt, os.path.join(self.test_library_directory, MetaData.get_filename(sname))
        )

        metadata = MetaData(
            sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        assert metadata.sname == sname
        assert metadata.data["ParameterEstimation"]["Reviewers"] == ["Gregory Ashton"]

    def test_modify_metadata_from_file(self):
        # Write a metadata file to test
        tgt = "tests/cbc-meta-data-example.json"
        sname = "S220331b"
        os.makedirs(self.test_library_directory)
        shutil.copy(tgt, self.test_library_directory + f"/{sname}.json")

        metadata = MetaData(
            sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        metadata.data["ParameterEstimation"]["Reviewers"].append("michael.kiwanuka")
        metadata.write_to_library()

        metadata_mod = MetaData(
            sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        assert metadata.data == metadata_mod.data

    def test_parsing_of_user_inputs(self):
        pass

    def test_update_metadata_with_json(self):
        pass

    def test_update_metadata_from_yaml(self):
        pass


if __name__ == "__main__":
    unittest.main()
