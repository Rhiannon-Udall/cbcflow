import copy
import hashlib
import logging
import os
import subprocess
from collections import OrderedDict
from datetime import datetime

from benedict import benedict

from .parser import group_shorthands

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


def process_user_input(args, metadata, schema, parser):
    # Get the args which are changes in the schema, as opposed to control args
    # TODO make this list a variable somewhere
    active_args = {
        key: val
        for key, val in args.__dict__.items()
        if key
        not in [
            "sname",
            "library",
            "schema_file",
            "no_git_library",
            "gracedb_service_url",
            "update",
            "print",
            "pull_from_gracedb",
        ]
        and (val is not None)
    }

    # Run the new process on the arguments which will actually be used
    process_changes(active_args, metadata.data, schema)


def update_reduced_uids(
    reduced_uids,
    analyses_list,
    uid_value,
    reduced_key,
    full_key,
    defaults_for_refs,
    precursor=None,
):
    """ """
    # Analysis index tracks what position in the analysis list is correct
    analysis_index = None
    for jj, analysis in enumerate(analyses_list):
        if analysis["UID"] == uid_value:
            # If it's present, store the index
            analysis_index = jj
    # If it wasn't found, make a nested dict with the corresponding UID
    # And add the newly formed index to reduced_uids, with None as the second part of the tuple
    if analysis_index is None:
        # If making it anew, get the correct defaults
        default_dict = copy.deepcopy(defaults_for_refs[full_key])
        default_dict["UID"] = uid_value
        analyses_list.append(default_dict)
        reduced_uids[reduced_key] = (len(analyses_list) - 1, precursor)
    # Otherwise, store the old index in reduced_uids
    else:
        reduced_uids[reduced_key] = (analysis_index, precursor)


def process_action(metadata, key_path, action, value):
    if action == "set":
        if key_path.split("_")[-1] == "Path":
            metadata[key_path] = f"{get_cluster()}:{value}"
            md5sum_path = key_path.replace("Path", "MD5Sum")
            metadata[md5sum_path] = get_md5sum(value)
            date_last_modified_path = key_path.replace("Path", "DateLastModified")
            metadata[date_last_modified_path] = get_date_last_modified(value)
        else:
            metadata[key_path] = value
    elif action == "add":
        metadata[key_path].append(value)
        metadata[key_path] = standardize_list(metadata[key_path])
    elif action == "remove":
        metadata[key_path].remove(value)
        metadata[key_path] = standardize_list(metadata[key_path])
    else:
        raise ValueError(f"Could not understand action {action}")


def get_sub_dict_from_precursor(nested_dict, reduced_uids, precursor):
    precursor_index, precursors_precursor = reduced_uids[precursor]
    if precursors_precursor is None:
        return nested_dict[precursor][precursor_index]
    else:
        sub_dict = get_sub_dict_from_precursor(
            nested_dict, reduced_uids, precursors_precursor
        )
        return sub_dict[precursor][precursor_index]


def get_all_schema_defaults(schema):
    if not isinstance(schema, benedict):
        schema = benedict(schema, keypath_separator="_")

    # keypaths is the object of all the keypaths in the schema
    keypaths = schema.keypaths()
    # referencing_keypaths gives the schema object for each keypath that has a $ref in it
    referencing_schema_keypaths = benedict(
        {keypath: schema[keypath] for keypath in keypaths if "$ref" in keypath}
    )
    # referencing_call_keypaths turns these into Metadata like keypaths
    referencing_call_keypaths = benedict(
        {
            key.replace("$defs_", "")
            .replace("properties_", "")
            .replace("items_", "")
            .replace("$ref", "")
            .strip("_"): val
            for key, val in referencing_schema_keypaths.items()
        }
    )

    # This gives a dict for which each def has a corresponding set of reference keypaths
    # So, e.g. every time LinkedFile gets referenced
    linked_file_call_keypaths = referencing_call_keypaths.invert()

    # While there are still paths which are prefixed by a reference keep going
    some_to_expand = True
    while some_to_expand:
        # Assume there aren't any until proven otherwise - this will overshoot one round but oh well
        some_to_expand = False
        # Iterate over each linked_file, and the list of keypaths that reference it
        for linked_file, call_keypaths in linked_file_call_keypaths.items():
            # Make a list of the unexpanded keypaths to remove at the end of the loop
            keypaths_to_remove = list()
            # Iterate over keypaths in the list (copy to allow modification)
            for call_keypath in copy.copy(call_keypaths):
                # Now, compare to each linked file, and the keypaths it includes
                for (
                    linked_file,
                    reference_keypaths,
                ) in linked_file_call_keypaths.items():
                    # We are looking for cases where the first element of the path (e.g. PEResult)
                    # Matches the last element of a file def (e.g. #/$defs/PEResult)
                    if call_keypath.split("_")[0] == linked_file.split("/")[-1]:
                        # when this happens, first add this keypath to the removal list
                        keypaths_to_remove.append(call_keypath)
                        # Now, for each case in the referenced file def, expand out the list
                        # e.g. PEResult occurs both for the ParameterEstimation_Results object *and*
                        # the TestingGR_Analyses_TGRAnalysis_Results object
                        # so for each of these all 3 further refs (config, result, pesummary) are needed
                        for reference_path in reference_keypaths:
                            # Extend the path by joining, and add to the list
                            extended_path = "_".join(
                                [reference_path] + call_keypath.split("_")[1:]
                            )
                            call_keypaths.append(extended_path)
                        # The fact that we triggered this conditional means there may still be work to do
                        # In case of nested refs
                        some_to_expand = True
            # Remove repeats
            keypaths_to_remove = standardize_list(keypaths_to_remove)
            # Remove the now extended results
            for keypath in keypaths_to_remove:
                call_keypaths.remove(keypath)

    # Get the reinversion - so the ref object for every path, and make it str:str
    linked_file_for_keypath = {
        key: val[0] for key, val in linked_file_call_keypaths.invert().items()
    }

    linked_file_defaults = dict()
    # Now, for every ref object get the associated Default Metadata
    for def_path in linked_file_call_keypaths.keys():
        # Get the keypath format
        call_path_notation = def_path.replace("#", "").replace("/", "_").strip("_")
        # Get the schema data for the linked file
        schema_for_def = schema[call_path_notation]
        defaults = {}
        for key, val in schema_for_def["properties"].items():
            # Assign the various defaults
            if val["type"] == "array":
                defaults[key] = val.get("default", [])
            else:
                defaults[key] = val.get("default", None)
        # set defaults for each ref object
        linked_file_defaults[def_path] = {
            key: val for key, val in defaults.items() if val is not None
        }

    defaults_for_keypath = {
        key: linked_file_defaults[val] for key, val in linked_file_for_keypath.items()
    }

    return defaults_for_keypath


