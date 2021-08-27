import logging

import zmq
import zmq.asyncio


logger = logging.getLogger(__name__)


class WmApi:
    def __init__(self):
        self._context = zmq.asyncio.Context()
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:5557")

    async def set_fullscreen(self, fullscreen: bool):
        await self._socket.send_json({"type": "fullscreen", "fullscreen": fullscreen})

    async def clear_viewport(self):
        await self._socket.send_json({"type": "clear_viewport"})
