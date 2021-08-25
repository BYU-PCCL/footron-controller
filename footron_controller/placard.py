import json
import os
from typing import Optional

import aiohttp
from pydantic import BaseModel

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")


class PlacardExperienceData(BaseModel):
    title: Optional[str]
    description: Optional[str]
    artist: Optional[str]


class PlacardUrlData(BaseModel):
    url: Optional[str]


class PlacardApi:
    def __init__(self):
        self._aiohttp_session = aiohttp.ClientSession(
            connector=aiohttp.UnixConnector(path=_PLACARD_SOCKETS_PATH)
        )

    async def set_experience(self, data: PlacardExperienceData):
        async with self._aiohttp_session.put(
            "http://localhost/experience", json=data.dict(exclude_none=True)
        ) as response:
            return await response.json()

    async def experience(self):
        async with self._aiohttp_session.get("http://localhost/experience") as response:
            return await response.json()

    async def set_url(self, url: str):
        async with self._aiohttp_session.put(
            "http://localhost/url",
            json=PlacardUrlData(url=url).dict(exclude_none=True),
        ) as response:
            return await response.json()

    async def url(self):
        async with self._aiohttp_session.get("http://localhost/url") as response:
            return await response.json()
