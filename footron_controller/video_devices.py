from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Dict

_VIDEO_DEVICE_ENV_PREFIX = "FT_VIDEO_DEV_"
_ENV_MATCH_PATTERN = re.compile(fr"{_VIDEO_DEVICE_ENV_PREFIX}.*")

_device_manager: Optional[VideoDeviceManager] = None


class VideoDeviceManager:
    _devices = Dict[str, Path]

    def __init__(self):
        self.load_devices()

    @property
    def devices(self):
        return self._devices

    def load_devices(self):
        env_keys = list(filter(_ENV_MATCH_PATTERN.match, os.environ))
        self._devices = {
            key[len(_VIDEO_DEVICE_ENV_PREFIX) :].lower(): Path(os.environ[key])
            for key in env_keys
        }


def get_video_device_manager():
    global _device_manager
    if _device_manager is None:
        _device_manager = VideoDeviceManager()

    return _device_manager
