from typing import List, Optional

from pydantic import BaseModel


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
