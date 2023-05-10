"""Low level methods for intelligently updating json dictionaries"""
from __future__ import annotations

import argparse
import copy
import json
from typing import TYPE_CHECKING, Union, Tuple

from jsonmerge import Merger
from jsonmerge.strategies import ArrayStrategy

from .utils import fill_out_linked_file, standardize_list, setup_logger

if TYPE_CHECKING:
    from .metadata import MetaData

logger = setup_logger()


def form_update_json_from_args(
    args: argparse.Namespace, removal_json: bool = False
) -> dict:
    """Given args output from argparse, make a json to merge into metadata.data

    Parameters
    ==========
    args : `argparse.Namespace`
        The arguments input by the user via argparse
    removal_json : bool, default=False
        Whether or not this is a json for doing removals
        Removal jsons are essentially negative images of the expected change

    Returns
    =======
    update_json : dict
        The json containing the update information
    """
    args_dict = {
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

    # This sorts keys in a way we will use later
    arg_keys_by_depth = sorted(
        list(args_dict.keys()), key=lambda x: (len(x.split("_")), "UID" not in x)
    )

    update_json = dict()

    for arg_key in arg_keys_by_depth:
        working_dict = update_json
        elements = arg_key.split("_")[:-1]
        action = arg_key.split("_")[-1]
        if removal_json and (
            action == "add" or (action == "set" and elements[-1] != "UID")
        ):
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
                        # Just set the element
                        # Note linked files will be modified later on by another function
                        working_dict[element] = args_dict[arg_key]
                    elif action == "add" or action == "remove":
                        # For adding we are making an array of one element to update with
                        working_dict[element] = args_dict[arg_key]
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


def recurse_add_array_merge_options(
    schema: dict,
    is_removal_dict: bool = False,
    is_merge_dict: bool = False,
    idRef: str = "/UID",
) -> None:
    """Add the requisite jsonmerge details to the schema, in prep to make a Merger

    Parameters
    ==========
    schema : dict
        The schema to which the merge options will be added
    is_removal_dict : bool, default=False
        Whether this will be used for performing a removal operation
    is_merge_dict : bool, default=False
        Whether this will be used for a merging operation
    idRef : str, optional
        The key to use as a unique ID reference, defaulting to UID
    """
    if schema["type"] == "array":
        if "$ref" in schema["items"]:
            schema.update(
                dict(mergeStrategy="arrayMergeById", mergeOptions=dict(idRef=idRef))
            )
        elif "type" in schema["items"]:
            if is_removal_dict:
                schema.update(
                    dict(
                        mergeStrategy="remove",
                    )
                )
            elif is_merge_dict:
                schema.update(dict(mergeStrategy="unique"))
            else:
                schema.update(
                    dict(
                        mergeStrategy="append",
                    )
                )
    elif schema["type"] == "object" and "properties" in schema.keys():
        for prop in schema["properties"]:
            recurse_add_array_merge_options(
                schema["properties"][prop],
                is_removal_dict=is_removal_dict,
                is_merge_dict=is_merge_dict,
            )


def get_merger(
    schema: dict,
    for_removal: bool = False,
    for_merging: bool = False,
    idRef: str = "/UID",
) -> Merger:
    """Generate the `jsonmerge.Merger` object we will use

    Parameters
    ==========
    schema : dict
        The base schema, this will be modified then used for the merger
    for_removal : bool, default=False
        If true make a merger which performs removals
    idRef : str, default='/UID'
        The key which serves as a unique ID - this should consistently be /UID
    for_merging : bool, default=False
        If true make a merger which uses the Unique strategy on arrays
        Returning an array that contains one copy of each element in either head or base

    Returns
    =======
    merger : `jsonmerge.Merger`
        The merger which will be used to do the update
    """
    merge_schema = copy.deepcopy(schema)
    recurse_add_array_merge_options(
        merge_schema, is_removal_dict=for_removal, is_merge_dict=for_merging
    )
    for ref in merge_schema["$defs"]:
        recurse_add_array_merge_options(
            merge_schema["$defs"][ref],
            is_removal_dict=for_removal,
            is_merge_dict=for_merging,
            idRef=idRef,
        )

    # Some hackery to get the very specific behavior we want for negative images.
    class RemoveStrategy(ArrayStrategy):
        """A subclass of `jsonmerge.strategies.ArrayStrategy`
        which removes all elements in head from base"""

        def _merge(
            self, walk, base, head, schema, sortByRef=None, sortReverse=None, **kwargs
        ):
            new_array = []
            for array_element in base.val:
                if array_element not in head.val:
                    new_array.append(array_element)

            base.val = new_array

            self.sort_array(walk, base, sortByRef, sortReverse)
            if sortByRef is None:
                base.val.sort()

            return base

        def get_schema(self, walk, schema, **kwargs):
            schema.val.pop("maxItems", None)
            schema.val.pop("uniqueItems", None)

            return schema

    class UniqueStrategy(ArrayStrategy):
        """A subclass of `jsonmerge.strategies.ArrayStrategy`
        which produces a list with all unique elements contained in both head and base"""

        def _merge(
            self, walk, base, head, schema, sortByRef=None, sortReverse=None, **kwargs
        ):
            new_array = list(set(head.val + base.val))

            base.val = new_array

            base.val = sorted(base.val)
            self.sort_array(walk, base, sortByRef, sortReverse)

            return base

        def get_schema(self, walk, schema, **kwargs):
            """An incantation which may or may not be necessary, I'm just not messing with it"""
            schema.val.pop("maxItems", None)
            schema.val.pop("uniqueItems", None)

            return schema

    merger = Merger(
        merge_schema, strategies=dict(remove=RemoveStrategy(), unique=UniqueStrategy())
    )
    return merger


def get_simple_schema_defaults(schema: dict) -> dict:
    """Populates defaults typical objects which don't involve any object referencing

    Parameters
    ==========
    schema : dict
        The schema for which defaults are desired

    Returns
    =======
    dict
        The defaults of properties and sub-properties for the schema
    """
    default_data = {}
    for prop_key, prop_contents in schema["properties"].items():
        if prop_contents["type"] == "object":
            default_data[prop_key] = get_simple_schema_defaults(
                schema["properties"][prop_key]
            )
        elif prop_contents["type"] == "array":
            default_data[prop_key] = []
        elif "default" in prop_contents.keys():
            default_data[prop_key] = prop_contents["default"]
    return default_data


def get_all_schema_def_defaults(schema: dict) -> dict:
    """Provides defaults for referenced objects, indexed by keypath

    Parameters
    ==========
    schema : dict
        The schema for which defaults are desired

    Returns
    =======
    dict
        The defaults of referenced objects in the schema, referenced by keypaths.
        These are the the possible call paths for the referenced object, with each
        level of hierarchy separated by underscores.
    """
    from benedict import benedict

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
    base: Union[dict, list],
    head: Union[dict, list],
    schema_defaults: dict,
    key_path: str = "",
    idRef: str = "UID",
) -> dict:
    """New defaults are necessary if we create a new instance of an object.
    This determines when a new instance is being made, rather than just modifying and old one,
    and then edits the update json accordingly.
    This also deals with linked files when appropriate

    Parameters
    ==========
    base : Union[dict, list]
        The object which will be updated.
        The list case may occur in case of recursion
    head : Union[dict, list]
        The update json, or a component array, before defaults are set.
        The list case may occur in case of recursion.
    schema_defaults : dict
        A set of keypaths which specify defaults for various objects.
    key_path : str, default=""
        The path which will be build up as we descend.
    idRef : str, default="UID"
        The reference ID used to identify different objects.

    Returns
    =======
    dict
        The updated head, with defaults set where appropriate.
    """
    if isinstance(base, dict) and isinstance(head, dict):
        new_head_dict = dict()
        for key in head.keys():
            new_key_path = (key_path + f"_{key}").strip("_")
            if key in base.keys():
                new_head_dict[key] = copy.deepcopy(head[key])
                # If the key is present in both, then continue onwards
                new_head_dict[key] = populate_defaults_if_necessary(
                    base[key],
                    head[key],
                    schema_defaults,
                    new_key_path,
                    idRef=idRef,
                )
            else:
                if isinstance(head[key], dict):
                    new_head_dict[key] = dict()
                    if key_path in schema_defaults.keys():
                        new_head_dict[key].update(schema_defaults[new_key_path])
                    new_head_dict[key].update(head[key])
                if isinstance(head[key], list):
                    new_head_dict[key] = list()
                    new_head_dict[key] = populate_defaults_if_necessary(
                        list(),
                        head[key],
                        schema_defaults,
                        new_key_path,
                        idRef=idRef,
                    )
                else:
                    new_head_dict[key] = populate_defaults_if_necessary(
                        dict(),
                        head[key],
                        schema_defaults,
                        new_key_path,
                        idRef=idRef,
                    )
        return new_head_dict
    elif isinstance(base, list) and isinstance(head, list):
        # In this case we are now at an array
        new_head_array = []
        for head_list_element in head:
            # For each element in head, we want to see if there is anything corresponding yet in base
            if isinstance(head_list_element, dict):
                head_ref = head_list_element[idRef]
                already_exists = False
                for base_list_element in base:
                    if base_list_element[idRef] == head_ref:
                        already_exists = True
                        # It is possible this object already exists but some object within it does not
                        # So recurse further down
                        new_element = populate_defaults_if_necessary(
                            base_list_element,
                            head_list_element,
                            schema_defaults,
                            key_path=key_path,
                        )
                        new_head_array.append(new_element)
                        break
                    else:
                        continue
                if not already_exists:
                    # If there isn't anything corresponding in base, we want to make the default
                    default = copy.copy(schema_defaults[key_path])
                    default.update(head_list_element)
                    new_element = populate_defaults_if_necessary(
                        dict(), default, schema_defaults, key_path=key_path
                    )
                    new_head_array.append(new_element)
            else:
                new_head_array.append(head_list_element)
        return new_head_array
    else:
        return head


