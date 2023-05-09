import logging
import unittest

from cbcflow.database import LocalLibraryDatabase

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
