import os
from pathlib import Path
from xdg import xdg_config_home

BASE_DATA_PATH = (
    Path(os.environ["FT_DATA_PATH"])
    if "FT_DATA_PATH" in os.environ
    else Path(xdg_config_home(), "footron")
)

# Once we automate app packaging and deployment, we should use XDG_DATA_HOME instead
BASE_CONFIG_PATH = (
    Path(os.environ["FT_CONFIG_PATH"])
    if "FT_CONFIG_PATH" in os.environ
    else Path(xdg_config_home(), "footron")
)

EXPERIENCES_PATH = Path(BASE_CONFIG_PATH, "experiences")
