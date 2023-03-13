class Collector:

    def __init__(self, ledger):
        """
        Collect data from the asimov ledger and write it to a CBCFlow library.
        """

        self.ledger = ledger

    def run(self):
        """
        Run the hook.
        """

        for event in self.ledger.get_event():
            output = {}
            pe = output["ParameterEstimation"] = []
            
            for analysis in event.productions:
                analysis_output = {}
                analysis_output['uid'] = analysis.name
                analysis_output['InferenceSoftware'] = str(analysis.pipeline)
                analysis_output['RunStatus'] = str(analysis.status)
                if "waveform" in analysis.meta:
                    if "approximant" in analysis.meta['waveform']:
                        analysis_output['WaveformApproximant'] = str(analysis.meta['waveform']['approximant'])
                analysis_output['Notes'] = [analysis.comment]
                if analysis.finished:
                    analysis_output['ResultFile'] = analysis.pipeline.collect_assets()
                pe.append(analysis_output)
