import argparse

from .parser import group_shorthands
from .schema import get_special_keys


def standardize_list(inlist):
    inlist = list(set(inlist))
    inlist = sorted(inlist)
    return inlist


def get_subkey(arg, group, suffix):
    for key, val in group_shorthands.items():
        group = group.replace(val, key)
    return arg.replace(group + "_", "").replace("_" + suffix, "")


def process_arg(arg, val, metadata, group, ignore_keys):
    if val is None or group in ["positional arguments", "optional arguments"]:
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


def process_special_arguments(arg_groups, metadata, special_keys):
    for key in special_keys:
        special_key_set = {}
        for group, group_args in arg_groups.items():
            for arg, val in group_args.__dict__.items():
                if key in arg:
                    special_key_key = arg.replace(key + "_", "")
                    if "_set" in special_key_key:
                        if val is not None:
                            special_key_set[special_key_key.replace("_set", "")] = val
            subkey = key.replace(group + "_", "")
            if len(special_key_set) > 0:

                if "UID" not in special_key_set:
                    raise ValueError(
                        f"To set {key} properties, you must provide the UID"
                    )

                new_run = True
                for item in metadata.data[group][subkey]:
                    if item["UID"] == special_key_set["UID"]:
                        item.update(special_key_set)
                        new_run = False

                if new_run:
                    metadata.data[group][subkey].append(special_key_set)


def process_user_input(args, parser, schema, metadata):
    special_keys = get_special_keys(schema)
    arg_groups = get_arg_groups_dictionary(args, parser)
    process_standard_arguments(arg_groups, metadata, ignore_keys=special_keys)
    process_special_arguments(arg_groups, metadata, special_keys=special_keys)
