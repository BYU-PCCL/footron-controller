import datetime
import logging
from typing import Optional, List

import zmq
import zmq.asyncio


logger = logging.getLogger(__name__)


class WmApi:
    def __init__(self):
        self._context = zmq.asyncio.Context()
        # noinspection PyUnresolvedReferences
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:5557")

    async def set_fullscreen(self, fullscreen: bool):
        await self._socket.send_json(
            {
                "type": "fullscreen",
                "after": int(datetime.datetime.now().timestamp() * 1000),
                "fullscreen": fullscreen,
            }
        )

    async def clear_viewport(self, include: Optional[List[str]] = None):
        data = {
            "type": "clear_viewport",
            "before": int(datetime.datetime.now().timestamp() * 1000),
        }

        if include is not None:
            data["include"] = include

        await self._socket.send_json(data)
