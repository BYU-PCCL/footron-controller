import os
from pathlib import Path
from typing import Dict, Union, Any

from xdg import xdg_config_home, xdg_data_home

from . import __file__ as module_path

# TODO: If we ever move to a src/<package-name> layout, we'll need to add another
#  .parent here
PACKAGE_PATH = Path(module_path).parent
print(module_path)

PACKAGE_STATIC_PATH = PACKAGE_PATH / "static"

BASE_DATA_PATH = (
    Path(os.environ["FT_DATA_PATH"])
    if "FT_DATA_PATH" in os.environ
    else Path(xdg_data_home(), "footron")
)

# Once we automate app packaging and deployment, we should use XDG_DATA_HOME instead
BASE_CONFIG_PATH = (
    Path(os.environ["FT_CONFIG_PATH"])
    if "FT_CONFIG_PATH" in os.environ
    else Path(xdg_config_home(), "footron")
)

EXPERIENCES_PATH = Path(BASE_DATA_PATH, "experiences")

JsonDict = Dict[str, Union[Any, Any]]
