import os
from pathlib import Path
from xdg import (
    xdg_config_home
)

# Once we automate app packaging and deployment, we should use XDG_DATA_HOME instead
BASE_PATH = (
    Path(os.environ["FT_BASE_PATH"])
    if "FT_BASE_PATH" in os.environ
    else Path(xdg_config_home(), "footron")
)
EXPERIENCES_PATH = Path(BASE_PATH, "experiences")
