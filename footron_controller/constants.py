import os
import re
from pathlib import Path
from typing import Dict, Union, Any, List, Pattern

from xdg import xdg_config_home, xdg_data_home

from . import __file__ as module_path
from .data.placard import PlacardExperienceData

PACKAGE_PATH = Path(module_path).parent

PACKAGE_STATIC_PATH = PACKAGE_PATH / "static"
PACKAGE_SCRIPTS_PATH = PACKAGE_PATH / "scripts"

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

ROLLBAR_TOKEN = os.environ["FT_ROLLBAR"] if "FT_ROLLBAR" in os.environ else None

EXPERIENCES_PATH = Path(BASE_DATA_PATH, "experiences")

EMPTY_EXPERIENCE_DATA = PlacardExperienceData(
    title="Footron",
    artist="Vin Howe, Chris Luangrath, Matt Powley",
    description="Built with <pre style='display:inline;'>&lt;3</pre> by BYU students",
)

CURRENT_EXPERIENCE_SET_DELAY_S = 5

# noinspection PyTypeChecker
LOG_IGNORE_PATTERNS: List[Pattern] = list(
    map(
        re.compile,
        [r"(GET|PATCH) /current.*200", r"(GET|PATCH) /placard/url.*200"],
    )
)

JsonDict = Dict[str, Union[Any, Any]]
