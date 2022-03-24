#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse

import argcomplete

from .metadata import MetaData
from .schema import get_schema

group_shorthands = dict(
    parameter_estimation="parameter_estimation",
    publications="publications",
)

IGNORE_ARGS = ["info-sname"]


def standardize_list(inlist):
    inlist = list(set(inlist))
    inlist = sorted(inlist)
    return inlist


def get_subkey(arg, group, suffix):
    for key, val in group_shorthands.items():
        group = group.replace(val, key)
    return arg.replace(group + "_", "").replace("_" + suffix, "")


def get_special_keys(schema, prekey=""):
    special_keys = []
    properties = schema["properties"]
    for key in properties:
        if properties[key]["type"] == "object":
            get_special_keys(schema["properties"][key], prekey=key)
        elif properties[key]["type"] == "array" and "$ref" in properties[key]["items"]:
            special_keys.append(prekey + "_" + key)
    return special_keys


def process_arg(arg, val, metadata, group, special_keys):
    if val is None or group in ["positional arguments", "optional arguments"]:
        return

    if any([sk in arg for sk in special_keys]):
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


def process_property(key, value, arg, parser, default_data, schema):
    arg = arg + f"-{key}"
    if value["type"] == "object":
        default_data[key] = {}
        process_property(key, value, arg, parser, default_data[key], schema)

    for k, v in group_shorthands.items():
        arg = arg.replace(k, v)
    arg = arg.replace("_", "-")

    if arg in IGNORE_ARGS:
        pass
    elif value["type"] == "string":
        default = value.get("default", None)
        parser.add_argument(
            "--" + arg + "-set",
            action="store",
            help=f"Set the {arg}",
            default=default,
        )
        default_data[key] = default

    elif value["type"] == "array":
        if value["items"].get("type") == "string":
            parser.add_argument(
                "--" + arg + "-add", action="store", help=f"Append to the {arg}"
            )
            parser.add_argument(
                "--" + arg + "-remove",
                action="store",
                help=f"Remove from {arg}: note this must be an exact match",
            )
            default_data[key] = []
        elif "$ref" in value["items"]:
            _, l0, l1 = value["items"]["$ref"].split("/")
            ref = schema[l0][l1]
            default_data[key] = []
            for k, v in ref["properties"].items():
                process_property(k, v, arg, parser, {}, schema)


def main():
    schema = get_schema()

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("sname", help="The superevent SNAME")
    parser.add_argument("--library", default="library", help="The library")
    parser.add_argument("--print", action="store_true")
    parser.add_argument("--schema-file", help="TESTING ONLY: A path to a schema file")
    parser.add_argument("--schema-version", help="The schema version to use")

    data = {}
    for group, subschema in schema["properties"].items():
        arg_group = parser.add_argument_group(
            group, description=subschema["description"]
        )
        arg = f"{group}"
        data[group] = {}
        for key, value in subschema["properties"].items():
            process_property(key, value, arg, arg_group, data[group], schema)

    special_keys = get_special_keys(schema)

    argcomplete.autocomplete(parser)
    main_args = parser.parse_args()
    arg_groups = {}
    for group in parser._action_groups:
        group_dict = {
            a.dest: getattr(main_args, a.dest, None) for a in group._group_actions
        }
        arg_groups[group.title] = argparse.Namespace(**group_dict)

    metadata = MetaData(
        main_args.sname, main_args.library, init_data=data, schema=schema
    )
    for group, args in arg_groups.items():
        for arg, val in args.__dict__.items():
            process_arg(arg, val, metadata, group, special_keys)

    for key in special_keys:
        special_key_set = {}
        for group, args in arg_groups.items():
            for arg, val in args.__dict__.items():
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

    metadata.validate(metadata.data)
    metadata.write_to_library()
    if main_args.print:
        metadata.pretty_print(metadata.data)
