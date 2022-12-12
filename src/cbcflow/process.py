import copy
import hashlib
import logging
import os
import subprocess
from datetime import datetime

from benedict import benedict
from jsonmerge import Merger
from jsonmerge.strategies import ArrayStrategy

logger = logging.getLogger(__name__)


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


def form_update_json_from_args(args, removal_json=False):
    # This allows for testing with input dicts, which is convenient
    if not isinstance(args, dict):
        args_dict = args.__dict__
    else:
        args_dict = args

    # This sorts keys in a way we will use later
    arg_keys_by_depth = sorted(
        list(args_dict.keys()), key=lambda x: (len(x.split("_")), "UID" not in x)
    )

    update_json = dict()

    for arg_key in arg_keys_by_depth:
        working_dict = update_json
        elements = arg_key.split("_")[:-1]
        action = arg_key.split("_")[-1]
        if removal_json and action == "add":
            # if this json is for removing, skip all the adds (they will be done separately)
            continue
        if not removal_json and action == "remove":
            # if this json is not for removing, skip all the removes (they will be done separately)
            continue
        for ii, element in enumerate(elements):
            if element in working_dict.keys():
                if isinstance(working_dict[element], dict):
                    working_dict = working_dict[element]
                elif isinstance(working_dict[element], list):
                    # In this construction only one UID identified object can be modified at a time
                    # We pre-sorted to make sure it already exists
                    working_dict = working_dict[element][0]
            else:
                if ii == len(elements) - 1:
                    if action == "set":
                        # setting is straightforward
                        working_dict[element] = args_dict[arg_key]
                    elif action == "add" or action == "remove":
                        # For adding we are making an array of one element to update with
                        working_dict[element] = [args_dict[arg_key]]
                    if element == "Path":
                        # This is the special case of linked files
                        path = args_dict[arg_key].split(":")[-1]
                        working_dict["MD5Sum"] = get_md5sum(path)
                        working_dict["DateLastModified"] = get_date_last_modified(path)
                else:
                    # If the next thing will be setting a UID, we need to make the array it will go in
                    if elements[ii + 1] == "UID":
                        working_dict[element] = [dict()]
                        working_dict = working_dict[element][0]
                    # Otherwise we are just going down the dict
                    else:
                        working_dict[element] = dict()
                        working_dict = working_dict[element]
    return update_json


def recurse_add_array_merge_options(schema, is_removal_dict=False):
    if schema["type"] == "array":
        if "$ref" in schema["items"]:
            schema.update(
                dict(mergeStrategy="arrayMergeById", mergeOptions=dict(idRef="/UID"))
            )
        elif "type" in schema["items"]:
            if is_removal_dict:
                schema.update(
                    dict(
                        mergeStrategy="remove",
                    )
                )
            else:
                schema.update(
                    dict(
                        mergeStrategy="append",
                    )
                )
    elif schema["type"] == "object" and "properties" in schema.keys():
        for prop in schema["properties"]:
            recurse_add_array_merge_options(
                schema["properties"][prop], is_removal_dict=is_removal_dict
            )


def get_merger(schema, for_removal=False):
    merge_schema = copy.deepcopy(schema)
    recurse_add_array_merge_options(merge_schema, is_removal_dict=for_removal)
    for ref in merge_schema["$defs"]:
        recurse_add_array_merge_options(
            merge_schema["$defs"][ref], is_removal_dict=for_removal
        )

    class RemoveStrategy(ArrayStrategy):
        def _merge(
            self, walk, base, head, schema, sortByRef=None, sortReverse=None, **kwargs
        ):
            new_array = []
            for array_element in base.val:
                if array_element not in head.val:
                    new_array.append(array_element)

            base.val = new_array

            self.sort_array(walk, base, sortByRef, sortReverse)

            return base

        def get_schema(self, walk, schema, **kwargs):
            schema.val.pop("maxItems", None)
            schema.val.pop("uniqueItems", None)

            return schema

    merger = Merger(merge_schema, strategies=dict(remove=RemoveStrategy()))
    return merger


def get_all_schema_defaults(schema):
    """ """
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


def populate_defaults_if_necessary(
    base, head, schema_defaults, key_path="", refId="UID"
):
    if isinstance(base, dict) and isinstance(head, dict):
        # If both are dicts, we aren't in a place where it makes sense to populate new defaults, so we keep going
        new_head_dict = head
        for key in head.keys():
            if key in base.keys():
                # If the key is present in both, then continue onwards
                new_head_dict[key] = populate_defaults_if_necessary(
                    base[key],
                    head[key],
                    schema_defaults,
                    (key_path + f"_{key}").strip("_"),
                    refId=refId,
                )
        return new_head_dict
    elif isinstance(base, list) and isinstance(head, list):
        # In this case we are now at an array
        new_head_array = []
        for head_list_element in head:
            # For each element in head, we want to see if there is anything corresponding yet in base
            if isinstance(head_list_element, dict):
                head_ref = head_list_element[refId]
                already_exists = False
                for base_list_element in base:
                    if base_list_element[refId] == head_ref:
                        already_exists = True
                        new_head_array.append(head_list_element)
                        break
                    else:
                        continue
                if not already_exists:
                    # If there isn't anything corresponding in base, we want to make the default
                    default = copy.copy(schema_defaults[key_path])
                    default.update(head_list_element)
                    new_head_array.append(default)
            else:
                new_head_array.append(head_list_element)
        return new_head_array
