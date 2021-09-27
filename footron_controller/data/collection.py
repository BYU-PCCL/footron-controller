import json
from dataclasses import dataclass
from typing import Dict, List

from ..constants import BASE_DATA_PATH


@dataclass
class Collection:
    id: str
    experiences: List[str]
