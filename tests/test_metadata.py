import copy
import json
import os
import shutil
import unittest

from cbcflow.metadata import MetaData
from cbcflow.parser import get_parser_and_default_data
from cbcflow.schema import get_schema
from cbcflow.utils import get_cluster, get_date_last_modified, get_md5sum


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
        self.path_to_testing_linked_file_1 = "tests/test-file-for-linking-1.txt"
        self.path_to_testing_linked_file_2 = "tests/test-file-for-linking-2.txt"
        with open("tests/update_json_1.json", "r") as f:
            self.update_json_1 = json.load(f)
        with open("tests/update_json_2.json", "r") as f:
            self.update_json_2 = json.load(f)

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

    def test_update_metadata_with_json_add(self):
        metadata = MetaData(
            self.test_sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        check_metadata = copy.deepcopy(metadata)
        # Write out the update_json

        metadata.update(self.update_json_1)
        metadata.update(self.update_json_2)

        # Perform the changes manually as a check
        check_metadata.data["Info"]["Labels"].append(
            "A test label, showing that appending works"
        )
        check_metadata.data["Info"]["Labels"].append("A second test label")

        check_metadata.data["Cosmology"][
            "PreferredSkymap"
        ] = "A sample preferred skymap, showing that setting works correctly"
        check_metadata.data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF1",
                "RightAscension": 0,
                "Declination": 0,
                "Redshift": 1,
                "RedshiftUncertainty": 0.5,
                "PeculiarMotion": 100,
                "UncertaintyPeculiarMotion": 50,
                "GCN": "A sample GCN",
                "Type": "GRB",
                "TimeDelay": 2,
                "Notes": [],
            }
        )
        check_metadata.data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF2",
                "Notes": [],
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Reviewers": ["Gregory Ashton", "Jonah Kanner"],
                "Analysts": ["Rhiannon Udall"],
                "AnalysisSoftware": "A fake software",
                "AnalysisStatus": "ongoing",
                "ResultFile": {
                    "Path": get_cluster()
                    + ":"
                    + os.path.join(os.getcwd(), self.path_to_testing_linked_file_2),
                    "PublicHTML": "fake-url.org",
                    "MD5Sum": get_md5sum(self.path_to_testing_linked_file_2),
                    "DateLastModified": get_date_last_modified(
                        self.path_to_testing_linked_file_2
                    ),
                },
                "Notes": [],
                "ReviewStatus": "unstarted",
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "Reviewers": [],
                "Analysts": [],
                "AnalysisStatus": "unstarted",
                "ReviewStatus": "unstarted",
                "Notes": [],
                "UID": "TestF2",
                "Description": "Another fake analysis",
                "ResultFile": {
                    "Path": get_cluster()
                    + ":"
                    + os.path.join(os.getcwd(), self.path_to_testing_linked_file_1),
                    "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                    "DateLastModified": get_date_last_modified(
                        self.path_to_testing_linked_file_1
                    ),
                },
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "Reviewers": [],
                "Analysts": [],
                "AnalysisStatus": "unstarted",
                "ReviewStatus": "unstarted",
                "Notes": [],
                "UID": "TestF3",
                "Description": "Yet another fake analysis",
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Analysts": ["Rhiannon Udall", "Mr C++"],
                "Reviewers": [],
                "Results": [
                    {
                        "UID": "TestF1",
                        "WaveformApproximant": "NRSur7dq4",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_2
                            ),
                            "PublicHTML": "a-fake-url.org",
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_2),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_2
                            ),
                        },
                        "Notes": ["A note", "Another note"],
                        "ReviewStatus": "unstarted",
                    },
                    {
                        "UID": "TestF2",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_1
                            ),
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_1
                            ),
                        },
                        "Notes": ["A note"],
                        "ReviewStatus": "unstarted",
                    },
                    {
                        "UID": "TestF3",
                        "WaveformApproximant": "IMRPhenomXPHM",
                        "Notes": [],
                        "ReviewStatus": "unstarted",
                    },
                ],
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF2",
                "Description": "Another fake analysis",
                "Analysts": ["Rhiannon Udall"],
                "Results": [
                    {
                        "UID": "TestF1",
                        "WaveformApproximant": "SEOBNRv4PHM",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_1
                            ),
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_1
                            ),
                            "PublicHTML": "a-fake-url.org",
                        },
                        "ReviewStatus": "unstarted",
                        "Notes": [],
                    },
                ],
                "Reviewers": [],
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF3",
                "Analysts": ["Donald Knuth"],
                "Results": [],
                "Reviewers": [],
            }
        )

        assert check_metadata.data == metadata.data

    def test_update_metadata_with_json_remove(self):
        # Start out the same as above
        metadata = MetaData(
            self.test_sname, self.test_library_directory, **self.default_metadata_kwargs
        )
        check_metadata = copy.deepcopy(metadata)

        # Perform the updates
        metadata.update(self.update_json_1)
        metadata.update(self.update_json_2)

        # Now the core test distinguishing this from the test above
        # Do some removals

        removal_json = {
            "Info": {
                "Labels": ["A test label, showing that appending works"],
            },
            "ExtremeMatter": {
                "Analyses": [{"UID": "TestF1", "Reviewers": ["Gregory Ashton"]}]
            },
            "TestingGR": {
                "IMRCTAnalyses": [
                    {
                        "UID": "TestF1",
                        "Analysts": ["Rhiannon Udall"],
                        "Results": [{"UID": "TestF1", "Notes": ["A note"]}],
                    }
                ]
            },
        }

        metadata.update(removal_json, is_removal=True)

        # Perform the changes manually as a check
        check_metadata.data["Info"]["Labels"].append("A second test label")

        check_metadata.data["Cosmology"][
            "PreferredSkymap"
        ] = "A sample preferred skymap, showing that setting works correctly"
        check_metadata.data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF1",
                "RightAscension": 0,
                "Declination": 0,
                "Redshift": 1,
                "RedshiftUncertainty": 0.5,
                "PeculiarMotion": 100,
                "UncertaintyPeculiarMotion": 50,
                "GCN": "A sample GCN",
                "Type": "GRB",
                "TimeDelay": 2,
                "Notes": [],
            }
        )
        check_metadata.data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF2",
                "Notes": [],
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Reviewers": ["Jonah Kanner"],
                "Analysts": ["Rhiannon Udall"],
                "AnalysisSoftware": "A fake software",
                "AnalysisStatus": "ongoing",
                "ResultFile": {
                    "Path": get_cluster()
                    + ":"
                    + os.path.join(os.getcwd(), self.path_to_testing_linked_file_2),
                    "PublicHTML": "fake-url.org",
                    "MD5Sum": get_md5sum(self.path_to_testing_linked_file_2),
                    "DateLastModified": get_date_last_modified(
                        self.path_to_testing_linked_file_2
                    ),
                },
                "Notes": [],
                "ReviewStatus": "unstarted",
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "Reviewers": [],
                "Analysts": [],
                "AnalysisStatus": "unstarted",
                "ReviewStatus": "unstarted",
                "Notes": [],
                "UID": "TestF2",
                "Description": "Another fake analysis",
                "ResultFile": {
                    "Path": get_cluster()
                    + ":"
                    + os.path.join(os.getcwd(), self.path_to_testing_linked_file_1),
                    "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                    "DateLastModified": get_date_last_modified(
                        self.path_to_testing_linked_file_1
                    ),
                },
            }
        )
        check_metadata.data["ExtremeMatter"]["Analyses"].append(
            {
                "Reviewers": [],
                "Analysts": [],
                "AnalysisStatus": "unstarted",
                "ReviewStatus": "unstarted",
                "Notes": [],
                "UID": "TestF3",
                "Description": "Yet another fake analysis",
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Analysts": ["Mr C++"],
                "Reviewers": [],
                "Results": [
                    {
                        "UID": "TestF1",
                        "WaveformApproximant": "NRSur7dq4",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_2
                            ),
                            "PublicHTML": "a-fake-url.org",
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_2),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_2
                            ),
                        },
                        "Notes": ["Another note"],
                        "ReviewStatus": "unstarted",
                    },
                    {
                        "UID": "TestF2",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_1
                            ),
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_1
                            ),
                        },
                        "Notes": ["A note"],
                        "ReviewStatus": "unstarted",
                    },
                    {
                        "UID": "TestF3",
                        "WaveformApproximant": "IMRPhenomXPHM",
                        "Notes": [],
                        "ReviewStatus": "unstarted",
                    },
                ],
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF2",
                "Description": "Another fake analysis",
                "Analysts": ["Rhiannon Udall"],
                "Results": [
                    {
                        "UID": "TestF1",
                        "WaveformApproximant": "SEOBNRv4PHM",
                        "ResultFile": {
                            "Path": get_cluster()
                            + ":"
                            + os.path.join(
                                os.getcwd(), self.path_to_testing_linked_file_1
                            ),
                            "MD5Sum": get_md5sum(self.path_to_testing_linked_file_1),
                            "DateLastModified": get_date_last_modified(
                                self.path_to_testing_linked_file_1
                            ),
                            "PublicHTML": "a-fake-url.org",
                        },
                        "ReviewStatus": "unstarted",
                        "Notes": [],
                    },
                ],
                "Reviewers": [],
            }
        )
        check_metadata.data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF3",
                "Analysts": ["Donald Knuth"],
                "Results": [],
                "Reviewers": [],
            }
        )

        assert check_metadata.data == metadata.data

    def test_update_metadata_from_json(self):
        pass

    def test_update_metadata_from_yaml(self):
        pass


if __name__ == "__main__":
    unittest.main()
