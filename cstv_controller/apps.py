import abc
import json
import multiprocessing
import socketserver
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Optional, List, Dict, Type
from http import server

_BASE_APPS_PATH = Path("/opt/cstv/apps")
_JSON_MAPPINGS = {}

_DEFAULT_LIFETIME = 60

bound_ports = list()



class AppInitError(Exception):
    pass


class BaseApp(abc.ABC):



    def __init__(
        self, path, id, app_type, title, description, show_sidebar=True, artist=None, lifetime=_DEFAULT_LIFETIME
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
        self.lifetime = lifetime

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
            "lifetime": self.lifetime,
        }

    @classmethod
    def deserialize(cls, data, path):
        return cls(**_map_json_to_app_object_fields(data), path=path)


class WebApp(BaseApp):
    _process: Optional[subprocess.Popen]
    _server_process: Optional[multiprocessing.Process]

    def __init__(
        self,
        path,
        id,
        title,
        description,
        show_sidebar=True,
        artist=None,
        lifetime=_DEFAULT_LIFETIME,
    ):
        BaseApp.__init__(
            self, path, id, "web", title, description, show_sidebar, artist, lifetime
        )
        self._static_path = self.path.joinpath("static")

        if not self._static_path.exists():
            raise AppInitError(
                f"Couldn't load static path for app {self.id} at path {self.path.absolute()}"
            )

        self._port = None
        self._process = None
        self._server_process = None

    def _reserve_port(self):
        # TODO: Consider actually checking if another application has reserved this port on the OS. Not sure if this
        #  would be a problem since we have a lot of control over the OS
        if not len(bound_ports):
            self._port = 8085
        else:
            self._port = bound_ports[-1] + 1

        bound_ports.append(self._port)

    def _release_port(self):
        bound_ports.remove(self._port)

    def _server_process_loop(self):
        with socketserver.TCPServer(
            ("", self._port),
            partial(server.SimpleHTTPRequestHandler, directory=str(self._static_path)),
        ) as httpd:
            httpd.serve_forever()

    def _start_server(self):
        self._reserve_port()
        self._server_process = multiprocessing.Process(
            target=self._server_process_loop
        )
        self._server_process.start()

    def _start_browser(self):
        command = [
            "google-chrome",
            f"--app=http://localhost:{self._port}",
            f"--user-data-dir=/tmp/cstv-chrome-data/{self.id}",
            "--no-first-run",
        ]
        self._process = subprocess.Popen(command)

    def start(self):
        self._start_server()
        self._start_browser()

    def stop(self):
        self._server_process.terminate()
        self._process.terminate()

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
