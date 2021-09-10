from __future__ import annotations
import asyncio
import logging
import subprocess
from typing import Optional, TYPE_CHECKING

from ..util import mercilessly_kill_process
from ..constants import BASE_BIN_PATH
if TYPE_CHECKING:
    from .wm import WmApi

LOADER_PATH = BASE_BIN_PATH / "footron-loader"


logger = logging.getLogger(__name__)


class LoaderManager:
    _loader_process: Optional[subprocess.Popen]
    _process_operation_lock: asyncio.Lock
    _wm: WmApi

    def __init__(self, wm: WmApi):
        self._loader_process = None
        self._process_operation_lock = asyncio.Lock()
        self._wm = wm

    async def stop_after_timeout(self, timeout: int):
        await asyncio.sleep(timeout)
        await self.stop()

    async def start(self):
        if not LOADER_PATH:
            logger.warning(f"Loader binary couldn't be found at {LOADER_PATH}")
            return
        async with self._process_operation_lock:
            self._loader_process = subprocess.Popen([LOADER_PATH])

    async def stop(self):
        async with self._process_operation_lock:
            if not self._loader_process:
                return

            await self._wm.clear_viewport(include=["loader"])
            await mercilessly_kill_process(self._loader_process)
            self._loader_process = None
