from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Collection:
    id: str
    experiences: List[str]


@dataclass
class Tag:
    id: str
    experiences: List[str]
    title: str
    description: Optional[str]


@dataclass
class Folder:
    id: str
    tags: List[str]
    title: str
    description: Optional[str]
