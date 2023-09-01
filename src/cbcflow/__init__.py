"""The core (and presently only) module for cbcflow"""
from typing import Union

from . import _version
from .core.utils import setup_logger
from .client.cbcflow import (
    from_file,
    setup_args_metadata,
    pull,
    print_metadata,
    update,
    validate_library,
    cbcflow_git_merge,
)
from .core.configuration import get_cbcflow_config
from .core.metadata import MetaData
from .core.database import LocalLibraryDatabase
from .client.monitor import generate_crondor, generate_crontab, run_monitor
from .core.parser import get_parser_and_default_data
from .core.schema import get_schema
from .core.wrapped import get_superevent

__version__ = _version.__version__
