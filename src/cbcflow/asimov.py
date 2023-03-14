import cbcflow
import json

from asimov.event import Event
from asimov import config


class Collector:
    def __init__(self, ledger):
        """
        Collect data from the asimov ledger and write it to a CBCFlow library.
        """
        self.library = ledger.data["hooks"]["cbcflow"]["library location"]
        self.schema_section = ledger.data["hooks"]["cbcflow"]["schema section"]
        self.ledger = ledger

    def run(self):
        """
        Run the hook.
        """

        for event in self.ledger.get_event():
            output = {}
            pe = output[self.schema_section] = []
            metadata = cbcflow.get_superevent(event.meta['ligo']['sname'], library=self.library)
            for analysis in event.productions:
                analysis_output = {}
                analysis_output["uid"] = analysis.name
                analysis_output["InferenceSoftware"] = str(analysis.pipeline)
                analysis_output["RunStatus"] = str(analysis.status)
                if "waveform" in analysis.meta:
                    if "approximant" in analysis.meta["waveform"]:
                        analysis_output["WaveformApproximant"] = str(
                            analysis.meta["waveform"]["approximant"]
                        )
                analysis_output["Notes"] = [analysis.comment]
                if analysis.finished:
                    # TODO: Change this to provide the stored results if uploaded
                    analysis_output["ResultFile"] = analysis.pipeline.collect_assets()
                pe.append(analysis_output)
                metadata.update(output)
            


class Applicator:
    """Apply information from CBCFlow to an asimov event"""

    def __init__(self, ledger):
        self.ledger = ledger
        self.library = ledger.data["hooks"]["cbcflow"]["library location"]

    def run(self, sid=None):

        metadata = cbcflow.get_superevent(sid, library=self.library)
        detchar = metadata.data["DetectorCharacterization"]
        grace = metadata.data["GraceDB"]
        ifos = detchar["RecommendedDetectors"]
        if len(ifos) == 0:
            ifos = grace["Instruments"].split(",")

        quality = {}
        max_f = quality["maximum frequency"] = {}
        min_f = quality["minimum frequency"] = {}

        for ifo in ifos:
            max_f[ifo] = detchar["RecommendedMaximumFrequency"]
            min_f[ifo] = detchar["RecommendedMinimumFrequency"]

        # Data settings
        data = {}
        channels = data["channels"] = {}
        for i, ifo in enumerate(ifos):
            channels[ifo] = detchar["RecommendedChannels"][i]
        data["segment length"] = detchar["RecommendedDuration"]

        # GraceDB Settings
        ligo = {}
        ligo["preferred event"] = grace["PreferredEvent"]
        ligo["sname"] = sid
        ligo["false alarm rate"] = grace["FAR"]

        event_time = grace["GPSTime"]

        output = {
            "name": metadata.data["Sname"],
            "quality": quality,
            "ligo": ligo,
            "data": data,
            "event time": grace["GPSTime"],
        }

        event = Event.from_dict(output)
