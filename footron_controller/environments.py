import abc
import os
from pathlib import Path
from typing import Optional, Union
import docker
import urllib.parse

from docker.models.containers import Container
from docker.types import DeviceRequest

from .ports import PortManager, get_port_manager
from .browser_runner import BrowserRunner
from .constants import PACKAGE_STATIC_PATH, BASE_MESSAGING_URL

docker_client = docker.from_env()


class EnvironmentInitializationError(Exception):
    pass


class BaseEnvironment(abc.ABC):
    async def start(self):
        ...

    async def stop(self):
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
                f"Couldn't load static path for video {self.id}"
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
    _http_port: Optional[int]
    _zmq_port: Optional[int]

    def __init__(
        self,
        id: str,
        image_id,
    ):
        self._id = id
        self._image_id = image_id
        self._container = None
        self._ports = get_port_manager()
        self._http_port = None
        self._zmq_port = None

    async def start(self):
        self._http_port = self._ports.reserve_port()
        self._zmq_port = self._ports.reserve_port()
        self._container = docker_client.containers.run(
            self._image_id,
            detach=True,
            volumes={"/tmp/.X11-unix": {"bind": "/tmp/.X11-unix", "mode": "rw"}},
            remove=True,
            stdout=False,
            environment=[
                f"DISPLAY={os.environ['DISPLAY']}",
                "NVIDIA_DRIVER_CAPABILITIES=all",
                f"FT_MSG_URL={urllib.parse.urljoin(BASE_MESSAGING_URL, self._id)}"
            ],
            device_requests=[
                DeviceRequest(driver="nvidia", count=-1, capabilities=[["gpu"]])
            ],
            # Chromium needs these to work, per @wingated
            cap_add=["SYS_ADMIN"],
            shm_size="1g",
            # TODO: Figure out how to expose ROS2 ports
            ports={"80": self._http_port, "5555": self._zmq_port},
        )

    async def stop(self):
        if self._container.status in ["running", "created"]:
            self._container.kill()

        self._ports.release_port(self._http_port)
        self._ports.release_port(self._zmq_port)
