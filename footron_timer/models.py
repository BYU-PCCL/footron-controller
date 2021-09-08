from typing import Optional, Union
from pydantic import BaseModel


class Experience(BaseModel):
    id: str
    unlisted: bool
    queueable: bool
    collection: Optional[str]
    lifetime: int
    title: str
    artist: Optional[str]
    description: Optional[str]


class CurrentExperience(Experience):
    end_time: Optional[int]
    lock: Union[bool, int]
    last_update: int
