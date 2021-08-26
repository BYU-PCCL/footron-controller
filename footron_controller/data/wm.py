import logging

import zmq
import zmq.asyncio


logger = logging.getLogger(__name__)


class WmApi:
    def __init__(self):
        self._context = zmq.asyncio.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect("tcp://localhost:5557")

    async def set_fullscreen(self, fullscreen: bool):
        await self._socket.send_json({"fullscreen": fullscreen})
        # Should really handle errors here
        await self._socket.recv_json()
