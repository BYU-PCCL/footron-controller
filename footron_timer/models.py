from typing import List, Optional, Union

from pydantic import BaseModel


class Experience(BaseModel):
    id: str
    unlisted: bool
    queueable: bool
    collection: Optional[str]
    folders: List[str] = []
    lifetime: int
    title: str
    artist: Optional[str]
    description: Optional[str]


class CurrentExperience(Experience):
    end_time: Optional[int]
    last_interaction: Optional[int]
    start_time: int
    last_update: int
    lock: Union[bool, int]
    last_lock_update: Optional[int]
