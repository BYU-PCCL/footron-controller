import abc
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, Type, Optional

from pydantic import BaseModel, PrivateAttr

from .environments import (
    BaseEnvironment,
    DockerEnvironment,
    WebEnvironment,
    VideoEnvironment,
)
from .constants import EXPERIENCES_PATH, JsonDict

FIELD_MSG_TYPE = "type"


class ExperienceType(str, Enum):
    DOCKER = "docker"
    WEB = "web"
    VIDEO = "video"


class BaseExperience(BaseModel, abc.ABC):
    type: ExperienceType
    id: str
    title: str
    description: str
    artist: Optional[str]
    collection: Optional[str]
    lifetime: Optional[int]
    path: Path
    _environment: BaseEnvironment = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._environment = self.create_environment()

    async def start(self):
        await self._environment.start()

    async def stop(self):
        await self._environment.stop()

    @abc.abstractmethod
    def create_environment(self) -> BaseEnvironment:
        ...


class DockerExperience(BaseExperience):
    type = ExperienceType.DOCKER
    image_id: str

    def create_environment(self) -> DockerEnvironment:
        return DockerEnvironment(self.image_id)


class WebExperience(BaseExperience):
    type = ExperienceType.WEB
    url: Optional[str]

    def create_environment(self) -> WebEnvironment:
        return WebEnvironment(self.id, self.path / "static", self.url)


class VideoExperience(BaseExperience):
    type = ExperienceType.VIDEO
    filename: str

    def create_environment(self) -> VideoEnvironment:
        return VideoEnvironment(self.id, self.path, self.filename)


experience_type_map: Dict[ExperienceType, Type[BaseExperience]] = {
    ExperienceType.DOCKER: DockerExperience,
    ExperienceType.WEB: WebExperience,
    ExperienceType.VIDEO: VideoExperience,
}


def _serialize_experience(data: JsonDict, path: Path) -> BaseExperience:
    if FIELD_MSG_TYPE not in data:
        raise TypeError(f"Experience doesn't contain required field '{FIELD_MSG_TYPE}'")

    if not isinstance(data[FIELD_MSG_TYPE], ExperienceType):
        data[FIELD_MSG_TYPE] = ExperienceType(data[FIELD_MSG_TYPE])

    msg_type: ExperienceType = data[FIELD_MSG_TYPE]

    return experience_type_map[msg_type](**data, path=path)


def _load_config_at_path(path: Path):
    if not path.exists():
        return

    try:
        with open(path) as config_path:
            config = json.load(config_path)
    except ValueError:
        print(
            f"Failed to parse config at path '{path.absolute()}'",
            file=sys.stderr,
        )
        return

    return config


def _load_experience_at_path(path: Path) -> Optional[BaseExperience]:
    if not path.is_dir():
        return

    return _serialize_experience(
        _load_config_at_path(path.joinpath("config.json")), path
    )


def load_experiences_fs(path=EXPERIENCES_PATH):
    if not path.exists():
        path.mkdir(parents=True)

    return list(map(_load_experience_at_path, path.iterdir()))