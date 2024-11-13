"""Methods for interacting with PE results stored on CIT"""
import os
from glob import glob
import yaml
import gitlab
import copy
from typing import Union, Tuple, Dict

from ..core.utils import (
    setup_logger,
    get_cluster,
    get_url_from_public_html_dir,
    get_uids_from_object_array,
)
from ..core.metadata import MetaData

logger = setup_logger(name=__name__)


def scrape_bayeswave_result(path: str):
    """Read in results from standardised BayesWave output directory

    Parameters
    ==========
    path : str
        The path to the run directory

    Returns
    =======
    dict
        The update dictionary associated with this analysis
    """
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
    """Read in results from standardised bilby output directory

    Parameters
    ==========
    path : str
        The path to the run directory

    Returns
    =======
    dict
        The update dictionary associated with this analysis
    """
    result = {}

    detstr = ""

    # Try to grab the config
    possible_configs = glob(f"{path}/*config_complete.ini")
    if len(possible_configs) == 1:
        result["ConfigFile"] = {}
        result["ConfigFile"]["Path"] = possible_configs[0]
        # Read waveform approximant out of config file
        # I am going to just read the file directly rather than use configparse
        # Since bilby_pipe has its own special parser that we don't want to import right now
        with open(possible_configs[0], "r") as file:
            config_lines = file.readlines()
        waveform_approximant_lines = [
            x
            for x in config_lines
            if "waveform-approximant=" in x and "injection" not in x
        ]
        if len(waveform_approximant_lines) == 1:
            result["WaveformApproximant"] = (
                waveform_approximant_lines[0].split("=")[1].strip()
            )
        else:
            logger.warning(
                "Multiple waveform approximants given\n"
                "Or no waveform approximant given\n"
                "Is this a valid config file?"
            )
        detector_lines = [x for x in config_lines if x.startswith("detectors")]
        if len(detector_lines) == 1:
            detstr = detector_lines[0].split("=")[1].strip()
            # We only want the full network analysis when using the coherence test
            # this can be formatted like "detectors=["H1", 'L1']"
            for bad in [" ", "[", "]", ",", "'", '"']:
                detstr = detstr.replace(bad, "")
            # Alphabetize detstr
            detstr = "".join(
                sorted([detstr[2 * ii : 2 * ii + 2] for ii in range(len(detstr) // 2)])
            )
        else:
            logger.warning(
                "Multiple or no entries found for detectors\n"
                "Is this a valid config file?"
            )
    elif len(possible_configs) > 1:
        logger.warning("Multiple config files found: unclear how to proceed")
    else:
        logger.info("No config file found!")

    # Try to grab existing result files
    result_files = glob(f"{path}/final_result/*{detstr}_merge_result*hdf5")

    # Try looking for a single merge file
    if len(result_files) == 0:
        result_files = glob(f"{path}/result/*{detstr}_merge_result*hdf5")

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
    """Read in results from standardised pesummary output directory

    Parameters
    ==========
    path : str
        The path to the run directory

    Returns
    =======
    dict
        The update dictionary associated with this analysis
    """
    result = {}

    samples_path = f"{pes_path}/samples/posterior_samples.h5"
    if os.path.exists(samples_path):
        result["PESummaryResultFile"] = {}
        result["PESummaryResultFile"]["Path"] = samples_path
    pes_home = f"{pes_path}/home.html"
    if os.path.exists(pes_home):
        result["PESummaryPageURL"] = get_url_from_public_html_dir(pes_home)
    return result


def add_pe_information(
    metadata: "MetaData", sname: str, pe_rota_token: Union[str, None] = None
) -> "MetaData":
    """Top level function to add pe information for a given sname

    Parameters
    ==========
    metadata : `cbcflow.metadata.MetaData`
        The metadata object being updated
    sname : str
        The Sname for the metadata
    pe_rota_token : str, optional
        The string representation of the token for accessing the PE rota repository

    Returns
    =======
    `cbcflow.metadata.MetaData`
        The updated metadata object
    """

    # Define where to expect results
    directories = glob("/home/pe.o4/public_html/*")
    cluster = "CIT"

    # Iterate over directories
    for directory in directories:
        base_path = f"{cluster}:{directory}"
        metadata = add_pe_information_from_base_path(metadata, sname, base_path)

    if pe_rota_token is not None:
        determine_pe_status(sname, metadata, pe_rota_token)


def determine_pe_status(
    sname: str, metadata: "MetaData", pe_rota_token: str, gitlab_project_id: int = 14074
):
    """Check the PE rota repository to determine the status of the PE for this event

    Parameters
    ==========
    sname : str
        The sname for this event
    metadata : `cbcflow.metadata.MetaData`
        The metadata object to update with the status of the PE
    pe_rota_token : str
        The token to use when accessing the PE ROTA repository to check status
    gitlab_project_id : int, optional
        The project id to identify the PE ROTA repository - hardcoded to the O4a repository
    """
    CI_SERVER_URL = "https://git.ligo.org/"
    PRIVATE_TOKEN = pe_rota_token
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
    metadata: "MetaData", sname: str, base_path: str
) -> "MetaData":
    """Fetch any available PE information for this superevent

    Parameters
    ==========
    metadata : `cbcflow.metadata.MetaData`
        The existing metadata object
    sname : str
        The sname of the superevent to fetch.
    base_path : str
        The path (including cluster name) where PE results are stored.
        This should point to the top-level directory (with snames in
        subdirectories).

    Returns
    =======
    `cbcflow.metadata.MetaData`
        The updated metadata object
    """

    cluster, base_directory = base_path.split(":")

    if cluster.upper() != get_cluster():
        logger.info(f"Unable to fetch PE as we are not running on {cluster}")
        return metadata
    elif os.path.exists(base_directory) is False:
        logger.info(f"Unable to fetch PE as {base_directory} does not exist")
        return metadata

    # Get existing results, analysts list, reviewers list
    existing_results_dict = {
        res["UID"]: res for res in metadata["ParameterEstimation"]["Results"]
    }
    existing_analysts = metadata["ParameterEstimation"]["Analysts"]
    existing_reviewers = metadata["ParameterEstimation"]["Reviewers"]
    existing_notes = metadata["ParameterEstimation"]["Notes"]
    current_status = metadata["ParameterEstimation"]["Status"]

    all_analysts = copy.copy(existing_analysts)
    all_reviewers = copy.copy(existing_reviewers)
    all_notes = copy.copy(existing_notes)

    update_dictionary = {"ParameterEstimation": {"Results": []}}

    if current_status == "unstarted" and existing_results_dict != {}:
        update_dictionary["ParameterEstimation"]["Status"] = "ongoing"

    directories = sorted(glob(f"{base_directory}/{sname}/*"))
    if "EventInfo.yml" in [x.split("/")[-1] for x in directories]:
        event_info_yml = os.path.join(base_directory, sname, "EventInfo.yml")
        event_info = process_event_info_yml(event_info_yml)
        if "Notes" in event_info:
            all_notes += event_info["Notes"]
        if "Status" in event_info:
            update_dictionary["ParameterEstimation"]["Status"] = event_info["Status"]
    else:
        event_info = dict()

    for directory in [
        directory for directory in directories if os.path.isdir(directory)
    ]:
        # For each directory under this superevents heading...
        uid = directory.split("/")[-1]
        existing_result = existing_results_dict.get(uid, dict(UID=uid))

        # ... generate the update dictionary for the PEResult
        result_update, result_analysts, result_reviewers = generate_result_update(
            directory, existing_result, uid
        )

        # Build up list of all analysts and reviewers
        all_analysts += result_analysts
        all_reviewers += result_reviewers

        # Add this result update to the full update dictionary
        if len(list(result_update.keys())) > 0:
            update_dictionary["ParameterEstimation"]["Results"].append(result_update)

    # Add only reviewers and analysts not yet
    new_analysts = list(set(all_analysts) - set(existing_analysts))
    new_reviewers = list(set(all_reviewers) - set(existing_reviewers))
    new_notes = list(set(all_notes) - set(existing_notes))

    if "IllustrativeResult" in event_info:
        update_dictionary["ParameterEstimation"]["IllustrativeResult"] = event_info[
            "IllustrativeResult"
        ]
    if "SkymapReleaseResult" in event_info:
        update_dictionary["ParameterEstimation"]["SkymapReleaseResult"] = event_info[
            "SkymapReleaseResult"
        ]
    update_dictionary["ParameterEstimation"]["Analysts"] = new_analysts
    update_dictionary["ParameterEstimation"]["Reviewers"] = new_reviewers
    update_dictionary["ParameterEstimation"]["Notes"] = new_notes

    metadata.update(update_dict=update_dictionary)

    for pointer_name in ["IllustrativeResult", "SkymapReleaseResult"]:
        if pointer_name in metadata["ParameterEstimation"]:
            result_update = regularize_result_pointer_case(
                metadata, pointer_name=pointer_name
            )
            metadata.update(result_update)

    return metadata


def generate_result_update(
    directory: str, existing_result: dict, uid: str
) -> Tuple[dict, list, list]:
    """Process a directory for updates to the corresponding PEResult

    Parameters
    ==========
    directory : str
        The directory corresponding to the PEResult
    existing_result : dict
        The PEResult object which already exists, to be updated
    uid : str
        The UID of the PEResult object

    Returns
    =======
    dict
        The update dictionary for the PEResult
    list
        The list of analysts corresponding to this PEResult
    list
        The list of reviewers corresponding to this PEResult
    """
    result_update = dict(UID=uid)

    # Figure out which sampler we are looking
    content = glob(f"{directory}/*")
    if len(content) == 0:
        logger.debug(f"Directory {directory} is empty")
        return dict(), list(), list()
    elif any(["BayesWave" in fname for fname in content]):
        sampler = "bayeswave"
        result_update.update(scrape_bayeswave_result(directory))
    else:
        directories = [s.split("/")[-1] for s in content]
        if "summary" in directories:
            result_update.update(
                scrape_pesummary_pages(os.path.join(directory, "summary"))
            )
        if "bilby" in directories:
            sampler = "bilby"
            result_update.update(scrape_bilby_result(directory + f"/{sampler}"))
        elif "parallel_bilby" in directories:
            sampler = "parallel_bilby"
            result_update.update(scrape_bilby_result(directory + f"/{sampler}"))
        else:
            logger.info(f"Sampler in {uid} not yet implemented")
            return dict(), list(), list()

    result_update["InferenceSoftware"] = sampler

    run_info_data = process_run_info_yml(
        path_to_run_info=f"{directory}/RunInfo.yml",
    )

    for key in ["Deprecated", "ReviewStatus"]:
        # If these aren't set do nothing
        if key in run_info_data.keys():
            result_update[key] = run_info_data[key]

    result_update["Notes"] = list(
        set(run_info_data.get("Notes", [])) - set(existing_result.get("Notes", []))
    )

    return (
        result_update,
        run_info_data.get("Analysts", list()),
        run_info_data.get("Reviewers", list()),
    )


def process_run_info_yml(
    path_to_run_info: str,
) -> Dict[str, Union[list, str, bool]]:
    """Extracts information from a RunInfo.yml file

    Parameters
    ==========
    path_to_run_info : str
        The path to the RunInfo.yml file

    Returns
    =======
    dict
        A dictionary containing processed contents of the RunInfo, including:
        - Reviewers
        - Analysts
        - Notes
        - Deprecated
        - ReviewStatus
    """
    if os.path.exists(path_to_run_info):
        with open(path_to_run_info, "r") as file:
            try:
                run_info_data = yaml.safe_load(file)
            except Exception:
                logger.warning(f"Yaml file {path_to_run_info} corrupted")
                return dict()
    else:
        return dict()

    for key in ["Analyst", "Reviewer", "Note"]:
        # correct when people don't put plurals correctly
        if key in run_info_data:
            run_info_data[key + "s"] = run_info_data.pop(key)

    # Process information for Analysts, Reviewers, and Notes
    # Each of these may be screwed up in some way by the writer of the RunInfo
    for key in ["Analysts", "Reviewers", "Notes"]:
        if key in run_info_data:
            yaml_content = run_info_data.pop(key)
            yaml_elements = process_ambiguous_yaml_list(yaml_content=yaml_content)
            run_info_data[key] = yaml_elements

        # ReviewStatus is an enum, and hence expects specific values, which the PE expert may mess up
        # This drops everything to lowercase, to fix one such failure mode
    if "ReviewStatus" in run_info_data:
        if isinstance("ReviewStatus", bool):
            # If a reviewer says the ReviewStatus is "False" they presumably mean it failed
            # And if they say it's true they presumably mean it passed
            # While this is not guaranteed, it's preferable to failing entirely, or softly ignoring it
            run_info_data["ReviewStatus"] = (
                "pass" if run_info_data["ReviewStatus"] else "fail"
            )

        run_info_data["ReviewStatus"] = run_info_data["ReviewStatus"].lower()
        if run_info_data["ReviewStatus"] in ["passed"]:
            # Catch a specific case which has gone wrong in the past
            # We'll add more to this list if people invent new ways to get things wrong
            run_info_data["ReviewStatus"] = "pass"
        if run_info_data["ReviewStatus"] in ["not reviewed"]:
            run_info_data["ReviewStatus"] = "unstarted"

    return run_info_data


def process_event_info_yml(
    path_to_event_info_yml: str,
) -> Dict[str, Union[list, str, bool]]:
    """Extracts information from an EventInfo.yml file"""
    if os.path.exists(path_to_event_info_yml):
        with open(path_to_event_info_yml, "r") as file:
            try:
                event_info_data = yaml.safe_load(file)
            except Exception:
                logger.warning(f"Yaml file {path_to_event_info_yml} corrupted")
                return dict()
    else:
        return dict()

    for key in ["IllustrativeResult", "Status", "SkymapReleaseResult"]:
        info_update = event_info_data.get(key, 0)
        if info_update is None:
            # The case where the key is present but has no contents
            event_info_data.pop(key)
        elif info_update == 0:
            # The case where the key isn't even present, so nothing to worry about
            pass

    if "Notes" in event_info_data:
        yaml_content = event_info_data.pop("Notes")
        yaml_elements = process_ambiguous_yaml_list(yaml_content=yaml_content)
        event_info_data["Notes"] = yaml_elements

    return event_info_data


def regularize_result_pointer_case(
    metadata: MetaData, pointer_name="IllustrativeResult"
) -> dict:
    illustrative_result = metadata["ParameterEstimation"][pointer_name]
    pe_result_uids = get_uids_from_object_array(
        metadata["ParameterEstimation"]["Results"]
    )
    if illustrative_result in pe_result_uids:
        return dict()
    elif illustrative_result.lower() in [x.lower() for x in pe_result_uids]:
        correct_uid = pe_result_uids[
            [x.lower() for x in pe_result_uids].index(illustrative_result.lower())
        ]
        return {"ParameterEstimation": {pointer_name: correct_uid}}
    else:
        logger.warning(
            f"{pointer_name} key {illustrative_result} is not in list of UIDs {pe_result_uids}"
        )
        return dict()


def process_ambiguous_yaml_list(yaml_content: Union[str, list]) -> list:
    """Process heterogeneous yaml contents smoothly

    Parameters
    ==========
    yaml_content : Union[str, list]
        The content of the yaml, which should be either a string or a list
        If its neither it will be ignored

    Returns
    =======
    list
        The list of elements in the yaml
    """
    if isinstance(yaml_content, str):
        yaml_elements = set([x.lstrip(" ").strip("-") for x in yaml_content.split(",")])
    elif isinstance(yaml_content, list):
        yaml_elements = set([x.lstrip() for x in yaml_content])
    else:
        yaml_elements = list()
    return yaml_elements
