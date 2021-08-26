import os
from pathlib import Path
from typing import Dict, Union, Any

from xdg import xdg_config_home, xdg_data_home

from . import __file__ as module_path
from .data.placard import PlacardExperienceData

PACKAGE_PATH = Path(module_path).parent

PACKAGE_STATIC_PATH = PACKAGE_PATH / "static"

BASE_DATA_PATH = (
    Path(os.environ["FT_DATA_PATH"])
    if "FT_DATA_PATH" in os.environ
    else Path(xdg_data_home(), "footron")
)

BASE_CONFIG_PATH = (
    Path(os.environ["FT_CONFIG_PATH"])
    if "FT_CONFIG_PATH" in os.environ
    else Path(xdg_config_home(), "footron")
)

BASE_MESSAGING_URL = (
    os.environ["FT_MSG_URL"]
    if "FT_MSG_URL" in os.environ
    else "ws://localhost:8088/messaging/out/"
)

EXPERIENCES_PATH = Path(BASE_DATA_PATH, "experiences")

EMPTY_EXPERIENCE_DATA = PlacardExperienceData(
    title="Footron",
    artist="Vin Howe, Chris Luangrath, Matt Powley",
    description="Built with <pre style='display:inline;'>&lt;3</pre> by BYU students",
)

JsonDict = Dict[str, Union[Any, Any]]
