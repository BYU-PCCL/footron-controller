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

from .data.ports import PortManager, get_port_manager
from .browser_runner import BrowserRunner
from .constants import PACKAGE_STATIC_PATH, BASE_MESSAGING_URL
from .data.video_devices import get_video_device_manager, VideoDeviceManager

docker_client = docker.from_env()

logger = logging.getLogger(__name__)


class EnvironmentInitializationError(Exception):
    pass


class BaseEnvironment(abc.ABC):
    def start(self):
        ...

    def stop(self):
        ...


class WebEnvironment(BaseEnvironment):
    _runner: BrowserRunner

    def __init__(
        self, profile_key: str, path: Union[str, Path], url: Optional[str] = "/"
    ):
        self._static_path = Path(path) if not isinstance(path, Path) else path

        if not self._static_path.exists():
            raise EnvironmentInitializationError(
                f"Couldn't load static path for experience {profile_key}"
                f" at path {self._static_path.absolute()}"
            )

        self._runner = BrowserRunner(profile_key, {"/": path}, url)

    async def start(self):
        await self._runner.start()

    async def stop(self):
        await self._runner.stop()


class VideoEnvironment(BaseEnvironment):
    _runner: BrowserRunner

    def __init__(self, id: str, path: Union[str, Path], video_filename: str):
        self._static_path = Path(path) if not isinstance(path, Path) else path

        if not self._static_path.exists():
            raise EnvironmentInitializationError(
                f"Couldn't load static path for video {id}"
                f" at path {self._static_path.absolute()}"
            )

        self._runner = BrowserRunner(
            id,
            {"/video": path, "/": PACKAGE_STATIC_PATH / "video-player"},
            f"/?url=/video/{video_filename}&posterUrl=/video/poster.jpg&id={id}",
        )

    async def start(self):
        await self._runner.start()

    async def stop(self):
        await self._runner.stop()


class DockerEnvironment(BaseEnvironment):
    _id: str
    _container: Optional[Container]
    _ports: PortManager
    _video_devices: VideoDeviceManager
    _http_port: Optional[int]
    _zmq_port: Optional[int]
    _host_network: Optional[int]

    def __init__(
        self,
        id: str,
        image_id,
        host_network: bool,
    ):
        self._id = id
        self._image_id = image_id
        self._container = None
        self._ports = get_port_manager()
        self._video_devices = get_video_device_manager()
        self._http_port = None
        self._zmq_port = None
        self._host_network = host_network

    def start(self):
        self._http_port = self._ports.reserve_port()
        self._zmq_port = self._ports.reserve_port()
        # For now, we will expose only a "center" video device, accessible as
        # /dev/videocenter within containers
        video_devices = [
            f"{path}:/dev/video{name}:rw"
            for name, path in self._video_devices.devices.items()
        ]
        network_config = {"network_device": "host"} if self._host_network else {}
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
            # TODO: Figure out how to expose ROS2 ports
            ports={"80": self._http_port, "5555": self._zmq_port},
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

        self._ports.release_port(self._http_port)
        self._ports.release_port(self._zmq_port)
