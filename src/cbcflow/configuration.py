import configparser
import logging
import os

logger = logging.getLogger(__name__)


def get_cbcflow_config(config_file="~/.cbcflow.cfg"):
    config = configparser.ConfigParser()
    cfile = os.path.expanduser(config_file)
    config_defaults = dict(
        gracedb_service_url="https://gracedb-test.ligo.org/api/",
        library=None,
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
