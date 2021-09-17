from datetime import datetime
import logging
from enum import Enum
from typing import Optional, List

import zmq
import zmq.asyncio

from ..util import datetime_to_timestamp

logger = logging.getLogger(__name__)


class DisplayLayout(str, Enum):
    Full = "full"
    Wide = "wide"
    Hd = "hd"


class WmApi:
    def __init__(self):
        self._context = zmq.asyncio.Context()
        # noinspection PyUnresolvedReferences
        self._socket = self._context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:5557")

    async def set_layout(self, layout: DisplayLayout):
        await self._socket.send_json(
            {
                "type": "layout",
                "after": datetime_to_timestamp(datetime.now()),
                "layout": layout,
            }
        )

    async def clear_viewport(self, include: Optional[List[str]] = None):
        data = {
            "type": "clear_viewport",
            "before": datetime_to_timestamp(datetime.now()),
        }

        if include is not None:
            data["include"] = include

        await self._socket.send_json(data)
