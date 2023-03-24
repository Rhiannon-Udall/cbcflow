import argparse
import logging
from typing import Tuple

import argcomplete

from .configuration import config_defaults

logger = logging.getLogger(__name__)

IGNORE_ARGS = ["info-sname"]

group_shorthands = dict(
    parameter_estimation="parameter_estimation",
    publications="publications",
)


def process_property(key, value, arg, parser, default_data, schema):
    arg = arg + f"-{key}"
    if value["type"] == "object":
        if "$ref" in value.keys():
            _, l0, l1 = value["$ref"].split("/")
            # Special logic for linked files - only take the path and public html
            # Infer the rest from the path
            if l1 == "LinkedFile":
                # Linked files should have no default data, so this should be fine
                default_data[key] = {}
                parser.add_argument(
                    f"--{arg.replace('_', '-')}-Path-set",
                    action="store",
                    help="Set the file path\
                        this will automatically set the md5sum and data-last-modified,\
                        and infer the cluster",
                )
                parser.add_argument(
                    f"--{arg.replace('_', '-')}-PublicHTML-set",
                    action="store",
                    help="Set a url from which this can be accessed via public_html",
                )
            else:
                ref = schema[l0][l1]
                default_data[key] = []
                for k, v in ref["properties"].items():
                    process_property(k, v, arg, parser, {}, schema)
        else:
            default_data[key] = {}
            process_property(key, value, arg, parser, default_data[key], schema)

    for k, v in group_shorthands.items():
        arg = arg.replace(k, v)
    arg = arg.replace("_", "-")

    if arg in IGNORE_ARGS:
        pass
    elif value["type"] == "string":
        parser.add_argument(
            "--" + arg + "-set",
            action="store",
            help=f"Set the {arg}",
        )
        default = value.get("default", None)
        if default is not None:
            default_data[key] = default
    elif value["type"] == "number":
        parser.add_argument(
            "--" + arg + "-set",
            action="store",
            help=f"Set the {arg}",
            type=float,
        )
        default = value.get("default", None)
        if default is not None:
            default_data[key] = default
    elif value["type"] == "array":
        if value["items"].get("type") == "string":
            parser.add_argument(
                "--" + arg + "-add",
                action="append",
                help=f"Append to the {arg}",
            )
            parser.add_argument(
                "--" + arg + "-remove",
                action="append",
                help=f"Remove from {arg}: note this must be an exact match",
            )
            default_data[key] = []
        elif value["type"] == "number":
            parser.add_argument(
                "--" + arg + "-add",
                action="store",
                help=f"Append to the {arg}",
                type=float,
            )
            parser.add_argument(
                "--" + arg + "-remove",
                action="store",
                help=f"Remove from {arg}: note this must be an exact match",
                type=float,
            )
            default_data[key] = []
        elif "$ref" in value["items"]:
            _, l0, l1 = value["items"]["$ref"].split("/")
            ref = schema[l0][l1]
            default_data[key] = []
            for k, v in ref["properties"].items():
                process_property(k, v, arg, parser, {}, schema)


def build_parser_from_schema(
    parser: argparse.ArgumentParser, schema: dict
) -> Tuple[argparse.ArgumentParser, dict]:
    default_data = {"Sname": None}
    ignore_groups = ["Sname"]
    for group, subschema in schema["properties"].items():
        if group in ignore_groups:
            continue
        arg_group = parser.add_argument_group(
            group, description=subschema["description"]
        )
        arg = f"{group}"
        default_data[group] = {}
        print(subschema)
        for key, value in subschema["properties"].items():
            process_property(key, value, arg, arg_group, default_data[group], schema)
    return parser, default_data


def get_parser_and_default_data(schema):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("sname", help="The superevent SNAME")
    parser.add_argument(
        "--library", default=config_defaults["library"], help="The library"
    )
    parser.add_argument("--schema-version", help="The schema version to use")
    parser.add_argument(
        "--schema-file",
        help="Explicit path to the schema-file. If None (default) the inbuilt schema is used",
        default=config_defaults["gracedb_service_url"],
    )
    parser.add_argument(
        "--no-git-library",
        action="store_true",
        help="If true, do not treat the library as a git repo",
    )
    parser.add_argument(
        "--gracedb-service-url",
        help="The GraceDb service url",
        default=config_defaults["gracedb_service_url"],
    )

    parser, default_data = build_parser_from_schema(parser, schema)
    argcomplete.autocomplete(parser)
    return parser, default_data
