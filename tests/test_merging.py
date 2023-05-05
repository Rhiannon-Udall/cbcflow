import copy
import json
import logging
import unittest

from cbcflow.process import process_merge_json
from cbcflow.schema import get_schema

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestMergingMetadata(unittest.TestCase):
    """Testing merging methods between jsons
    (since testing the git implementation itself is infeasible)"""

    def setUp(self) -> None:
        """Standard setup for test cases"""
        self.schema = get_schema()

        # Load the files to manipulate
        with open("tests/files_for_testing/merge_test.json", "r") as file:
            self.template_json = json.load(file)

        # Make 3 copies of the template
        self.head_json = copy.deepcopy(self.template_json)
        self.base_json = copy.deepcopy(self.template_json)
        self.mrca_json = copy.deepcopy(self.template_json)
        # Make a json for the correct answers
        self.check_json = copy.deepcopy(self.template_json)

    def test_basic_list_merging(self) -> None:
        """A test that basic lists merge correctly outside objects
        We will use Info-Labels for this test"""
        # MRCA : 1, 2, 3
        # Head : 1, 3, 4, 6
        # Base : 1, 2, 5, 6
        # 1 tests that a value untouched remains
        # 2 tests that a value removed in Head stays removed
        # 3 tests that a value removed in Base stays removed
        # 4 tests that a value added in Head stays added
        # 5 tests that a value added in Base stays added
        # 6 tests that a value added in both stays added, but only once
        self.mrca_json["Info"]["Labels"] = ["1", "2", "3"]
        self.head_json["Info"]["Labels"] = ["1", "3", "4", "6"]
        self.base_json["Info"]["Labels"] = ["1", "2", "5", "6"]

        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        self.check_json["Info"]["Labels"] = ["1", "4", "5", "6"]

        assert merge_json == self.check_json
        assert return_status == 0

    def test_list_merging_inside_object_in_array(self) -> None:
        """A test that basic lists merge correctly inside objects
        We will use the Publications field of two PEResult objects in ParameterEstimation-Results"""
        # Same inclusion/exclusion logic as test_basic_list_merging
        self.mrca_json["ParameterEstimation"]["Results"][0]["Publications"] = [
            "1",
            "2",
            "3",
        ]
        self.head_json["ParameterEstimation"]["Results"][0]["Publications"] = [
            "1",
            "3",
            "4",
            "6",
        ]
        self.base_json["ParameterEstimation"]["Results"][0]["Publications"] = [
            "1",
            "2",
            "5",
            "6",
        ]

        # Same inclusion/exclusion logic as test_basic_list_merging, add a 1 for uniqueness
        self.mrca_json["ParameterEstimation"]["Results"][1]["Publications"] = [
            "11",
            "12",
            "13",
        ]
        self.head_json["ParameterEstimation"]["Results"][1]["Publications"] = [
            "11",
            "13",
            "14",
            "16",
        ]
        self.base_json["ParameterEstimation"]["Results"][1]["Publications"] = [
            "11",
            "12",
            "15",
            "16",
        ]

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set check values
        self.check_json["ParameterEstimation"]["Results"][0]["Publications"] = [
            "1",
            "4",
            "5",
            "6",
        ]
        self.check_json["ParameterEstimation"]["Results"][1]["Publications"] = [
            "11",
            "14",
            "15",
            "16",
        ]

        # Evaluate similarity
        assert merge_json == self.check_json
        # Evaluate no merge conflicts
        assert return_status == 0

    def test_list_merging_inside_object_inside_object_in_array(self) -> None:
        """A test that basic lists merge correctly inside objects in arrays inside objects in arrays
        We will use the Analysts field of four PEResult objects, two each in
        TestingGR-SIMAnalyses
        """
        # Same inclusion/exclusion logic as test_basic_list_merging
        self.mrca_json["TestingGR"]["SIMAnalyses"][0]["Results"][0]["Publications"] = [
            "1",
            "2",
            "3",
        ]
        self.head_json["TestingGR"]["SIMAnalyses"][0]["Results"][0]["Publications"] = [
            "1",
            "3",
            "4",
            "6",
        ]
        self.base_json["TestingGR"]["SIMAnalyses"][0]["Results"][0]["Publications"] = [
            "1",
            "2",
            "5",
            "6",
        ]

        # Same inclusion/exclusion logic as test_basic_list_merging, add a 1 for uniqueness
        self.mrca_json["TestingGR"]["SIMAnalyses"][0]["Results"][1]["Publications"] = [
            "11",
            "12",
            "13",
        ]
        self.head_json["TestingGR"]["SIMAnalyses"][0]["Results"][1]["Publications"] = [
            "11",
            "13",
            "14",
            "16",
        ]
        self.base_json["TestingGR"]["SIMAnalyses"][0]["Results"][1]["Publications"] = [
            "11",
            "12",
            "15",
            "16",
        ]

        # Same inclusion/exclusion logic as test_basic_list_merging, add a 2 for uniqueness
        self.mrca_json["TestingGR"]["SIMAnalyses"][1]["Results"][0]["Publications"] = [
            "21",
            "22",
            "23",
        ]
        self.head_json["TestingGR"]["SIMAnalyses"][1]["Results"][0]["Publications"] = [
            "21",
            "23",
            "24",
            "26",
        ]
        self.base_json["TestingGR"]["SIMAnalyses"][1]["Results"][0]["Publications"] = [
            "21",
            "22",
            "25",
            "26",
        ]

        # Same inclusion/exclusion logic as test_basic_list_merging, add a 3 for uniqueness
        self.mrca_json["TestingGR"]["SIMAnalyses"][1]["Results"][1]["Publications"] = [
            "31",
            "32",
            "33",
        ]
        self.head_json["TestingGR"]["SIMAnalyses"][1]["Results"][1]["Publications"] = [
            "31",
            "33",
            "34",
            "36",
        ]
        self.base_json["TestingGR"]["SIMAnalyses"][1]["Results"][1]["Publications"] = [
            "31",
            "32",
            "35",
            "36",
        ]

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["TestingGR"]["SIMAnalyses"][0]["Results"][0]["Publications"] = [
            "1",
            "4",
            "5",
            "6",
        ]
        self.check_json["TestingGR"]["SIMAnalyses"][0]["Results"][1]["Publications"] = [
            "11",
            "14",
            "15",
            "16",
        ]
        self.check_json["TestingGR"]["SIMAnalyses"][1]["Results"][0]["Publications"] = [
            "21",
            "24",
            "25",
            "26",
        ]
        self.check_json["TestingGR"]["SIMAnalyses"][1]["Results"][1]["Publications"] = [
            "31",
            "34",
            "35",
            "36",
        ]

        # Assess similarity
        assert merge_json == self.check_json
        # Assess no merge conflicts
        assert return_status == 0

    def test_basic_scalar_overwrite(self) -> None:
        """A test that a scalar outside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use ParameterEstimation-SafeLowerChirpMass, ParameterEstimation-SafeUpperChirpMass,
        ParameterEstimation-SafeLowerPrimaryMass and ParameterEstimation-SafeUpperPrimaryMass
        """

        # Case 1 - MRCA sets, head maintains, base changes
        self.mrca_json["ParameterEstimation"]["SafeLowerChirpMass"] = 5
        self.base_json["ParameterEstimation"]["SafeLowerChirpMass"] = 4
        self.head_json["ParameterEstimation"]["SafeLowerChirpMass"] = 5

        # Case 2 - MRCA sets, base maintains, head changes
        self.mrca_json["ParameterEstimation"]["SafeUpperChirpMass"] = 15
        self.head_json["ParameterEstimation"]["SafeUpperChirpMass"] = 16
        self.base_json["ParameterEstimation"]["SafeUpperChirpMass"] = 15

        # Case 3 - MRCA blank, base blank, head adds
        self.head_json["ParameterEstimation"]["SafeUpperPrimaryMass"] = 40

        # Case 4 - MRCA blank, base adds, head blank
        self.base_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 5

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["SafeLowerChirpMass"] = 4
        self.check_json["ParameterEstimation"]["SafeUpperChirpMass"] = 16
        self.check_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 5
        self.check_json["ParameterEstimation"]["SafeUpperPrimaryMass"] = 40

        # Assess similarity
        assert merge_json == self.check_json
        # Assess no merge conflicts
        assert return_status == 0

    def test_scalar_overwrite_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the InferenceSoftware and WaveformApproximant field of two PEResult objects in
        ParameterEstimation-Results for base and head respectively
        """
        # Case 1 : MRCA sets, base changes, head maintains
        self.mrca_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "1"
        self.head_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "5"
        self.base_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "1"

        # Case 2: MRCA sets, base maintains, head changes
        self.mrca_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "2"
        self.base_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "6"
        self.head_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "2"

        # Case 3: MRCA blank, base blank, head changes
        self.head_json["ParameterEstimation"]["Results"][1]["WaveformApproximant"] = "7"

        # Case 4: MRCA blank, base changes, head blank
        self.base_json["ParameterEstimation"]["Results"][1]["InferenceSoftware"] = "8"

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set check values
        self.check_json["ParameterEstimation"]["Results"][0][
            "WaveformApproximant"
        ] = "5"
        self.check_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "6"
        self.check_json["ParameterEstimation"]["Results"][1][
            "WaveformApproximant"
        ] = "7"
        self.check_json["ParameterEstimation"]["Results"][1]["InferenceSoftware"] = "8"

        # Assess similarity
        assert merge_json == self.check_json
        # Assess no merge conflicts
        assert return_status == 0

    def test_scalar_overwrite_inside_object_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the ConfigFile and ResultFile fields of two PEResult objects in
        ParameterEstimation-Results
        """
        # Case 1: MRCA Sets, base maintains, head changes
        self.mrca_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.base_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.head_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }

        # Case 2: MRCA sets, base changes, head maintains
        self.mrca_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.head_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.base_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }

        # Case 3: MRCA blank, base blank, head adds
        self.head_json["ParameterEstimation"]["Results"][1]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }

        # Case 4: MRCA blank, base adds, head blank
        self.base_json["ParameterEstimation"]["Results"][1]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.check_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.check_json["ParameterEstimation"]["Results"][1]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.check_json["ParameterEstimation"]["Results"][1]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:49",
        }

        # Assert similarity
        assert merge_json == self.check_json
        # Assert no merge conflicts
        assert return_status == 0

    def test_scalar_overwrite_inside_object_in_array_inside_object_in_array(
        self,
    ) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the InferenceSoftware field for four PEResult objects, two each in two
        TestingGR-BHMAnalyses Analysis objects
        """
        # Case 1: MRCA set, base maintains, head changes
        self.mrca_json["TestingGR"]["BHMAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "1"
        self.base_json["TestingGR"]["BHMAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "1"
        self.head_json["TestingGR"]["BHMAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "3"

        # Case 2: MRCA set, base changes, head maintains
        self.mrca_json["TestingGR"]["BHMAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "2"
        self.head_json["TestingGR"]["BHMAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "4"
        self.base_json["TestingGR"]["BHMAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "2"

        # Case 3: MRCA blank, base blank, head adds
        self.head_json["TestingGR"]["BHMAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "5"

        # Case 4: MRCA blank, base adds, head blank
        self.base_json["TestingGR"]["BHMAnalyses"][1]["Results"][1][
            "InferenceSoftware"
        ] = "6"

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["TestingGR"]["BHMAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "3"
        self.check_json["TestingGR"]["BHMAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "4"
        self.check_json["TestingGR"]["BHMAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "5"
        self.check_json["TestingGR"]["BHMAnalyses"][1]["Results"][1][
            "InferenceSoftware"
        ] = "6"

        # Assess similarity
        assert merge_json == self.check_json
        # Assess no merge conflicts
        assert return_status == 0

    def test_basic_scalar_conflict(self) -> None:
        """A test that a scalar outside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use ParameterEstimation-SafeLowerChirpMass, ParameterEstimation-SafeUpperChirpMass,
        ParameterEstimation-SafeLowerPrimaryMass, ParameterEstimation-SafeUpperPrimaryMass
        """
        # Case 1: MRCA sets, both base and head change
        self.mrca_json["ParameterEstimation"]["SafeLowerChirpMass"] = 5
        self.head_json["ParameterEstimation"]["SafeLowerChirpMass"] = 4
        self.base_json["ParameterEstimation"]["SafeLowerChirpMass"] = 6

        # Case 2: MRCA blank, both base and head add
        self.head_json["ParameterEstimation"]["SafeUpperChirpMass"] = 14
        self.base_json["ParameterEstimation"]["SafeUpperChirpMass"] = 16

        # Case 3: MRCA sets, both base and head change in the same way
        self.mrca_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 25
        self.head_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 24
        self.base_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 24

        # Case 4: MRCA blank, both base and head set in the same way
        self.head_json["ParameterEstimation"]["SafeUpperPrimaryMass"] = 36
        self.base_json["ParameterEstimation"]["SafeUpperPrimaryMass"] = 36

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"][
            "SafeLowerChirpMass"
        ] = "<<<<<<Base Value:6 - Head Value:4 - MRCA Value:5>>>>>>"
        self.check_json["ParameterEstimation"][
            "SafeUpperChirpMass"
        ] = "<<<<<<Base Value:16 - Head Value:14 - MRCA Value:None>>>>>>"
        self.check_json["ParameterEstimation"]["SafeLowerPrimaryMass"] = 24
        self.check_json["ParameterEstimation"]["SafeUpperPrimaryMass"] = 36

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 1

    def test_scalar_conflict_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the WaveformApproximant and InferenceSoftware fields of two PEResult objects in
        ParameterEstimation-Results
        """
        # Case 1: MRCA sets, both base and head change
        self.mrca_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "1"
        self.base_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "2"
        self.head_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "3"

        # Case 2: MRCA blank, both base and head add
        self.base_json["ParameterEstimation"]["Results"][1]["WaveformApproximant"] = "4"
        self.head_json["ParameterEstimation"]["Results"][1]["WaveformApproximant"] = "5"

        # Case 3: MRCA sets, both base and head change
        self.mrca_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "11"
        self.base_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "12"
        self.head_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "12"

        # Case 4: MRCA blank, both base and head change
        self.base_json["ParameterEstimation"]["Results"][1]["InferenceSoftware"] = "14"
        self.head_json["ParameterEstimation"]["Results"][1]["InferenceSoftware"] = "14"

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"][0][
            "WaveformApproximant"
        ] = "<<<<<<Base Value:2 - Head Value:3 - MRCA Value:1>>>>>>"
        self.check_json["ParameterEstimation"]["Results"][1][
            "WaveformApproximant"
        ] = "<<<<<<Base Value:4 - Head Value:5 - MRCA Value:None>>>>>>"
        self.check_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "12"
        self.check_json["ParameterEstimation"]["Results"][1]["InferenceSoftware"] = "14"

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 1

    def test_scalar_conflict_inside_object_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the ConfigFile and ResultFile fields of two PEResult objects in
        ParameterEstimation-Results
        """
        # Case 1: MRCA sets, both base and head change
        self.mrca_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.base_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }
        self.head_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-3.txt",
            "MD5Sum": "29542515ebea994dab9faee07167a0e3",
            "DateLastModified": "2023/05/02 01:04:54",
        }

        # Case 2: MRCA blank, both base and head add
        self.base_json["ParameterEstimation"]["Results"][1]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }
        self.head_json["ParameterEstimation"]["Results"][1]["ConfigFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-3.txt",
            "MD5Sum": "29542515ebea994dab9faee07167a0e3",
            "DateLastModified": "2023/05/02 01:04:54",
        }

        # Case 3: MRCA sets, both base and head change
        self.mrca_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-1.txt",
            "MD5Sum": "eef9ce62b99d7f164ee1f2cc93867cca",
            "DateLastModified": "2023/04/07 12:31:49",
        }
        self.base_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }
        self.head_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }

        # Case 4: MRCA blank, both base and head change
        self.base_json["ParameterEstimation"]["Results"][1]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }
        self.head_json["ParameterEstimation"]["Results"][1]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        logger.error(json.dumps(merge_json["ParameterEstimation"]["Results"], indent=2))

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"][0]["ConfigFile"] = {
            "Path": (
                "<<<<<<Base Value:CIT:/home/rhiannon.udall/meta-data/meta-data/"
                "tests/files_for_testing/test-file-for-linking-2.txt -"
                " Head Value:CIT:/home/rhiannon.udall/meta-data/meta-data/"
                "tests/files_for_testing/test-file-for-linking-3.txt -"
                " MRCA Value:CIT:/home/rhiannon.udall/meta-data/meta-data/"
                "tests/files_for_testing/test-file-for-linking-1.txt>>>>>>"
            ),
            "MD5Sum": (
                "<<<<<<Base Value:c4cf5fdc9c3efd65ca3d549f188e82cf -"
                " Head Value:29542515ebea994dab9faee07167a0e3 -"
                " MRCA Value:eef9ce62b99d7f164ee1f2cc93867cca>>>>>>"
            ),
            "DateLastModified": (
                "<<<<<<Base Value:2023/04/07 12:31:50 -"
                " Head Value:2023/05/02 01:04:54 -"
                " MRCA Value:2023/04/07 12:31:49>>>>>>"
            ),
        }
        self.check_json["ParameterEstimation"]["Results"][1]["ConfigFile"] = {
            "Path": (
                "<<<<<<Base Value:CIT:/home/rhiannon.udall/meta-data/meta-data/"
                "tests/files_for_testing/test-file-for-linking-2.txt -"
                " Head Value:CIT:/home/rhiannon.udall/meta-data/meta-data/"
                "tests/files_for_testing/test-file-for-linking-3.txt -"
                " MRCA Value:None>>>>>>"
            ),
            "MD5Sum": (
                "<<<<<<Base Value:c4cf5fdc9c3efd65ca3d549f188e82cf -"
                " Head Value:29542515ebea994dab9faee07167a0e3 -"
                " MRCA Value:None>>>>>>"
            ),
            "DateLastModified": (
                "<<<<<<Base Value:2023/04/07 12:31:50 -"
                " Head Value:2023/05/02 01:04:54 -"
                " MRCA Value:None>>>>>>"
            ),
        }
        self.check_json["ParameterEstimation"]["Results"][0]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }
        self.check_json["ParameterEstimation"]["Results"][1]["ResultFile"] = {
            "Path": "CIT:/home/rhiannon.udall/meta-data/meta-data/tests/files_for_testing/test-file-for-linking-2.txt",
            "MD5Sum": "c4cf5fdc9c3efd65ca3d549f188e82cf",
            "DateLastModified": "2023/04/07 12:31:50",
        }

        logger.error(
            json.dumps(self.check_json["ParameterEstimation"]["Results"], indent=2)
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 1

    def test_scalar_conflict_inside_object_in_array_inside_object_in_array(
        self,
    ) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the InferenceSoftware field for four PEResult objects, two each in two
        TestingGR-IMRCTAnalyses Analysis objects
        """
        # Case 1: MRCA sets, both base and head change
        self.mrca_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "1"
        self.base_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "2"
        self.head_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "3"

        # Case 2: MRCA blank, both base and head add
        self.base_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "4"
        self.head_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "5"

        # Case 3: MRCA sets, both base and head change
        self.mrca_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "11"
        self.base_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "12"
        self.head_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "12"

        # Case 4: MRCA blank, both base and head change
        self.base_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][1][
            "InferenceSoftware"
        ] = "14"
        self.head_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][1][
            "InferenceSoftware"
        ] = "14"

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][0][
            "InferenceSoftware"
        ] = "<<<<<<Base Value:2 - Head Value:3 - MRCA Value:1>>>>>>"
        self.check_json["TestingGR"]["IMRCTAnalyses"][0]["Results"][1][
            "InferenceSoftware"
        ] = "<<<<<<Base Value:4 - Head Value:5 - MRCA Value:None>>>>>>"
        self.check_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][0][
            "InferenceSoftware"
        ] = "12"
        self.check_json["TestingGR"]["IMRCTAnalyses"][1]["Results"][1][
            "InferenceSoftware"
        ] = "14"

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 1

    def test_adding_objects_to_array_noninteracting_head(self) -> None:
        """Test 1: add an object to head and do nothing else"""
        self.head_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 0

    def test_adding_objects_to_array_noninteracting_base(self) -> None:
        """Test 2: add an object to head and do nothing else"""
        # Make changes
        self.base_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 0

    def test_adding_objects_to_array_noninteracting_base_and_head(self) -> None:
        """Test 3: add objects to head and base with different UIDs"""
        # Make changes
        self.base_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )
        self.head_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test4", "WaveformApproximant": "2"}
        )

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1"}
        )
        self.check_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test4", "WaveformApproximant": "2"}
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 0

    def test_adding_objects_to_array_interacting_no_conflict(self) -> None:
        """Test that we can track adding objects to an array of objects,
        for cases where the altered nodes are not totally disjoint, but don't conflict"""
        # Case 1: Base and Head add objects with the same UID, alter different scalar fields
        # and Case 2: Base and Head add objects with the same UID, alter the same array field,
        # check array resolution is as expected
        self.base_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1", "Notes": ["1", "2"]}
        )
        self.head_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "InferenceSoftware": "2", "Notes": ["1", "3"]}
        )

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"].append(
            {
                "UID": "Test3",
                "WaveformApproximant": "1",
                "InferenceSoftware": "2",
                "Notes": ["1", "2", "3"],
            }
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 0

    def test_adding_objects_to_array_interacting_conflict(self) -> None:
        """Test that we can track adding objects to an array of objects,
        for cases where the altered nodes will conflict"""
        # Make the changes, intentionally conflicting
        self.base_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "1", "Notes": ["1", "2"]}
        )
        self.head_json["ParameterEstimation"]["Results"].append(
            {"UID": "Test3", "WaveformApproximant": "2", "Notes": ["1", "3"]}
        )

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["Results"].append(
            {
                "UID": "Test3",
                "WaveformApproximant": "<<<<<<Base Value:1 - Head Value:2 - MRCA Value:None>>>>>>",
                "Notes": ["1", "2", "3"],
            }
        )

        # Assess similarity
        assert merge_json == self.check_json
        # Assess that there are indeed merge conflicts
        assert return_status == 1