def process_changes(changes_dict, metadata, schema):
    if not isinstance(metadata, benedict):
        metadata = benedict(metadata, keypath_separator="_")

    # Make a list of all UID flags
    uids_list = []
    for key, val in changes_dict.items():
        if "UID" in key:
            uids_list.append(("_".join(key.split("_")[:-2]), val))

    # Sort by increasing depth, convert to OrderedDict
    uids_list.sort(key=lambda x: len(x[0].split("_")))
    uids_dict = OrderedDict(uids_list)

    # Get the default metadata for ref objects that may be invoked
    defaults_by_keypath = get_all_schema_defaults(schema)

    # reduced_uids will be a more useful set of keys, connecting paths for nested analyses
    # and also indices for each analysis, as identified by the UID
    reduced_uids = OrderedDict()

    for ii, key in enumerate(uids_dict):
        # Cleanup changes_dict while we're in this loop
        del changes_dict[key + "_UID_set"]

        # Some hacky stuff to find nested analysis keys
        precursor = None

        # We've sorted, so we only need to go through the preceding keys
        for jj in reversed(range(ii)):
            if list(uids_dict)[jj] in key:
                # If a previous key is in this key, it's the precursor
                # We only want the longest precursor
                # If depth ever exceeds 2 this will still work accordingly
                precursor = list(uids_dict)[jj]
                break

        # In this case, depth of analyses is 1
        # So, no precursor, trace down directly from metadata
        if precursor is None:
            analyses_list = metadata[key]
            reduced_uids_key = key
        # Depth > 1
        # There is a precursor, so trace down from it to get the analyses list
        else:
            # Get the part of the key that goes past the precursor
            reduced_uids_key = key.replace(precursor, "").strip("_")
            # Get the dict using the precursor's place in the analyses list
            analysis_sub_dict = get_sub_dict_from_precursor(
                metadata, reduced_uids, precursor
            )
            # If the precursor hasn't had any results made yet, make an empty list
            if reduced_uids_key not in analysis_sub_dict:
                analysis_sub_dict[reduced_uids_key] = []
            # The list of analyses to check through will be that list
            analyses_list = analysis_sub_dict[reduced_uids_key]

        # Get the value to assign
        uid_value = uids_dict[key]

        # Update the reduced_uids dict
        update_reduced_uids(
            reduced_uids,
            analyses_list,
            uid_value,
            reduced_uids_key,
            key,
            defaults_by_keypath,
            precursor=precursor,
        )

    for key, val in changes_dict.items():
        # Get the action and the path to the action
        action = key.split("_")[-1]
        key_path = "_".join(key.split("_")[:-1])

        # Search for what UIDs will be used to arrive at the field we want to change
        relevant_uids = []
        for uid_path in uids_dict:
            if uid_path in key_path:
                relevant_uids.append(uid_path)

        # Sort by ascending order of size
        relevant_uids.sort(key=lambda x: len(x))

        # If no UIDs are relevant we can modify directly by keypath
        if relevant_uids == []:
            process_action(metadata, key_path, action, val)

        # If there are UIDs to follow
        else:
            # Start from the top
            dict_under_consideration = metadata
            # Loop over the uids to follow
            for ii, uid_path in enumerate(relevant_uids):
                if ii > 0:
                    # If there's a precursor, reduce down
                    reduced_uid_path = uid_path.replace(
                        relevant_uids[ii - 1], ""
                    ).strip("_")
                else:
                    reduced_uid_path = uid_path
                # Get the index in the analyses_list
                analysis_index, _ = reduced_uids[reduced_uid_path]
                # Grab the analysis dict, make it a benedict
                dict_under_consideration = benedict(
                    dict_under_consideration[reduced_uid_path][analysis_index],
                    keypath_separator="_",
                )
                # reduce the key down
                reduced_key = key_path.replace(uid_path, "").strip("_")
            # perform this action
            process_action(dict_under_consideration, reduced_key, action, val)
