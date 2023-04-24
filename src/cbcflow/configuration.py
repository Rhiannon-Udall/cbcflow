"""Methods for fetching cbcflow configuration information"""
import configparser
import os

from .utils import setup_logger

logger = setup_logger()


def get_cbcflow_config(config_file: str = "~/.cbcflow.cfg") -> dict:
    """Get the configuration information for cbcflow

    Parameters
    ==========
    config_file : str, optional
        The path to the configuration file, defaults to ~/.cbcflow.cfg

    Returns
    =======
    dict
        The configuration data, from defaults and the proferred configuration file
    """
    config = configparser.ConfigParser()
    cfile = os.path.expanduser(config_file)
    config_defaults = dict(
        gracedb_service_url="https://gracedb-test.ligo.org/api/",
        library=None,
        schema=None,
        index_schema=None,
    )
    if os.path.exists(cfile):
        config.read(cfile)
        section_key = "cbcflow"
        if section_key not in config.sections():
            raise ValueError(f"You need a [cbcflow] section header in {cfile}")
        section = config[section_key]
        for key in config_defaults:
            if key in list(section.keys()):
                config_defaults[key] = section[key]
    else:
        logger.info("Could not read config file, falling back on defaults.")
    return config_defaults


config_defaults = get_cbcflow_config()