def fill_linked_files_if_necessary(head):
    """Go through a dictionary, and if a LinkedFile is spotted,
    fill out md5sum and date of last modification based on Path.

    Parameters
    ==========
    head : dict
        The dictionary to pass through

    Returns
    =======
    dict
        The head with any LinkedFile objects filled out
    """
    if isinstance(head, dict):
        if "Path" in head.keys():
            temp_head = copy.deepcopy(head)
            # This is the case we are looking for
            # If Path is in head.keys(), then head must be a LinkedFile
            path = head["Path"]
            return fill_out_linked_file(path, temp_head)
        else:
            new_head_dict = head
            for key in head.keys():
                new_head_dict[key] = fill_linked_files_if_necessary(new_head_dict[key])
            return new_head_dict
    elif isinstance(head, list):
        new_array = []
        for element in head:
            if isinstance(element, dict):
                new_array.append(fill_linked_files_if_necessary(element))
            else:
                new_array.append(element)
        return new_array
    else:
        return head


def process_user_input(args: argparse.Namespace, metadata: MetaData):
    """Chains commands to take in user args and update the metadata with them

    Parameters
    ==========
    args : `argparse.Namespace`
        The arguments from the argparser with which to update the metadata
    metadata : `cbcflow.metadata.MetaData`
        The metadata to which the update will be applied
    schema : dict
        The schema which describes the metadata
    """
    # Form the add and remove jsons from arguments
    # Adding and subtraction should be done separately
    update_json_add = form_update_json_from_args(args)
    logger.debug(json.dumps(update_json_add, indent=4))
    update_json_remove = form_update_json_from_args(args, removal_json=True)

    metadata.update(update_json_add)
    metadata.update(update_json_remove, is_removal=True)


