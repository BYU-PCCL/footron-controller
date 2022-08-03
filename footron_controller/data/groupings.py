from typing import List, Optional, Type

import tomli
from pydantic import BaseModel

from ..constants import BASE_DATA_PATH


class Collection(BaseModel):
    id: str
    experiences: List[str]


class Tag(BaseModel):
    id: str
    experiences: List[str]
    title: str
    description: Optional[str]


class Folder(BaseModel):
    id: str
    tags: List[str]
    title: str
    featured: str
    description: Optional[str]
    visible: bool = True


def load_experience_grouping(type: Type, file_name: str, path=BASE_DATA_PATH):
    file_path = path / file_name

    if not file_path.exists():
        return {}

    with open(file_path, "rb") as file:
        data = tomli.load(file)

    return {id: type(id=id, **value) for id, value in data.items()}
