"""Convenience wrappers for other lower level functions"""
from typing import Union

from .schema import get_schema
from .parser import get_parser_and_default_data
from .metadata import MetaData
from .database import LocalLibraryDatabase
import os


def get_superevent(
    sname: str,
    library: Union[str, "LocalLibraryDatabase", None] = None,
    no_git_library: bool = False,
):
    """
    A helper method to easily fetch information on a given superevent.

    Parameters
    ==========
    sname : str
        The sname of the superevent in question, according to GraceDB
    library : str | `cbcflow.database.LocalLibraryDatabase` | None
        The library from which to fetch information, defaults to cwd
    no_git_library : bool
        If true, don't attempt to treat this library as a git repository

    Returns
    =======
    cbcflow.metadata.MetaData
        The metadata object associated with the superevent in question
    """

    schema = get_schema()
    _, default_data = get_parser_and_default_data(schema)

    if library is None:
        library = os.getcwd()

    if isinstance(library, LocalLibraryDatabase):
        metadata = MetaData(
            sname,
            local_library=library,
            default_data=default_data,
            schema=schema,
            no_git_library=no_git_library,
        )
    else:
        metadata = MetaData(
            sname,
            local_library_path=library,
            default_data=default_data,
            schema=schema,
            no_git_library=no_git_library,
        )

    return metadata
