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
        response = await self._socket.recv_json()
        logger.debug(f"Got response from WM for set_fullscreen: {response}")

    async def clear_viewport(self):
        await self._socket.send_json({"type": "clear_viewport"})
        response = await self._socket.recv_json()
        logger.debug(f"Got response from WM for clear_viewport: {response}")
