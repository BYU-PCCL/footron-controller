import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .tag import Tag
from ..constants import BASE_DATA_PATH


@dataclass
class Folder:
    id: str
    tags: List[str]
    title: str
    description: Optional[str]
