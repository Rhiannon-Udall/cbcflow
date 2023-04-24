"""Methods for fetching schema information"""
import importlib.resources as importlib_resources
import json
import sys
from typing import Union
from pathlib import Path

from .configuration import get_cbcflow_config
from .utils import setup_logger

logger = setup_logger()


def get_schema_path(version, schema_type_designator="cbc"):
    """Get the path to the schema file

    Parameters
    ==========
    version : str
        The version to search for, e.g. v1 or v2
    schema_type_designator : str, optional
        The type of schema to be grabbed defaulting to cbc for superevent metadata.
        For the index schema, this would be passed as index

    Returns
    =======
    str
        The path to the appropriate schema file
    """
    ddir = importlib_resources.files("cbcflow") / "schema"
    files = ddir.glob(f"{schema_type_designator}*schema")
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


def get_schema(args: Union[list, None] = None, index_schema: bool = False) -> dict:
    """Get the schema json

    Parameters
    ==========
    args : Union[list, None], optional
        The arguments to use in grabbing the schema. If none are passed defaults to sys.argv
    index_schema : bool, optional
        Whether to grab the index schema instead of the cbc schema, defaults False

    Returns
    =======
    dict
        The schema dict loaded from the appropriate file.
    """
    if args is None:
        args = sys.argv
    VERSION = "v2"

    # Set up bootstrap variables
    fileflag = "--schema-file"
    versionflag = "--schema-version"
    configuration = get_cbcflow_config()
    if index_schema:
        config_schema = configuration["index_schema"]
        schema_type_designator = "index"
    else:
        config_schema = configuration["schema"]
        schema_type_designator = "cbc"

    if config_schema is not None:
        schema_file = config_schema
    elif fileflag in args:
        schema_file = args[args.index(fileflag) + 1]
    elif versionflag in args:
        version = args[args.index(versionflag) + 1]
        schema_file = get_schema_path(
            version, schema_type_designator=schema_type_designator
        )
    else:
        schema_file = get_schema_path(
            VERSION, schema_type_designator=schema_type_designator
        )

    logger.info(f"Using {schema_type_designator} schema file {schema_file}")
    with Path(schema_file).open("r") as file:
        schema = json.load(file)

    return schema
