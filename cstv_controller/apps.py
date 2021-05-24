import abc
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Type

_BASE_APPS_PATH = Path("/opt/cstv/apps")
_JSON_MAPPINGS = {}


class AppInitError(Exception):
    pass


class BaseApp(abc.ABC):
    def __init__(
        self, path, id, app_type, title, description, show_sidebar=True, artist=None
    ):

        # TODO: Add user control component (though that may need to be done statically beforehand if we want to work
        #  with the "compiled" JS)

        self.path = Path(path)
        self.id = id
        self.app_type = app_type
        self.title = title
        self.description = description
        self.artist = artist
        self.show_sidebar = show_sidebar

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self):
        ...

    def serialize(self):
        return {
            "id": self.id,
            "type": self.app_type,
            "title": self.title,
            "description": self.description,
            "artist": self.artist,
            "show_sidebar": self.show_sidebar,
        }

    @classmethod
    def deserialize(cls, data, path):
        return cls(**_map_json_to_app_object_fields(data), path=path)


class WebApp(BaseApp):
    process: Optional[subprocess.Popen]

    def __init__(
        self,
        path,
        id,
        title,
        description,
        show_sidebar=True,
        artist=None,
    ):
        BaseApp.__init__(
            self, path, id, "web", title, description, show_sidebar, artist
        )
        self.static_path = self.path.joinpath("static")

        if not self.static_path.exists() or not self.static_path.is_dir():
            raise AppInitError(
                f"Couldn't load static path for app {self.id} at path {self.path.absolute()}"
            )

        self.process = None

    def start(self):
        command = [
            "google-chrome",
            f'--app="file://{self.static_path}"',
            f"--user-data-dir=/tmp/cstv-chrome-data/{self.id}",
            "--no-first-run",
        ]
        self.process = subprocess.Popen(command)

    def stop(self):
        self.process.terminate()

    def serialize(self):
        return super(self).serialize()


APP_TYPES: Dict[str, Type[BaseApp]] = {"web": WebApp}


def _create_app_object(config: Dict, path: Path):
    app_type = config["type"]
    try:
        del config["type"]
        app = APP_TYPES[app_type].deserialize(config, path)
    except AppInitError as e:
        print(
            f"Failed to load app at {path.absolute()} with error:\n{e}\n",
            file=sys.stderr,
        )
        return
    return app


def _map_json_to_app_object_fields(data):
    for (json_field, object_field) in _JSON_MAPPINGS.items():
        data[object_field] = data[json_field]
        del data[json_field]
    return data


def _load_app_at_path(path: Path) -> Optional[BaseApp]:
    if not path.is_dir():
        return

    config_path = path.joinpath("config.json")
    # TODO: Add thumbnail

    if not config_path.exists():
        return

    try:
        with open(config_path) as config_path:
            app_config = json.load(config_path)
    except ValueError as e:
        print(
            f"Failed to parse config for app at '{path.absolute()}'",
            file=sys.stderr,
        )
        return

    return _create_app_object(app_config, path)


def load_apps_from_fs(path=_BASE_APPS_PATH) -> List[BaseApp]:
    if not path.exists():
        path.mkdir(parents=True)

    return list(map(_load_app_at_path, path.iterdir()))
