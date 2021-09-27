import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..constants import BASE_DATA_PATH


@dataclass
class Tag:
    id: str
    experiences: List[str]
    title: str
    description: Optional[str]
