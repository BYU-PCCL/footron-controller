import asyncio
import io
import logging
import socket
import subprocess
from contextlib import closing
from datetime import datetime
from typing import Optional

from PIL import Image

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


async def create_image_bytes_generator(
    image: Image,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: int = 95,
    format: str = "jpeg",
):
    image_width, image_height = image.size
    image_bytes = io.BytesIO()

    width = width if width is not None else image_width
    height = height if height is not None else image_height

    ratio = max(min(width / image_width, height / image_height, 1), 0)

    if ratio != 1 and ratio != 0:
        image = image.resize((int(ratio * image_width), int(ratio * image_height)))

    format_params = {}

    if format == "jpeg":
        format_params = {"quality": quality}

    image.save(image_bytes, format=format, **format_params)
    yield image_bytes.getvalue()
