import argparse
import hashlib
import logging
import os
import subprocess
from datetime import datetime

from .parser import group_shorthands
from .schema import get_linked_file_keys, get_special_keys

logger = logging.getLogger(__name__)


def standardize_list(inlist):
    inlist = list(set(inlist))
    inlist = sorted(inlist)
    return inlist


def get_subkey(arg, group, suffix):
    for key, val in group_shorthands.items():
        group = group.replace(val, key)
    return arg.replace(group + "_", "").replace("_" + suffix, "")


def get_cluster():
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
    else:
        raise ValueError("Could not identify cluster from `hostname -f` call")


def get_date_last_modified(path):
    mtime = os.path.getmtime(path)
    dtime = datetime.fromtimestamp(mtime)
    return dtime.strftime("%Y/%m/%d %H:%M:%S")


def get_md5sum(path):
    # https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def process_arg(arg, val, metadata, group, ignore_keys):
    if val is None or group in [
        "positional arguments",
        "optional arguments",
        "options",
    ]:
        return

    if any([sk in arg for sk in ignore_keys]):
        return

    dict_to_update = metadata.data[group]

    if "_set" in arg:
        subkey = get_subkey(arg, group, "set")
        dict_to_update[subkey] = val
    elif "_add" in arg:
        subkey = get_subkey(arg, group, "add")
        dict_to_update[subkey].append(val)
        dict_to_update[subkey] = standardize_list(dict_to_update[subkey])
    elif "_remove" in arg:
        subkey = get_subkey(arg, group, "remove")
        try:
            dict_to_update[subkey].remove(val)
        except ValueError:
            raise ValueError(
                f"Request to remove {val} from {group}/{subkey} failed: no match"
            )
    else:
        raise ValueError("Processing failed")


def process_linked_file_path(val):
    linked_file_dict = dict()
    # Expand user for the path
    path = os.path.expanduser(val)
    # Any argument with path in the name should be the path for a linked file
    cluster = get_cluster()
    # Update the path
    linked_file_dict["path"] = f"{cluster}:{path}"
    # Get date last modified
    linked_file_dict["date_last_modified"] = get_date_last_modified(path)
    # Get md5sum
    linked_file_dict["md5sum"] = get_md5sum(path)
    return linked_file_dict


def get_arg_groups_dictionary(args, parser):
    arg_groups = {}
    for group in parser._action_groups:
        group_dict = {a.dest: getattr(args, a.dest, None) for a in group._group_actions}
        arg_groups[group.title] = argparse.Namespace(**group_dict)
    return arg_groups


def process_standard_arguments(arg_groups, metadata, ignore_keys):
    for group, group_args in arg_groups.items():
        for arg, val in group_args.__dict__.items():
            process_arg(arg, val, metadata, group, ignore_keys)


def process_special_arguments(arg_groups, metadata, special_keys, linked_file_keys):
    for key in special_keys:
        special_key_set = {}
        for group, group_args in arg_groups.items():
            if group not in key:
                continue
            for arg, val in group_args.__dict__.items():
                if key in arg:
                    special_key_key = arg.replace(key + "_", "")
                    if "_set" in special_key_key:
                        if val is not None:
                            # Some hacky stuff to determine if this is a linked file
                            # And if it is, keep track of *which* linked file for naming purposes
                            is_linked_file = False
                            for (file_prefix, linked_file_name) in linked_file_keys:
                                # Check if
                                # a) the prefix is the current key, e.g. that we are matching
                                # parameter_estimation_results_... to parameter_estimation_results_...
                                # b) that removing the linked_file_name leaves one of the two possible setter strings
                                # This prevents conflict between e.g. pesummary_result_file and result_file
                                if file_prefix == key and (
                                    special_key_key.replace(linked_file_name, "")
                                    == "_path_set"
                                    or special_key_key.replace(linked_file_name, "")
                                    == "_public_html_set"
                                ):
                                    is_linked_file = True
                                    linked_file_name_to_use = linked_file_name
                                    break
                            # If it is a linked file, only one of two inputs should be possible
                            if is_linked_file:
                                if "path" in special_key_key:
                                    # If the path is being edited, get metadata as well
                                    if (
                                        linked_file_name_to_use
                                        not in special_key_set.keys()
                                    ):
                                        special_key_set[
                                            linked_file_name_to_use
                                        ] = process_linked_file_path(val)
                                    else:
                                        special_key_set[linked_file_name_to_use].update(
                                            process_linked_file_path(val)
                                        )
                                elif "public_html" in special_key_key:
                                    # If the public_html, it's a URL so just add directly
                                    if (
                                        linked_file_name_to_use
                                        not in special_key_set.keys()
                                    ):
                                        special_key_set[
                                            linked_file_name_to_use
                                        ] = dict()
                                    special_key_set[linked_file_name_to_use][
                                        "public_html"
                                    ] = val
                                else:
                                    raise KeyError(
                                        f"The only linked file elements which may be edited are\n\
                                        the path or the public_html path\n\
                                        The key which was to be modified was {special_key_key}"
                                    )
                            else:
                                special_key_set[
                                    special_key_key.replace("_set", "")
                                ] = val
            subkey = key.replace(group + "_", "")
            if len(special_key_set) > 0:

                if "UID" not in special_key_set:
                    raise ValueError(
                        f"To set {key} properties, you must provide the UID"
                    )

                new_run = True
                for item in metadata.data[group][subkey]:
                    if item["UID"] == special_key_set["UID"]:
                        # Hack to make popping work
                        check_internal_update_keys = [
                            kk
                            for kk, vv in special_key_set.items()
                            if type(vv) == dict and kk in item.keys()
                        ]
                        for kk in check_internal_update_keys:
                            item[kk].update(special_key_set.pop(kk))
                        item.update(special_key_set)
                        new_run = False

                if new_run:
                    metadata.data[group][subkey].append(special_key_set)


def process_user_input(args, parser, schema, metadata):
    special_keys = get_special_keys(schema)
    linked_file_keys = get_linked_file_keys(schema, schema)
    arg_groups = get_arg_groups_dictionary(args, parser)
    process_standard_arguments(
        arg_groups,
        metadata,
        ignore_keys=special_keys,
    )
    process_special_arguments(
        arg_groups,
        metadata,
        special_keys=special_keys,
        linked_file_keys=linked_file_keys,
    )
