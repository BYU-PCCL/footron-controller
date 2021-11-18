from __future__ import annotations

from typing import Optional

import aiohttp

from ..constants import CAPTURE_API_URL

_capture_api: Optional[CaptureApi] = None

_ENDPOINT_CURRENT = "/current"


class CaptureApi:
    def __init__(self):
        self._aiohttp_session = aiohttp.ClientSession()

    @staticmethod
    def _url_with_endpoint(endpoint) -> str:
        return f"{CAPTURE_API_URL}{endpoint}"

    async def set_current_experience(
        self, id: Optional[str], path: Optional[str] = None
    ):
        async with self._aiohttp_session.put(
            self._url_with_endpoint(_ENDPOINT_CURRENT), json={"id": id, "path": path}
        ) as response:
            return await response.json()


def get_capture_api():
    global _capture_api
    if _capture_api is None:
        _capture_api = CaptureApi()

    return _capture_api
