"""Methods for interacting with onlinepe"""
import os
from glob import glob
import yaml

from .utils import (
    setup_logger,
    get_cluster,
    get_url_from_public_html_dir,
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


def scrape_bayeswave_result(path):
    result = {}

    # Try to grab the config
    possible_configs = sorted(glob(f"{path}/*.ini"))
    # BayesWave produces one config per detector, we can only store one of
    # these: this will be fixed in a future schema.
    if len(possible_configs) > 0:
        result["ConfigFile"] = {}
        result["ConfigFile"]["Path"] = possible_configs[0]

    # Try to grab existing dat files
    result_files = glob(f"{path}/*dat")
    if len(result_files) > 0:
        result["BayeswaveResults"] = {}
        for res_file in result_files:
            det = res_file.split("_")[-1].rstrip(".dat")
            result["BayeswaveResults"][f"{det}PSD"] = {}
            result["BayeswaveResults"][f"{det}PSD"]["Path"] = res_file
            result["RunStatus"] = "complete"
    elif len(result_files) == 0:
        logger.info(f"No result file found in {path}")
    return result


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


def scrape_pesummary_pages(pes_path):
    result = {}

    samples_path = f"{pes_path}/posterior_samples.h5"
    if os.path.exists(samples_path):
        result["PESummaryResultFile"] = {}
        result["PESummaryResultFile"]["Path"] = samples_path
    pes_home = f"{pes_path}/home.html"
    if os.path.exists(pes_home):
        result["PESummaryPageURL"] = get_url_from_public_html_dir(pes_home)
    return result


def add_pe_information(metadata: dict, sname: str) -> dict:
    # Define where to expect results
    directories = glob("/home/pe.o4/public_html/*")
    cluster = "CIT"
    for dir in directories:
        base_path = f"{cluster}:{dir}"
        metadata = add_pe_information_from_base_path(metadata, sname, base_path)


def add_pe_information_from_base_path(
    metadata: dict, sname: str, base_path: str
) -> dict:
    """Fetch any available PE information for this superevent

    Parameters
    ==========
    metadata : dict
        The existing metadata dictionary
    sname : str
        The sname of the superevent to fetch.
    base_path : str
        The path (including cluster name) where PE results are stored.
        This should point to the top-level directory (with snames in
        subdirectories).

    Returns
    =======
    metadata:
        The updated metadata dictionary
    """

    cluster, base_dir = base_path.split(":")

    if cluster.upper() != get_cluster():
        logger.info(f"Unable to fetch PE as we are not running on {cluster}")
        return metadata
    elif os.path.exists(base_dir) is False:
        logger.info(f"Unable to fetch PE as {base_dir} does not exist")
        return metadata

    dirs = sorted(glob(f"{base_dir}/{sname}/*"))
    for dir in dirs:

        update_dict = {}
        update_dict["ParameterEstimation"] = {}
        update_dict["ParameterEstimation"]["Results"] = []

        UID = dir.split("/")[-1]
        # Figure out which sampler we are looking
        content = glob(f"{dir}/*")
        if len(content) == 0:
            logger.info(f"Directory {UID} is empty")
            continue
        elif any(["BayesWave" in fname for fname in content]):
            sampler = "bayeswave"
        elif any(["final_result" in fname for fname in content]):
            sampler = "bilby"
        elif UID == "online":
            sampler = "bilby"
            UID = "online-bilby"
        else:
            logger.info(f"Sampler in {UID} not yet implemented")

        # Initialise result dictionary
        result = dict(
            UID=UID,
            InferenceSoftware=sampler,
        )

        # Read RunInfo
        run_info = f"{dir}/RunInfo.yml"
        if os.path.exists(run_info):
            with open(run_info, "r") as file:
                run_info_data = yaml.safe_load(file)

            # Append the analysts and reviewers to the global PE data
            for key in ["Analysts", "Reviewers"]:
                entries = run_info_data.pop(key, "").split(",")
                update_dict["ParameterEstimation"][key] = entries

            # All other elements are result specific
            result.update(run_info_data)

        # Scrape the online directory
        if UID == "online-bilby":
            result.update(scrape_bilby_result(dir + "/bilby"))
            result.update(scrape_pesummary_pages(dir + "/summary"))
        elif sampler == "bayeswave":
            result.update(scrape_bayeswave_result(dir))

        update_dict["ParameterEstimation"]["Results"] = [result]
        print(update_dict)
        metadata.update(update_dict)

    return metadata
