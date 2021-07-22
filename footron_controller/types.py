from typing import Optional

from pydantic import BaseModel


class PlacardData(BaseModel):
    title: Optional[str]
    description: Optional[str]
    artist: Optional[str]
    url: Optional[str]
