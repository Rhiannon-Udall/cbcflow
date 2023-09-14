import cbcflow

from asimov.event import Event
from asimov import logger


class Applicator:
    """Apply information from CBCFlow to an asimov event"""

    def __init__(self, ledger):
        hook_data = ledger.data["hooks"]["applicator"]["cbcflow"]
        self.ledger = ledger
        self.library = cbcflow.database.LocalLibraryDatabase(
            hook_data["library location"]
        )
        self.library.git_pull_from_remote(automated=True)

    def run(self, sid=None):

        metadata = cbcflow.get_superevent(sid, library=self.library)
        detchar = metadata.data["DetectorCharacterization"]
        grace = metadata.data["GraceDB"]
        ifos = detchar["RecommendedDetectors"]
        participating_detectors = detchar["ParticipatingDetectors"]
        quality = {}
        max_f = quality["maximum frequency"] = {}
        min_f = quality["minimum frequency"] = {}

        # Data settings
        data = {}
        channels = data["channels"] = {}
        frame_types = data["frame types"] = {}
        # NOTE there are also detector specific quantities "RecommendedStart/EndTime"
        # but it is not clear how these should be reconciled with

        ifo_list = []

        for ifo in ifos:
            # Grab IFO specific quantities
            ifo_name = ifo["UID"]
            ifo_list.append(ifo_name)
            if "RecommendedDuration" in detchar.keys():
                data["segment length"] = int(detchar["RecommendedDuration"])
            if "RecommendedMaximumFrequency" in ifo.keys():
                max_f[ifo_name] = ifo["RecommendedMaximumFrequency"]
            if "RecommendedMinimumFrequency" in ifo.keys():
                min_f[ifo_name] = ifo["RecommendedMinimumFrequency"]
            if "RecommendedChannel" in ifo.keys():
                channels[ifo_name] = ifo["RecommendedChannel"]
            if "FrameType" in ifo.keys():
                frame_types[ifo_name] = ifo["FrameType"]

        recommended_ifos_list = list()
        if ifo_list != []:
            recommended_ifos_list = ifo_list
        else:
            recommended_ifos_list = participating_detectors
            logger.info(
                "No detchar recommended IFOs provided, falling back to participating detectors"
            )

        # GraceDB Settings
        ligo = {}
        for event in grace["Events"]:
            if event["State"] == "preferred":
                ligo["preferred event"] = event["UID"]
                ligo["false alarm rate"] = event["FAR"]
                event_time = event["GPSTime"]
        ligo["sname"] = sid

        output = {
            "name": metadata.data["Sname"],
            "quality": quality,
            "ligo": ligo,
            "data": data,
            "interferometers": recommended_ifos_list,
            "event time": event_time,
        }

        event = Event.from_dict(output)
        self.ledger.add_event(event)