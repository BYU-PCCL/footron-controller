from __future__ import annotations

import io
from PIL import ImageGrab
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PIL import Image


SCREENSHOT_MIME_TYPES = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
}


def take_screenshot() -> Image:
    return ImageGrab.grab()


async def create_screenshot_bytes_generator(
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: int = 95,
    format: str = "jpeg",
):
    image = take_screenshot()
    image_width, image_height = image.size
    image_bytes = io.BytesIO()

    width = width if width is not None else image_width
    height = height if height is not None else image_height

    ratio = max(min(width / image_width, height / image_height, 1), 0)

    if ratio != 1 and ratio != 0:
        image = image.resize((int(ratio * image_width), int(ratio * image_height)))

    format_params = {}

    if format in ["jpg", "jpeg"]:
        format_params = {"quality": quality}

    image.save(image_bytes, format=format, **format_params)
    yield image_bytes.getvalue()
