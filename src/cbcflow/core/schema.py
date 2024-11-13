"""Methods for fetching schema information"""
import importlib.resources as importlib_resources
import json
import sys
from typing import Union, Optional
from pathlib import Path


CURRENT_CBC_SCHEMA_VERSION = "v3"
CURRENT_INDEX_SCHEMA_VERSION = "v1"


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
        if version in str(file).rsplit("/", 1)[-1]:
            matches.append(file)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        raise ValueError(f"No schema file for version {version} found")
    elif len(matches) > 1:
        raise ValueError("Too many matching schema files found")


def get_schema(
    schema_path: Optional[str] = None,
    version: Optional[str] = None,
    index_schema: bool = False,
):
    """Gets the cbc or index schema given a schema path, or a requested version

    Parameters
    ==========
    schema_path : Optional[str]
        If passed, overwrites all defaults to point to given schema file, which will be loaded
    version : Optional[str]
        If passed and schema_path is not passed, sets version to read, else up-to-date schema will be used
    index_schema : bool
        If set true, loads the index schema, else loads CBC metadata schema by default

    Returns
    =======
    dict
        The json form of the schema
    """
    schema_type_designator = "index" if index_schema else "cbc"
    if version is not None:
        schema_version = version
    elif index_schema:
        schema_version = CURRENT_INDEX_SCHEMA_VERSION
    else:
        schema_version = CURRENT_CBC_SCHEMA_VERSION
    if schema_path is None:
        schema_path = get_schema_path(
            version=schema_version, schema_type_designator=schema_type_designator
        )
    with Path(schema_path).open("r") as file:
        schema = json.load(file)
    return schema


def get_schema_from_args(
    args: Union[list, None] = None, index_schema: bool = False
) -> dict:
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

    # Set up bootstrap variables
    fileflag = "--schema-file"
    versionflag = "--schema-version"

    if fileflag in args:
        schema_file = args[args.index(fileflag) + 1]
        version = None
    elif versionflag in args:
        schema_file = None
        version = args[args.index(versionflag) + 1]
    else:
        schema_file = None
        version = None
    schema = get_schema(
        schema_path=schema_file, version=version, index_schema=index_schema
    )

    return schema
