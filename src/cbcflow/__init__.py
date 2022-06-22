from . import _version
from .cbcflow import main
from .monitor import generate_crondor, run_monitor

__version__ = _version.get_versions()["version"]
