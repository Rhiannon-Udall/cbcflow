#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import copy
import logging

import jsonschema

from .gracedb import fetch_gracedb_information
from .metadata import MetaData
from .oldprocess import process_user_input
from .parser import get_parser_and_default_data
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
        process_user_input(args, metadata, schema, parser)
        metadata.write_to_library()

    if args.print:
        metadata.pretty_print(metadata.data)
