"""Methods for interacting with onlinepe"""
import os
from glob import glob

from .utils import (
    setup_logger,
    get_cluster,
    get_url_from_public_html_dir,
    get_number_suffixed_key,
    get_uids_from_object_array,
)

logger = setup_logger()


def get_emfollow_paths(base_dir, sampler, sname):
    # Match all possible basedir* cases
    paths = []
    exts = ["", "-test", "-playground", "-dev"]
    for ext in exts:
        if sampler == "bilby":
            pattern = f"{base_dir}{ext}/.cache/{sampler}/{sname}/*"
        elif sampler == "rapidpe":
            pattern = f"{base_dir}{ext}/.cache/{sampler}/{sname}/"
        paths += glob(pattern)
    return paths


def scrape_bilby_result(path):
    result = {}

    # Try to grab the config
    possible_configs = glob(f"{path}/*config_complete.ini")
    if len(possible_configs) == 1:
        result["ConfigFile"] = {}
        result["ConfigFile"]["Path"] = possible_configs[0]
    elif len(possible_configs) > 1:
        logger.warning("Multiple config files found: unclear how to proceed")
    else:
        logger.info("No config file found!")

    # Try to grab existing result files
    result_files = glob(f"{path}/final_result/*merge_result*")
    if len(result_files) > 1:
        logger.warning(
            f"Found multiple result files {result_files}, unclear how to proceed"
        )
    elif len(result_files) == 1:
        result["ResultFile"] = {}
        result["ResultFile"]["Path"] = result_files[0]
        result["RunStatus"] = "complete"
    elif len(result_files) == 0:
        logger.info(f"No result file found in {path}")
    return result


def scrape_rapidpe_result(path):
    result = {}

    # Try to grab the config
    possible_configs = glob(f"{path}/*rapidpe.ini")
    if len(possible_configs) == 1:
        result["ConfigFile"] = {}
        result["ConfigFile"]["Path"] = possible_configs[0]
    elif len(possible_configs) > 1:
        logger.warning("Multiple config files found: unclear how to proceed")
    else:
        logger.info("No config file found!")

    return result


def scrape_pesummary_pages(top_level, sname, rundir, sampler):
    result = {}

    # Try to find the pesummary outputs
    pes_path = (
        f"/home/{top_level}/public_html/online_pe/{sname}/{sampler}/{rundir}/pesummary"
    )
    samples_path = f"{pes_path}/posterior_samples.h5"
    if os.path.exists(samples_path):
        result["PESummaryResultFile"] = {}
        result["PESummaryResultFile"]["Path"] = samples_path
    pes_home = f"{pes_path}/home.html"
    if os.path.exists(pes_home):
        result["PESummaryPageURL"] = get_url_from_public_html_dir(pes_home)
    return result


def add_onlinepe_information(
    metadata: dict, sname: str, base_path: str = "CIT:/home/emfollow"
) -> dict:
    """Fetch any available online PE information for this superevent

    Parameters
    ==========
    metadata : dict
        The existing metadata dictionary
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

    if cluster.upper() != get_cluster():
        logger.info(f"Unable to fetch onlinePE info as we are not running on {cluster}")
        return {}
    elif os.path.exists(base_dir) is False:
        logger.info(f"Unable to fetch onlinePE info as {base_dir} does not exist")
        return {}

    results = []
    for sampler in ["bilby", "rapidpe"]:
        paths = get_emfollow_paths(base_dir, sampler, sname)
        for path in paths:
            # Path should be of the form /home/emfollow-test/.cache/bilby/S230502m/fast_test
            _, _, top_level, _, _, _, rundir = path.split("/")
            if rundir != "":
                UID = f"{top_level}_{sampler}_{rundir}"
            else:
                UID = f"{top_level}_{sampler}"

            keys_so_far = get_uids_from_object_array(results)
            UID = get_number_suffixed_key(key=UID, keys_so_far=keys_so_far)

            # Initialise result dictionary
            result = dict(
                UID=UID,
                InferenceSoftware=sampler,
            )

            # Scrape the analysis directories
            if sampler == "bilby":
                result.update(scrape_bilby_result(path))
            elif sampler == "rapidpe":
                result.update(scrape_rapidpe_result(path))

            # Scrape the pesummary pages
            result.update(scrape_pesummary_pages(top_level, sname, rundir, sampler))

            # Check if results contains anything
            if "ConfigFile" in result:
                results.append(result)

    update_dict = {}
    update_dict["ParameterEstimation"] = {}
    update_dict["ParameterEstimation"]["Results"] = results

    metadata.update(update_dict)

    return metadata
