import importlib.resources as importlib_resources
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_schema_path(version):
    ddir = importlib_resources.files("cbcflow") / "schema"
    files = ddir.glob("*schema")
    matches = []
    for file in files:
        if version in str(file):
            matches.append(file)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        raise ValueError(f"No schema file for version {version} found")
    elif len(matches) > 1:
        raise ValueError("Too many matching schema files found")


def get_schema(args=None):
    if args is None:
        args = sys.argv
    VERSION = "v1"

    # Bootstrap the schema file if requested
    fileflag = "--schema-file"
    versionflag = "--schema-version"
    if fileflag in args:
        schema_file = Path(args[args.index(fileflag) + 1])
    elif versionflag in args:
        version = args[args.index(versionflag) + 1]
        schema_file = get_schema_path(version)
    else:
        schema_file = get_schema_path(VERSION)

    logger.info(f"Using schema file {schema_file}")
    with schema_file.open("r") as file:
        schema = json.load(file)

    return schema


def get_special_keys(schema, prekey=""):
    special_keys = []
    properties = schema["properties"]
    for key in properties:
        if properties[key]["type"] == "object":
            special_keys += get_special_keys(schema["properties"][key], prekey=key)
        elif properties[key]["type"] == "array" and "$ref" in properties[key]["items"]:
            special_keys.append(prekey + "_" + key)
    return special_keys
