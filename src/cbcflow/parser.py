"""Parsing tools, and tools for generating default data"""
import argparse
from typing import Tuple, Union
import re

import argcomplete

from .configuration import config_defaults
from .utils import setup_logger

logger = setup_logger()

IGNORE_ARGS = ["info-sname"]

group_shorthands = dict(
    parameter_estimation="parameter_estimation",
    publications="publications",
)


def str2bool(v: Union[str, bool]) -> bool:
    """Helper type for argparse so we can do set True, etc,
    from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

    Parameters
    ==========
    v : str | bool
        The value to comprehend. If a string will attempt to interpret.

    Returns
    =======
    bool
        The True/False interpretation of the value
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def process_property(
    key: str,
    value: dict,
    arg: str,
    parser: argparse.ArgumentParser,
    default_data: dict,
    schema: dict,
) -> None:
    """Recursively process a schema into parser elements and default data

    Parameters
    ==========
    key : str
        The next key in the recursive chain to construct the property's hierarchy
    value : dict
        The branches of the tree associated with the key
    arg : str
        The recursively constructed argument flag, to add to the parser once a leaf is reached
    parser : `argparser.ArgumentParser`
        The parser which is being built up
    default_data : dict
        The default data which is being built up
    schema : dict
        The schema used in the construction
    """
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
    elif value["type"] == "boolean":
        parser.add_argument(
            "--" + arg + "-set", action="store", help=f"Set the {arg}", type=str2bool
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
    """Adds schema specific arguments to a parser

    Parameters
    ==========
    parser : `argparse.ArgumentParser`
        The initial parser to modify
    schema : dict
        The schema to use in modifying the parser

    Returns
    =======
    `argparse.ArgumentParser`
        The parser with new arguments added based on the schema
    dict
        The default data generated from the schema

    """
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
        for key, value in subschema["properties"].items():
            process_property(key, value, arg, arg_group, default_data[group], schema)
    return parser, default_data


def get_parser_and_default_data(schema: dict):
    """Get a filled out parser, and default data, given a schema

    Parameters
    ==========
    schema : dict
        The schema file to parse through

    Returns
    =======
    `argparse.ArgumentParser`
        A parser object, associated with this schema
    dict
        The default data associated with this schema
    """
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("sname", help="The superevent SNAME", type=sname_string)
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
    parser.add_argument(
        "--yes",
        help="Do not ask for confirmation",
        action="store_true",
    )
    parser.add_argument(
        "--branch-name",
        help="The name of the branch to which commits should be written."
        "If this is not provided and main is the current active branch"
        "A new branch will be constructed with format"
        "user-name-yyyy-mm-dd",
        default=None,
    )

    parser, default_data = build_parser_from_schema(parser, schema)
    argcomplete.autocomplete(parser)
    return parser, default_data


def sname_string(sname):
    """Sanitize and check the given sname string

    This will check there is one unique sname in the given string. Other text
    is ignored (allowing the meta-data filename to be passed) while no match
    or multiple matches will raise an error

    Parameters
    ==========
    sname : str
        The input sname it sanitize and check

    Returns
    =======
    sname
        The unique sname

    """
    matches = re.findall("S[0-9]{6}[a-z]+", sname)
    if len(matches) == 0:
        raise TypeError("Given sname invalid")
    elif len(matches) > 1:
        raise TypeError("Multiple snames given, we can only handle one at a time")
    else:
        return matches[0]
