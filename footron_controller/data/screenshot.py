from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import Xlib
import Xlib.display
from PIL import Image
from Xlib.xobject.drawable import Window

SCREENSHOT_MIME_TYPES = {
    "jpeg": "image/jpeg",
    "png": "image/png",
}


class ScreenshotCapture:
    def __init__(self):
        self._display = Xlib.display.Display()
        self._root: Window = self._display.screen().root
        self._net_wm_name_atom = self._display.intern_atom("_NET_WM_NAME")

    def _window_by_name(self, name: str) -> Optional[Window]:
        children = self._root.query_tree().children
        for child in children:
            # Note here that we only search through windows which implement the newer
            # _NET_WM_NAME atom, because that's what the specific window we're looking
            # for uses
            wm_name = child.get_full_property(self._net_wm_name_atom, 0)
            if not wm_name or not wm_name.value:
                continue
            decoded_name = wm_name.value.decode("utf8")
            if decoded_name == name:
                return child

    @staticmethod
    def _capture_window(window: Window) -> Image:
        geometry = window.get_geometry()
        width, height = geometry.width, geometry.height
        raw_image = window.get_image(0, 0, width, height, Xlib.X.ZPixmap, 0xFFFFFFFF)
        return Image.frombytes("RGB", (width, height), raw_image.data, "raw", "BGRX")

    def capture_root(self):
        return self._capture_window(self._root)

    def capture_viewport(self):
        return self._capture_window(self._window_by_name("FOOTRON_EXPERIENCE_VIEWPORT"))
