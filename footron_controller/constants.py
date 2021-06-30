from pathlib import Path
from xdg import (
    xdg_config_home
)

# Once we automate app packaging and deployment, we should use XDG_DATA_HOME instead
BASE_PATH = Path(xdg_config_home(), "footron")
EXPERIENCES_PATH = Path(BASE_PATH, "experiences")
