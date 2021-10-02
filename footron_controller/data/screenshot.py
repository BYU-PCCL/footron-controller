from __future__ import annotations

import io
from PIL import ImageGrab
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


def take_screenshot() -> Image:
    return ImageGrab.grab()


async def create_screenshot_bytes_generator():
    image_bytes = io.BytesIO()
    take_screenshot().save(image_bytes, format="PNG")
    yield image_bytes.getvalue()
