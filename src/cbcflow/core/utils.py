"""Miscellaneous functions, especially relating to OS I/O"""
import hashlib
from typing import Union, List, Dict
import os
import subprocess
from datetime import datetime
from jsondiff import Symbol
import logging


def configure_logging():
    ch = logging.StreamHandler()
    PRINT_LEVEL = logging.WARNING
    LOGGER_LEVEL = logging.INFO
    print_formatter = logging.Formatter(
        "%(asctime)s CBCFlow %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(print_formatter)
    ch.setLevel(PRINT_LEVEL)

    logfile = "cbcflow.log"
    fh = logging.FileHandler(logfile)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s][%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    fh.setLevel(LOGGER_LEVEL)

    return ch, fh


ch, fh = configure_logging()


def setup_logger(name=None) -> "logging.Logger":
    """Setup a logger for CBCFlow"""

    name = __name__ if name is None else name

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def reset_root_handlers():
    # https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


logger = setup_logger()


def standardize_list(inlist: list) -> list:
    """Creates a list sorted in a standard way

    Parameters
    ==========
    inlist : list
        The input list

    Returns
    =======
    list
        inlist sorted in a way - how doesn't matter, just that it's consistent
    """
    inlist = list(set(inlist))
    inlist = sorted(inlist)
    return inlist


def get_cluster() -> str:
    """
    Get the cluster this is running on

    Returns
    =======
    str
        The cluster name, in quasi-conventional form
    """
    hostname = str(subprocess.check_output(["hostname", "-f"]))
    if "ligo-wa" in hostname:
        return "LHO"
    elif "ligo-la" in hostname:
        return "LLO"
    elif "ligo.caltech" in hostname:
        return "CIT"
    elif hostname == "cl8":
        return "CDF"
    elif "gwave.ics.psu.edu" in hostname:
        return "PSU"
    elif "nemo.uwm.edu" in hostname:
        return "UWM"
    elif "iucaa" in hostname:
        return "IUCAA"
    elif "runner" in hostname:
        # This is not technically correct
        # But also this will only be triggered by
        # gitlab CIs anyways
        return "UWM"
    else:
        print("Could not identify cluster from `hostname -f` call, using fallback")
        return "UNKNOWN"


def get_date_last_modified(path: str) -> str:
    """
    Get the date this file was last modified

    Parameters
    ==========
    path
        A path to the file (on this filesystem)

    Returns
    =======
    str
        The string formatting of the datetime this file was last modified

    """
    mtime = os.path.getmtime(path)
    dtime = datetime.fromtimestamp(mtime)
    return dtime.strftime("%Y/%m/%d %H:%M:%S")


def get_md5sum(path: str) -> str:
    """
    Get the md5sum of the file given the path

    Parameters
    ==========
    path : str
        A path to the file (on this filesystem)

    Returns
    =======
    str
        A string of the md5sum for the file at the path location
    """
    # https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def fill_out_linked_file(path: str, linked_file_dict: Union[dict, None] = None) -> dict:
    """Fill out the contents of a LinkedFile object

    Parameters
    ==========
    path : str
        A path - absolute or relative - to the file on the cluster.
    linked_file_dict : dict, optional
        A pre-existing object to modify, if applicable

    Returns
    =======
    dict
        Either the linked_file_dict updated, or a new linked_file dict
    """

    if linked_file_dict is None:
        linked_file_dict = dict()

    path = os.path.expanduser(path)
    if path[0] != "/":
        # presumably this means it's a relative path, so prepend cwd
        path = os.path.join(os.getcwd(), path)
    working_dict = dict()
    working_dict["Path"] = ":".join([get_cluster(), path])
    working_dict["MD5Sum"] = get_md5sum(path)
    working_dict["DateLastModified"] = get_date_last_modified(path)
    linked_file_dict.update(working_dict)
    return linked_file_dict


def get_dumpable_json_diff(diff: dict) -> dict:
    """jsondiff produces dictionaries where some keys are instances of
    jsondiff.symbols.Symbol, which json.dumps cannot parse.
    This function converts these to a string representation so that they can be parsed.

    Parameters
    ==========
    diff : dict
        The output of jsondiff to parse

    Returns
    =======
    dict
        The output of jsondiff with all symbols parsed to their string representation
    """
    string_rep_diff = dict()
    for key, val in diff.items():
        if isinstance(val, dict):
            val_to_write = get_dumpable_json_diff(val)
        else:
            val_to_write = val
        if isinstance(key, Symbol):
            string_rep_diff[key.label] = val_to_write
        else:
            string_rep_diff[key] = val_to_write
    return string_rep_diff


def get_url_from_public_html_dir(dirpath):
    """Given a path to a directory in public_html, get the corresponding URL (on CIT)"""
    # Ensure the path is well formed
    if dirpath[0] != "/":
        dirpath = "/" + dirpath

    elements = dirpath.split("/")

    # Check if it is in public_html
    if "public_html" not in elements:
        logger.info(
            "Given dirpath was not in public HTML, so URL cannot be extrapolated from it"
            " returning the path"
        )
        return dirpath

    # First get the stuff that comes after public_html - this structure will stay the same
    public_html_index = elements.index("public_html")
    url_extension = "/".join(elements[public_html_index + 1 :])

    # next get the user in ldas form
    url_user = elements[2]

    # Combine them
    dir_url = f"https://ldas-jobs.ligo.caltech.edu/~{url_user}/{url_extension}"
    return dir_url


def get_number_suffixed_key(key: str, keys_so_far: list) -> str:
    """We want unique keys - this will suffix a number to make one if necessary

    Parameters
    ==========
    key : str
       The key to check and possibly modify
    keys_so_far : list
        The keys so far to reference for uniqueness

    Returns
    =======
    str
        The key, suffixed if necessary for uniqueness
    """
    overlapping_keys = [x for x in keys_so_far if key in x]
    if key in overlapping_keys:
        suffixes = [x.split("_")[-1] for x in overlapping_keys if "_" in x]
        highest_integer_not_yet_taken = 1
        for suffix in suffixes:
            if suffix.isdigit():
                if int(suffix) == highest_integer_not_yet_taken:
                    highest_integer_not_yet_taken += 1
        new_key = f"{key}_{highest_integer_not_yet_taken}"
        return new_key
    else:
        return key


def get_uids_from_object_array(array: List[Dict], refId: str = "UID") -> list:
    """Get the list of unique IDs from the object array

    Parameters
    ==========
    array : List[Dict]
        A list of objects each with a unique ID (the refId)
    refId : str
        The reference ID which uniquely identifies objects, in normal operation UID

    Returns
    =======
    list
        The list of UIDs reflected in the object array
    """
    list_of_uids = []
    for entry in array:
        try:
            list_of_uids.append(entry[refId])
        except KeyError as e:
            raise KeyError(
                (
                    f"Failed with key error {e}\n"
                    f"Why is there an object without {refId} in this key-tracked array?"
                )
            )
    return list_of_uids


def get_uid_index_for_object_array(
    uid: str, array: List[Dict], refId: str = "UID"
) -> int:
    """Get the index where the object with this uid can be found

    Parameters
    ==========
    uid : str
        The UID corresponding to the object you want to find
    array : List[Dict]
        A list of objects each with a unique ID (the refId)
    refId : str
        The reference ID which uniquely identifies objects, in normal operation UID
    """
    list_of_uids = get_uids_from_object_array(array=array, refId=refId)
    return list_of_uids.index(uid)
