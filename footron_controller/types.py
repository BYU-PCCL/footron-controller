from typing import Optional, Dict, Union, Any

from pydantic import BaseModel


class PlacardData(BaseModel):
    title: Optional[str]
    description: Optional[str]
    artist: Optional[str]
    url: Optional[str]


JsonDict = Dict[str, Union[Any, Any]]
