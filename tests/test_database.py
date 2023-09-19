import logging
import unittest

from cbcflow.core.database import LocalLibraryDatabase
from cbcflow.core.metadata import MetaData

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestDatabase(unittest.TestCase):
    def cleanup(self):
        pass

    def setUp(self) -> None:
        # Our test library has some events which should be included, and some which should not be
        # This is the comparison of ones which *should* be included
        self.superevents_satisfying_conditions = ["S230331e", "S230401h", "S230402dv"]
        # The others should be excluded because:
        # S230227hp -> Created before March 1st 2023
        # S230403ae -> Preferred FAR = 3.2e-10 > 1e-16
        # S230404hb -> Created after April 3rd
        # S230404jc -> Created after April 3rd
        self.library_path = "tests/library_for_testing/"
        self.working_library = LocalLibraryDatabase(self.library_path)

    def test_index_generation(self):
        """Check whether the index generates correctly"""
        self.working_library.working_index = (
            self.working_library.generate_index_from_metadata()
        )
        superevents_in_index = self._check_events_in_library_json(
            self.working_library.working_index
        )
        assert superevents_in_index == self.superevents_satisfying_conditions

    def test_changing_metadata_nongracedb(self):
        """A test of changing metadata directly, but not affecting the downselection criteria"""

        # Load in one piece of metadata to exemplify one case
        s230331e_metadata = MetaData(
            sname="S230331e", local_library=self.working_library
        )

        # Get the other metadata by bulk loading when we invoke downselected_metadata_dict
        assert (
            sorted(list(self.working_library.downselected_metadata_dict.keys()))
            == self.superevents_satisfying_conditions
        )
        assert (
            self.working_library.downselected_metadata_dict["S230331e"].data["Info"][
                "Labels"
            ]
            == []
        )
        assert (
            self.working_library.downselected_metadata_dict["S230401h"].data["Info"][
                "Labels"
            ]
            == []
        )

        # Change S230331e in some trivial way
        s230331e_metadata.update({"Info": {"Labels": ["A test label #1"]}})

        logger.error(self.working_library.metadata_dict["S230331e"].data["Info"])

        # Change S2304041h similarly
        self.working_library.metadata_dict["S230401h"].update(
            {"Info": {"Labels": ["A test label #2"]}}
        )

        # Check both have been changed in the downselected metadata
        assert self.working_library.downselected_metadata_dict["S230331e"].data["Info"][
            "Labels"
        ] == ["A test label #1"]
        assert self.working_library.downselected_metadata_dict["S230401h"].data["Info"][
            "Labels"
        ] == ["A test label #2"]

    @staticmethod
    def _check_events_in_library_json(json):
        """Helper function to get the snames of events in the library index

        Parameters
        ==========
        json : dict
            The library index json dict

        Returns
        =======
        list
            The superevents located in the library json
        """
        events_in_library = []
        for superevent in json["Superevents"]:
            events_in_library.append(superevent["UID"])
        return events_in_library
