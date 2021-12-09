import os
from enum import Enum
from typing import Optional

import aiohttp
from pydantic import BaseModel

from .wm import DisplayLayout

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")


class PlacardLayout(str, Enum):
    Full = "full"
    Slim = "slim"
    Hidden = "hidden"


_DISPLAY_PLACARD_LAYOUT_MAP = {
    DisplayLayout.Hd: PlacardLayout.Full,
    DisplayLayout.Wide: PlacardLayout.Slim,
    DisplayLayout.Full: PlacardLayout.Hidden,
}


class PlacardExperienceData(BaseModel):
    title: Optional[str]
    description: Optional[str]
    artist: Optional[str]


class PlacardUrlData(BaseModel):
    url: Optional[str]


class PlacardVisibilityData(BaseModel):
    layout: PlacardLayout


class EffectVisibilityData(BaseModel):
    show: bool


class PlacardApi:
    def __init__(self):
        self._aiohttp_session = aiohttp.ClientSession(
            connector=aiohttp.UnixConnector(path=_PLACARD_SOCKETS_PATH)
        )

    @staticmethod
    def placard_layout_from_display_layout(layout: DisplayLayout):
        return _DISPLAY_PLACARD_LAYOUT_MAP[layout]

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

    async def set_layout(self, layout: PlacardLayout):
        async with self._aiohttp_session.put(
            "http://localhost/layout",
            json=PlacardVisibilityData(layout=layout).dict(exclude_none=True),
        ) as response:
            return await response.json()

    async def show_effect(self, show: bool):
        async with self._aiohttp_session.put(
            "http://localhost/showEffect",
            json=EffectVisibilityData(show=show).dict(exclude_none=True),
        ) as response:
            return await response.json()

    async def layout(self):
        async with self._aiohttp_session.get("http://localhost/layout") as response:
            return await response.json()
