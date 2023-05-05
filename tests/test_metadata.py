import copy
import json
import logging
import os
import shutil
import subprocess
import unittest

from cbcflow.metadata import MetaData
from cbcflow.parser import get_parser_and_default_data
from cbcflow.schema import get_schema
from cbcflow.utils import get_cluster, get_date_last_modified, get_md5sum

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestMetaData(unittest.TestCase):
    def clean_up(self):
        if os.path.exists(self.test_library_directory):
            shutil.rmtree(self.test_library_directory)

    def setUp(self):
        self.test_library_directory = "tests/files_for_testing/test_library"
        self.test_sname = "S190425z"
        self.schema = get_schema()
        _, default_data = get_parser_and_default_data(self.schema)
        self.default_data = default_data
        self.default_data["Sname"] = self.test_sname
        self.default_metadata_kwargs = dict(
            schema=self.schema, default_data=self.default_data, no_git_library=True
        )
        self.clean_up()
        self.path_to_testing_linked_file_1 = (
            "tests/files_for_testing/test-file-for-linking-1.txt"
        )
        self.path_to_testing_linked_file_2 = (
            "tests/files_for_testing/test-file-for-linking-2.txt"
        )
        with open("tests/files_for_testing/update_json_1.json", "r") as f:
            self.update_json_1 = json.load(f)
        with open("tests/files_for_testing/update_json_2.json", "r") as f:
            self.update_json_2 = json.load(f)

        self.check_metadata_data = copy.deepcopy(
            MetaData(
                self.test_sname,
                local_library_path=self.test_library_directory,
                **self.default_metadata_kwargs,
            ).data
        )
        self.clean_up()

        self.check_metadata_data["Info"]["Labels"].append(
            "A test label, showing that appending works"
        )
        self.check_metadata_data["Info"]["Labels"].append("A second test label")

        self.check_metadata_data["Cosmology"][
            "PreferredLowLatencySkymap"
        ] = "A sample preferred skymap, showing that setting works correctly"
        self.check_metadata_data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF1",
                "RightAscension": 0.0,
                "Declination": 0.0,
                "Redshift": 1.0,
                "RedshiftUncertainty": 0.5,
                "PeculiarMotion": 100,
                "UncertaintyPeculiarMotion": 50.0,
                "GCN": "A sample GCN",
                "Type": "GRB",
                "TimeDelay": 2.0,
                "Notes": [],
            }
        )
        self.check_metadata_data["Cosmology"]["Counterparts"].append(
            {
                "UID": "TestF2",
                "Notes": [],
            }
        )
        self.check_metadata_data["ExtremeMatter"]["Analyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Reviewers": ["Prospero", "Alonso"],
                "Analysts": ["Miranda"],
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
        self.check_metadata_data["ExtremeMatter"]["Analyses"].append(
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
        self.check_metadata_data["ExtremeMatter"]["Analyses"].append(
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
        self.check_metadata_data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF1",
                "Description": "A fake analysis",
                "Analysts": ["Miranda", "Caliban"],
                "Reviewers": [],
                "Results": [
                    {
                        "UID": "TestF1",
                        "Deprecated": False,
                        "Publications": [],
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
                        "Deprecated": False,
                        "Publications": [],
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
                        "Deprecated": False,
                        "Publications": [],
                        "WaveformApproximant": "IMRPhenomXPHM",
                        "Notes": [],
                        "ReviewStatus": "unstarted",
                    },
                ],
                "Notes": [],
            }
        )
        self.check_metadata_data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF2",
                "Description": "Another fake analysis",
                "Analysts": ["Miranda"],
                "Results": [
                    {
                        "UID": "TestF1",
                        "WaveformApproximant": "SEOBNRv4PHM",
                        "Deprecated": False,
                        "Publications": [],
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
                "Notes": [],
            }
        )
        self.check_metadata_data["TestingGR"]["IMRCTAnalyses"].append(
            {
                "UID": "TestF3",
                "Analysts": ["Gonzalo"],
                "Results": [],
                "Reviewers": [],
                "Notes": [],
            }
        )

    def tearDown(self):
        self.clean_up()

    def test_empty_metadata_sname(self):
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        assert metadata.sname == self.test_sname

    def test_empty_metadata_library(self):
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        assert metadata.library.library == self.test_library_directory

    def test_empty_metadata_library_print(self):
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        metadata.pretty_print()

    def test_metadata_from_file(self):
        # Write a metadata file to test
        tgt = "tests/files_for_testing/cbc-meta-data-example.json"
        sname = "S220331b"
        os.makedirs(self.test_library_directory)
        shutil.copy(
            tgt, os.path.join(self.test_library_directory, MetaData.get_filename(sname))
        )

        metadata = MetaData(
            sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        assert metadata.sname == sname
        assert metadata.data["ParameterEstimation"]["Reviewers"] == ["Prospero"]

    def test_modify_metadata_from_file(self):
        # Write a metadata file to test
        tgt = "tests/files_for_testing/cbc-meta-data-example.json"
        sname = "S220331b"
        os.makedirs(self.test_library_directory)
        shutil.copy(tgt, self.test_library_directory + f"/{sname}.json")

        metadata = MetaData(
            sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        metadata.data["ParameterEstimation"]["Reviewers"].append("Ariel")
        metadata.write_to_library()

        metadata_mod = MetaData(
            sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        assert metadata.data == metadata_mod.data

    def test_update_metadata_with_json_add(self):
        if not os.path.exists(self.test_library_directory):
            os.makedirs(self.test_library_directory)

        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        # Write out the update_json

        metadata.update(self.update_json_1)
        metadata.update(self.update_json_2)

        # Perform the changes manually as a check
        assert self.check_metadata_data == metadata.data

    def test_update_metadata_with_json_remove(self):
        if not os.path.exists(self.test_library_directory):
            os.makedirs(self.test_library_directory)

        # Start out the same as above
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )

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
                "Analyses": [{"UID": "TestF1", "Reviewers": ["Prospero"]}]
            },
            "TestingGR": {
                "IMRCTAnalyses": [
                    {
                        "UID": "TestF1",
                        "Analysts": ["Miranda"],
                        "Results": [{"UID": "TestF1", "Notes": ["A note"]}],
                    }
                ]
            },
        }

        metadata.update(removal_json, is_removal=True)

        self.check_metadata_data["Info"]["Labels"] = ["A second test label"]
        self.check_metadata_data["ExtremeMatter"]["Analyses"][0]["Reviewers"] = [
            "Alonso"
        ]
        self.check_metadata_data["TestingGR"]["IMRCTAnalyses"][0]["Analysts"] = [
            "Caliban"
        ]
        self.check_metadata_data["TestingGR"]["IMRCTAnalyses"][0]["Results"][0][
            "Notes"
        ] = ["Another note"]

        assert self.check_metadata_data == metadata.data

    def test_update_metadata_from_json(self):
        if not os.path.exists(self.test_library_directory):
            os.makedirs(self.test_library_directory)

        # Use the command line argument to modify directly from a json
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        metadata.write_to_library()
        logger.info(metadata.library.library)
        cmd_1 = [
            "cbcflow_update_from_file",
            "S190425z",
            "tests/files_for_testing/update_json_1.json",
            "--library",
            self.test_library_directory,
            "--no-git-library",
            "--yes",
        ]
        subprocess.check_output(cmd_1)
        cmd_2 = [
            "cbcflow_update_from_file",
            "S190425z",
            "tests/files_for_testing/update_json_2.json",
            "--library",
            self.test_library_directory,
            "--no-git-library",
            "--yes",
        ]
        subprocess.check_output(cmd_2)
        altered_metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )

        assert altered_metadata.data == self.check_metadata_data

    def test_update_metadata_from_yaml(self):
        if not os.path.exists(self.test_library_directory):
            os.makedirs(self.test_library_directory)

        # now as above, just with yamls
        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        metadata.write_to_library()
        cmd_1 = [
            "cbcflow_update_from_file",
            "S190425z",
            "tests/files_for_testing/update_yaml_1.yaml",
            "--library",
            self.test_library_directory,
            "--no-git-library",
            "--yes",
        ]
        subprocess.check_output(cmd_1)
        cmd_2 = [
            "cbcflow_update_from_file",
            "S190425z",
            "tests/files_for_testing/update_yaml_2.yaml",
            "--library",
            self.test_library_directory,
            "--no-git-library",
            "--yes",
        ]
        subprocess.check_output(cmd_2)
        altered_metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )

        assert altered_metadata.data == self.check_metadata_data

    def test_update_with_flag_commands(self):
        if not os.path.exists(self.test_library_directory):
            os.makedirs(self.test_library_directory)

        metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )
        metadata.write_to_library()
        base_cmd = [
            "cbcflow_update_from_flags",
            "S190425z",
            "--library",
            self.test_library_directory,
            "--no-git-library",
            "--yes",
        ]
        cmd_1 = copy.copy(base_cmd)
        cmd_1 += [
            "--Cosmology-Counterparts-UID-set",
            "TestF1",
            "--Cosmology-Counterparts-Declination-set",
            "0",
            "--Cosmology-Counterparts-PeculiarMotion-set",
            "100",
            "--Cosmology-Counterparts-Redshift-set",
            "1",
            "--Cosmology-Counterparts-RedshiftUncertainty-set",
            "0.5",
            "--Cosmology-Counterparts-RightAscension-set",
            "0",
            "--Cosmology-Counterparts-TimeDelay-set",
            "2",
            "--Cosmology-Counterparts-Type-set",
            "GRB",
            "--Cosmology-Counterparts-UncertaintyPeculiarMotion-set",
            "50",
            "--Cosmology-Counterparts-GCN-set",
            "A sample GCN",
        ]
        subprocess.check_output(cmd_1)
        cmd_2 = copy.copy(base_cmd)
        cmd_2 += [
            "--Cosmology-Counterparts-UID-set",
            "TestF2",
            "--Cosmology-PreferredLowLatencySkymap-set",
            "A sample preferred skymap, showing that setting works correctly",
        ]
        subprocess.check_output(cmd_2)
        cmd_3 = copy.copy(base_cmd)
        cmd_3 += [
            "--ExtremeMatter-Analyses-UID-set",
            "TestF1",
            "--ExtremeMatter-Analyses-AnalysisStatus-set",
            "ongoing",
            "--ExtremeMatter-Analyses-AnalysisSoftware-set",
            "A fake software",
            "--ExtremeMatter-Analyses-Analysts-add",
            "Miranda",
            "--ExtremeMatter-Analyses-Reviewers-add",
            "Prospero",
            "--ExtremeMatter-Analyses-Description-set",
            "A fake analysis",
            "--ExtremeMatter-Analyses-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-1.txt",
            "--ExtremeMatter-Analyses-ResultFile-PublicHTML-set",
            "fake-url.org",
        ]
        subprocess.check_output(cmd_3)
        cmd_4 = copy.copy(base_cmd)
        cmd_4 += [
            "--ExtremeMatter-Analyses-UID-set",
            "TestF2",
            "--ExtremeMatter-Analyses-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-1.txt",
            "--ExtremeMatter-Analyses-Description-set",
            "Another fake analysis",
            "--Info-Labels-add",
            "A test label, showing that appending works",
            "--Info-Labels-add",
            "A second test label",
        ]
        subprocess.check_output(cmd_4)
        cmd_5 = copy.copy(base_cmd)
        cmd_5 += [
            "--ExtremeMatter-Analyses-UID-set",
            "TestF3",
            "--ExtremeMatter-Analyses-Description-set",
            "Yet another fake analysis",
        ]
        subprocess.check_output(cmd_5)
        cmd_6 = copy.copy(base_cmd)
        cmd_6 += [
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Analysts-add",
            "Miranda",
            "--TestingGR-IMRCTAnalyses-Description-set",
            "A fake analysis",
            "--TestingGR-IMRCTAnalyses-Results-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Results-Notes-add",
            "A note",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-1.txt",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-PublicHTML-set",
            "a-fake-url.org",
            "--TestingGR-IMRCTAnalyses-Results-WaveformApproximant-set",
            "IMRPhenomXPHM",
        ]
        subprocess.check_output(cmd_6)
        cmd_7 = copy.copy(base_cmd)
        cmd_7 += [
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Results-UID-set",
            "TestF2",
            "--TestingGR-IMRCTAnalyses-Results-Notes-add",
            "A note",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-1.txt",
        ]
        subprocess.check_output(cmd_7)
        cmd_8 = copy.copy(base_cmd)
        cmd_8 += [
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF2",
            "--TestingGR-IMRCTAnalyses-Analysts-add",
            "Miranda",
            "--TestingGR-IMRCTAnalyses-Description-set",
            "Another fake analysis",
            "--TestingGR-IMRCTAnalyses-Results-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-1.txt",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-PublicHTML-set",
            "a-fake-url.org",
            "--TestingGR-IMRCTAnalyses-Results-WaveformApproximant-set",
            "SEOBNRv4PHM",
        ]
        subprocess.check_output(cmd_8)
        cmd_9 = copy.copy(base_cmd)
        cmd_9 += [
            "--ExtremeMatter-Analyses-UID-set",
            "TestF1",
            "--ExtremeMatter-Analyses-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-2.txt",
            "--ExtremeMatter-Analyses-Reviewers-add",
            "Alonso",
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Analysts-add",
            "Caliban",
            "--TestingGR-IMRCTAnalyses-Results-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Results-Notes-add",
            "Another note",
            "--TestingGR-IMRCTAnalyses-Results-ResultFile-Path-set",
            "tests/files_for_testing/test-file-for-linking-2.txt",
            "--TestingGR-IMRCTAnalyses-Results-WaveformApproximant-set",
            "NRSur7dq4",
        ]
        subprocess.check_output(cmd_9)
        cmd_10 = copy.copy(base_cmd)
        cmd_10 += [
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF1",
            "--TestingGR-IMRCTAnalyses-Results-UID-set",
            "TestF3",
            "--TestingGR-IMRCTAnalyses-Results-WaveformApproximant-set",
            "IMRPhenomXPHM",
        ]
        subprocess.check_output(cmd_10)
        cmd_11 = copy.copy(base_cmd)
        cmd_11 += [
            "--TestingGR-IMRCTAnalyses-UID-set",
            "TestF3",
            "--TestingGR-IMRCTAnalyses-Analysts-add",
            "Gonzalo",
        ]
        subprocess.check_output(cmd_11)
        altered_metadata = MetaData(
            self.test_sname,
            local_library_path=self.test_library_directory,
            **self.default_metadata_kwargs,
        )

        assert altered_metadata.data == self.check_metadata_data


if __name__ == "__main__":
    unittest.main()
