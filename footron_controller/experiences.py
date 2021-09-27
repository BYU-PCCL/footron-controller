import abc
import asyncio
from dataclasses import dataclass
import json
import operator
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Type, Optional

from pydantic import BaseModel, PrivateAttr, validator
import footron_protocol as protocol

from .data.wm import DisplayLayout
from .environments import (
    BaseEnvironment,
    DockerEnvironment,
    WebEnvironment,
    VideoEnvironment,
)
from .constants import BASE_DATA_PATH, EXPERIENCES_PATH, JsonDict

_DEFAULT_LIFETIME = 60
_FIELD_TYPE = "type"


class ExperienceType(str, Enum):
    Docker = "docker"
    Web = "web"
    Video = "video"


class BaseExperience(BaseModel, abc.ABC):
    type: ExperienceType
    id: str
    title: str
    description: Optional[str]
    long_description: Optional[str]
    artist: Optional[str]
    lifetime: int = _DEFAULT_LIFETIME
    layout: DisplayLayout = DisplayLayout.Wide
    unlisted: bool = False
    queueable: bool = True
    load_time: Optional[int] = None
    path: Path
    _environment: BaseEnvironment = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._environment = self._create_environment()

    @property
    def available(self) -> bool:
        return self._environment.available

    @validator("long_description")
    def long_description_requires_description(cls, value, values):
        if "description" not in values or values["description"] is None:
            raise ValueError(
                "'description' must be set for 'long_description' to be set"
            )
        return value

    async def start(self):
        if asyncio.iscoroutinefunction(self._environment.start):
            await self._environment.start()
        else:
            self._environment.start()

    async def stop(self, after: Optional[int] = None):
        if after:
            await asyncio.sleep(after)
        if asyncio.iscoroutinefunction(self._environment.stop):
            await self._environment.stop()
        else:
            self._environment.stop()

    @abc.abstractmethod
    def _create_environment(self) -> BaseEnvironment:
        ...


class DockerExperience(BaseExperience):
    type = ExperienceType.Docker
    image_id: str
    host_network: bool = False
    layout = DisplayLayout.Wide

    def _create_environment(self) -> DockerEnvironment:
        return DockerEnvironment(self.id, self.image_id, self.host_network)

    async def attempt_cleanup(self):
        await self._environment.shutdown_by_tag()


class WebExperience(BaseExperience):
    type = ExperienceType.Web
    url: Optional[str]
    layout = DisplayLayout.Wide

    def _create_environment(self) -> WebEnvironment:
        return WebEnvironment(self.id, self.path / "static", self.url)


class VideoExperience(BaseExperience):
    type = ExperienceType.Video
    layout = DisplayLayout.Hd
    filename: str
    scrubbing: bool = False

    def _create_environment(self) -> VideoEnvironment:
        return VideoEnvironment(self.id, self.path, self.filename)


class Lock:
    status: protocol.Lock
    last_update: Optional[datetime]

    def __init__(self, status: protocol.Lock, last_update: Optional[datetime]):
        self.status = status
        self.last_update = last_update


class CurrentExperience:
    _experience: BaseExperience
    _start_time: datetime
    _lock: Lock
    end_time: Optional[datetime]
    last_interaction: Optional[datetime]

    def __init__(self, experience: BaseExperience, start_time: datetime):
        self._experience = experience
        self._start_time = start_time
        self._lock = Lock(False, None)
        self.end_time = None
        self.last_interaction = None

    @property
    def id(self):
        return self._experience.id

    @property
    def experience(self):
        return self._experience

    @property
    def start_time(self):
        return self._start_time

    @property
    def lock(self):
        return self._lock

    @lock.setter
    def lock(self, value: protocol.Lock):
        if type(value) != int and type(value) != bool:
            raise ValueError("lock value must be of type int or bool")

        # Setting the value to what it was before doesn't represent
        # an "update," and we don't want to store a new last update
        # time. This is especially true because we use a non-null value
        # in that field as "breaking the seal" on a lock—any time we
        # set and unset a lock, we want to immediately cycle to the next
        # experience.
        if self._lock.status == value:
            return

        self._lock.status = value
        self._lock.last_update = datetime.now()

    async def start(self):
        return await self._experience.start()

    async def stop(self, after: Optional[int] = None):
        return await self._experience.stop(after)

    async def stop_(self):
        return await self._experience.stop()


experience_type_map: Dict[ExperienceType, Type[BaseExperience]] = {
    ExperienceType.Docker: DockerExperience,
    ExperienceType.Web: WebExperience,
    ExperienceType.Video: VideoExperience,
}


def _serialize_experience(data: JsonDict, path: Path) -> BaseExperience:
    if _FIELD_TYPE not in data:
        raise TypeError(f"Experience doesn't contain required field '{_FIELD_TYPE}'")

    if not isinstance(data[_FIELD_TYPE], ExperienceType):
        data[_FIELD_TYPE] = ExperienceType(data[_FIELD_TYPE])

    msg_type: ExperienceType = data[_FIELD_TYPE]

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
    return list(
        filter(
            operator.attrgetter("available"),
            map(_load_experience_at_path, path.iterdir()),
        )
    )

    

def load_experience_grouping(type: dataclass, file_name:str, path=BASE_DATA_PATH):
    file_path = path.joinpath(file_name)

    if not file_path.exists():
        return {}

    with open(file_path) as file:
        data = json.load(file)

    return {id: type(id=id, **value) for id, value in data.items()}
