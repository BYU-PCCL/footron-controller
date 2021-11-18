from __future__ import annotations
import abc
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Union
import docker
import docker.errors
import urllib.parse

from docker.models.containers import Container
from docker.types import DeviceRequest

from .data.capture import CaptureApi, get_capture_api
from .util import mercilessly_kill_process
from .browser_runner import BrowserRunner
from .constants import (
    PACKAGE_STATIC_PATH,
    BASE_MESSAGING_URL,
    EXPERIENCE_DATA_PATH,
    BASE_BIN_PATH,
)
from .data.video_devices import get_video_device_manager, VideoDeviceManager

CAPTURE_SHELL_PATH = BASE_BIN_PATH / "footron-capture-shell"

logger = logging.getLogger(__name__)

try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    docker_client = None
    logger.warning("Couldn't create Docker client, Docker experiences will be disabled")


class EnvironmentInitializationError(Exception):
    pass


class BaseEnvironment(abc.ABC):
    @abc.abstractmethod
    def start(self, last_environment: Optional[BaseEnvironment] = None):
        ...

    @abc.abstractmethod
    def stop(self, next_environment: Optional[BaseEnvironment] = None):
        ...

    @property
    def available(self) -> bool:
        return True


class _BaseWebEnvironmentMixin:
    _runner: BrowserRunner
    _static_path: Path
    _available: bool
    _id: str

    def __init__(self, id, path, routes, url):
        self._available = True
        self._static_path = Path(path) if not isinstance(path, Path) else path
        self._check_static_path()
        self._runner = BrowserRunner(id, routes, url)

    async def start(self, last_environment=None):
        await self._runner.start()

    async def stop(self, next_environment=None):
        await self._runner.stop()

    def _check_static_path(self):
        if self._static_path.exists():
            return
        self._available = False
        raise EnvironmentInitializationError(
            f"Couldn't load static path for experience {self._id}"
            f" at path {self._static_path.absolute()}"
        )

    @property
    def available(self):
        return self._available


class WebEnvironment(_BaseWebEnvironmentMixin, BaseEnvironment):
    def __init__(self, id: str, path: Union[str, Path], url: Optional[str] = "/"):
        super().__init__(id, path, {"/": path}, url)


class VideoEnvironment(_BaseWebEnvironmentMixin, BaseEnvironment):
    def __init__(self, id: str, path: Union[str, Path], video_filename: str):
        super().__init__(
            id,
            path,
            {"/video": path, "/": PACKAGE_STATIC_PATH / "video-player"},
            f"/?url=/video/{video_filename}&posterUrl=/video/poster.jpg&id={id}",
        )


class DockerEnvironment(BaseEnvironment):
    _id: str
    _container: Optional[Container]
    _video_devices: VideoDeviceManager
    _host_network: Optional[int]
    _image_exists: Optional[bool]
    _data_path: Optional[Path]

    def __init__(
        self,
        id: str,
        image_id: str,
        host_network: bool,
    ):
        self._id = id
        self._image_id = image_id
        self._container = None
        self._video_devices = get_video_device_manager()
        self._host_network = host_network
        self._image_exists = None
        self._data_path = EXPERIENCE_DATA_PATH / image_id.replace(":", "_").replace(
            "/", "_"
        )
        self._data_path.mkdir(parents=True, exist_ok=True)

    def start(self, last_environment=None):
        # For now, we will expose only our center webcam as /dev/video0 within
        # containers
        video_devices = [
            f"{path}:/dev/video{name}:rw"
            for name, path in self._video_devices.devices.items()
        ]
        network_config = {"network_mode": "host"} if self._host_network else {}
        self._container = docker_client.containers.run(
            self._image_id,
            detach=True,
            volumes={
                "/tmp/.X11-unix": {"bind": "/tmp/.X11-unix", "mode": "rw"},
                str(self._data_path): {"bind": "/localdata", "mode": "rw"},
            },
            remove=True,
            stdout=False,
            environment=[
                f"DISPLAY={os.environ['DISPLAY']}",
                "NVIDIA_DRIVER_CAPABILITIES=all",
                f"FT_MSG_URL={urllib.parse.urljoin(BASE_MESSAGING_URL, self._id)}",
            ],
            device_requests=[
                DeviceRequest(driver="nvidia", count=-1, capabilities=[["gpu"]])
            ],
            devices=[*video_devices],
            # Chromium needs these to work, per @wingated
            cap_add=["SYS_ADMIN"],
            shm_size="1g",
            **network_config,
        )

    def _kill_container_checked(self, container: Container):
        if container.status not in ["running", "created"]:
            return

        try:
            self._container.kill()
        except docker.errors.APIError as e:
            logger.error(
                f"Docker errored while trying to kill container for app ID {self._id}:"
            )
            logger.exception(e)

    async def shutdown_by_tag(self):
        if self._container is None:
            return

        matching_containers = docker_client.containers.list(
            filters={"ancestor": self._image_id, "status": "running"}
        )
        if not matching_containers:
            return
        logger.warning(
            f"Found live containers with image ID {self._image_id}, attempting to kill in 1s"
        )
        await asyncio.sleep(1)
        map(self._kill_container_checked, matching_containers)

    async def stop(self, next_environment=None):
        self._kill_container_checked(self._container)
        await self.shutdown_by_tag()
        self._container = None

    @property
    def available(self) -> bool:
        if not docker_client:
            return False
        if self._image_exists is not None:
            return self._image_exists

        try:
            docker_client.images.get(self._image_id)
            self._image_exists = True
            return True
        except docker.errors.ImageNotFound:
            logger.info(
                f"Couldn't find Docker image '{self._image_id}' locally, attempting to pull..."
            )
            try:
                docker_client.images.pull(self._image_id)
            except docker.errors.NotFound:
                logger.warning(
                    f"Couldn't find Docker image '{self._image_id}', experience will be disabled"
                )
                self._image_exists = False
                return False

            self._image_exists = True
            return True


class CaptureEnvironment(BaseEnvironment):
    _id: str
    _path: str
    _capture_process: Optional[subprocess.Popen]
    _api: CaptureApi

    def __init__(
        self,
        id: str,
        path: str,
    ):
        self._id = id
        self._path = path
        self._api = get_capture_api()

    async def _start_capture_api(self):
        await self._api.set_current_experience(self._id, self._path)

    async def _stop_capture_api(self):
        await self._api.set_current_experience(None)

    async def _start_capture_process(self):
        self._capture_process = subprocess.Popen([CAPTURE_SHELL_PATH])

    async def _stop_capture_process(self):
        if not self._capture_process:
            return

        await mercilessly_kill_process(self._capture_process)

    async def start(self, last_environment=None):
        await self._start_capture_api()
        await self._start_capture_process()

    async def stop(self, next_environment=None):
        await self._stop_capture_process()
        if not next_environment or not isinstance(next_environment, CaptureEnvironment):
            await self._stop_capture_api()

    @property
    def available(self) -> bool:
        # TODO: Consider whether we need some availability signal for Windows apps
        return True
