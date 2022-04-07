import argparse

import argcomplete

IGNORE_ARGS = ["info-sname"]

group_shorthands = dict(
    parameter_estimation="parameter_estimation",
    publications="publications",
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


def build_parser_from_schema(parser, schema):
    default_data = {"sname": None}
    ignore_groups = ["sname"]
    for group, subschema in schema["properties"].items():
        if group in ignore_groups:
            continue
        arg_group = parser.add_argument_group(
            group, description=subschema["description"]
        )
        arg = f"{group}"
        default_data[group] = {}
        for key, value in subschema["properties"].items():
            process_property(key, value, arg, arg_group, default_data[group], schema)
    return parser, default_data


def get_parser_and_default_data(schema):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("sname", help="The superevent SNAME")
    parser.add_argument("--library", default="library", help="The library")
    parser.add_argument("--schema-version", help="The schema version to use")
    parser.add_argument("--schema-file", help="TESTING ONLY: A path to a schema file")
    parser.add_argument(
        "--no-git-library",
        action="store_true",
        help="If true, do not treat the library as a git repo",
    )
    parser.add_argument(
        "--gracedb-service-url",
        help="The GraceDb service url",
        default="https://gracedb-test.ligo.org/api/",
    )

    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--update", action="store_true", help="Update the metadata for the event"
    )
    actions.add_argument(
        "--print", action="store_true", help="Print the metadata for the event"
    )
    actions.add_argument(
        "--push-to-gracedb",
        action="store_true",
        help="Push changes to the metadata to GraceDB",
    )
    actions.add_argument(
        "--pull-from-gracedb",
        action="store_true",
        help="Pull changes to the metadata from GraceDB",
    )

    parser, default_data = build_parser_from_schema(parser, schema)
    argcomplete.autocomplete(parser)
    return parser, default_data
