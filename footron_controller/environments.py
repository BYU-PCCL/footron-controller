import abc
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Union
import docker
import docker.errors
import urllib.parse

from docker.models.containers import Container
from docker.types import DeviceRequest

from .browser_runner import BrowserRunner
from .constants import PACKAGE_STATIC_PATH, BASE_MESSAGING_URL
from .data.video_devices import get_video_device_manager, VideoDeviceManager

logger = logging.getLogger(__name__)

try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    docker_client = None
    logger.warning("Couldn't create Docker client, Docker experiences will be disabled")


class EnvironmentInitializationError(Exception):
    pass


class BaseEnvironment(abc.ABC):
    def start(self):
        ...

    def stop(self):
        ...

    @property
    @abc.abstractmethod
    def available(self) -> bool:
        ...


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

    async def start(self):
        await self._runner.start()

    async def stop(self):
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
        super(_BaseWebEnvironmentMixin).__init__(id, path, {"/": path}, url)


class VideoEnvironment(_BaseWebEnvironmentMixin, BaseEnvironment):
    def __init__(self, id: str, path: Union[str, Path], video_filename: str):
        super(_BaseWebEnvironmentMixin).__init__(
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

    def start(self):
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
            volumes={"/tmp/.X11-unix": {"bind": "/tmp/.X11-unix", "mode": "rw"}},
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

    async def stop(self):
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
                docker_client.images.pull(id)
            except docker.errors.NotFound:
                logger.warning(
                    f"Couldn't find Docker image '{self._image_id}', experience will be disabled"
                )
                self._image_exists = False
                return False

            self._image_exists = True
            return True
