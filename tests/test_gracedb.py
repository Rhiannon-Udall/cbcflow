import logging
import unittest

from cbcflow.inputs import gracedb


class TestGraceDB(unittest.TestCase):
    def cleanup(self):
        pass

    def setUp(self) -> None:
        pass

    def test_add_common_gevent_metadata_preferred(self):
        gevent_data = {
            "graceid": "G111111",
            "pipeline": "gstlal",
            "gpstime": 111111111.1,
            "far": 1e-8,
            "instruments": "H1L1",
            "offline": False,
            "labels": ["EARLY_WARNING"],
        }
        gevent_dict, sevent_dict = gracedb.add_common_gevent_metadata(
            gevent_data=gevent_data, preferred=False
        )
        assert gevent_dict == {
            "UID": "G111111",
            "Pipeline": "gstlal",
            "GPSTime": 111111111.1,
            "FAR": 1e-8,
            "State": "neighbor",
            "SearchType": "low latency",
            "EarlyWarning": True,
        }
        assert sevent_dict == {}

    def test_add_common_gevent_metadata_not_preferred(self):
        gevent_data = {
            "graceid": "G111111",
            "pipeline": "gstlal",
            "gpstime": 111111111.1,
            "far": 1e-8,
            "instruments": "H1L1",
            "offline": True,
            "labels": [],
        }
        gevent_dict, sevent_dict = gracedb.add_common_gevent_metadata(
            gevent_data=gevent_data, preferred=True
        )
        assert gevent_dict == {
            "UID": "G111111",
            "Pipeline": "gstlal",
            "GPSTime": 111111111.1,
            "FAR": 1e-8,
            "State": "preferred",
            "SearchType": "offline",
            "EarlyWarning": False,
        }
        assert sevent_dict == {"Instruments": "H1L1"}

    def test_add_pastro_data_all_provided(self):
        pastro_data = {"Terrestrial": 0.01, "BBH": 0.98, "NSBH": 0.01, "BNS": 0.00}
        update_dict = gracedb.add_pastro_gevent_metadata(pastro_data=pastro_data)
        assert update_dict == {
            "Pastro": 0.99,
            "Pbbh": 0.98,
            "Pnsbh": 0.01,
            "Pbns": 0.00,
        }

    def test_add_pastro_data_no_terrestrial(self):
        pastro_data = {"BBH": 0.98, "NSBH": 0.01, "BNS": 0.00}
        update_dict = gracedb.add_pastro_gevent_metadata(pastro_data=pastro_data)
        assert update_dict == {"Pbbh": 0.98, "Pnsbh": 0.01, "Pbns": 0.00}

    def test_add_pastro_data_none_provided(self):
        pastro_data = {}
        update_dict = gracedb.add_pastro_gevent_metadata(pastro_data=pastro_data)
        assert update_dict == {}

    def test_add_embright_all_provided(self):
        embright_data = {"HasNS": 0.9, "HasRemnant": 0.1, "HasMassGap": 0.1}
        update_dict = gracedb.add_embright_gevent_metadata(
            embright_data=embright_data, pipeline_embright=False
        )
        assert update_dict == {"HasNS": 0.9, "HasRemnant": 0.1, "HasMassGap": 0.1}

    def test_add_embright_none_provided(self):
        embright_data = {}
        update_dict = gracedb.add_embright_gevent_metadata(
            embright_data=embright_data, pipeline_embright=False
        )
        assert update_dict == {}

    def test_add_pipeline_embright_all_provided(self):
        embright_data = {"HasNS": 0.9, "HasRemnant": 0.1, "HasMassGap": 0.1}
        update_dict = gracedb.add_embright_gevent_metadata(
            embright_data=embright_data, pipeline_embright=True
        )
        assert update_dict == {
            "PipelineHasNS": 0.9,
            "PipelineHasRemnant": 0.1,
            "PipelineHasMassGap": 0.1,
        }

    def test_add_pipeline_embright_none_provided(self):
        embright_data = {}
        update_dict = gracedb.add_embright_gevent_metadata(
            embright_data=embright_data, pipeline_embright=True
        )
        assert update_dict == {}

    # def test_cwb_trigger_gevent_metadata(self):
