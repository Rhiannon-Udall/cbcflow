"""The core (and presently only) module for cbcflow"""
from typing import Union

from . import _version
from .utils import setup_logger
from .cbcflow import from_file, setup_args_metadata
from .configuration import get_cbcflow_config
from .metadata import MetaData
from .monitor import generate_crondor, generate_crontab, run_monitor
from .parser import get_parser_and_default_data
from .schema import get_schema

__version__ = _version.__version__


def get_superevent(
    sname: str, library: Union[str, None] = None, no_git_library: bool = False
):
    """
    A helper method to easily fetch information on a given superevent.

    Parameters
    ==========
    sname : str
        The sname of the superevent in question, according to GraceDB
    library : str | None
        The library from which to fetch information
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
        config_defaults = get_cbcflow_config()
        library = config_defaults["library"]

    metadata = MetaData(
        sname,
        local_library_path=library,
        default_data=default_data,
        schema=schema,
        no_git_library=no_git_library,
    )

    return metadata
