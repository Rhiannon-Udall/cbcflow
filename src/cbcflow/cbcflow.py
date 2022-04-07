#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

from .database import GraceDbDatabase
from .metadata import MetaData
from .parser import get_parser_and_default_data
from .process import process_user_input
from .schema import get_schema


def main():
    schema = get_schema()
    parser, default_data = get_parser_and_default_data(schema)
    args = parser.parse_args()

    default_data["sname"] = args.sname
    metadata = MetaData(
        args.sname, args.library, default_data=default_data, schema=schema
    )

    gdb = GraceDbDatabase()
    database_data = gdb.fetch(args.sname)
    metadata.data.update(database_data)

    process_user_input(args, parser, schema, metadata)

    metadata.validate(metadata.data)
    metadata.write_to_library()
    if args.print:
        metadata.pretty_print(metadata.data)
