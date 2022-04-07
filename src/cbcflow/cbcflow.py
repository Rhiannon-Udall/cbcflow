#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

from .database import GraceDbDatabase
from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import process_user_input
from .schema import get_schema


def main():
    # Read in command line arguments
    schema = get_schema()
    parser, default_data = get_parser_and_default_data(schema)
    args = parser.parse_args()

    # Set the sname in the default data
    default_data["sname"] = args.sname

    # Instantiate the metadata
    metadata = MetaData(
        args.sname, args.library, default_data=default_data, schema=schema
    )

    if args.pull_from_gracedb:
        gdb = GraceDbDatabase()
        database_data = gdb.pull(args.sname)
        metadata.data.update(database_data)
        metadata.write_to_library()

    if args.update:
        process_user_input(args, parser, schema, metadata)
        if metadata.is_updated:
            metadata.write_to_library()

    if args.push_to_gracedb:
        gdb = GraceDbDatabase()
        gdb.push(metadata)

    if args.print:
        metadata.pretty_print(metadata.data)
