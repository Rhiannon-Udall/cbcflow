import configparser
import os

config_defaults = dict(
    gracedb_service_url="https://gracedb-test.ligo.org/api/",
    library=None,
)

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.cbcflow.cfg"))
section = config["cbcflow"]
for key in config_defaults:
    if key in list(section.keys()):
        config_defaults[key] = section[key]
