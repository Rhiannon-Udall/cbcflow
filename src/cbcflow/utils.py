import hashlib
import os
import subprocess
from datetime import datetime


def standardize_list(inlist: list) -> list:
    """Creates a list sorted in a standard way"""
    inlist = list(set(inlist))
    inlist = sorted(inlist)
    return inlist


def get_cluster() -> str:
    """
    Get the cluster this is running on
    """
    # TODO if a better api is implemented use it
    # Also maybe add NIK?
    # I can't even access that cluster to test, so...
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
        raise ValueError("Could not identify cluster from `hostname -f` call")


def get_date_last_modified(path: str) -> str:
    """
    Get the date this file was last modified

    Parameters
    -------------
    path
        A path to the file (on this filesystem)

    Returns
    -------------
    date_last_modified : str
        The string formatting of the datetime this file was last modified

    """
    mtime = os.path.getmtime(path)
    dtime = datetime.fromtimestamp(mtime)
    return dtime.strftime("%Y/%m/%d %H:%M:%S")


def get_md5sum(path: str) -> str:
    """
    Get the md5sum of the file given the path

    Parameters
    ----------
    path : str
        A path to the file (on this filesystem)

    Returns
    --------------
    md5sum : str
        A string of the md5sum for the file at the path location
    """
    # https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def fill_out_linked_file(path: str, linked_file_dict: dict = dict()) -> dict:
    """Fill out the contents of a LinkedFile object

    Parameters
    ==========
    path : str
        A path - absolute or relative - to the file on the cluster.
    linked_file_dict : dict
        A pre-existing object to modify, if applicable

    Returns
    =======
    dict
        Either the linked_file_dict updated, or a new linked_file dict
    """
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