def process_update_json(
    update_json: dict,
    target_json: dict,
    schema: dict,
    is_removal: bool = False,
    idRef="UID",
):
    """Chains commands to take in and update json and update the metadata with it

    Parameters
    ==========
    update_json : dict
        The dict to update the metadata with
    metadata : `cbcflow.metadata.MetaData`
        The metadata to which the update will be applied
    schema : dict
        The schema which describes the metadata
    is_removal : bool, default=False
        If true, this json will be interpreted as a negative image, and the update will be a removal
    idRef : str, default='/UID'
        The key which serves as a unique ID - for this should consistently be UID
    """
    if not is_removal:
        # If we are adding, we may need defaults
        # Get the schema defaults, and use them to make defaults where necessary in the add json
        schema_defaults = get_all_schema_def_defaults(schema)
        update_json = populate_defaults_if_necessary(
            target_json, update_json, schema_defaults, idRef=idRef
        )
    update_json = fill_linked_files_if_necessary(update_json)

    # generate the merger objects
    merger = get_merger(schema, for_removal=is_removal, idRef=f"/{idRef}")

    # apply merges
    target_json = merger.merge(target_json, update_json)
    return target_json


def process_merge_json(
    base_json: dict, head_json: dict, mrca_json: dict, schema: dict
) -> Tuple[dict, int]:
    """Perform a merge between two different versions of the metadata.
    This requires singificantly different logic than updating with a json.
    But at least we can skip a lot of complicated stuff (defaults, LinkedFiles, etc)

    Parameters
    ==========
    base_json : dict
        The json which is the head (for our purposes largely interchangeable with base)
    head_json : dict
        The json which is the head (for our purposes largely interchangeable with head)
    mrca_json : dict
        The json which for the most recent common ancestor (mrca). Used to parse what is a change
    schema : dict
        The schema for the data.

    Returns
    =======
    dict
        The result of the merge, possibly with conflicts
    int
        The exit value: 0 if no conflicts, 1 if conflicts
    """
    # generate the merger objects
    merger = get_merger(schema, for_merging=True)
    removal_merger = get_merger(schema, for_removal=True)

    # The first step is easy: combine base and head using the unique strategy for arrays
    working_json = merger.merge(base_json, head_json)

    # Now the tricky bits, involving the MRCA
    # The issue is that jsondiff is not really suitable to provide the identification of conflicts we need
    # So, do a recursion to capture
    # a) whether there are any merge conflicts
    # b) whether any list elements need to be removed
    changes_given_mrca, return_status = recurse_capture_changes_from_mrca(
        base_json=base_json, head_json=head_json, mrca_json=mrca_json
    )

    if changes_given_mrca is None:
        changes_given_mrca = dict()

    working_json = removal_merger.merge(working_json, changes_given_mrca)
    return working_json, return_status


