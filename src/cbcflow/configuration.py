import configparser
import os

config_defaults = dict(
    gracedb_service_url="https://gracedb-test.ligo.org/api/",
    library=None,
)

config = configparser.ConfigParser()
cfile = os.path.expanduser("~/.cbcflow.cfg")

if os.path.exists(cfile):
    config.read(cfile)
    section_key = "cbcflow"
    if section_key not in config.sections():
        raise ValueError(f"You need a [cbcflow] section header in {cfile}")
    section = config[section_key]
    for key in config_defaults:
        if key in list(section.keys()):
            config_defaults[key] = section[key]
