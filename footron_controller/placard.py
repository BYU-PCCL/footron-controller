import os
from typing import Optional

import aiohttp
from pydantic import BaseModel

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")


class PlacardData(BaseModel):
    title: Optional[str]
    description: Optional[str]
    artist: Optional[str]
    url: Optional[str]


class PlacardApi:
    def __init__(self):
        self._aiohttp_session = aiohttp.ClientSession(
            connector=aiohttp.UnixConnector(path=_PLACARD_SOCKETS_PATH)
        )

    async def update(self, data: PlacardData):
        async with self._aiohttp_session.patch(
            "http://localhost/placard", json=data.dict()
        ) as response:
            return await response.json()

    async def get(self):
        async with self._aiohttp_session.get("http://localhost/placard") as response:
            return await response.json()
