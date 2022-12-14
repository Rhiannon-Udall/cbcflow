#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import copy
import logging

import jsonschema

from .configuration import config_defaults
from .gracedb import fetch_gracedb_information
from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import process_update_json, process_user_input
from .schema import get_schema


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Read in command line arguments
    schema = get_schema()
    parser, default_data = get_parser_and_default_data(schema)
    args = parser.parse_args()

    # Set the sname in the default data
    default_data["Sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname,
        args.library,
        default_data=default_data,
        schema=schema,
        no_git_library=args.no_git_library,
    )
    default_metadata = copy.deepcopy(metadata)

    if args.pull_from_gracedb:
        gdb_data = fetch_gracedb_information(args.sname, args.gracedb_service_url)
        metadata.data.update(gdb_data)
        try:
            metadata.write_to_library()
        except jsonschema.exceptions.ValidationError:
            logger.info(
                "GraceDB data cannot be validated against current schema\n\
                Accordingly, the local library will not be updated"
            )
            if not metadata.library_file_exists:
                logger.info(
                    "Since no local library file exists yet, it will be initialized with valid defaults"
                )
                default_metadata.write_to_library()

    elif metadata.library_file_exists is False:
        raise ValueError(
            f"The library file {metadata.library_file} does not yet exist. "
            "Please initialise with --pull-from-gracedb"
        )

    if args.update:
        process_user_input(args, metadata, schema)
        metadata.write_to_library()

    if args.print:
        metadata.pretty_print(metadata.data)


def from_file():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Read in command line arguments
    schema = get_schema()
    _, default_data = get_parser_and_default_data(schema)

    file_parser = argparse.ArgumentParser()
    file_parser.add_argument("sname", help="The superevent SNAME")
    file_parser.add_argument(
        "update-file",
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
        args.library,
        default_data=default_data,
        schema=schema,
        no_git_library=args.no_git_library,
    )

    if args.update_file.split(".") == "yaml" or args.update_file.split(".") == "yml":
        # In this case, we treat the file as a yaml
        import yaml

        with open(args.update_file, "r") as file:
            file_contents = yaml.safe_load(file)
    elif args.update_file.split(".") == "json":
        import json

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
    process_update_json(file_contents, metadata, schema, is_removal=args.removal_file)
