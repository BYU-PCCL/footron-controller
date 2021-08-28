from typing import Optional
from pydantic import BaseModel


class Experience(BaseModel):
    id: str
    unlisted: bool
    collection: Optional[str]
    lifetime: int
    title: str
    artist: Optional[str]
    description: Optional[str]


class CurrentExperience(Experience):
    end_time: Optional[int]
    lock: bool
    last_update: int
    

    