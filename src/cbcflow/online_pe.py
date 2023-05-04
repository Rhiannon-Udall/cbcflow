"""Methods for interacting with onlinepe"""
import os
from glob import glob

from .utils import setup_logger, get_cluster

logger = setup_logger()


def fetch_bilby_onlinepe(sname, base_dir):
    # Match all basedir* cases
    pattern = f"{base_dir}*/bilby/{sname}/*"
    paths = glob(pattern)
    results = []
    for path in paths:
        _, top_level, _, _, _, rundir = path.split("/")
        UID = "onlinepe_bilby_{rundir}"
        result = dict(UID=UID)

        # Try to grab existing result files
        result_files = glob(f"{path}/final_result/*merge_result*")
        if len(result_files) > 1:
            logger.info(f"Found multiple result files {result_files}, taking the first")
            result["ResultFile"] = result_files[0]
            result["RunStatus"] = "complete"
        elif len(result_files) == 1:
            result["ResultFile"] = result_files[0]
            result["RunStatus"] = "complete"
        elif len(result_files) == 0:
            logger.info("No result file found")

        # Try to find the pesummary pages
        pes_path = f"/home/{top_level}/public_html/online_pe/{sname}/bilby/{rundir}/pesummary/"
        if os.path.exists(pes_path + "/samples/



def fetch_onlinepe_information(sname: str, base_path: str = "CIT:/home/emfollow") -> dict:
    """Fetch any available online PE information for this superevent

    Parameters
    ==========
    sname : str
        The sname of the superevent to fetch.
    base_path : str
        The path (including cluster name) where emfollow tests are performed.
        This should point to the top-level directory (with, e.g. bilby as a
        subdirectory).

    Returns
    =======
    dict
        An update dictionary to apply to the metadata, containing the onlinePE info.
    """

    cluster, base_dir = base_path.split(":")

    metadata = {}

    if cluster.upper() != get_cluster():
        logger.info(f"Unable to fetch onlinePE info as we are not running on {cluster}")
        return {}
    elif os.path.exists(base_dir) is False:
        logger.info(f"Unable to fetch onlinePE info as {base_dir} does not exist")
        return {}

    metadata.update(fetch_bilby_onlinepe(sname, base_dir)



