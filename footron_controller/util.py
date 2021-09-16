import asyncio
import logging
import subprocess
import socket
from contextlib import closing
from datetime import datetime

logger = logging.getLogger(__name__)


async def mercilessly_kill_process(process: subprocess.Popen):
    while True:
        process.terminate()
        if process.poll() is not None:
            break
        logger.warning(
            f"Managed process with PID {process.pid} didn't die, trying again in 1s..."
        )
        await asyncio.sleep(1)


# https://stackoverflow.com/a/45690594/1979008
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def datetime_to_timestamp(at: datetime):
    return int(at.timestamp() * 1000)


def timestamp_to_datetime(timestamp: int):
    return datetime.fromtimestamp(timestamp / 1000)
