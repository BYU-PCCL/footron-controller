from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional

_VIDEO_DEVICE_ENV_PREFIX = "FT_VIDEO_DEV_"
_ENV_MATCH_PATTERN = re.compile(rf"{_VIDEO_DEVICE_ENV_PREFIX}.*")

_device_manager: Optional[VideoDeviceManager] = None


class VideoDeviceManager:
    _devices: Dict[str, Path]

    def __init__(self):
        self._devices = {}

    @property
    def devices(self):
        self.load_devices()
        return self._devices

    def load_devices(self):
        self._devices = {}
        video_devs = list(
            sorted(
                map(lambda p: p.name, Path("/dev").glob("video*")),
                key=lambda a: int(re.findall(r"\d+", a)[0]),
            )
        )
        # This is basically what Chrome does, but note that it isn't useful if there
        # are multiple instances of the same product. For that we need probably need
        # pyudev to get a serial number.
        # See https://source.chromium.org/chromium/chromium/src/+/main:media/capture/video/linux/video_capture_device_factory_linux.cc
        devices = []
        for device_name in video_devs:
            try:
                device_info = (
                    ":".join(
                        open(
                            f"/sys/class/video4linux/{device_name}/device/../{id_file}"
                        )
                        .read()
                        .strip()
                        for id_file in ["idVendor", "idProduct"]
                    ),
                    f"/dev/{device_name}",
                )
            except FileNotFoundError:
                continue
            devices.append(device_info)
        env_keys = list(filter(_ENV_MATCH_PATTERN.match, os.environ))
        for env_key in env_keys:
            key = env_key[len(_VIDEO_DEVICE_ENV_PREFIX) :].lower()
            device = next(
                (Path(path) for (id, path) in devices if id == os.environ[env_key]),
                None,
            )
            if device is None:
                continue
            self._devices[key] = device


def get_video_device_manager():
    global _device_manager
    if _device_manager is None:
        _device_manager = VideoDeviceManager()

    return _device_manager
