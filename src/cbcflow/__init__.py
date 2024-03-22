"""The overarching cbcflow module"""
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
from .core.metadata import MetaData
from .core.database import LocalLibraryDatabase
from .client.monitor import generate_crondor, generate_crontab, run_monitor
from .core.parser import get_parser_and_default_data
from .core.schema import get_schema
from .core.wrapped import get_superevent
from .client.migrate_v2_to_v3 import main as migrate_schema_v2_to_v3

logger = setup_logger()
logger.info(
    "Also including old import paths as well, e.g. `cbcflow.database`\n\
    These will be deprecated at some point in the future."
)

from .core import database
from .core import wrapped as cbcflow
from .inputs import gracedb
from .core import metadata
from .client import monitor
from .core import parser
from .inputs import pe_scraper
from .core import process
from .core import schema
from .core import utils

__version__ = _version.__version__
