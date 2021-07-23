import json
from datetime import datetime
from typing import Dict, Optional

import pydantic
import pydantic.json
from pydantic import BaseModel

from .constants import BASE_DATA_PATH, EXPERIENCES_PATH

_RELEASES_DIR_NAME = "releases"
_DATA_FILENAME = "data.json"


class _Release(BaseModel):
    hash: str
    created: datetime


class _ExperienceReleases(BaseModel):
    current: Optional[str]
    releases: Dict[str, _Release]


class ReleaseManager:
    _release_data: Dict[str, _ExperienceReleases]

    # TODO: Figure out how we limit # of older releases kept per app--maybe by size?
    def __init__(self):
        self._releases_path = BASE_DATA_PATH / _RELEASES_DIR_NAME
        self._linked_path = EXPERIENCES_PATH / "apps"
        self._data_path = self._releases_path / _DATA_FILENAME

        self._load_releases_data()

    @property
    def path(self):
        return self._linked_path

    @property
    def data(self):
        return self._release_data

    def _load_releases_data(self):
        if not self._data_path.exists():
            self._release_data = {}
            return

        with open(self._data_path) as data_file:
            self._release_data = {
                id: _ExperienceReleases.parse_obj(data)
                for id, data in json.load(data_file).items()
            }

    def _save_release_data(self):
        with open(self._data_path, "w") as data_file:
            json.dump(
                {id: data for id, data in self._release_data.items()},
                data_file,
                default=pydantic.json.pydantic_encoder,
            )

    def create_release(self, id: str, hash: str):
        # TODO: This is probably the right place to clean up old releases
        if id not in self._release_data:
            self._release_data[id] = _ExperienceReleases(current=None, releases={})

        # TODO: We don't check if there's an existing release here--might be a good
        #  idea?
        self._release_data[id].releases[hash] = _Release(
            hash=hash, created=datetime.now()
        )
        self._save_release_data()

        release_path = self.path_for_release(id, hash)
        if not release_path.exists():
            release_path.mkdir(parents=True)

        return release_path

    def set_release(self, id: str, hash: str):
        if not self.release_exists(id, hash):
            raise FileNotFoundError(f"Release path does not exist: {id}/{hash}")

        if not self._linked_path.exists():
            self._linked_path.mkdir(parents=True)

        linked_path = self._linked_path / id
        if linked_path.exists():
            linked_path.unlink()

        linked_path.symlink_to(
            self.path_for_release(id, hash), target_is_directory=True
        )

        self._release_data[id].current = hash
        self._save_release_data()

    def release_exists(self, id, hash) -> bool:
        return (
            id in self._release_data
            and hash in self._release_data[id].releases
            and self.path_for_release(id, hash).exists()
        )

    def path_for_release(self, id, hash):
        return self._releases_path / id / hash
