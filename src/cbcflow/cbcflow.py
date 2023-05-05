#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""Client level methods for cbcflow (i.e. those that use argument parsing)"""

import argparse
import copy
import glob
import json
from typing import Tuple

import jsonschema

from .configuration import config_defaults
from .gracedb import fetch_gracedb_information
from .online_pe import add_onlinepe_information
from .metadata import MetaData
from .database import LocalLibraryDatabase
from .parser import get_parser_and_default_data, sname_string
from .process import process_user_input
from .schema import get_schema
from .utils import setup_logger


def setup_args_metadata() -> Tuple[argparse.Namespace, "MetaData"]:
    """Take in command line arguments, and return a metadata object

    Returns
    =======
    argparse.Namespace
        A namespace generated by parsing the input arguments
    MetaData
        A metadata object generated by the parsing of the arguments
    """
    schema = get_schema()
    parser, default_data = get_parser_and_default_data(schema)
    args = parser.parse_args()

    # Set the sname in the default data
    default_data["Sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname,
        local_library_path=args.library,
        default_data=default_data,
        schema=schema,
        no_git_library=args.no_git_library,
    )
    return args, metadata


def pull() -> None:
    """Pull updates from GraceDB to the library"""
    logger = setup_logger()
    args, metadata = setup_args_metadata()

    default_metadata = copy.deepcopy(metadata)

    # Pull information from GraceDB
    gdb_data = fetch_gracedb_information(args.sname, args.gracedb_service_url)
    metadata.data.update(gdb_data)

    # Pull information from onlinePE
    add_onlinepe_information(metadata, args.sname)

    try:
        metadata.write_to_library()
    except jsonschema.exceptions.ValidationError:
        logger.info(
            "Recorded meta-data cannot be validated against current schema\n\
            Accordingly, the local library will not be updated"
        )
        if not metadata.library_file_exists:
            logger.info(
                "Since no local library file exists yet, it will be initialized with valid defaults"
            )
            default_metadata.write_to_library()


def update() -> None:
    """Update the library metadata according to input arguments"""
    args, metadata = setup_args_metadata()
    if metadata.library_file_exists is False:
        raise ValueError(
            f"The library file {metadata.library_file} does not yet exist. "
            "Please initialise with --pull-from-gracedb"
        )
    else:
        process_user_input(args, metadata)
        if args.yes:
            check_changes = False
        else:
            check_changes = True
        metadata.write_to_library(check_changes=check_changes)


def print_metadata() -> None:
    """Print the metadata for a given event in a given library, as passed in args"""
    # Read in command line arguments
    schema = get_schema()
    _, default_data = get_parser_and_default_data(schema)

    parser = argparse.ArgumentParser()
    parser.add_argument("sname", help="The superevent SNAME", type=sname_string)
    parser.add_argument(
        "--library", default=config_defaults["library"], help="The library"
    )
    args = parser.parse_args()

    # Set the sname in the default data
    default_data["Sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname,
        local_library_path=args.library,
        default_data=default_data,
        schema=schema,
    )

    metadata.pretty_print()


def from_file() -> None:
    """Given a superevent and an update file, apply the updates"""
    logger = setup_logger()

    # Read in command line arguments
    schema = get_schema()
    _, default_data = get_parser_and_default_data(schema)

    file_parser = argparse.ArgumentParser()
    file_parser.add_argument("sname", help="The superevent SNAME", type=sname_string)
    file_parser.add_argument(
        "update_file",
        help="The file to update from, either a json or a yaml.\
        The type of file will be inferred from the ending .yaml or .json",
    )
    file_parser.add_argument(
        "--removal-file",
        action="store_true",
        help="If passed, this will be treated as a negative image,\
            so array elements will be removed instead of added",
    )
    file_parser.add_argument(
        "--library", default=config_defaults["library"], help="The library"
    )
    file_parser.add_argument("--schema-version", help="The schema version to use")
    file_parser.add_argument(
        "--schema-file",
        help="Explicit path to the schema-file. If None (default) the inbuilt schema is used",
        default=config_defaults["schema"],
    )
    file_parser.add_argument(
        "--no-git-library",
        action="store_true",
        help="If true, do not treat the library as a git repo",
    )
    args = file_parser.parse_args()

    # Set the sname in the default data
    default_data["Sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname,
        local_library_path=args.library,
        default_data=default_data,
        schema=schema,
        no_git_library=args.no_git_library,
    )

    if (
        args.update_file.split(".")[-1] == "yaml"
        or args.update_file.split(".")[-1] == "yml"
    ):
        # In this case, we treat the file as a yaml
        import yaml

        with open(args.update_file, "r") as file:
            file_contents = yaml.safe_load(file)
    elif args.update_file.split(".")[-1] == "json":

        with open(args.update_file, "r") as file:
            file_contents = json.load(file)
    else:
        raise ValueError(
            "Could not interpret type of file,\
            check that it is either a json or a yaml,\
            and that it's ending reflects this."
        )

    logger.info("Read File Contents:")
    logger.info(json.dumps(file_contents, indent=4))

    logger.info("Updating Metadata")
    metadata.update(file_contents, is_removal=args.removal_file)

    logger.info("Writing to library")
    metadata.write_to_library()


def validate_library() -> None:
    """Go through the library, validating that all metadata files satisfy the schema"""
    # Read in command line arguments
    schema = get_schema()
    _, default_data = get_parser_and_default_data(schema)

    # Set up argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("library", help="The library to validate")
    args = parser.parse_args()

    # Glob for all files in the library
    metadata_files = glob.glob(f"{args.library}/S*json")
    if len(metadata_files) == 0:
        raise ValidationError(f"No metadata files found in library {args.library}")

    # Load the library
    library = LocalLibraryDatabase(
        args.library, schema=schema, default_data=default_data
    )

    for fname in metadata_files:
        # Load the metadata: if it is not valid it will fail
        MetaData.from_file(
            fname,
            schema=schema,
            local_library=library,
        )


class ValidationError(Exception):
    """An error in schema validation"""

    pass
