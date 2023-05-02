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
        We will use ParameterEstimation-SafeLowerChirpMass and ParameterEstimation-SafeUpperChirpMass
        for base and head respectively.
        SafeLowerMassRatio acts as a built in consistency check
        """
        # Set MRCA values for lower and upper
        self.mrca_json["ParameterEstimation"]["SafeLowerChirpMass"] = 5
        self.mrca_json["ParameterEstimation"]["SafeUpperChirpMass"] = 15

        # Set Base and Head to have changed values for different fields respectively
        self.base_json["ParameterEstimation"]["SafeLowerChirpMass"] = 4
        self.head_json["ParameterEstimation"]["SafeUpperChirpMass"] = 16

        # Do the merge
        merge_json, return_status = process_merge_json(
            self.base_json, self.head_json, self.mrca_json, self.schema
        )

        # Set the check values
        self.check_json["ParameterEstimation"]["SafeLowerChirpMass"] = 4
        self.check_json["ParameterEstimation"]["SafeUpperChirpMass"] = 16

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
        # Setup some MRCA values for one result
        # Intentionally leave blank for the other
        self.mrca_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "1"
        self.mrca_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "2"

        # Set head and base changes
        self.head_json["ParameterEstimation"]["Results"][0]["WaveformApproximant"] = "5"
        self.base_json["ParameterEstimation"]["Results"][0]["InferenceSoftware"] = "6"
        self.head_json["ParameterEstimation"]["Results"][1]["WaveformApproximant"] = "7"
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
        We will use the ConfigFile field of two PEResult objects in
        ParameterEstimation-Results
        """
        pass

    def test_scalar_overwrite_inside_object_in_array_inside_object_in_array(
        self,
    ) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the InferenceSoftware field for four PEResult objects, two each in two
        TestingGR-BHMAnalyses Analysis objects
        """
        pass

    def test_basic_scalar_conflict(self) -> None:
        """A test that a scalar outside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use ParameterEstimation-Status
        """
        pass

    def test_scalar_conflict_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the WaveformApproximant field of two PEResult objects in
        ParameterEstimation-Results
        """
        pass

    def test_scalar_conflict_inside_object_inside_object_in_array(self) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the ResultFile field of two PEResult objects in
        ParameterEstimation-Results
        """
        pass

    def test_scalar_conflict_inside_object_in_array_inside_object_in_array(
        self,
    ) -> None:
        """A test that a scalar inside of an object inside of an object in an array can be
        written correctly when it changes from MRCA in either the head or the base,
        but not in both.
        We will use the InferenceSoftware field for four PEResult objects, two each in two
        TestingGR-IMRCTAnalyses Analysis objects
        """
        pass