def recurse_capture_changes_from_mrca(
    base_json: dict,
    head_json: dict,
    mrca_json: dict,
    refId: str = "UID",
) -> Tuple[Union[dict, None], int]:
    """A recursive function to yield changes of both base and head from mrca
    We want to know when:
    a) scalars change in both
    b) elements of arrays which need to be removed

    Parameters
    ==========
    base_json : dict
        The json which is the head (for our purposes largely interchangeable with base)
    head_json : dict
        The json which is the head (for our purposes largely interchangeable with head)
    mrca_json : dict
        The json which for the most recent common ancestor (mrca). Used to parse what is a change
    refId : str
        The string to use as a unique ID, defaults to 'UID'

    Returns
    =======
    Union[dict, None]
        If no changes are made along this branch, return None. Else return a dict of changes/conflicts
    """
    # Return status starts as 0
    # It will change to 1 if there is a conflict somewhere down the chain
    return_status = 0
    # Two cases - either we are looking at a dict, or we are looking at an array
    if isinstance(head_json, dict):
        working_json = dict()
        for key, val in head_json.items():
            # If it's a dict, loop over key/val pairs
            # Note this will therefore not touch any key/val present in
            # Base or MRCA but not in Head
            # This is good: if a k/v pair is in Base but not Head then it's an addition
            # which should be accepted
            # or it was removed in Head, which shouldn't happen and ought to be reverted
            # if it's in MRCA but not in Base or Head then, well, I guess we *really*
            # wanted to remove it
            if key in base_json.keys() and key in mrca_json.keys():
                # This node has a value in all 3 jsons, so we can descend in a standard way
                if isinstance(val, dict) or isinstance(val, list):
                    (
                        descend_value,
                        descend_return_status,
                    ) = recurse_capture_changes_from_mrca(
                        base_json=base_json[key],
                        head_json=val,
                        mrca_json=mrca_json[key],
                        refId=refId,
                    )
                    if descend_value is None:
                        pass
                    else:
                        working_json[key] = descend_value
                        return_status = max(descend_return_status, return_status)
                else:
                    # This is the case where we are down to a scalar value
                    if base_json[key] == head_json[key]:
                        # If base and head agree
                        # whether that means nothing changed or both changed in the same way
                        # Then there's no change that needs to be made
                        pass
                    elif (
                        base_json[key] == mrca_json[key]
                        and head_json[key] != mrca_json[key]
                    ):
                        # If only head has changed, the baseline merge will cover that already
                        pass
                    elif (
                        base_json[key] != mrca_json[key]
                        and head_json[key] == mrca_json[key]
                    ):
                        # If only base has changed, we can accept that change
                        working_json[key] = base_json[key]
                    else:
                        # This is a true conflict - we must note that with git markers
                        # These will sometimes but not always pass validation?
                        # I think that doesn't matter - we *shouldn't* git_add_and_commit these
                        # So we'll write these conflict files explicitly
                        working_json[key] = (
                            f"<<<<<<Base Value:{base_json[key]} -"
                            f" Head Value:{head_json[key]} -"
                            f" MRCA Value:{mrca_json[key]}>>>>>>"
                        )
                        return_status = 1
            elif key in base_json.keys():
                # This node has a value in the base but not in mrca
                # Thus, it was *added* in both base and head
                # So descend but we need to do something curious for mrca
                if isinstance(val, dict) or isinstance(val, list):
                    # If val is a dict, descend with working_json as a dict
                    (
                        descend_value,
                        descend_return_status,
                    ) = recurse_capture_changes_from_mrca(
                        base_json=base_json[key],
                        head_json=val,
                        mrca_json={},
                        refId=refId,
                    )
                    if descend_value is None:
                        pass
                    else:
                        working_json[key] = descend_value
                        return_status = max(descend_return_status, return_status)
                else:
                    # This is the case where we are down to a scalar value
                    # Now, because we are in the case where something was newly added since MRCA
                    # we can't check against MRCA
                    # So instead we just check if base and head differ
                    # Note that in this case any time where a key is in base but not in head
                    # Will show up in the baseline merge, so we don't need to worry about it
                    if base_json[key] != head_json[key]:
                        # This is a true conflict - we must note that with git markers
                        # These will sometimes but not always pass validation?
                        # I think that doesn't matter - we *shouldn't* git_add_and_commit these
                        # So we'll write these conflict files explicitly
                        working_json[key] = (
                            f"<<<<<<Base Value:{base_json[key]} -"
                            f" Head Value:{head_json[key]} -"
                            f" MRCA Value:{None}>>>>>>"
                        )
                        return_status = 1

            elif key in mrca_json.keys():
                # The case where this key was *removed* in base but not in head
                # This is weird and shouldn't happen in normal operation, so we will pass and
                # let the baseline merge, which will have the k/v, stand
                continue
        if working_json == dict():
            return None, return_status
        else:
            return working_json, return_status
    elif isinstance(head_json, list):
        working_json = list()
        # We will loop through all the elements in the array
        # Three options:
        # The elements are scalar, in which case we operate on the list as an object
        # The elements are dicts, which is to say they are objects to recurse through
        # The elements are heterogeneous, which is bad and should error
        all_scalar = all([not isinstance(x, dict) for x in head_json])
        all_objects = all([isinstance(x, dict) for x in head_json])
        if all_scalar:
            # In the case the elements are all scalar, we want to check whether
            # Something has been removed since MRCA in either head or base
            # So that we can remove it accordingly
            for el in mrca_json:
                if el not in base_json or el not in head_json:
                    working_json.append(el)
        elif all_objects:
            # In the case where we have a list of objects, we identify by UID
            # Then recurse accordingly
            for el in head_json:
                # Loop over elements in head_json
                # If an element only appears in base_json (such that we don't loop over it)
                # that's fine because it will be reflected correctly in the baseline merge
                # If an element appears in MRCA but not head or base, well, that's weird
                # but I guess we accept it
                # Get the elements in MRCA and Base which share a UID with this element
                corresponding_mrca_list = [
                    x for x in mrca_json if x[refId] == el[refId]
                ]
                corresponding_base_list = [
                    x for x in base_json if x[refId] == el[refId]
                ]
                if len(corresponding_base_list) > 1 or len(corresponding_mrca_list) > 1:
                    # Something weird has happened
                    raise KeyError(
                        "A branch has an array with multiple elements sharing a UID;\
                                   that is by definition wrong"
                    )
                elif (
                    len(corresponding_base_list) == 1
                    and len(corresponding_mrca_list) == 1
                ):
                    # The case where the object appears in all 3 lists
                    corresponding_mrca_el = corresponding_mrca_list[0]
                    corresponding_base_el = corresponding_base_list[0]
                    (
                        descend_value,
                        descend_return_status,
                    ) = recurse_capture_changes_from_mrca(
                        base_json=corresponding_base_el,
                        head_json=el,
                        mrca_json=corresponding_mrca_el,
                        refId=refId,
                    )
                    if descend_value is None:
                        pass
                    else:
                        descend_value[refId] = el[refId]
                        working_json.append(descend_value)
                        return_status = max(descend_return_status, return_status)
                elif (
                    len(corresponding_base_list) == 1
                    and len(corresponding_mrca_list) == 0
                ):
                    # The case where an object was added in base and head but wasn't present in MRCA
                    corresponding_base_el = corresponding_base_list[0]
                    (
                        descend_value,
                        descend_return_status,
                    ) = recurse_capture_changes_from_mrca(
                        base_json=corresponding_base_el,
                        head_json=el,
                        mrca_json={},
                        refId=refId,
                    )
                    if descend_value is None:
                        pass
                    else:
                        descend_value[refId] = el[refId]
                        working_json.append(descend_value)
                        return_status = max(descend_return_status, return_status)
                else:
                    # Someone removed this in base?
                    # That's really not supposed to happen
                    # and since the baseline reflects that by just using head
                    # we'll pass
                    pass
        else:
            raise ValueError("List is heterogeneous where it shouldn't be")
        if working_json == list():
            return None, return_status
        else:
            return working_json, return_status
    else:
        return None, 0
