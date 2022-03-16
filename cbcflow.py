import argparse
import json
import os

import jsonschema


group_shorthands = dict(
    parameter_estimation="parameter_estimation",
    publications="publications",
)

SCHEMA = "cbc-meta-data.schema"
with open(SCHEMA, "r") as file:
    schema = json.load(file)

IGNORE_ARGS = ["info-sname"]


def get_subkey(arg, group, suffix):
    for key, val in group_shorthands.items():
        group = group.replace(val, key)
    return arg.replace(group + "_", "").replace("_" + suffix, "")


class MetaData(object):
    fname_suffix = "json"

    def __init__(self, sname, library, init_data=None):
        self.sname = sname
        self.library = library
        if os.path.exists(self.library_file):
            print("Found existing library file: loading")
            self.load_from_library()
        else:
            if init_data is None:
                self.data = {}
            else:
                self.validate(init_data)
                self.data = init_data

    @property
    def library_file(self):
        return os.path.join(self.library, self.sname + "." + self.fname_suffix)

    def load_from_library(self):
        with open(self.library_file, "r") as file:
            data = json.load(file)

        self.validate(data)
        self.data = data
        self._loaded_data = data.copy()

    def write_to_library(self):
        self.validate(self.data)
        with open(self.library_file, "w") as file:
            json.dump(self.data, file, indent=2)

    def validate(self, data):
        jsonschema.validate(data, schema)

    def construct(self):
        for key, val in schema["properties"].items():
            pass


def process_property(key, value, arg, parser, default_data):
    arg = arg + f"-{key}"
    if value["type"] == "object":
        default_data[key] = {}
        process_property(key, value, arg, parser, default_data[key])

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
                "--" + arg + "-add",
                action="store",
                help=f"Append to the {arg}"
            )
            parser.add_argument(
                "--" + arg + "-remove",
                action="store",
                help=f"Remove from {arg}: note this must be an exact match"
            )
            default_data[key] = []
        elif "$ref" in value["items"]:
            _, l0, l1 = value["items"]["$ref"].split("/")
            ref = schema[l0][l1]
            default_data[key] = []
            for k, v in ref["properties"].items():
                process_property(k, v, arg, parser, {})


parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument("sname", help="The superevent SNAME")
parser.add_argument("--library", default=".", help="The library")


data = {}
for group, subschema in schema["properties"].items():
    arg_group = parser.add_argument_group(group, description=subschema["description"])
    arg = f"{group}"
    data[group] = {}
    for key, value in subschema["properties"].items():
        process_property(key, value, arg, arg_group, data[group])


def process_arg(arg, val, meta_data, group):
    if val is None or group in ["positional arguments", "optional arguments"]:
        return

    if any([sk in arg for sk in special_keys]):
        return

    dict_to_update = meta_data.data[group]

    if "_set" in arg:
        subkey = get_subkey(arg, group, "set")
        dict_to_update[subkey] = val
    elif "_add" in arg:
        subkey = get_subkey(arg, group, "add")
        dict_to_update[subkey].append(val)
        dict_to_update[subkey] = list(set(dict_to_update[subkey]))
    elif "_remove" in arg:
        subkey = get_subkey(arg, group, "remove")
        try:
            dict_to_update[subkey].remove(val)
        except ValueError:
            raise ValueError(f"Request to remove {val} from {group}/{subkey} failed: no match")


special_keys = []


def get_special_keys(schema, prekey=''):
    properties = schema["properties"]
    for key in properties:
        if properties[key]["type"] == "object":
            get_special_keys(schema["properties"][key], prekey=key)
        elif properties[key]["type"] == "array" and "$ref" in properties[key]["items"]:
            special_keys.append(prekey + "_" + key)


get_special_keys(schema)

args = parser.parse_args()
arg_groups = {}
for group in parser._action_groups:
    group_dict={a.dest: getattr(args, a.dest, None) for a in group._group_actions}
    arg_groups[group.title]=argparse.Namespace(**group_dict)

meta_data = MetaData(args.sname, args.library, init_data=data)
for group, args in arg_groups.items():
    for arg, val in args.__dict__.items():
        process_arg(arg, val, meta_data, group)

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
                raise ValueError(f"To set {key} properties, you must provide the UID")

            new_run = True
            for item in meta_data.data[group][subkey]:
                if item["UID"] == special_key_set["UID"]:
                    item.update(special_key_set)
                    new_run = False

            if new_run:
                meta_data.data[group][subkey].append(special_key_set)

print(json.dumps(meta_data.data, indent=4))
meta_data.validate(meta_data.data)
meta_data.write_to_library()
