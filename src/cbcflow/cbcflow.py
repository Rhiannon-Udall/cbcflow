#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import logging

from .gracedb import fetch_gracedb_information
from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import process_user_input
from .schema import get_schema


def main():
    logging.basicConfig(level=logging.INFO)

    # Read in command line arguments
    schema = get_schema()
    parser, default_data = get_parser_and_default_data(schema)
    args = parser.parse_args()

    # Set the sname in the default data
    default_data["sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname,
        args.library,
        default_data=default_data,
        schema=schema,
        no_git_library=args.no_git_library,
    )

    if args.pull_from_gracedb:
        gdb_data = fetch_gracedb_information(args.sname, args.gracedb_service_url)
        metadata.data.update(gdb_data)
        metadata.write_to_library()
    elif metadata.library_file_exists is False:
        raise ValueError(
            f"The library file {metadata.library_file} does not yet exist. "
            "Please initialise with --pull-from-gracedb"
        )

    if args.update:
        process_user_input(args, parser, schema, metadata)
        metadata.write_to_library()

    if args.print:
        metadata.pretty_print(metadata.data)
