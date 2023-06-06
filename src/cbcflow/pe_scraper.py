"""Methods for interacting with PE results stored on CIT"""
import os
from glob import glob
import yaml
import gitlab

from .utils import (
    setup_logger,
    get_cluster,
    get_url_from_public_html_dir,
)

logger = setup_logger()


def scrape_bayeswave_result(path):
    """Read in results from standardised BayesWave output directory"""
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
    """Read in results from standardised bilby output directory"""
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
    result_files = glob(f"{path}/final_result/*merge_result*hdf5")

    # Try looking for a single merge file
    if len(result_files) == 0:
        result_files = glob(f"{path}/result/*merge_result*hdf5")

    # Deal with pbilby cases
    if len(result_files) == 0:
        result_files = glob(f"{path}/result/*result*hdf5")

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


def scrape_pesummary_pages(pes_path):
    """Read in results from standardised pesummary output directory"""
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
    """Top level function to add pe information for a given sname"""

    # Define where to expect results
    directories = glob("/home/pe.o4/public_html/*")
    cluster = "CIT"

    # Iterate over directories
    for dir in directories:
        base_path = f"{cluster}:{dir}"
        metadata = add_pe_information_from_base_path(metadata, sname, base_path)

    determine_pe_status(sname, metadata)


def determine_pe_status(sname, metadata, gitlab_project_id=14074):

    CI_SERVER_URL = "https://git.ligo.org/"
    PRIVATE_TOKEN = os.environ["PRIVATE_TOKEN"]
    CI_PROJECT_ID = str(gitlab_project_id)
    gl = gitlab.Gitlab(CI_SERVER_URL, private_token=PRIVATE_TOKEN)
    project = gl.projects.get(CI_PROJECT_ID)
    issues = project.issues.list(get_all=True)
    issue_dict = {issue.title: issue for issue in issues}
    if sname in issue_dict:
        if issue_dict[sname].state == "closed":
            status = "complete"
        else:
            status = "ongoing"

    update_dict = {"ParameterEstimation": {"Status": status}}
    metadata.update(update_dict)


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

    # Get existing results
    results_dict = {
        res["UID"]: res for res in metadata.data["ParameterEstimation"]["Results"]
    }

    dirs = sorted(glob(f"{base_dir}/{sname}/*"))
    for dir in dirs:

        # Initialise an empty update dictionary
        update_dict = {}
        update_dict["ParameterEstimation"] = {}
        update_dict["ParameterEstimation"]["Results"] = []

        UID = dir.split("/")[-1]

        # Initialise result dictionary
        result = dict(
            UID=UID,
        )

        # Figure out which sampler we are looking
        content = glob(f"{dir}/*")
        if len(content) == 0:
            logger.debug(f"Directory {dir} is empty")
            continue
        elif any(["BayesWave" in fname for fname in content]):
            sampler = "bayeswave"
            result.update(scrape_bayeswave_result(dir))
        else:
            directories = [s.split("/")[-1] for s in content]

            if "summary" in directories:
                result.update(scrape_pesummary_pages(dir + "/summary"))

            if "bilby" in directories:
                sampler = "bilby"
                result.update(scrape_bilby_result(dir + f"/{sampler}"))
            elif "parallel_bilby" in directories:
                sampler = "parallel_bilby"
                result.update(scrape_bilby_result(dir + f"/{sampler}"))
            else:
                logger.info(f"Sampler in {UID} not yet implemented")
                continue

        result["InferenceSoftware"] = sampler

        # Read RunInfo
        run_info = f"{dir}/RunInfo.yml"
        if os.path.exists(run_info):
            with open(run_info, "r") as file:
                try:
                    run_info_data = yaml.safe_load(file)
                except Exception:
                    logger.warning(f"Yaml file {run_info} corrupted")
                    run_info_data = {}

            # Append the analysts and reviewers to the global PE data
            for key in ["Analysts", "Reviewers"]:
                if key in run_info_data:
                    existing_entries = set(metadata.data["ParameterEstimation"][key])
                    entries_string = run_info_data.pop(key)
                    if entries_string is not None:
                        entries = entries_string.split(",")
                        entries = set([ent.lstrip(" ") for ent in entries])
                        new_entries = list(entries - existing_entries)
                        update_dict["ParameterEstimation"][key] = new_entries

            # Treat notes as a set
            if UID in results_dict and "Notes" in run_info_data:
                existing_entries = set(results_dict[UID]["Notes"])
                entries = set(run_info_data["Notes"])
                new_entries = list(entries - existing_entries)
                run_info_data["Notes"] = new_entries

            # Update the result with the info data
            result.update(run_info_data)

        update_dict["ParameterEstimation"]["Results"] = [result]
        metadata.update(update_dict)

    return metadata
